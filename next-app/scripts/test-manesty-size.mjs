import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { chromium } from '@playwright/test';
import sharp from 'sharp';
import { catalogData, catalogRoutes } from '../lib/catalog.mjs';
const app = process.cwd(), root = path.resolve(app,'..'), out = path.join(app,'out');
const evidence = path.join(root,'manesty-size-evidence');
fs.mkdirSync(evidence,{recursive:true});
const servers = [spawn('python3',['-m','http.server','8041','--bind','127.0.0.1','--directory',root],{stdio:'ignore'}),spawn('python3',['-m','http.server','8042','--bind','127.0.0.1','--directory',out],{stdio:'ignore'})];
const data = catalogData(), parts = data.parts.filter(p=>p.brand==='manesty');
const routes = catalogRoutes().filter(r=>r.brand==='manesty' && !r.model);
const first = parts[0], last = parts.at(-1);
const errors = [], measurements = {};
let browser;
try {
  for (const port of [8041,8042]) {
    let ready=false;
    for(let n=0;n<100;n++) { try { const r=await fetch(`http://127.0.0.1:${port}/parts/manesty/`); if(r.ok) { ready=true; break; } } catch {} await new Promise(resolve=>setTimeout(resolve,100)); }
    assert.ok(ready,'Preview server unavailable');
  }
  browser = await chromium.launch({headless:true});
  for (const [label,port] of [['before',8041],['after',8042]]) {
    const context = await browser.newContext({viewport:{width:1440,height:1000},deviceScaleFactor:1});
    const page = await context.newPage();
    if(label==='after') page.on('pageerror',e=>errors.push(e.message));
    await page.goto(`http://127.0.0.1:${port}/parts/manesty/`,{waitUntil:'networkidle'});
    await page.evaluate(()=>{ for(const img of document.images) img.loading='eager'; });
    await page.waitForFunction(()=>[...document.images].every(i=>i.complete && i.naturalWidth>0),{},{timeout:60000});
    await page.waitForLoadState('networkidle');
    measurements[label] = await page.evaluate(()=>({cards:document.querySelectorAll('.pc-card').length, htmlBytes:performance.getEntriesByType('navigation')[0].decodedBodySize, resourceDecodedBytes:performance.getEntriesByType('resource').reduce((n,r)=>n+(r.decodedBodySize||0),0), imageRequests:performance.getEntriesByType('resource').filter(r=>r.initiatorType==='img'||/\.(webp|png|jpe?g)(\?|$)/.test(r.name)).length, horizontalOverflow:document.documentElement.scrollWidth>innerWidth+1}));
    assert.ok(!measurements[label].horizontalOverflow);
    if(label==='after') {
      assert.equal(measurements.after.cards,25);
      await page.screenshot({path:path.join(evidence,'manesty-desktop-after.png')});
      await page.locator(`[data-pc-add="${first.sku}"]`).click();
      await page.locator('dialog[open]').waitFor();
      await page.getByRole('button',{name:'Close quote cart',exact:true}).click();
      await page.goto(`http://127.0.0.1:8042${first.url}`,{waitUntil:'networkidle'});
      const cart=await page.evaluate(()=>JSON.parse(localStorage.getItem('pge-parts-quote-cart-v1')||'{}'));
      assert.equal(cart[first.sku].url,first.url);
      const detailImage=await page.locator('.part-image img').evaluate(i=>({src:i.getAttribute('src'),selected:i.currentSrc,width:i.naturalWidth}));
      assert.ok(detailImage.width>0); assert.ok(detailImage.selected.includes('manesty-light-v1') || detailImage.src.endsWith('.svg'));
      await page.screenshot({path:path.join(evidence,'manesty-detail-after.png')});
      await page.goto(`http://127.0.0.1:8042/parts/search/?brand=manesty&q=${encodeURIComponent(last.sku)}`,{waitUntil:'networkidle'});
      await page.locator(`[data-pc-sku="${last.sku}"]`).waitFor({timeout:30000});
    }
    await context.close();
  }
  const nojs=await browser.newContext({javaScriptEnabled:false});
  const np=await nojs.newPage();
  for(const route of [routes[0],routes[1],routes.at(-1)]) {
    await np.goto(`http://127.0.0.1:8042${route.url}`);
    assert.deepEqual(await np.locator('.pc-card').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('data-pc-sku'))),route.skus);
    assert.equal(await np.locator('link[rel="canonical"]').getAttribute('href'),'https://pharmaglobaleng.com'+route.url);
    assert.ok(await np.locator('nav.pc-pagination a[href]').count()>1);
  }
  await nojs.close();
  const mobile=await browser.newContext({viewport:{width:390,height:844},deviceScaleFactor:2,isMobile:true,hasTouch:true});
  const mp=await mobile.newPage(); mp.on('pageerror',e=>errors.push(e.message));
  await mp.goto('http://127.0.0.1:8042/parts/manesty/',{waitUntil:'networkidle'});
  assert.ok(await mp.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  await mp.screenshot({path:path.join(evidence,'manesty-mobile-after.png')});
  await mobile.close();
  assert.deepEqual(errors,[],'Browser JavaScript errors');
  assert.ok(measurements.after.htmlBytes<measurements.before.htmlBytes,'HTML was not reduced');
  assert.ok(measurements.after.resourceDecodedBytes<measurements.before.resourceDecodedBytes,'Catalog resource weight was not reduced');
  const state=JSON.parse(fs.readFileSync(path.join(app,'.manesty-optimization.json'),'utf8'));
  const examples=Object.values(state.images).filter(i=>i.fullUrl!==i.original).sort((a,b)=>b.originalBytes-a.originalBytes).slice(0,3);
  const composite=[];
  for(let i=0;i<examples.length;i++) {
    for(const [side,url,base] of [[0,examples[i].original,root],[1,examples[i].fullUrl,out]]) {
      const buffer=await sharp(path.join(base,url.slice(1))).resize({width:420,height:420,fit:'contain',background:'#071126'}).png().toBuffer();
      composite.push({input:buffer,left:side*420,top:i*420});
    }
  }
  if(composite.length) await sharp({create:{width:840,height:420*examples.length,channels:3,background:'#071126'}}).composite(composite).png().toFile(path.join(evidence,'photo-comparison-original-left-webp-right.png'));
  const report={status:'passed',manestyProducts:parts.length,primaryCatalogPages:routes.length,noJavaScriptNavigationPassed:true,lastProductSearchPassed:true,quoteCartPersistsToOriginalDetailPage:true,desktopAndMobileLayoutPassed:true,originalVsWebpComparison:examples.map(i=>({image:i.original,originalBytes:i.originalBytes,webpBytes:i.fullBytes})),measurements,measurementNote:'Local Chromium cold-page test at 1440x1000, DPR 1, with all images on that catalog page explicitly loaded. Decoded resource bytes are not compressed live-network bytes, initial viewport bytes, or a speed score.'};
  fs.writeFileSync(path.join(evidence,'browser-checks.json'),JSON.stringify(report,null,2));
  fs.copyFileSync(path.join(root,'docs/manesty-size-optimization-report.json'),path.join(evidence,'size-report.json'));
  fs.copyFileSync(path.join(app,'.manesty-final-report.json'),path.join(root,'docs/manesty-size-optimization-report.json'));
  fs.writeFileSync(path.join(root,'docs/manesty-size-browser-checks.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report,null,2));
} finally { if(browser) await browser.close(); for(const s of servers)s.kill(); }
