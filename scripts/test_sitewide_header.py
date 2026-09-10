#!/usr/bin/env python3
"""Browser acceptance checks for the approved header. Never sends mail or calls."""
import argparse,functools,json,threading
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright

PATHS=['/','/about/','/contact.html','/parts/','/parts/kikusui/','/parts/stokes/','/parts/pge-kik-003/','/parts/pge-fet-001/','/parts/identify/','/services/','/services/tablet-tooling-inspection.html','/solutions/','/solutions/tablet-weight-variation.html','/knowledge-center/','/coatings/titanium-nitride-tin.html','/parts/korsch/korsch-300/']
MEASURE='''() => {const el=document.querySelector('header[data-pge-header="v1"]');const sel=s=>el?.querySelector(s);const rect=e=>{if(!e)return null;const b=e.getBoundingClientRect();return {x:b.x,y:b.y,w:b.width,h:b.height,r:b.right,b:b.bottom}};return {headers:document.querySelectorAll('header[data-pge-header="v1"]').length,identities:document.querySelectorAll('.pge-header-identity').length,logoLoaded:sel('.pge-header-logo')?.complete && sel('.pge-header-logo')?.naturalWidth>0,phone:sel('.pge-header-phone')?.textContent,href:sel('.pge-header-phone')?.getAttribute('href'),header:rect(el),identity:rect(sel('.pge-header-identity')),brand:rect(sel('.pge-header-brand')),number:rect(sel('.pge-header-phone')),oldFloat:document.querySelectorAll('a.pge-sitewide-phone').length,cartEnabled:document.querySelector('.pc-cart-trigger') ? !document.querySelector('.pc-cart-trigger').disabled : null,viewport:innerWidth}}'''
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--url');ap.add_argument('--quick',action='store_true');args=ap.parse_args()
    args.output.mkdir(parents=True,exist_ok=True);server=None;results=[];behavior=[];errors=[]
    if args.url:base=args.url.rstrip('/')
    else:
        server=ThreadingHTTPServer(('127.0.0.1',8878),functools.partial(Quiet,directory=str(args.root)))
        threading.Thread(target=server.serve_forever,daemon=True).start();base='http://127.0.0.1:8878'
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True)
            for width in ([1440,390] if args.quick else [1440,1050,768,390,320]):
                context=browser.new_context(viewport={'width':width,'height':950},device_scale_factor=2)
                for path in (['/','/about/','/parts/kikusui/','/parts/pge-kik-003/','/contact.html'] if args.quick else PATHS):
                    page=context.new_page();local=[]
                    page.on('pageerror',lambda error:local.append(str(error)))
                    response=page.goto(base+path,wait_until='networkidle',timeout=60000)
                    page.locator('header[data-pge-header="v1"] .pge-header-logo').wait_for(timeout=15000)
                    page.wait_for_timeout(250)
                    item=page.evaluate(MEASURE);item.update(path=path,width=width,status=response.status,errors=local)
                    item['passed']=(response.status==200 and item['headers']==item['identities']==1 and item['logoLoaded'] and item['phone']=='+1 (732) 439-7849' and item['href']=='tel:+17324397849' and item['oldFloat']==0 and item['identity']['r']<=width+1 and item['number']['r']<=width+1 and item['number']['x']>=item['brand']['r']+4 and abs(item['number']['y']+item['number']['h']/2-item['brand']['y']-item['brand']['h']/2)<2 and item['cartEnabled'] is not False and not local)
                    results.append(item);errors.extend(local)
                    if width in [1440,390] and path in ['/','/about/','/contact.html','/parts/kikusui/','/parts/pge-kik-003/']:
                        stem='home' if path=='/' else path.strip('/').replace('/','-').replace('.html','')
                        page.screenshot(path=str(args.output/f'{stem}-{width}.png'))
                        page.locator('header[data-pge-header="v1"]').screenshot(path=str(args.output/f'{stem}-header-{width}.png'))
                    print(width,path,'PASS' if item['passed'] else json.dumps(item),flush=True)
                    if not item['passed']:raise AssertionError(item)
                    page.close()
                context.close()
            # Exact production JS: menus and cart must survive hydration.
            ctx=browser.new_context(viewport={'width':1440,'height':950})
            page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(base+'/',wait_until='networkidle')
            button=page.locator('.dropdown-trigger[aria-controls="services-menu"]');button.click()
            assert button.get_attribute('aria-expanded')=='true'
            assert page.locator('#services-menu').is_visible();behavior.append('Homepage Services dropdown')
            page.set_viewport_size({'width':390,'height':844});page.locator('.menu-toggle').click()
            assert page.locator('.primary-nav').is_visible();behavior.append('Homepage mobile menu')
            page.goto(base+'/parts/kikusui/',wait_until='networkidle')
            page.locator('[data-pc-add="PGE-KIK-008"]').click(timeout=15000)
            page.locator('dialog.pc-quote[open]').wait_for()
            assert page.evaluate("JSON.parse(localStorage.getItem('pge-parts-quote-cart-v1'))['PGE-KIK-008'].brand")=='Kikusui'
            page.get_by_role('button',name='Close quote cart',exact=True).click();behavior.append('Hydrated catalog add-to-quote and dialog')
            page.locator('.pc-mobile-nav>summary').click();assert page.locator('.pc-mobile-nav nav').is_visible();behavior.append('Catalog mobile navigation')
            page.goto(base+'/parts/search/?q=PGE-KIK-008&brand=kikusui',wait_until='networkidle')
            page.locator('[data-pc-sku="PGE-KIK-008"]').wait_for(timeout=20000);behavior.append('Interactive parts search')
            page.goto(base+'/parts/pge-kik-003/',wait_until='networkidle');page.locator('[data-pge-cart-add]').click();assert page.evaluate("Boolean(JSON.parse(localStorage.getItem('pge-parts-quote-cart-v1'))['PGE-KIK-003'])");behavior.append('Individual product quote button')
            assert not errors,errors
            ctx.close()
            ctx=browser.new_context(java_script_enabled=False,viewport={'width':390,'height':844})
            for path in ['/','/parts/kikusui/','/about/','/services/']:
                page=ctx.new_page();page.goto(base+path,wait_until='load');assert page.locator('.pge-header-phone').count()==1;assert page.locator('.pge-header-phone').is_visible();page.close()
            behavior.append('Phone and logo available without JavaScript');ctx.close();browser.close()
    finally:
        if server:server.shutdown()
        report={'pages':results,'behavior':behavior,'page_errors':errors,'passed':bool(results) and all(x['passed'] for x in results) and len(behavior)==7 and not errors}
        (args.output/'browser-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    assert report['passed'],report
if __name__=='__main__':main()
