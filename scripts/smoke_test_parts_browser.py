#!/usr/bin/env python3
"""Functional smoke tests; does not send mail or certify photos or engineering fit."""
import functools
import json
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass

def main():
    server=ThreadingHTTPServer(('127.0.0.1',8877),functools.partial(Quiet,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    results=[]
    errors=[]
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True)
            page=browser.new_page(viewport={'width':1440,'height':1000})
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto('http://127.0.0.1:8877/parts/kikusui/',wait_until='networkidle')
            card=page.locator('[data-pc-sku="PGE-KIK-008"]')
            assert 'Not verified; confirm during quotation' in card.inner_text()
            page.locator('[data-pc-add="PGE-KIK-008"]').click(timeout=10000)
            page.locator('dialog.pc-quote[open]').wait_for()
            saved=page.evaluate("JSON.parse(localStorage.getItem('pge-parts-quote-cart-v1'))")
            assert saved['PGE-KIK-008']['brand']=='Kikusui'
            results.append({'test':'Hydrated Kikusui card, quote button and dialog','status':'passed','sku':'PGE-KIK-008'})
            page.get_by_role('button',name='Close quote cart',exact=True).click()
            page.goto('http://127.0.0.1:8877/parts/search/?q=PGE-KIK-008&brand=kikusui',wait_until='networkidle')
            card=page.locator('[data-pc-sku="PGE-KIK-008"]')
            card.wait_for(timeout=15000)
            assert 'Not verified; confirm during quotation' in card.inner_text()
            results.append({'test':'Interactive search uses reviewed OEM status','status':'passed'})
            page.goto('http://127.0.0.1:8877/parts/pge-stk-017/',wait_until='networkidle')
            assert 'Stokes' in page.locator('h1').inner_text() and 'Korsch' not in page.locator('h1').inner_text()
            page.locator('[data-pge-cart-add]').click()
            saved=page.evaluate("JSON.parse(localStorage.getItem('pge-parts-quote-cart-v1'))")
            assert saved['PGE-STK-017']['brand']=='Stokes' and saved['PGE-STK-017']['model']=='Confirm during quotation'
            results.append({'test':'Corrected Stokes quote identity and model','status':'passed','sku':'PGE-STK-017'})
            page.set_viewport_size({'width':390,'height':844})
            page.goto('http://127.0.0.1:8877/parts/identify/',wait_until='networkidle')
            directory=page.locator('[data-pge-legacy-directory]')
            assert directory.locator('a[href^="/parts/pge-"]').count()==96
            page.get_by_text('Stokes earlier reference records (47)',exact=True).click()
            directory.locator('a[href="/parts/pge-stk-017/"]').click()
            assert page.url.endswith('/parts/pge-stk-017/')
            assert page.locator('[data-pge-reference-review]').count()==1
            results.append({'test':'Mobile identification directory and legacy navigation','status':'passed','legacy_links':96})
            assert not errors, errors
            results.append({'test':'Browser JavaScript page errors','status':'passed','errors':errors})
            browser.close()
    finally:
        server.shutdown()
        out=ROOT/'audit-output';out.mkdir(exist_ok=True)
        output={'results':results,'page_errors':errors,'scope':'Chromium against corrected repository HTML and JavaScript. Image bytes are excluded by sparse checkout: this is not photo verification or a Core Web Vitals measurement.'}
        (out/'browser-validation.json').write_text(json.dumps(output,indent=2)+'\n')
        print(json.dumps(output,indent=2))

if __name__=='__main__':main()
