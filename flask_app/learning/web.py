from __future__ import annotations
import hashlib
import hmac
import json
import os
import re
import secrets
from html import escape
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from flask import Blueprint, abort, current_app, g, redirect, render_template, request, send_file, session, url_for
from .catalog import LANGUAGES, LEVELS, LEVEL_LABELS, UI, direction, text_html
from .bank import questions_for

bp = Blueprint('learning', __name__, template_folder='templates', static_folder='assets', static_url_path='/assets/learning')
ORIGIN = 'https://englishasaforeignlanguage.com'


def safe_next(value):
    # Reject browser-normalised network paths as well as explicit external URLs.
    if not value or not value.startswith('/') or value.startswith('//') or '\\' in value or any(ord(c)<32 for c in value):
        return '/'
    parsed = urlsplit(value)
    return parsed.path if not parsed.netloc and not parsed.scheme else '/'


def catalog():
    try:
        return json.loads((Path(current_app.config['PRODUCTS_DIR'])/'catalog.json').read_text())
    except (OSError, ValueError):
        return []


def get_product(product_id):
    return next((p for p in catalog() if p['id'] == product_id), None)


def ready():
    # Explicit gate stays closed until the operator verifies live checkout and delivery.
    return bool(current_app.config.get('EFL_SALES_ENABLED') and current_app.config.get('STRIPE_SECRET_KEY'))


def page(view, title=None, **kwargs):
    lang = g.efl_language
    if 'csrf' not in session:
        session['csrf'] = secrets.token_urlsafe(32)
    return render_template('learning.html', view=view, title=title or UI[lang]['home'], t=UI[lang], lang=lang, direction=direction, languages=LANGUAGES, levels=LEVELS, level_labels=LEVEL_LABELS, csrf=session['csrf'], checkout_ready=ready(), **kwargs)


def valid_post():
    origin = request.headers.get('Origin')
    if origin and urlsplit(origin).netloc != request.host:
        return False
    value = request.form.get('csrf', '')
    return bool(value and session.get('csrf') and hmac.compare_digest(value, session['csrf']))


@bp.get('/languages/')
def languages():
    return page('languages', next_path=safe_next(request.args.get('next', '/')))


@bp.get('/language/<code>/')
def set_language(code):
    if code not in LANGUAGES:
        abort(404)
    response = redirect(safe_next(request.args.get('next')), code=303)
    response.set_cookie('efl_language', code, max_age=31536000, secure=not current_app.testing, httponly=True, samesite='Lax')
    response.headers['Cache-Control'] = 'no-store'
    return response


@bp.get('/study/')
def home():
    return page('home')


@bp.get('/resources/')
@bp.get('/shop/')
def shop():
    return page('shop', title=UI[g.efl_language]['shop'], products=[p for p in catalog() if not p.get('archived')])


@bp.get('/resources/<product_id>/')
def product(product_id):
    p = get_product(product_id)
    if not p:
        abort(404)
    if p.get('archived'):
        latest = next((x for x in catalog() if x['level']==p['level'] and not x.get('archived')), None)
        if latest:
            return redirect(url_for('learning.product', product_id=latest['id']), 302)
    qs = questions_for(p['level'])
    return page('product', product=p, level=p['level'], questions=[qs[i] for i in (0,4,8)], title=f'{p["level"]} · {UI[g.efl_language]["pack"]}')


@bp.get('/practice/<level>/')
def practice(level):
    level=level.upper()
    if level not in LEVELS:
        abort(404)
    p=next((p for p in catalog() if p['level']==level), None)
    if not p:
        abort(503)
    qs=questions_for(level)
    return page('practice', level=level, product=p, questions=[qs[i] for i in (0,4,8)], title=f'{level} · {UI[g.efl_language]["practice"]}')


def test_questions():
    # Separate from the free samples: four items from each level.
    return [questions_for(level)[i] for level in LEVELS for i in (1,5,9,11)]


