#!/usr/bin/env python3
"""Apply the approved header identity, preserving page content and React payloads.

Only public landing-page headers, the legacy floating phone widget, and header
stylesheet links are changed. Product data, JSON-LD, canonical URLs, main content,
forms, and navigation destinations must remain intact. Safe to run repeatedly.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
PHONE = '+1 (732) 439-7849'
TEL = '+17324397849'
LOGO = '/assets/images/pge-header-logo.webp'
CSS = '/assets/css/pge-header.css'
MARK = 'data-pge-header="v1"'
SKIP_PREFIXES = ('next-app/', '_next/', '.git/', '.github/', 'docs/')
SKIP_FILES = {'googleb09af90219443617.html'}
HEADER_RE = re.compile(r'<header\b[^>]*>.*?</header\s*>', re.I | re.S)
BRAND_RE = re.compile(r'<a\b(?=[^>]*\bclass=["\'][^"\']*\b(?:brand|pc-brand|logo)\b)[^>]*>.*?</a\s*>', re.I | re.S)
FLOAT_RE = re.compile(r'<!-- PGE-SITEWIDE-PHONE:START -->.*?<!-- PGE-SITEWIDE-PHONE:END -->', re.S)
OLD_CSS_RE = re.compile(r'<link\b[^>]*href=["\']/assets/css/pge-phone\.css(?:\?[^"\']*)?["\'][^>]*>\n?', re.I)
FLIGHT_RE = re.compile(r'<script\b[^>]*>self\.__next_f\.push\((\[.*?\])\)</script>', re.S)

IDENTITY = ('<div class="pge-header-identity">'
 '<a class="pge-header-brand" href="/" aria-label="PharmaGlobalEng home">'
 f'<img class="pge-header-logo" src="{LOGO}" width="34" height="30" alt="" decoding="async">'
 '<span class="pge-header-wordmark">PharmaGlobal<span>Eng</span></span></a>'
 f'<a class="pge-header-phone" href="tel:{TEL}" aria-label="Call PharmaGlobalEng at {PHONE}">{PHONE}</a></div>')
CSS_LINK = f'<link rel="stylesheet" href="{CSS}" data-pge-header-css="true">'
BASIC_HEADER = (f'<header class="pge-header-bar" {MARK}><div class="pge-header-shell">'+IDENTITY+
 '<nav class="pge-basic-nav" aria-label="Primary navigation"><a href="/">Home</a><a href="/parts/">Parts Store</a><a href="/contact.html">Contact</a></nav></div></header>')


def element(tag: str, props: dict):
    return ['$', tag, None, props]


def identity_node():
    return element('div', {'className': 'pge-header-identity', 'children': [
        element('a', {'className':'pge-header-brand','href':'/','aria-label':'PharmaGlobalEng home','children':[
            element('img',{'className':'pge-header-logo','src':LOGO,'width':34,'height':30,'alt':'','decoding':'async'}),
            element('span',{'className':'pge-header-wordmark','children':['PharmaGlobal',element('span',{'children':'Eng'})]})]}),
        element('a',{'className':'pge-header-phone','href':'tel:'+TEL,'aria-label':'Call PharmaGlobalEng at '+PHONE,'children':PHONE})]})


def fragment(text: str, *, insert: bool = False) -> str:
    """Edit only the visible header region in HTML or a React raw-HTML string."""
    text = FLOAT_RE.sub('', text)
    match = HEADER_RE.search(text)
    if match and MARK in match[0]:
        return text
    if match:
        header = match[0]
        brand = BRAND_RE.search(header)
        if brand and 'Pharma' in brand[0]:
            new_header = header[:brand.start()] + IDENTITY + header[brand.end():]
            new_header = re.sub(r'<header\b', '<header '+MARK, new_header, count=1, flags=re.I)
            return text[:match.start()]+new_header+text[match.end():]
    if insert:
        # These pages have an article header, not a site-navigation header.
        # Keep their entire original article and insert a separate banner.
        text, n = re.subn(r'(<body\b[^>]*>)', lambda m:m[1]+'\n'+BASIC_HEADER, text, count=1, flags=re.I)
        if n != 1:
            raise ValueError('Expected a body element when adding a missing site header')
    return text


def walk_flight(value):
    """Update server-rendered catalog headers and raw legacy-homepage HTML only."""
    if isinstance(value, str):
        return fragment(value) if '<header' in value or '<!-- PGE-SITEWIDE-PHONE:START -->' in value else value
    if isinstance(value, dict):
        return {k:walk_flight(v) for k,v in value.items()}
    if not isinstance(value, list):
        return value
    if len(value)>=4 and value[0]=='$' and value[1]=='header' and isinstance(value[3],dict):
        props=value[3]
        if props.get('data-pge-header')=='v1': return value
        if props.get('className')=='pc-header':
            result=copy.deepcopy(value)
            inner=result[3]['children']
            if not (isinstance(inner,list) and inner[1]=='div' and inner[3].get('className')=='pc-container pc-header-inner'):
                raise ValueError('Unexpected catalog header container; refusing partial hydration update')
            children=inner[3]['children']
            matches=[i for i,node in enumerate(children) if isinstance(node,list) and len(node)>=4 and node[1]=='a' and node[3].get('className')=='pc-brand']
            if len(matches)!=1: raise ValueError('Expected exactly one catalog brand in React header')
            children[matches[0]]=identity_node()
            result[3]['data-pge-header']='v1'
            return result
    return [walk_flight(v) for v in value]


def flight_payload(payload: str) -> str:
    """Parse text records by UTF-8 byte length, not by newlines or guessed tokens."""
    raw=payload.encode('utf-8'); out=[]; pos=0
    while pos<len(raw):
        match=re.match(rb'([0-9a-f]+):T([0-9a-f]+),', raw[pos:])
        if match:
            length=int(match[2],16); start=pos+match.end(); stop=start+length
            if stop>len(raw): raise ValueError('Incomplete React text record')
            text=raw[start:stop].decode('utf-8')
            updated=fragment(text) if '<header' in text or '<!-- PGE-SITEWIDE-PHONE:START -->' in text else text
            encoded=updated.encode('utf-8')
            out.append(match[1]+b':T'+format(len(encoded),'x').encode()+b','+encoded)
            pos=stop
            continue
        end=raw.find(b'\n',pos)
        if end<0: end=len(raw)
        line=raw[pos:end]
        m=re.match(rb'^([0-9a-f]+:)([\[\{"].*)$',line)
        if m:
            try: data=json.loads(m[2])
            except (json.JSONDecodeError,UnicodeDecodeError):
                raise ValueError('Unrecognized JSON in React flight record')
            changed=walk_flight(data)
            if changed!=data:
                line=m[1]+json.dumps(changed,ensure_ascii=False,separators=(',',':')).encode()
        out.append(line+(b'\n' if end<len(raw) else b'')); pos=end+1
    return b''.join(out).decode('utf-8')


def patch_flight_scripts(text: str) -> str:
    matches=[]; chunks=[]
    for match in FLIGHT_RE.finditer(text):
        data=json.loads(match[1])
        if len(data)==2 and data[0]==1 and isinstance(data[1],str):
            matches.append(match); chunks.append(data[1])
    if not matches: return text
    payload=''.join(chunks); changed=flight_payload(payload)
    if changed==payload: return text
    # Preserve initialization and other script types; coalesce only the text stream.
    # RSC permits arbitrary transport boundaries. UTF-8 text lengths are recalculated.
    first='<script>self.__next_f.push('+json.dumps([1,changed],ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')+')</script>'
    for i,m in reversed(list(enumerate(matches))):
        text=text[:m.start()]+(first if i==0 else '')+text[m.end():]
    return text


def protected(text: str):
    """Exact user content and SEO invariants; no engine/OEM data is regenerated."""
    return {
      'main': re.findall(r'<main\b.*?</main\s*>',text,re.I|re.S),
      'metadata': re.findall(r'<(?:meta|title)\b[^>]*>(?:[^<]*</title>)?',text,re.I),
      'canonical': re.findall(r'<link\b[^>]*rel=["\']canonical["\'][^>]*>',text,re.I),
      'schema':re.findall(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>.*?</script>',text,re.I|re.S),
      'scripts':[m[0] for m in re.finditer(r'<script\b[^>]*>.*?</script>',text,re.I|re.S) if 'self.__next_f' not in m[0] and 'application/ld+json' not in m[0]],
    }


def transform_html(text: str) -> str:
    saved=protected(text)
    updated=fragment(text,insert=True)
    updated=OLD_CSS_RE.sub('',updated)
    if 'data-pge-header-css=' not in updated:
        updated,n=re.subn(r'</head\s*>',CSS_LINK+'\n</head>',updated,count=1,flags=re.I)
        if n!=1: raise ValueError('Missing head for header CSS')
    updated=patch_flight_scripts(updated)
    if protected(updated)!=saved:
        raise ValueError('Protected main content, SEO or behavior changed')
    visible=updated.split('<script>self.__next_f')[0]
    if visible.count('class="pge-header-identity"')!=1:
        raise ValueError('Expected one visible header identity')
    if 'class="pge-sitewide-phone"' in updated:
        raise ValueError('A legacy floating phone widget remains')
    return updated


def public_pages(root):
    pages=[]; excluded=[]
    for p in sorted(root.rglob('*.html')):
        rel=p.relative_to(root).as_posix()
        if rel.startswith(SKIP_PREFIXES):continue
        text=p.read_text(encoding='utf-8')
        if rel in SKIP_FILES or re.search(r'<meta\b[^>]*http-equiv=["\']refresh["\']',text,re.I):
            excluded.append(rel);continue
        pages.append(p)
    return pages,excluded


def prepare_sources(root: Path):
    """One-time, explicit template migration for future Next.js exports."""
    from PIL import Image
    jsx=IDENTITY.replace('class=', 'className=').replace('decoding="async">', 'decoding="async" />')
    path=root/'next-app/components/catalog/CatalogShell.jsx'; text=path.read_text()
    if 'data-pge-header="v1"' not in text:
        old='<a href="/" className="pc-brand" aria-label="PharmaGlobalEng home">Pharma<span>Global</span>Eng<small>PHARMACEUTICAL EQUIPMENT SOLUTIONS</small></a>'
        if text.count(old)!=1:raise ValueError('Unexpected CatalogShell brand source')
        text=text.replace(old,jsx,1).replace('<header className="pc-header">','<header className="pc-header" data-pge-header="v1">',1)
        path.write_text(text)
    path=root/'next-app/components/SiteHeader.js';text=path.read_text()
    if 'data-pge-header="v1"' not in text:
        old='<Link className="brand" href="/" aria-label="PharmaGlobalEng home">PharmaGlobal<span>Eng</span></Link>'
        if text.count(old)!=1:raise ValueError('Unexpected SiteHeader brand source')
        path.write_text(text.replace(old,jsx,1).replace('<header className="site-header">','<header className="site-header" data-pge-header="v1">',1))
    path=root/'next-app/app/layout.js';text=path.read_text()
    if "import './pge-header.css';" not in text:
        if "import './globals.css';" not in text:raise ValueError('Unexpected root layout')
        path.write_text(text.replace("import './globals.css';","import './globals.css';\nimport './pge-header.css';",1))
    (root/'next-app/app/pge-header.css').write_bytes((root/CSS.lstrip('/')).read_bytes())
    (root/'scripts/apply_sitewide_phone.py').write_text('#!/usr/bin/env python3\n"""Compatibility entry point: the approved phone CTA now lives in the header.\nExisting workflows retain this filename; never reintroduce a floating badge.\n"""\nfrom apply_sitewide_header import main\n\nif __name__ == "__main__":\n    main()\n')
    path=root/LOGO.lstrip('/')
    if not path.exists():
        with Image.open(root/'assets/images/about-pge-logo-restored-640.webp') as source:
            image=source.convert('RGB');image.thumbnail((102,102),Image.Resampling.LANCZOS)
            image.save(path,'WEBP',lossless=True,method=6)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--report',type=Path);parser.add_argument('--prepare-sources',action='store_true')
    args=parser.parse_args();root=args.root.resolve()
    if args.prepare_sources:prepare_sources(root)
    pages,excluded=public_pages(root)
    modified=[]; pending=[];kinds=Counter()
    for p in pages:
        rel=p.relative_to(root).as_posix();text=p.read_text(encoding='utf-8')
        try:updated=transform_html(text)
        except Exception as e: raise ValueError(f'{rel}: {e}') from e
        kinds['parts' if rel.startswith('parts/') else 'other']+=1
        if updated!=text:pending.append((p,updated));modified.append(rel)
    # Next.js navigation data must agree with the visible static HTML.
    flight_files=0
    for p in sorted(root.rglob('*.txt')):
        if p.relative_to(root).as_posix().startswith(SKIP_PREFIXES):continue
        text=p.read_text(encoding='utf-8')
        if not any(marker in text for marker in ('pc-header', '<header', 'pge-header-identity')):continue
        updated=flight_payload(text);flight_files+=1
        if updated!=text:pending.append((p,updated));modified.append(p.relative_to(root).as_posix())
    # Finish validation of every file before writing any of the generated output.
    for p,text in pending:p.write_text(text,encoding='utf-8')
    report={'landing_pages':len(pages),'parts_pages':kinds['parts'],'other_pages':kinds['other'],
      'react_navigation_payloads':flight_files,'excluded_verification_or_redirect_files':excluded,
      'changed_files':modified,'main_content_metadata_schema_and_behavior_preserved':True}
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='changed_files'},indent=2))
    print(f'{len(modified)} files changed.')

if __name__=='__main__':main()
