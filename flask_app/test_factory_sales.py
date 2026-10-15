import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from app import create_app
from learning.catalog import LANGUAGES

class FactorySales(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name);(root/'manifest.json').write_text('{}')
        self.ident='teacher-'+'a'*32+'-'+'b'*16
        self.data=b'private ZIP fixture'
        self.product={'id':self.ident,'source':'factory','filename':self.ident+'.zip','sha256':hashlib.sha256(self.data).hexdigest(),
                      'bundle_hash':'c'*64,'content_hash':'d'*64,'quality_policy':'efl-auto-release-v1','price_pence':399,'currency':'gbp','level':'B1','version':'b'*12,
                      'title':'Community repair lesson','titles':{'en':'Community repair lesson','fr':'Atelier de réparation'},'languages':['en','fr'],
                      'question_count':12,'duration_minutes':45,'objectives':['Discuss a problem','Agree on a plan'],
                      'samples':[{'id':'E1','instruction':'Read this','stimulus':'A short original text','prompt':'What happened?','options':[]},
                                 {'id':'E2','instruction':'Discuss','stimulus':'','prompt':'Suggest a solution','options':[]}]}
        self.dir=root/'factory';self.dir.mkdir();self.save()
        self.app=create_app({'TESTING':True,'SECRET_KEY':'fixture','PRODUCTS_DIR':str(root/'base'),'FACTORY_PRODUCTS_DIR':str(self.dir),'MANIFEST_PATH':str(root/'manifest.json'),
                             'STRIPE_SECRET_KEY':'sk_test_fixture','EFL_SALES_ENABLED':True})
        self.client=self.app.test_client()
    def save(self):
        (self.dir/(self.ident+'.json')).write_text(json.dumps(self.product))
        (self.dir/(self.ident+'.zip')).write_bytes(self.data)
    def token(self):
        self.client.get('/en/resources/'+self.ident+'/')
        with self.client.session_transaction() as s:return s['csrf']
    def payment(self):
        return {'payment_status':'paid','status':'complete','mode':'payment','currency':'gbp','amount_total':399,'client_reference_id':self.ident,'livemode':False,
                'metadata':{'site':'efl-by-level','product_id':self.ident,'edition_sha256':self.product['sha256'],'digital_consent':'immediate-access-v1'},
                'payment_intent':{'latest_charge':{'paid':True,'amount_refunded':0,'disputed':False}}}
    def test_real_listing_titles_samples_and_languages(self):
        for lang in LANGUAGES:
            r=self.client.get('/'+lang+'/resources/'+self.ident+'/')
            self.assertEqual(r.status_code,200)
            self.assertIn('What happened?',r.text)
            self.assertIn('Atelier de réparation' if lang=='fr' else 'Community repair lesson',r.text)
            self.assertNotIn('all nine',r.text)
        r=self.client.get('/fr/resources/')
        self.assertIn('Atelier de réparation',r.text)
        receipt=self.client.get('/resources/'+self.ident+'/release.json').json
        self.assertEqual(receipt['sha256'],self.product['sha256']);self.assertTrue(receipt['checkout_ready'])
    def test_bad_contract_and_traversal_withheld(self):
        self.product['filename']='../secret.zip';self.save()
        self.assertEqual(self.client.get('/resources/'+self.ident+'/').status_code,404)
    def test_checkout_uses_server_price_and_actual_title(self):
        with patch('learning.web.stripe_api',return_value={'url':'https://checkout.stripe.com/c/pay/test'}) as api:
            r=self.client.post('/en/checkout/'+self.ident+'/',data={'csrf':self.token(),'digital_consent':'yes','price_pence':1})
            self.assertEqual(r.status_code,303)
            data=api.call_args.args[1]
            self.assertEqual(data['line_items[0][price_data][unit_amount]'],'399')
            self.assertIn(self.product['title'],data['line_items[0][price_data][product_data][name]'])
    def test_paid_download_and_invalid_payment_denied(self):
        path='/fr/purchase/download/?session_id=cs_test_12345678901234567890'
        fixture=self.payment()
        with patch('learning.web.stripe_api',return_value=fixture):
            r=self.client.get(path);self.assertEqual(r.status_code,200);self.assertEqual(r.data,self.data);r.close()
        variants=[]
        for k,v in [('payment_status','unpaid'),('amount_total',1),('currency','usd'),('livemode',True)]:
            bad=copy.deepcopy(fixture);bad[k]=v;variants.append(bad)
        bad=copy.deepcopy(fixture);bad['metadata']['edition_sha256']='0'*64;variants.append(bad)
        bad=copy.deepcopy(fixture);bad['payment_intent']['latest_charge']['disputed']=True;variants.append(bad)
        for bad in variants:
            with patch('learning.web.stripe_api',return_value=bad):self.assertEqual(self.client.get(path).status_code,403)
        (self.dir/self.product['filename']).write_bytes(b'tampered')
        with patch('learning.web.stripe_api',return_value=fixture):self.assertEqual(self.client.get(path).status_code,503)
        self.assertEqual(self.client.get('/storage/factory_products/'+self.product['filename']).status_code,404)
    def test_sales_disabled_stays_closed(self):
        self.app.config['EFL_SALES_ENABLED']=False
        self.assertEqual(self.client.post('/checkout/'+self.ident+'/',data={'csrf':self.token(),'digital_consent':'yes'}).status_code,503)
        self.assertFalse(self.client.get('/resources/'+self.ident+'/release.json').json['checkout_ready'])

if __name__=='__main__':unittest.main()
