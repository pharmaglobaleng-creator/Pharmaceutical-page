"""Build the eight authorized guides without modifying shared site assets.
Runs on an isolated review branch. It never writes or pushes main.
"""
import copy, hashlib, html, json, re, subprocess, threading
from collections import Counter
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, unquote
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ROOT = Path.cwd()
OUT = ROOT / 'work-artifacts'
OUT.mkdir(exist_ok=True)
DOMAIN = 'https://pharmaglobaleng.com'
EXPECTED = {
 'solutions/tablet-sticking.html', 'solutions/tablet-picking.html',
 'solutions/tablet-binding.html', 'solutions/tablet-capping.html',
 'solutions/tablet-lamination.html', 'solutions/tablet-compression-defects.html',
 'services/tablet-punch-coatings.html', 'services/tablet-punch-polishing.html'
}
CSS = '''
.pge-guide{font-size:18px;line-height:1.75;overflow-wrap:break-word}
.pge-guide .hero{padding:64px 0 50px}.pge-guide .hero .wrap{max-width:1060px}
.pge-guide h1{font-size:clamp(34px,5.2vw,62px);line-height:1.12;letter-spacing:-.035em}
.pge-guide h2{font-size:clamp(25px,3.3vw,36px);line-height:1.25;letter-spacing:-.02em;margin:0 0 18px}
.pge-guide h3{font-size:22px;line-height:1.35;margin:26px 0 10px}
.pge-guide .guide-shell{max-width:980px;margin:auto;padding:0 22px 64px}
.pge-guide article>section,.pge-guide .guide-related,.pge-guide .guide-references{margin:46px 0 0;padding-top:32px;border-top:1px solid var(--line)}
.pge-guide p,.pge-guide li{color:var(--muted)}.pge-guide strong{color:var(--text)}
.pge-guide p{margin:0 0 18px}.pge-guide li+li{margin-top:10px}
.pge-guide .lead{margin:24px 0 0}.pge-guide .guide-meta{font-size:14px;margin:22px 0 0}
.pge-guide .guide-shell a{color:var(--cyan);text-underline-offset:3px}
.pge-guide .guide-toc{display:flex;flex-wrap:wrap;gap:10px 22px;margin:28px 0 0;font-size:15px}
.pge-guide .guide-toc a{color:var(--cyan)}
.pge-guide .guide-callout{padding:24px;border:1px solid var(--line);border-left:4px solid var(--cyan);border-radius:0 12px 12px 0;background:var(--bg-alt)}
.pge-guide .guide-callout p:last-child{margin-bottom:0}
.pge-guide .table-wrap{margin:25px 0;overflow-x:auto;border:1px solid var(--line);border-radius:12px}
.pge-guide table{min-width:580px;font-size:16px;line-height:1.6}.pge-guide th{font-size:15px;text-transform:none;letter-spacing:normal}
.pge-guide caption{padding:14px;text-align:left;color:var(--muted);font-size:15px}
.pge-guide .guide-related a{display:inline-block;margin:0 18px 12px 0}
.pge-guide .guide-references{font-size:14px}.pge-guide .guide-references h2{font-size:22px}
.pge-guide .guide-references li{overflow-wrap:anywhere}.pge-guide .ref{font-size:12px;vertical-align:super;white-space:nowrap}
.pge-guide .guide-faq details{margin:14px 0}.pge-guide .guide-faq details p{margin:14px 0 0}
.pge-guide section[id],.pge-guide h2[id],.pge-guide .legacy-anchor{scroll-margin-top:130px}
.pge-guide .guide-cta{padding:28px;background:var(--bg-alt);border:1px solid var(--line);border-radius:14px}
.pge-guide .guide-cta .actions a{color:white}.pge-guide .guide-cta h2{margin-top:0}
.pge-guide .microfinish-photo,.pge-guide .polishing-photo{margin:30px 0}.pge-guide figure img{max-width:100%;height:auto}
.pge-guide figure figcaption{font-size:14px;line-height:1.6}
.pge-skip{position:fixed;top:-100px;left:16px;background:white;color:#172437;padding:12px;z-index:100}.pge-skip:focus{top:10px}
.pge-guide a:focus-visible,.pge-guide summary:focus-visible,.pge-guide [tabindex]:focus-visible{outline:3px solid var(--cyan);outline-offset:4px}
@media(max-width:650px){.pge-guide{font-size:17px}.pge-guide .hero{padding:38px 0}.pge-guide .guide-shell{padding:0 18px 40px}.pge-guide article>section{margin-top:32px;padding-top:26px}.pge-guide .guide-callout,.pge-guide .guide-cta{padding:20px}.pge-guide .guide-toc{gap:12px 18px}.pge-guide .actions .btn{max-width:100%;white-space:normal;text-align:center}.pge-guide .guide-meta{font-size:13px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
'''