@bp.route('/english-level-test/', methods=['GET','POST'])
def level_test():
    qs=test_questions()
    t=UI[g.efl_language]
    if request.method=='GET':
        return page('test', title=t['level_test'], questions=qs)
    if not valid_post():
        abort(403)
    try:
        selected = {q['id']:int(request.form[q['id']]) for q in qs}
        if any(not 0 <= selected[q['id']] < len(q['options']) for q in qs):
            raise ValueError()
    except (KeyError, ValueError):
        return page('test', title=t['level_test'], questions=qs, error=t['required']), 422
    results = {q['id']:selected[q['id']]==q['answer'] for q in qs}
    # Recommend the first block with fewer than 3/4 correct, avoiding a high
    # aggregate concealing foundational gaps. This is not a CEFR certification.
    level='C2'
    for candidate in LEVELS:
        block=qs[LEVELS.index(candidate)*4:LEVELS.index(candidate)*4+4]
        if sum(results[q['id']] for q in block)<3:
            level=candidate
            break
    return page('result', title=t['result'], questions=qs, results=results, score=sum(results.values()), level=level)


@bp.get('/purchase-terms/')
def terms():
    return page('terms')


def stripe_api(path, data=None, idempotency=None):
    secret=current_app.config.get('STRIPE_SECRET_KEY')
    if not secret:
        raise ValueError('Payments not configured')
    headers={'Authorization':f'Bearer {secret}','Stripe-Version':'2024-06-20'}
    if idempotency:
        headers['Idempotency-Key']=idempotency
    encoded=urlencode(data).encode() if data is not None else None
    req=Request('https://api.stripe.com/v1/'+path, data=encoded, headers=headers)
    with urlopen(req, timeout=15) as response:
        return json.load(response)


@bp.post('/checkout/<product_id>/')
def checkout(product_id):
    p=get_product(product_id)
    if not p:
        abort(404)
    if p.get('archived'):
        abort(404)
    if not valid_post() or request.form.get('digital_consent')!='yes':
        abort(403)
    if not ready():
        return page('error', title=UI[g.efl_language]['shop'], error=UI[g.efl_language]['unavailable']),503
    lang=g.efl_language
    data={
        'mode':'payment','payment_method_types[0]':'card',
        'client_reference_id':p['id'], 'metadata[site]':'efl-by-level',
        'metadata[product_id]':p['id'], 'metadata[edition_sha256]':p['sha256'],
        'metadata[digital_consent]':'immediate-access-v1', 'metadata[language]':lang,
        'line_items[0][price_data][currency]':'gbp',
        'line_items[0][price_data][unit_amount]':str(p['price_pence']),
        'line_items[0][price_data][product_data][name]':f'EFL by Level {p["level"]} Practice Pack — Edition {p["version"]}',
        'line_items[0][price_data][product_data][description]':UI[lang]['formats'][:500],
        'line_items[0][quantity]':'1',
        'success_url':ORIGIN+'/purchase/success/?session_id={CHECKOUT_SESSION_ID}&lang='+lang,
        'cancel_url':ORIGIN+'/resources/'+p['id']+'/?lang='+lang,
        'locale':{'zh-Hans':'zh','zh-Hant':'zh-TW'}.get(lang, lang if lang in ('en','es','fr','pl') else 'auto'),
    }
    # Repeated clicks return the same checkout session for this browser/product.
    key='checkout_'+p['id']
    if key not in session:
        session[key]=secrets.token_urlsafe(24)
    try:
        result=stripe_api('checkout/sessions',data,session[key])
        checkout_url=result.get('url','')
        if urlsplit(checkout_url).scheme!='https' or urlsplit(checkout_url).netloc!='checkout.stripe.com':
            raise ValueError('Invalid checkout URL')
        return redirect(checkout_url,303)
    except (OSError, ValueError, TypeError):
        current_app.logger.warning('EFL checkout creation failed')
        return page('error', error=UI[lang]['payment_error']),502


