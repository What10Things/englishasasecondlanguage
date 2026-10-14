"""Reproducible product compiler, run on every deployment and weekly on schedule.

No LLM/API calls. Expanding the bank is an editorial action; this compiler does
not claim that reshuffled questions are newly authored educational content.
"""
from __future__ import annotations
import hashlib
import json
from html import escape as e
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
from .bank import BANK, TASKS, questions_for, validate_bank
from .catalog import LANGUAGES, LEVELS, UI

VERSION = '1'
CSS = '''body{font:17px/1.65 system-ui,sans-serif;color:#152d34;max-width:800px;margin:40px auto;padding:0 24px}h1{font-size:36px;line-height:1.15}h2{border-top:2px solid #137d79;padding-top:20px}header{border-bottom:5px solid #137d79}small{color:#43565c}li{margin-bottom:22px;break-inside:avoid}section{margin:24px 0}.space{height:95px;border-bottom:1px solid #aaa}footer{margin-top:32px;font-size:12px}@media print{body{margin:0;max-width:none;font-size:11pt}.answers{break-before:page}h1{font-size:24pt}a{color:inherit}}'''

def document(level, lang, kind):
    t = UI[lang]
    qs = questions_for(level)
    title = f'{level} — {t[kind]}'
    body = f'<header><p>EFL by Level · {level} · {e(LANGUAGES[lang])}</p><h1>{e(title)}</h1><p>{e(t["level_note"])}</p></header>'
    if kind == 'worksheet':
        body += f'<p>{e(t["choose_answer"])}</p><ol>'
        for q in qs:
            body += f'<li lang="en"><strong>{e(q["prompt"])}</strong><p>' + ' &nbsp; '.join(f'{chr(65+i)}. {e(v)}' for i,v in enumerate(q['options'])) + '</p></li>'
        body += f'</ol><h2>{e(t["writing"])}</h2><p>{e(t["write_help"])}</p>'
        body += ''.join(f'<section><p lang="en">{e(task)}</p><div class="space"></div></section>' for task in TASKS[level])
        body += f'<p>{e(t["checklist"])}</p>'
    elif kind == 'answers':
        body += '<ol>'
        for q in qs:
            body += f'<li><strong lang="en">{e(q["options"][q["answer"]])}</strong><p lang="en">{e(q["prompt"].replace("___", q["options"][q["answer"]]))}</p><p>{e(q["explanations"][lang])}</p></li>'
        body += f'</ol><h2>{e(t["writing"])}</h2><p>{e(t["write_help"])}</p><p>{e(t["checklist"])}</p>'
    else:
        body += f'<h2>{e(t["notes"])}</h2><p>{e(t["lesson"])}</p>'
        for r in BANK[level]:
            body += f'<section><h2>{e(r["id"].replace("-", " ").title())}</h2><p>{e(r["explanations"][lang])}</p></section>'
        body += f'<h2>{e(t["licence"].split(".")[0])}</h2><p>{e(t["licence"])}</p>'
    body += '<footer>© 2026 Urban Sky Web Ltd · englishasaforeignlanguage.com · Edition 1</footer>'
    return f'<!doctype html><html lang="{lang}"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(title)}</title><style>{CSS}</style><body>{body}</body></html>'

def compile_products(destination: Path):
    count = validate_bank()
    for lang in LANGUAGES:
        assert set(UI[lang]) == set(UI['en']) and all(UI[lang].values())
    destination.mkdir(parents=True, exist_ok=True)
    products = []
    for level in LEVELS:
        product_id = f'{level.lower()}-practice-v{VERSION}'
        filename = f'{product_id}.zip'
        with ZipFile(destination / filename, 'w', compression=ZIP_DEFLATED) as archive:
            for lang in LANGUAGES:
                for kind in ('worksheet', 'answers', 'notes'):
                    info = ZipInfo(f'{product_id}/{lang}/{kind}.html', date_time=(2026,10,14,0,0,0))
                    info.compress_type = ZIP_DEFLATED
                    archive.writestr(info, document(level, lang, kind).encode('utf-8'))
            info = ZipInfo(f'{product_id}/README.txt', date_time=(2026,10,14,0,0,0))
            archive.writestr(info, '\n\n'.join(f'{LANGUAGES[lang]}\n{UI[lang]["formats"]}\n{UI[lang]["licence"]}' for lang in LANGUAGES))
        digest = hashlib.sha256((destination / filename).read_bytes()).hexdigest()
        products.append({'id':product_id,'level':level,'version':VERSION,'filename':filename,'sha256':digest,'price_pence':399,'currency':'gbp','question_count':12,'languages':list(LANGUAGES)})
    # Fail closed rather than silently overwriting an already-sold edition.
    lock = Path(__file__).with_name('edition-lock.json')
    expected = json.loads(lock.read_text()) if lock.exists() else {}
    for p in products:
        if p['id'] in expected and expected[p['id']] != p['sha256']:
            raise ValueError(f'Published edition changed: {p["id"]}. Create a new version.')
    (destination / 'catalog.json').write_text(json.dumps(products, ensure_ascii=False, indent=2)+'\n')
    report = {'status':'passed','questions':count,'products':len(products),'language_editions':len(products)*len(LANGUAGES),'checks':['unique question IDs','valid answer indices','complete explanation locales','complete UI locales','immutable published editions','deterministic ZIPs']}
    (destination / 'build-report.json').write_text(json.dumps(report,indent=2)+'\n')
    return products

if __name__ == '__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    print(json.dumps(compile_products(p.parse_args().output),indent=2))
