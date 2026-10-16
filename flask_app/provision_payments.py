"""Provision private live configuration only after sandbox acceptance passes."""
import ftplib
import io
import json
import os
import re
import ssl
import time
from http.cookiejar import CookieJar
from urllib.request import urlopen, Request, build_opener, HTTPCookieProcessor, HTTPRedirectHandler
from urllib.parse import urlencode
from html import unescape
from urllib.error import HTTPError

def main():
    key=os.environ.get('EFL_STRIPE_SECRET_KEY','').strip()
    assert re.fullmatch(r'(sk|rk)_live_[A-Za-z0-9]+',key), 'Valid live key required'
    enabled=os.environ.get('EFL_ENABLE_SALES')=='1'
    payload=json.dumps({'secret_key':key,'sales_enabled':enabled}).encode()
    with ftplib.FTP_TLS(context=ssl.create_default_context(),timeout=30) as ftp:
        ftp.connect('englishasaforeignlanguage.com',21)
        # Exact hosting identity verified independently through the HTTPS application.
        ftp.host='p3plzcpnl508780.prod.phx3.secureserver.net'
        ftp.login(os.environ['FTP_USERNAME'],os.environ['FTP_PASSWORD']);ftp.prot_p()
        ftp.cwd(os.environ['FTP_SERVER_DIR'])
        ftp.storbinary('STOR storage/.htaccess',io.BytesIO(b'Require all denied\n'))
        ftp.storbinary('STOR storage/payment-config.json.part',io.BytesIO(payload))
        chunks=[];ftp.retrbinary('RETR storage/payment-config.json.part',chunks.append)
        assert b''.join(chunks)==payload, 'Configuration transfer verification failed'
        ftp.rename('storage/payment-config.json.part','storage/payment-config.json')
        ftp.storbinary('STOR tmp/restart.txt',io.BytesIO(str(time.time()).encode()))
    for attempt in range(12):
        with urlopen('https://englishasaforeignlanguage.com/health?payment_config='+str(time.time()),timeout=20) as response:
            health=json.load(response)
        if health.get('payments_configured') is True and health.get('sales_enabled') is enabled: break
        time.sleep(5)
    else: raise RuntimeError('Payment runtime configuration not confirmed')
    try:
        with urlopen('https://englishasaforeignlanguage.com/storage/payment-config.json',timeout=20):
            raise RuntimeError('Private configuration is exposed')
    except HTTPError as exc:
        assert exc.code in (403,404), 'Private configuration protection unconfirmed'
    if enabled:
        class NoRedirect(HTTPRedirectHandler):
            def redirect_request(self,*args,**kwargs): return None
        opener=build_opener(HTTPCookieProcessor(CookieJar()),NoRedirect())
        base='https://englishasaforeignlanguage.com'
        with opener.open(base+'/en/resources/a1-practice-v2/',timeout=20) as response: html=response.read().decode()
        csrf=re.search(r'name="csrf" value="([^"]+)"',html)
        assert csrf, 'Live checkout form unavailable'
        form=urlencode({'csrf':unescape(csrf.group(1)),'digital_consent':'yes'}).encode()
        try:
            opener.open(Request(base+'/en/checkout/a1-practice-v2/',data=form),timeout=30)
            raise RuntimeError('Live Checkout did not redirect')
        except HTTPError as exc:
            assert exc.code==303, 'Live Checkout creation failed'
            location=exc.headers['Location']
        assert location.startswith('https://checkout.stripe.com/'), 'Unexpected Checkout host'
        session=re.search(r'cs_live_[A-Za-z0-9]+',location)
        assert session, 'Live Checkout mode not confirmed'
        # Expire this unpaid session: no card details or real payment are used.
        req=Request('https://api.stripe.com/v1/checkout/sessions/'+session.group(0)+'/expire',data=b'',headers={'Authorization':'Bearer '+key,'Stripe-Version':'2024-06-20'})
        with urlopen(req,timeout=25) as response: expired=json.load(response)
        assert expired.get('status')=='expired' and expired.get('payment_status')=='unpaid'
        print('LIVE_CHECKOUT_CREATED_AND_EXPIRED_WITHOUT_CHARGE=PASS')
    print('Private payment configuration verified; sales_enabled='+str(enabled).lower())

if __name__=='__main__':main()