def parse(text):
    return BeautifulSoup(text, 'html.parser')

def words(node):
    node = copy.deepcopy(node)
    for x in node.select('script,style'):
        x.decompose()
    return len(re.findall(r"\b[\w'-]+\b", node.get_text(' ', strip=True)))

def append_fragment(target, content):
    frag = parse(content)
    for child in list(frag.contents):
        target.append(child.extract())

def update_meta(soup, key, val, prop=False):
    attr = 'property' if prop else 'name'
    found = soup.find_all('meta', attrs={attr:key})
    for tag in found[1:]: tag.decompose()
    tag = found[0] if found else soup.new_tag('meta', attrs={attr:key})
    tag['content'] = val
    if not found: soup.head.append(tag)

configs = [json.loads(p.read_text()) for p in sorted((ROOT / '.content-depth').glob('page-*.json'))]
assert {x['path'] for x in configs} == EXPECTED, 'Unexpected target set'
audit = []
originals = {}
for cfg in configs:
    path = cfg['path']
    source = (ROOT / path).read_text()
    originals[path] = source
    soup = parse(source)
    before = copy.deepcopy(soup)
    old_main = soup.main
    assert old_main is not None
    canonical = soup.find('link', rel='canonical')['href']
    assert canonical == DOMAIN + '/' + path
    old_header = str(soup.select_one('header.site-header'))
    old_footer = str(soup.body.find('footer', recursive=False))
    old_images = Counter(img.get('src','') for img in soup.find_all('img'))
    old_scripts = [str(x) for x in soup.find_all('script') if x.get('type') != 'application/ld+json']
    if cfg.get('mode') == 'extend':
        location = soup.find('h2', id='surface').find_parent('section')
        for tag in list(parse(cfg['body']).contents):
            location.insert_before(tag.extract())
        source3 = soup.find(id='source-3')
        if source3 and source3.a:
            source3.a['href'] = DOMAIN + '/solutions/tablet-compression-defects.html'
            source3.a.string = 'PharmaGlobalEng — Compression-defect investigation and evidence records'
        refs = soup.select_one('.references ol')
        for item in cfg.get('sources',[]):
            li = soup.new_tag('li', id=item['id'])
            a = soup.new_tag('a', href=item['url']); a.string = item['title']; li.append(a); refs.append(li)
        for tag in soup.find_all('script', type='application/ld+json'):
            doc = json.loads(tag.string)
            for node in doc.get('@graph',[doc]):
                if node.get('@type') in ('Article','WebPage'):
                    node['dateModified'] = '2026-09-10'
            tag.string = json.dumps(doc, ensure_ascii=False)
        small = soup.new_tag('p', attrs={'class':'small'}); small.string = 'Updated September 10, 2026 · PharmaGlobalEng'
        soup.select_one('.article-head').append(small)
    else:
        body = cfg['body']
        frag = parse(body)
        for placeholder in list(frag.select('[data-preserve-figure]')):
            selector = placeholder['data-preserve-figure']
            figure = old_main.select_one(selector)
            assert figure is not None, (path, selector)
            placeholder.replace_with(copy.deepcopy(figure))
        body = str(frag)
        toc = ''.join('<a href="#'+html.escape(x['id'])+'">'+html.escape(x['label'])+'</a>' for x in cfg['toc'])
        related = ''.join('<a href="'+html.escape(x['url'])+'">'+html.escape(x['title'])+'</a>' for x in cfg['links'])
        refs = ''.join('<li id="'+html.escape(x['id'])+'"><a href="'+html.escape(x['url'])+'">'+html.escape(x['title'])+'</a></li>' for x in cfg['sources'])
        group = 'Services' if path.startswith('services/') else 'Solutions'
        main = parse('<main id="main" class="pge-guide" tabindex="-1"><section class="hero"><div class="wrap"><nav class="crumb" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/'+group.lower()+'/">'+group+'</a> / '+html.escape(cfg['short'])+'</nav><p class="eyebrow">PharmaGlobalEng / Pharmaceutical tooling support</p><h1>'+html.escape(cfg['headline'])+'</h1><p class="lead">'+html.escape(cfg['lead'])+'</p><div class="actions"><a class="btn primary" href="/contact.html">Request a tooling evaluation</a><a class="btn secondary" href="tel:+17324397849">Call +1 (732) 439-7849</a></div><p class="guide-meta">Updated September 10, 2026 · PharmaGlobalEng</p><nav class="guide-toc" aria-label="On this page">'+toc+'</nav></div></section><div class="guide-shell"><article>'+body+'</article><aside class="guide-related" aria-labelledby="guide-related-title"><h2 id="guide-related-title">Related tooling guidance</h2>'+related+'</aside><section class="guide-references" aria-labelledby="guide-reference-title"><h2 id="guide-reference-title">Technical references</h2><p>These sources support the technical principles. The inspection prompts are guidance for organizing an evaluation, not a diagnosis or an approved manufacturing procedure. The cited authors do not endorse PharmaGlobalEng.</p><ol>'+refs+'</ol></section></div></main>').main
        ids = {x['id'] for x in main.select('[id]')}
        for x in old_main.select('[id]'):
            if x['id'] not in ids:
                anchor = soup.new_tag('span', id=x['id'], attrs={'class':'legacy-anchor','aria-hidden':'true'})
                main.select_one('article').insert(0, anchor); ids.add(x['id'])
        old_main.replace_with(main)
        soup.title.string = cfg['title']
        update_meta(soup, 'description', cfg['description'])
        for key,val in [('og:title',cfg['title']),('og:description',cfg['description']),('og:url',canonical),('og:type','article')]:
            update_meta(soup,key,val,True)
        for key,val in [('twitter:card','summary'),('twitter:title',cfg['title']),('twitter:description',cfg['description'])]: update_meta(soup,key,val)
        for tag in list(soup.find_all('script',type='application/ld+json')): tag.decompose()
        org={'@type':'Organization','@id':DOMAIN+'/#organization','name':'PharmaGlobalEng','url':DOMAIN+'/','telephone':'+1-732-439-7849','email':'info@pharmaglobaleng.com'}
        graph=[org,{'@type':'WebSite','@id':DOMAIN+'/#website','url':DOMAIN+'/','name':'PharmaGlobalEng','publisher':{'@id':org['@id']}},{'@type':'WebPage','@id':canonical+'#webpage','url':canonical,'name':cfg['title'],'description':cfg['description'],'inLanguage':'en','isPartOf':{'@id':DOMAIN+'/#website'},'dateModified':'2026-09-10','breadcrumb':{'@id':canonical+'#breadcrumb'}},{'@type':'Article','@id':canonical+'#article','headline':cfg['headline'],'author':{'@id':org['@id']},'publisher':{'@id':org['@id']},'mainEntityOfPage':{'@id':canonical+'#webpage'},'inLanguage':'en','dateModified':'2026-09-10'},{'@type':'BreadcrumbList','@id':canonical+'#breadcrumb','itemListElement':[{'@type':'ListItem','position':1,'name':'Home','item':DOMAIN+'/'},{'@type':'ListItem','position':2,'name':group,'item':DOMAIN+'/'+group.lower()+'/'},{'@type':'ListItem','position':3,'name':cfg['short'],'item':canonical}]}]
        if cfg.get('service'):
            graph.append({'@type':'Service','@id':canonical+'#service','name':cfg['service'],'url':canonical,'provider':{'@id':org['@id']},'description':cfg['description']})
        tag=soup.new_tag('script',type='application/ld+json'); tag.string=json.dumps({'@context':'https://schema.org','@graph':graph},ensure_ascii=False); soup.head.append(tag)
        style=soup.new_tag('style',id='pge-content-depth'); style.string=CSS; soup.head.append(style)
        if not soup.select_one('a[href="#main"]'):
            skip=soup.new_tag('a',href='#main',attrs={'class':'pge-skip'}); skip.string='Skip to content'; soup.body.insert(0,skip)
    assert str(soup.select_one('header.site-header')) == old_header, path+' header altered'
    assert str(soup.body.find('footer',recursive=False)) == old_footer, path+' footer altered'
    assert Counter(x.get('src','') for x in soup.find_all('img')) == old_images, path+' image lost'
    assert [str(x) for x in soup.find_all('script') if x.get('type') != 'application/ld+json'] == old_scripts, path+' scripts altered'
    text = str(soup)
    (ROOT/path).write_text(text)
    dest=OUT/path; dest.parent.mkdir(parents=True,exist_ok=True); dest.write_text(text)
    audit.append({'path':path,'before_words':words(before.main),'after_words':words(soup.main),'bytes':len(text.encode()),'preserved_images':len(soup.find_all('img')),'header_preserved':True,'footer_preserved':True})

