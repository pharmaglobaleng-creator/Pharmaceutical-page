import { readFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { load } from 'cheerio';
const pages=JSON.parse(readFileSync('src/content/manifest.json'));
const errors=[];
const norm=s=>s.replace(/\s+/g,' ').trim();
const digest=b=>createHash('sha256').update(b).digest('hex');
function snapshot(html) {
 const $=load(html);
 // The only added visible wording is a keyboard-focus-only accessibility link.
 $('[data-pge-semantic-skip]').remove();
 // Editorial discovery additions are generated only from reviewed, published news records.
 $('[data-pge-latest-news]').remove();
 $('link[rel="alternate"][type="application/rss+xml"]').remove();
 const text=selector=>$(selector).map((i,e)=>norm($(e).text())).get();
 const attrs=selector=>$(selector).map((i,e)=>{const a={...e.attribs};if(a.charset)a.charset=a.charset.toLowerCase();return JSON.stringify(a,Object.keys(a).sort());}).get();
 const scripts=$('script').filter((i,e)=>e.attribs.type!=='application/ld+json'&&!String(e.attribs.src||'').startsWith('/_next/')&&!$(e).text().includes('self.__next_f')&&e.attribs.src!=='/assets/js/pge-analytics.js').map((i,e)=>({src:e.attribs.src||null,text:$(e).text()})).get();
 const schema=$('script[type="application/ld+json"]').map((i,e)=>JSON.stringify(JSON.parse($(e).text()))).get();
 $('script,style').remove();
 return {title:text('title'),meta:attrs('meta'),canonical:attrs('link[rel="canonical"]'),headings:text('h1,h2,h3,h4,h5,h6'),scripts,schema,forms:attrs('form,input,textarea,select,button'),links:attrs('a'),images:attrs('img'),text:norm($('body').text())};
}
for(const page of pages){
 const target=resolve('dist',page.path);
 if(!existsSync(target)){errors.push(`${page.path}: missing output`);continue;}
 try{
  const before=snapshot(readFileSync(resolve('..',page.path),'utf8'));
  const after=snapshot(readFileSync(target,'utf8'));
  for(const key of Object.keys(before))if(JSON.stringify(before[key])!==JSON.stringify(after[key]))errors.push(`${page.path}: changed ${key}`);
 }catch(e){errors.push(`${page.path}: ${e.message}`)}
}
const protectedFiles=execFileSync('git',['ls-files','-z','parts','catalog-data','_next','sitemap.xml','sitemap-cremer.xml','sitemap-parts-images.xml','robots.txt','CNAME','google30e5ac579c88549d.html','googleb09af90219443617.html'],{cwd:'..',encoding:'utf8'}).split('\0').filter(Boolean);
for(const path of protectedFiles){
 if(!existsSync(resolve('dist',path))||digest(readFileSync(resolve('..',path)))!==digest(readFileSync(resolve('dist',path))))errors.push(`${path}: protected file changed or missing`);
}
const home=readFileSync('dist/index.html','utf8');
if(/<script[^>]+src=["']\/_next\//.test(home)||home.includes('self.__next_f'))errors.push('Homepage still loads Next.js runtime');
console.log(JSON.stringify({pages:pages.length,protectedFiles:protectedFiles.length,errors},null,2));
if(errors.length)process.exit(1);
