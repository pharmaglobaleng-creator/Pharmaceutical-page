const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const source=fs.readFileSync(require('node:path').join(__dirname,'../assets/js/pge-analytics.js'),'utf8');
function setup(host='pharmaglobaleng.com') {
 const listeners={};const scripts=[];
 const document={readyState:'complete',querySelector:()=>null,addEventListener:(n,f)=>{(listeners[n]??=[]).push(f)},createElement:()=>({}),head:{appendChild:e=>scripts.push(e)}};
 const window={location:{hostname:host,pathname:'/parts/pge-cre-004/'}};
 const ctx=vm.createContext({window,document});vm.runInContext(source,ctx);
 function click(href,canceled=false,cart=false){const link={getAttribute:()=>href,classList:{contains:()=>cart}};for(const cb of listeners.click||[])cb({defaultPrevented:canceled,target:{closest:()=>link}})}
 return {window,ctx,scripts,click};
}
test('only inquiry intent is collected; private query contents are excluded',()=>{
 const s=setup();s.click('mailto:info@example.com?subject=Private&body=Customer%20name',false,true);s.click('tel:+17324397849');s.click('/contact.html');s.click('mailto:a@b.com',true);
 const events=s.window.dataLayer.filter(a=>a[0]==='event');assert.equal(events.length,2);assert.equal(events[0][2].inquiry_context,'quote_cart');assert.equal(events[1][2].contact_method,'phone');assert.ok(!JSON.stringify(events).includes('Private'));assert.ok(!JSON.stringify(events).includes('17324397849'));
 vm.runInContext(source,s.ctx);s.click('tel:123');assert.equal(s.window.dataLayer.filter(a=>a[0]==='event').length,3);assert.equal(s.scripts.length,1);
});
test('preview traffic does not initialize analytics',()=>{const s=setup('127.0.0.1');s.click('tel:123');assert.equal(s.scripts.length,0);assert.equal(s.window.dataLayer,undefined)});