for row in audit:
    path=row['path']; soup=parse((ROOT/path).read_text())
    assert len(soup.find_all('h1')) == 1, path+' h1'
    ids=[x['id'] for x in soup.select('[id]')]
    assert len(ids)==len(set(ids)), path+' duplicate ids'
    assert row['after_words'] >= 650, path+' incomplete content'
    assert soup.find('link',rel='canonical')['href']==DOMAIN+'/'+path
    assert 'noindex' not in soup.find('meta',attrs={'name':'robots'})['content'].lower()
    for j in soup.find_all('script',type='application/ld+json'): json.loads(j.string)
    visible=soup.main.get_text(' ',strip=True)
    assert not any(x in visible for x in ('Internal Linking','Structured Data','SEO topics are integrated','What is tablet binding solutions','What is tablet capping solutions','What is tablet lamination solutions','What is tablet picking solutions'))
    for a in soup.main.find_all('a',href=True):
        u=urlparse(a['href'])
        if u.scheme in ('mailto','tel'): continue
        if u.netloc and u.netloc != 'pharmaglobaleng.com': continue
        if not u.path: target=ROOT/path
        else:
            target=ROOT/unquote(u.path).lstrip('/')
            if target.is_dir(): target=target/'index.html'
        assert target.is_file(), (path,'missing internal link',a['href'])
        if u.fragment:
            doc=parse(target.read_text())
            assert doc.find(id=unquote(u.fragment)), (path,'missing anchor',a['href'])
    row['html_checks']='passed'

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
server=ThreadingHTTPServer(('127.0.0.1',8765),partial(QuietHandler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
    browser=p.chromium.launch()
    for width,label in [(1440,'desktop'),(390,'mobile')]:
        page=browser.new_page(viewport={'width':width,'height':1000},device_scale_factor=1)
        for row in audit:
            response=page.goto('http://127.0.0.1:8765/'+row['path'],wait_until='domcontentloaded')
            assert response.status==200
            page.wait_for_timeout(300)
            assert page.locator('h1').is_visible()
            assert page.locator('header.site-header a[href="tel:+17324397849"]').is_visible()
            overflow=page.evaluate('document.documentElement.scrollWidth > window.innerWidth + 2')
            assert not overflow,(row['path'],label,'page overflows')
            page.screenshot(path=str(OUT/(Path(row['path']).stem+'-'+label+'.png')),full_page=True,timeout=30000)
            row[label+'_layout']='passed'
        page.close()
    browser.close()
server.shutdown()
for row in audit:
    row['sha']=subprocess.check_output(['git','hash-object','-w',row['path']],text=True).strip()
(OUT/'audit.json').write_text(json.dumps(audit,indent=2))
(ROOT/'.content-depth/manifest.json').write_text(json.dumps(audit,indent=2))
print(json.dumps(audit,indent=2))
