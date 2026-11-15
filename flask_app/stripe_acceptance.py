"""Bounded real sandbox Checkout journey; never accepts a live key."""
import hashlib
import json
import os
import re
import tempfile
import time
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from playwright.sync_api import sync_playwright
from app import create_app
from learning.generate import compile_products


def main():
    key=os.environ.get('EFL_STRIPE_TEST_SECRET_KEY','').strip()
    assert re.fullmatch(r'(sk|rk)_test_[A-Za-z0-9]+',key), 'Sandbox key required'
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        products=compile_products(root/'products')
        (root/'manifest.json').write_text('{}')
        app=create_app({'TESTING':True,'SECRET_KEY':'sandbox-only','PRODUCTS_DIR':str(root/'products'),
                        'MANIFEST_PATH':str(root/'manifest.json'),'STRIPE_SECRET_KEY':key,'EFL_SALES_ENABLED':True})
        client=app.test_client()
        product=next(p for p in products if not p.get('archived'))
        client.get('/en/resources/'+product['id']+'/')
        with client.session_transaction() as session: csrf=session['csrf']
        result=client.post('/en/checkout/'+product['id']+'/',data={'csrf':csrf,'digital_consent':'yes'})
        assert result.status_code==303, 'Checkout creation failed'
        checkout_url=result.location
        assert urlsplit(checkout_url).hostname=='checkout.stripe.com'
        callback=[]
        with sync_playwright() as pw:
            browser=pw.chromium.launch()
            page=browser.new_page()
            def complete(route):
                callback.append(route.request.url)
                route.fulfill(status=200,content_type='text/plain',body='Sandbox return captured')
            page.route('https://englishasaforeignlanguage.com/**/purchase/success/**',complete)
            page.route('https://englishasaforeignlanguage.com/purchase/success/**',complete)
            def checkout_control(selector=None, optional=False, pay_button=False):
                """Checkout can place its visible controls in Stripe-owned frames."""
                deadline=time.monotonic()+(2 if optional else 30)
                while time.monotonic()<deadline:
                    for frame in page.frames:
                        if urlsplit(frame.url).hostname not in {'checkout.stripe.com','js.stripe.com'}:
                            continue
                        control=(frame.get_by_role('button',name=re.compile(r'^Pay(?:\s+(?:£|GBP|\d).*)?$',re.I))
                                 if pay_button else frame.locator(':is('+selector+'):visible'))
                        if control.count() and control.first.is_visible(): return control.first
                    page.wait_for_timeout(100)
                if optional: return None
                raise RuntimeError('Required sandbox Checkout control was not available')
            stage='load_checkout'
            response=None
            try:
                response=page.goto(checkout_url,wait_until='domcontentloaded')
                stage='fill_email'
                checkout_control('input[type="email"],input[autocomplete~="email"]').fill('efl-acceptance@example.com')
                stage='fill_card'
                checkout_control('input[autocomplete~="cc-number"],input[name="cardNumber"],input[name="number"]').fill('4242424242424242')
                checkout_control('input[autocomplete~="cc-exp"],input[name="cardExpiry"],input[name="expiry"]').fill('1234')
                checkout_control('input[autocomplete~="cc-csc"],input[name="cardCvc"],input[name="cvc"]').fill('123')
                name=checkout_control('input[autocomplete~="cc-name"],input[autocomplete~="name"],input[name="billingName"]',optional=True)
                if name: name.fill('EFL Sandbox Test')
                country=checkout_control('select[autocomplete~="country"],select[name="country"],select[name="billingCountry"]',optional=True)
                if country: country.select_option('GB')
                postal=checkout_control('input[autocomplete~="postal-code"],input[name="billingPostalCode"]',optional=True)
                if postal: postal.fill('SW1A 1AA')
                stage='submit_checkout'
                checkout_control(pay_button=True).click()
                stage='wait_for_success_return'
                page.wait_for_url('https://englishasaforeignlanguage.com/**',timeout=60000)
                assert callback, 'No successful Checkout return'
            except Exception as error:
                # Report browser state without HTML, field values, keys or session URLs.
                def host_category(url):
                    host=urlsplit(url).hostname
                    expected={'checkout.stripe.com','js.stripe.com','hooks.stripe.com',
                              'englishasaforeignlanguage.com'}
                    if host in expected: return host
                    return 'other' if host else 'none'
                diagnostic={'stage':stage,'error_type':type(error).__name__,
                            'http_status':response.status if response else None,
                            'page_host':host_category(page.url),'frames':[]}
                for frame in page.frames:
                    try:
                        state=frame.evaluate('''() => {
                            const text=(document.body?.innerText || '').toLowerCase();
                            const phrases=['expired','not found','something went wrong','enable javascript',
                                           'checking your browser','verify you are human','access denied','captcha'];
                            const fields=['email','cardNumber','cardExpiry','cardCvc','billingName','billingCountry','billingPostalCode'];
                            return {readyState:document.readyState,
                                    control_count:document.querySelectorAll('input,select').length,
                                    expected_fields:fields.filter(id=>document.getElementById(id)),
                                    messages:phrases.filter(phrase=>text.includes(phrase))};
                        }''')
                        diagnostic['frames'].append({'host':host_category(frame.url),**state})
                    except Exception as frame_error:
                        diagnostic['frames'].append({'error_type':type(frame_error).__name__})
                print('sandbox_checkout_diagnostic='+json.dumps(diagnostic))
                raise RuntimeError('Sandbox browser checkout did not complete') from None
            finally: browser.close()
        sid=parse_qs(urlsplit(callback[0]).query)['session_id'][0]
        assert sid.startswith('cs_test_')
        result=client.get('/purchase/download/?session_id='+sid)
        assert result.status_code==200, 'Paid download verification failed'
        assert hashlib.sha256(result.data).hexdigest()==product['sha256'], 'Download hash mismatch'
        result.close()
        assert client.get('/purchase/download/?session_id=forged').status_code==403
        print('REAL_SANDBOX_PAID_CHECKOUT_AND_DOWNLOAD=PASS')

if __name__=='__main__': main()