def verify_purchase(session_id):
    if not re.fullmatch(r'cs_(?:test|live)_[A-Za-z0-9]{10,240}',session_id):
        return None
    result=stripe_api('checkout/sessions/'+session_id+'?expand[]=payment_intent.latest_charge')
    metadata=result.get('metadata') or {}
    p=get_product(metadata.get('product_id'))
    intent=result.get('payment_intent') or {}
    charge=intent.get('latest_charge',{}) if isinstance(intent,dict) else {}
    if not isinstance(charge,dict):
        return None
    if not p or result.get('payment_status')!='paid' or result.get('status')!='complete' or result.get('mode')!='payment':
        return None
    if metadata.get('site')!='efl-by-level' or metadata.get('edition_sha256')!=p['sha256'] or metadata.get('digital_consent')!='immediate-access-v1':
        return None
    if result.get('currency')!='gbp' or result.get('amount_total')!=p['price_pence'] or result.get('client_reference_id')!=p['id']:
        return None
    if not charge.get('paid') or charge.get('amount_refunded',0)>0 or charge.get('disputed'):
        return None
    if result.get('livemode') != current_app.config['STRIPE_SECRET_KEY'].startswith('sk_live_'):
        return None
    return p


@bp.get('/purchase/success/')
@bp.get('/purchase/download/')
def purchase():
    session_id=request.args.get('session_id','')
    try:
        p=verify_purchase(session_id)
    except (OSError, ValueError, TypeError):
        p=None
    if not p:
        return page('error', error=UI[g.efl_language]['payment_error']),403
    if request.path.endswith('/download/'):
        file=Path(current_app.config['PRODUCTS_DIR'])/p['filename']
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest()!=p['sha256']:
            abort(503)
        response=send_file(file, as_attachment=True, download_name=p['filename'], mimetype='application/zip')
    else:
        response=current_app.make_response(page('paid', download_url=url_for('learning.purchase', session_id=session_id).replace('/success/','/download/')))
    response.headers['Cache-Control']='private, no-store'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['X-Robots-Tag']='noindex, nofollow'
    return response


