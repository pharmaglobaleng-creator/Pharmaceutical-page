import { readFileSync } from 'node:fs';
import { load } from 'cheerio';
const pages = JSON.parse(readFileSync('src/content/manifest.json'));
const errors=[];
let checked=0;
for (const {path} of pages) {
 const $=load(readFileSync('dist/'+path,'utf8'));
 // Preserve the existing legacy coatings URL as a redirect, not an article.
 if ($('meta[http-equiv="refresh"]').length) continue;
 checked++;
 const fail=message=>errors.push(`${path}: ${message}`);
 if($('main').length!==1)fail('Expected one main landmark');
 if($('h1').length!==1)fail('Expected one H1');
 const ids=new Set();
 $('[id]').each((i,e)=>{if(ids.has(e.attribs.id))fail(`Duplicate ID ${e.attribs.id}`);ids.add(e.attribs.id);});
 let previous=0;
 $('h1,h2,h3,h4,h5,h6').each((i,e)=>{const level=Number(e.tagName[1]);if(level>previous+1)fail(`Heading jump to ${e.tagName}: ${$(e).text().trim()}`);previous=level;});
 const main=$('main').attr('id');
 if($('main').attr('tabindex')!=='-1')fail('Main skip target must accept programmatic focus');
 if(!$(`a[href="#${main}"]`).toArray().some(e=>/skip/i.test($(e).text())))fail('Missing main-content skip link');
 $('nav').each((i,e)=>{if(!e.attribs['aria-label']&&!e.attribs['aria-labelledby'])fail('Unnamed navigation');});
 $('table').each((i,e)=>{if(!$(e).find('caption').length&&!e.attribs['aria-label']&&!e.attribs['aria-labelledby'])fail('Unnamed table');});
 $('th').each((i,e)=>{if(!['col','row','colgroup','rowgroup'].includes(e.attribs.scope))fail('Missing table header scope');});
 $('[aria-labelledby],[aria-describedby]').each((i,e)=>{for(const attr of ['aria-labelledby','aria-describedby'])for(const id of (e.attribs[attr]||'').split(/\s+/).filter(Boolean))if(!ids.has(id))fail(`Unresolved ${attr}: ${id}`);});
 $('ul,ol').each((i,e)=>{$(e).children().each((j,c)=>{if(!['li','script','template'].includes(c.tagName))fail('Invalid list child');});});
 $('input:not([type="hidden"]),select,textarea').each((i,e)=>{if(['submit','button','reset'].includes(e.attribs.type))return;if(!e.attribs['aria-label']&&!e.attribs['aria-labelledby']&&!$(e).closest('label').length&&!$('label').toArray().some(l=>l.attribs.for&&l.attribs.for===e.attribs.id))fail('Unlabelled control');});
}
console.log(JSON.stringify({semanticPages:checked,preservedRedirects:pages.length-checked,errors},null,2));
if(errors.length)process.exit(1);
