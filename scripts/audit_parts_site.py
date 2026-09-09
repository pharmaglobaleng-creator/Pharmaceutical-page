#!/usr/bin/env python3
"""Read-only audit of every published parts HTML file; no ranking promises.
Uses the git inventory to check images without requiring an image checkout.
Warnings are review leads, not declarations of Google spam or penalties.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict, deque
import csv
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urljoin, urlsplit, unquote
from urllib.request import Request, urlopen
import urllib.robotparser
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://pharmaglobaleng.com'
JSONLD = re.compile(r'<script\b[^>]*type=[\"\']application/ld\+json[\"\'][^>]*>(.*?)</script>', re.I|re.S)
PLACEHOLDER = re.compile(r'\bmodel\s+(?:unresolved|unconfirmed|unspecified)\b', re.I)

def plain(s):
    return re.sub(r'\s+', ' ', unescape(re.sub(r'<[^>]*>', ' ', s))).strip()

def graph_nodes(obj):
    if isinstance(obj, dict):
        if '@type' in obj:
            yield obj
        for v in obj.values():
            yield from graph_nodes(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from graph_nodes(v)

class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.meta = defaultdict(list)
        self.canonicals = []
        self.links = []
        self.images = []
        self.resources = []
        self.headings = []
        self.heading = None
        self.hbuf = []
        self.title = ''
        self.in_title = False
        self.hidden_inline = []
        self.lang = None
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'html': self.lang = a.get('lang')
        if tag == 'title': self.in_title = True
        if tag == 'h1': self.heading = tag; self.hbuf = []
        if tag == 'meta':
            key = a.get('name', a.get('property', a.get('http-equiv',''))).lower()
            self.meta[key].append(a.get('content',''))
        if tag == 'link':
            rel = a.get('rel','').lower().split()
            if 'canonical' in rel: self.canonicals.append(a.get('href',''))
            if 'stylesheet' in rel: self.resources.append(a.get('href',''))
        if tag == 'a' and a.get('href'): self.links.append(a['href'])
        if tag == 'img': self.images.append(a)
        if tag == 'script' and a.get('src'): self.resources.append(a['src'])
        if re.search(r'(?:font-size\s*:\s*0(?:px|em|rem)?\s*[;}]|opacity\s*:\s*0\s*[;}])', a.get('style','')+'}'):
            self.hidden_inline.append(tag)
    def handle_endtag(self, tag):
        if tag == 'title': self.in_title = False
        if tag == self.heading:
            self.headings.append(' '.join(''.join(self.hbuf).split()))
            self.heading = None
    def handle_data(self, data):
        if self.in_title: self.title += data
        if self.heading: self.hbuf.append(data)

def route(path):
    rel = path.relative_to(ROOT).as_posix()
    return SITE + '/' + (rel[:-10] if rel.endswith('index.html') else rel)

def local_target(value, base, inventory):
    p = urlsplit(urljoin(base,value))
    if p.scheme not in ('http','https') or p.netloc not in ('pharmaglobaleng.com','www.pharmaglobaleng.com'):
        return None
    name = unquote(p.path).lstrip('/')
    candidates = [name, name+'index.html' if name.endswith('/') else name+'/index.html', name+'.html']
    for candidate in candidates:
        if candidate in inventory: return candidate
    return '!missing:' + name

def audit(out, live):
    inventory = set(subprocess.check_output(['git','ls-tree','-r','--name-only','HEAD'], cwd=ROOT, text=True).splitlines())
    files = sorted((ROOT/'parts').rglob('*.html'))
    records = []
    issues = defaultdict(list)
    pages = {}
    titles = defaultdict(list)
    descriptions = defaultdict(list)
    incoming = defaultdict(set)
    edges = defaultdict(set)
    def issue(kind, file, detail=''):
        issues[kind].append({'file':file,'detail':detail})
    for f in files:
        rel = f.relative_to(ROOT).as_posix()
        text = f.read_text(encoding='utf-8')
        p = Page(text)
        url = route(f)
        detail = bool(re.fullmatch(r'parts/pge-[^/]+/index.html', rel))
        redirect = bool(p.meta.get('refresh'))
        robots = ','.join(p.meta.get('robots', [])).lower()
        noindex = 'noindex' in robots
        pages[rel] = {'page':p, 'url':url, 'detail':detail, 'noindex':noindex, 'redirect':redirect}
        title = ' '.join(p.title.split())
        desc = p.meta.get('description', [''])[0]
        titles[title].append(rel)
        descriptions[desc].append(rel)
        nodes = []
        for raw in JSONLD.findall(text):
            try: nodes.extend(graph_nodes(json.loads(raw)))
            except json.JSONDecodeError as e: issue('invalid_jsonld', rel, str(e))
        types = Counter(str(n.get('@type')) for n in nodes)
        if not redirect:
            if not title: issue('missing_title', rel)
            if not desc: issue('missing_description',rel)
            if len(p.meta.get('description',[])) != 1: issue('description_tag_count',rel,str(len(p.meta.get('description',[]))))
            if len(p.headings) != 1: issue('h1_count',rel,str(len(p.headings)))
            if p.canonicals != [url]: issue('canonical_mismatch',rel,str(p.canonicals))
            if not p.lang: issue('missing_language',rel)
            if not p.meta.get('viewport'): issue('missing_viewport',rel)
            if detail and not types['Product']: issue('missing_product_schema',rel)
            if detail and noindex: issue('detail_noindex_review',rel)
            if 'nosnippet' in robots or re.search(r'max-snippet\s*:\s*0\b',robots): issue('snippet_disabled_review',rel)
            if p.meta.get('keywords'): issue('meta_keywords_review',rel,p.meta['keywords'][0][:180])
            if PLACEHOLDER.search(title+' '+' '.join(p.headings)): issue('placeholder_entity_name',rel,title)
            if len(title)>90: issue('long_title_review',rel,str(len(title)))
            if len(desc)>220: issue('long_description_review',rel,str(len(desc)))
        for n in nodes:
            if n.get('@type') == 'Product' and detail:
                if str(n.get('sku','')).upper() != f.parent.name.upper(): issue('schema_sku_mismatch',rel,str(n.get('sku')))
                if n.get('url') != url: issue('schema_product_url_mismatch',rel,str(n.get('url')))
                if p.headings and n.get('name') != p.headings[0]: issue('schema_h1_name_mismatch',rel,str(n.get('name')))
            if n.get('@type') in ('Product','ProductModel','CollectionPage') and PLACEHOLDER.search(str(n.get('name',''))):
                issue('schema_placeholder_entity',rel,str(n.get('name')))
            if n.get('@type') in ('Offer','AggregateOffer') and str(n.get('price',n.get('lowPrice',''))) in ('0','0.0','0.00'):
                issue('zero_price_review',rel,str(n)[:160])
        for href in p.links:
            target = local_target(href,url,inventory)
            if target and target.startswith('!missing:'): issue('broken_internal_link',rel,href)
            elif target:
                edges[rel].add(target)
                if target != rel: incoming[target].add(rel)
        for image in p.images:
            target = local_target(image.get('src',''),url,inventory)
            if target and target.startswith('!missing:'): issue('missing_image_file',rel,image.get('src',''))
            if 'alt' not in image: issue('missing_image_alt',rel,image.get('src',''))
            if not image.get('width') or not image.get('height'): issue('image_dimensions_review',rel,image.get('src',''))
        for resource in p.resources:
            target = local_target(resource,url,inventory)
            if target and target.startswith('!missing:'): issue('missing_script_or_stylesheet',rel,resource)
        if p.hidden_inline: issue('hidden_inline_style_review',rel,','.join(p.hidden_inline))
        alias_count = len(re.findall(r'class=[\"\']alias[\"\']',text))
        if alias_count>5: issue('excess_aliases_house_style',rel,str(alias_count))
        if re.search(r'(?:Search recognizes|Parts Store search recognizes)',plain(text),re.I): issue('search_directed_copy_review',rel)
        if re.search(r'Natoli\s+(?:replacement\s+)?(?:part\s+)?(?:number|no\.)',plain(text),re.I): issue('competitor_number_label_review',rel)
        records.append({'file':rel,'url':url,'kind':'detail' if detail else 'other_parts_html','title':title,'description':desc,'h1_count':len(p.headings),'noindex':noindex,'jsonld_types':';'.join(sorted(types)),'aliases':alias_count,'links':len(p.links),'images':len(p.images)})
    for group,data in [('duplicate_title',titles),('duplicate_description',descriptions)]:
        for value,paths in data.items():
            active = [p for p in paths if not pages[p]['noindex'] and not pages[p]['redirect']]
            if value and len(active)>1: issue(group,';'.join(active),value)
    reachable = set()
    queue = deque(['parts/index.html'])
    while queue:
        current=queue.popleft()
        if current in reachable: continue
        reachable.add(current)
        queue.extend(edges[current]-reachable)
    for rel,data in pages.items():
        if data['detail']:
            if not incoming[rel]: issue('no_static_inbound_parts_link_review',rel)
            if rel not in reachable: issue('not_statically_reachable_from_parts_hub_review',rel)
    sitemap_urls=set()
    sitemap_sources=[]
    for name in ('sitemap.xml','sitemap-parts-images.xml'):
        f=ROOT/name
        if not f.exists(): issue('missing_sitemap',name); continue
        try:
            doc=ET.fromstring(f.read_text(encoding='utf-8'))
            urls=[e.text for e in doc.findall('{*}url/{*}loc') if e.text]
            if name=='sitemap.xml': sitemap_urls.update(urls)
            if len(urls)!=len(set(urls)): issue('duplicate_sitemap_urls',name,str(len(urls)-len(set(urls))))
            for url in urls:
                target=local_target(url,SITE+'/',inventory)
                if target and target.startswith('!missing:'): issue('sitemap_missing_target',name,url)
                if target in pages and pages[target]['noindex']: issue('sitemap_noindex_target',name,url)
            for e in doc.findall('.//{http://www.google.com/schemas/sitemap-image/1.1}loc'):
                target=local_target(e.text or '',SITE+'/',inventory)
                if target and target.startswith('!missing:'): issue('sitemap_missing_image',name,e.text or '')
            sitemap_sources.append({'file':name,'urls':len(urls)})
        except ET.ParseError as e: issue('invalid_sitemap_xml',name,str(e))
    for rel,data in pages.items():
        if not data['noindex'] and not data['redirect'] and data['page'].canonicals==[data['url']] and data['url'] not in sitemap_urls:
            issue('indexable_parts_url_missing_from_sitemap',rel,data['url'])
    rp=urllib.robotparser.RobotFileParser()
    robots_path=ROOT/'robots.txt'
    rp.parse(robots_path.read_text(encoding='utf-8').splitlines() if robots_path.exists() else [])
    robots_checks={agent:rp.can_fetch(agent,SITE+'/parts/pge-kik-003/') for agent in ('Googlebot','Bingbot','OAI-SearchBot')}
    live_results=[]
    if live:
        samples=['parts/index.html','parts/kikusui/index.html','parts/korsch/korsch-300/index.html']
        for prefix in ('pge-fet-','pge-kik-','pge-kor-','pge-k300-','pge-man-','pge-stk-'):
            sample=next((r['file'] for r in records if r['kind']=='detail' and Path(r['file']).parent.name.startswith(prefix)),None)
            if sample: samples.append(sample)
        for rel in dict.fromkeys(samples):
            if rel not in pages: continue
            url=pages[rel]['url']
            result={'file':rel,'url':url}
            try:
                req=Request(url,headers={'User-Agent':'PGE-Owner-Quality-Audit/1.0','Cache-Control':'no-cache'})
                with urlopen(req,timeout=30) as response:
                    raw=response.read(3000000).decode('utf-8','replace')
                    parsed=Page(raw)
                    result.update(status=response.status,final_url=response.url,title=parsed.title,canonical=parsed.canonicals,x_robots_tag=response.headers.get('X-Robots-Tag'),repository_title_matches=parsed.title==pages[rel]['page'].title)
            except Exception as e: result['error']=str(e)
            live_results.append(result)
    counts={k:len(v) for k,v in sorted(issues.items())}
    summary={'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'html_pages':len(records),'detail_pages':sum(r['kind']=='detail' for r in records),'other_parts_html':sum(r['kind']!='detail' for r in records),'checks':counts,'sitemaps':sitemap_sources,'robots_source_allows':robots_checks,'live_samples':live_results,'limits':['Automated source audit, not proof of absence of Google manual actions or a ranking guarantee.','OEM and image identity require primary-source engineering validation; existing catalog assertions are not independent proof.','Static link reachability excludes JavaScript-generated links. Review flags are not automatic spam findings.','Live fetches sample only the listed URLs; no impersonation of Googlebot or other verified crawlers.']}
    out.mkdir(parents=True,exist_ok=True)
    (out/'parts-audit-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'parts-audit-issues.json').write_text(json.dumps(issues,indent=2)+'\n')
    with (out/'parts-audit-pages.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0]) if records else ['file']); writer.writeheader(); writer.writerows(records)
    lines=['# Expanded parts-site audit','',f"Commit: `{summary['commit']}`",f"Parts HTML: **{len(records)}**; detail pages: **{summary['detail_pages']}**; other parts pages: **{summary['other_parts_html']}**.",'','## Findings','| Check | Occurrences |','|---|---:|']
    lines += [f'| {k} | {v} |' for k,v in counts.items()]
    lines += ['','## Scope and limitations']+['- '+s for s in summary['limits']]
    (out/'parts-audit.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))
    print('ISSUE EXAMPLES')
    for kind,items in sorted(issues.items()):
        print(kind,json.dumps(items[:12],ensure_ascii=False))
    return summary

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=ROOT/'audit-output')
    parser.add_argument('--live',action='store_true')
    args=parser.parse_args()
    audit(args.output,args.live)