def install(app):
    app.config.setdefault('PRODUCTS_DIR',str(Path(app.root_path)/'private_products'))
    app.config.setdefault('STRIPE_SECRET_KEY',os.environ.get('EFL_STRIPE_SECRET_KEY',''))
    app.config.setdefault('EFL_SALES_ENABLED',os.environ.get('EFL_SALES_ENABLED')=='1')
    app.config.update(SESSION_COOKIE_SECURE=not app.testing,SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax')
    app.register_blueprint(bp)
    from markupsafe import Markup
    app.jinja_env.filters['bidi_text'] = lambda value: Markup(text_html(value, g.get('efl_language', 'en')))

    @app.before_request
    def language_context():
        lang=request.args.get('lang') or request.cookies.get('efl_language','en')
        g.efl_language=lang if lang in LANGUAGES else 'en'
        if request.method == 'GET' and re.fullmatch(r'/(study|resources|shop|english-level-test|practice/(a1|a2|b1|b2|c1|c2)|resources/[a-z0-9-]+)', request.path):
            suffix = '?' + urlencode(request.args) if request.args else ''
            return redirect(request.path + '/' + suffix, 308)
        # Block filesystem URLs even on hosts that pass them through Passenger.
        if request.path.startswith(('/private_products/','/learning/edition-lock','/storage/')):
            abort(404)
        if request.method=='GET' and g.efl_language!='en':
            if request.path in ('/','/learn-english/'):
                return home()
            match=re.fullmatch(r'/learn-english/(a1|a2|b1|b2|c1|c2)/?',request.path)
            if match:
                return practice(match.group(1))
        # All English level hubs gain an actual practice entry point in the hook below.

    @app.after_request
    def language_controls(response):
        if response.mimetype!='text/html' or response.direct_passthrough:
            return response
        html=response.get_data(as_text=True)
        if '</body>' not in html:
            return response
        # One vector identity across legacy snapshots and dynamic learning pages.
        brand = '<img class="identity-mark" src="/assets/learning/logo.svg?v=3" alt="" width="42" height="42"><span class="identity-type"><span class="identity-word">efl.</span><span class="identity-caption">by level</span></span>'
        html = re.sub(r'(<a\b[^>]*class="brand(?: brand-footer)?"[^>]*>).*?</a>', lambda m: m.group(1) + brand + '</a>', html, flags=re.DOTALL)
        html = re.sub(r'<link[^>]+rel="(?:shortcut )?icon"[^>]*>', '', html)
        html = html.replace('</head>', '<link rel="icon" type="image/svg+xml" href="/assets/learning/logo.svg?v=3"><link rel="stylesheet" href="/assets/learning/identity.css?v=3"></head>')
        lang=g.get('efl_language','en');t=UI[lang]
        first=request.cookies.get('efl_language') not in LANGUAGES and request.args.get('lang') not in LANGUAGES
        next_path=safe_next(request.path)
        options=''.join(f'<a lang="{code}" dir="{direction(code)}" href="{escape(url_for("learning.set_language",code=code,next=next_path),quote=True)}"'+(' aria-current="true"' if code==lang else '')+f'>{escape(name)}</a>' for code,name in LANGUAGES.items())
        controls=f'<a class="language-trigger" lang="{lang}" dir="{direction(lang)}" data-language-open href="/languages/?{urlencode({"next":next_path})}" aria-haspopup="dialog">{escape(t["language"])} · {escape(LANGUAGES[lang])}</a>'
        dialog=f'<dialog id="language-dialog" class="language-modal" lang="{lang}" dir="{direction(lang)}" aria-labelledby="language-title" data-first-visit="{str(first).lower()}"><button type="button" class="language-close" data-language-close>{escape(t["close"])}</button><div class="picker-brand" aria-hidden="true"><img src="/assets/learning/logo.svg?v=3" alt="" width="28" height="28"><span>efl.</span></div><h2 id="language-title">{escape(t["choose"])}</h2><p>{escape(t["language_help"])}</p><div class="language-options">{options}</div></dialog>'
        if 'class="header-inner"' in html or 'class="shell header-inner"' in html:
            html=html.replace('</nav>', '</nav>'+controls if 'class="site-nav"' in html else controls+'</nav>', 1)
        else:
            html=html.replace('<body>','<body>'+controls,1)
        if '/assets/learning/learning.css' not in html:
            html=html.replace('</head>','<link rel="stylesheet" href="/assets/learning/learning.css?v=1"></head>',1)
        if 'data-fully-localised' not in html:
            mapping={UI['en'][k]:t[k] for k in ('learn','teach','shop','free','about','find_level')}
            for source,target in mapping.items():
                html=html.replace('>'+source+'<','>'+escape(target)+'<')
            notice=''
            if lang!='en':
                notice=f'<p>{escape(t["fallback"])}</p>'
            if request.path in ('/privacy/','/privacy-policy/'):
                notice+='<p>We remember your selected language in an essential first-party cookie for one year. Checkout uses a secure session cookie and Stripe to process payment. Level-check answers are processed to show your result and are not saved to a learner profile.</p>'
            notice+=f'<a href="/study/">{escape(t["learn"])}</a> · <a href="/resources/">{escape(t["shop"])}</a>'
            level_match=re.fullmatch(r'/learn-english/(a1|a2|b1|b2|c1|c2)/?',request.path)
            if level_match:
                notice+=f' · <a href="/practice/{level_match.group(1)}/">{escape(t["practice"])}</a>'
            if request.path != '/' or lang != 'en':
                html=html.replace('<main id="main">','<main id="main"><aside class="shell localisation-notice">'+notice+'</aside>',1)
        html=html.replace('</body>',dialog+'<script defer src="/assets/learning/language.js?v=1"></script></body>')
        html=html.replace('<link rel="stylesheet" href="/assets/learning/identity.css?v=3">','')
        html=html.replace('</head>','<link rel="stylesheet" href="/assets/learning/identity.css?v=3"></head>')
        response.set_data(html)
        response.headers['Cache-Control']='private, no-store'
        response.vary.add('Cookie')
        response.headers['Content-Language']=lang if 'data-fully-localised' in html else 'en'
        if request.args.get('lang') in LANGUAGES:
            response.set_cookie('efl_language', lang, max_age=31536000, secure=not current_app.testing, httponly=True, samesite='Lax')
        return response
