"""Critical customer, language isolation, product and payment boundaries."""
import copy
import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile
from app import create_app
from learning.generate import compile_products
from learning.bank import questions_for
from learning.catalog import LANGUAGES, LEVELS, UI, direction, text_html
from learning.web import test_questions

class LearningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        root=Path(cls.tmp.name)
        cls.products=compile_products(root/'products')
        (root/'pages').mkdir()
        (root/'pages'/'home.html').write_text('<html lang="en"><head></head><body><header><div class="shell header-inner"><nav>Learn English</nav></div></header><main id="main">English home</main></body></html>')
        (root/'manifest.json').write_text(json.dumps({'/':'home.html','/about/':'home.html','/404/':'home.html'}))
        cls.app=create_app({'TESTING':True,'SECRET_KEY':'test-only-key','PRODUCTS_DIR':str(root/'products'),'PAGES_DIR':str(root/'pages'),'MANIFEST_PATH':str(root/'manifest.json'),'SUBMISSIONS_PATH':str(root/'submissions.csv'),'STRIPE_SECRET_KEY':'sk_test_not_a_real_key','EFL_SALES_ENABLED':False})
    def setUp(self):
        self.client=self.app.test_client()
    def token(self):
        self.client.get('/english-level-test/')
        with self.client.session_transaction() as s:
            return s['csrf']
    def test_previous_editions_retained(self):
        root=Path(self.app.config['PRODUCTS_DIR'])
        lock=json.loads((Path(__file__).parent/'learning'/'frozen_v1'/'edition-lock.json').read_text())
        for product_id, digest in lock.items():
            self.assertEqual(hashlib.sha256((root/(product_id+'.zip')).read_bytes()).hexdigest(),digest)
        self.assertEqual(self.client.get('/resources/a1-practice-v1/').status_code,302)

    def test_language_choice_persistence_and_no_open_redirect(self):
        self.assertIn('data-first-visit="true"',self.client.get('/').text)
        r=self.client.get('/language/pl/?next=//evil.example')
        self.assertEqual(r.location,'/')
        r=self.client.get('/')
        self.assertIn(UI['pl']['home'],r.text)
        self.assertIn('data-first-visit="false"',r.text)
        self.assertIn('no-store',r.headers['Cache-Control'])
        self.assertIn('Cookie',r.headers['Vary'])
        self.assertEqual(r.headers['Content-Language'],'pl')
        self.assertEqual(self.client.get('/language/unknown/').status_code,404)
        self.assertEqual(self.client.get('/language/en/?next=/%5Cevil.example').location,'/')
    def test_language_link_persists_and_canonical_routes(self):
        self.client.get('/resources/?lang=fr')
        self.assertIn(UI['fr']['home'], self.client.get('/study/').text)
        self.assertEqual(self.client.get('/english-level-test').status_code, 308)

    def test_all_level_language_customer_routes(self):
        for lang in LANGUAGES:
            for level in LEVELS:
                for prefix in ('practice/'+level.lower(),'resources/'+level.lower()+'-practice-v2'):
                    r=self.client.get('/'+prefix+'/?lang='+lang)
                    self.assertEqual(r.status_code,200)
                    self.assertIn(text_html(questions_for(level)[0]['explanations'][lang],lang),r.text)
                    self.assertIn('lang="en"',r.text)
                    self.assertIn(f'<html lang="{lang}" dir="{direction(lang)}">',r.text)
                    self.assertNotIn('<button class="button" type="submit">'+UI[lang]['buy'],r.text)
    def test_csrf_and_server_scoring_without_js(self):
        qs=test_questions()
        data={q['id']:str(q['answer']) for q in qs}
        self.assertEqual(self.client.post('/english-level-test/',data=data).status_code,403)
        data['csrf']=self.token()
        r=self.client.post('/english-level-test/',data=data)
        self.assertEqual(r.status_code,200)
        self.assertIn('24/24',r.text)
        self.assertIn('<h1>C2</h1>',r.text)
        data[qs[0]['id']]='20'
        self.assertEqual(self.client.post('/english-level-test/',data=data).status_code,422)
        self.assertEqual(self.client.post('/english-level-test/',data=data,headers={'Origin':'https://evil.example'}).status_code,403)
    def test_download_denied_and_checkout_closed(self):
        for path in ('/private_products/a1-practice-v2.zip','/purchase/download/?session_id=forged'):
            self.assertIn(self.client.get(path).status_code,(403,404))
        self.assertEqual(self.client.post('/checkout/a1-practice-v2/',data={'csrf':self.token(),'digital_consent':'yes'}).status_code,503)
    def test_deterministic_products_with_four_complete_editions(self):
        for p in self.products:
            file=Path(self.app.config['PRODUCTS_DIR'])/p['filename']
            with ZipFile(file) as z:
                self.assertEqual(len(z.namelist()),3*len(LANGUAGES)+1)
                for lang in LANGUAGES:
                    text=z.read(f'{p["id"]}/{lang}/answers.html').decode()
                    self.assertIn(text_html(questions_for(p['level'])[0]['explanations'][lang],lang),text)
            before=hashlib.sha256(file.read_bytes()).hexdigest()
            compile_products(Path(self.app.config['PRODUCTS_DIR']))
            self.assertEqual(before,hashlib.sha256(file.read_bytes()).hexdigest())
    def purchase_fixture(self):
        p=self.products[0]
        return {'payment_status':'paid','status':'complete','mode':'payment','currency':'gbp','amount_total':399,'client_reference_id':p['id'],'livemode':False,'metadata':{'site':'efl-by-level','product_id':p['id'],'edition_sha256':p['sha256'],'digital_consent':'immediate-access-v1'},'payment_intent':{'latest_charge':{'paid':True,'amount_refunded':0,'disputed':False}}}
    def test_payment_authorisation_and_refunds(self):
        fixture=self.purchase_fixture();path='/purchase/download/?session_id=cs_test_12345678901234567890'
        with patch('learning.web.stripe_api',return_value=fixture):
            r=self.client.get(path)
            self.assertEqual(r.status_code,200)
            self.assertEqual(r.mimetype,'application/zip')
            self.assertIn('no-store',r.headers['Cache-Control'])
            self.assertEqual(r.headers['Referrer-Policy'],'no-referrer')
        for key,value in [('payment_status','unpaid'),('currency','usd'),('amount_total',1),('client_reference_id','another-product'),('livemode',True)]:
            bad=copy.deepcopy(fixture);bad[key]=value
            with patch('learning.web.stripe_api',return_value=bad):
                self.assertEqual(self.client.get(path).status_code,403)
        bad=copy.deepcopy(fixture);bad['payment_intent']['latest_charge']['amount_refunded']=399
        with patch('learning.web.stripe_api',return_value=bad):
            self.assertEqual(self.client.get(path).status_code,403)

if __name__=='__main__':
    unittest.main()
