"""Real Chromium release gate; runs against the fully built Flask application."""
from pathlib import Path
from threading import Thread
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
from app import create_app

app=create_app({'TESTING':True})
server=make_server('127.0.0.1',5071,app)
thread=Thread(target=server.serve_forever,daemon=True);thread.start()
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        page=browser.new_page(viewport={'width':390,'height':844})
        page.goto('http://127.0.0.1:5071/')
        assert page.locator('#language-dialog').is_visible()
        page.locator('#language-dialog a[lang=pl]').click()
        assert page.locator('html').get_attribute('lang')=='pl'
        assert not page.locator('#language-dialog').is_visible()
        page.reload();assert not page.locator('#language-dialog').is_visible()
        page.locator('[data-language-open]').click();assert page.locator('#language-dialog').is_visible()
        page.keyboard.press('Escape');assert not page.locator('#language-dialog').is_visible()
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'mobile overflow'
        Path('browser-evidence').mkdir(exist_ok=True)
        page.screenshot(path='browser-evidence/polish-mobile.png',full_page=True)
        page.goto('http://127.0.0.1:5071/practice/b1/')
        page.locator('summary').first.click()
        assert page.locator('details').first.get_attribute('open') is not None
        page.goto('http://127.0.0.1:5071/english-level-test/')
        for fieldset in page.locator('fieldset').all():
            fieldset.locator('input').first.check()
        page.locator('button[type=submit]').click()
        assert page.locator('h1').inner_text() in ['A1','A2','B1','B2','C1','C2']
        page.goto('http://127.0.0.1:5071/resources/?lang=fr')
        page.set_viewport_size({'width':1440,'height':900})
        page.screenshot(path='browser-evidence/french-shop.png',full_page=True)
        from learning.catalog import LANGUAGES, direction
        for lang in ('hi','ur','ps','zh-Hans','zh-Hant'):
            page.set_viewport_size({'width':390,'height':844})
            page.goto('http://127.0.0.1:5071/practice/b1/?lang='+lang)
            assert page.locator('html').get_attribute('dir') == direction(lang)
            page.locator('summary').first.click()
            assert page.locator('h3[lang=en]').first.evaluate('(el)=>getComputedStyle(el).direction') == 'ltr'
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), lang
            page.locator('[data-language-open]').click()
            assert page.locator('#language-dialog a').count() == len(LANGUAGES)
            page.screenshot(path=f'browser-evidence/{lang}-picker.png',full_page=True)
            page.keyboard.press('Escape')
            page.screenshot(path=f'browser-evidence/{lang}-practice.png',full_page=True)
        # Print layout: inspect each local language edition at A4 viewport size.
        from learning.generate import document
        page.set_viewport_size({'width':794,'height':1123})
        for lang in LANGUAGES:
            page.set_content(document('C2',lang,'answers'))
            page.emulate_media(media='print')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        context=browser.new_context(java_script_enabled=False)
        nojs=context.new_page();nojs.goto('http://127.0.0.1:5071/english-level-test/')
        for fieldset in nojs.locator('fieldset').all():
            fieldset.locator('input').first.check()
        nojs.locator('button[type=submit]').click()
        assert nojs.locator('h1').inner_text() in ['A1','A2','B1','B2','C1','C2']
        browser.close()
    print('PASS: first visit, persistent selection, reopening, Escape, mobile overflow, explanations, translated shop, HTML print layout and level-test submission with/without JavaScript.')
finally:
    server.shutdown()
