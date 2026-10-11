#!/usr/bin/env python3
"""Expose every existing numbered catalog page in static HTML and Flight payloads.
No product, metadata or exclusion changes. Re-run after exporting Next pages.
"""
import argparse
import json
import re
from pathlib import Path

NAV = re.compile(r'<nav class="pc-pagination" aria-label="Catalog pages">.*?</nav>', re.S)
PUSH = re.compile(r'self\.__next_f\.push\(\[1,("(?:[^"\\]|\\.)*")\]\)')

def update(root):
    changed=[]
    for path in (root/'parts').rglob('index.html'):
        original=path.read_text(); match=NAV.search(original)
        if not match: continue
        numbers=[int(n) for n in re.findall(r'aria-label="Page (\d+)"',match[0])]
        if not numbers: continue
        total=max(numbers)
        if len(set(numbers)) == total: continue
        base='/' + path.parent.relative_to(root).as_posix().split('/page/')[0] + '/'
        current=int(path.parent.name) if '/page/' in path.as_posix() else 1
        url=lambda n: base if n==1 else base+f'page/{n}/'
        # Only publish links to existing catalog routes.
        assert all((root/url(n).lstrip('/')/'index.html').is_file() for n in range(1,total+1))
        def anchor(n,label=None,rel=None):
            extra=f' rel="{rel}"' if rel else f' aria-label="Page {n}"'+(' aria-current="page"' if n==current else '')
            return f'<a class="pc-page-number" href="{url(n)}"{extra}>{label or n}</a>'
        html='<nav class="pc-pagination" aria-label="Catalog pages">'
        if current>1: html+=anchor(current-1,'← Previous','prev')
        html+=''.join('<span class="pc-page-group">'+anchor(n)+'</span>' for n in range(1,total+1))
        if current<total: html+=anchor(current+1,'Next →','next')
        html+='</nav>'
        text=NAV.sub(lambda _:html, original)
        def flight_anchor(n,label=None,rel=None):
            props={'className':'pc-page-number','href':url(n),'children':label or n}
            if rel: props['rel']=rel
            else:
                props['aria-label']=f'Page {n}'
                props['aria-current']='page' if n==current else '$undefined'
            return ['$', 'a', None, props]
        def walk(node):
            if isinstance(node,list):
                if len(node)==4 and node[1]=='nav' and isinstance(node[3],dict) and node[3].get('className')=='pc-pagination':
                    node[3]['children']=([flight_anchor(current-1,'← Previous','prev')] if current>1 else [])+[ ['$', 'span', str(n), {'className':'pc-page-group','children':flight_anchor(n)}] for n in range(1,total+1)]+([flight_anchor(current+1,'Next →','next')] if current<total else [])
                else:
                    for v in node: walk(v)
            elif isinstance(node,dict):
                for v in node.values(): walk(v)
        def payload(raw):
            result=[]
            for line in raw.splitlines(keepends=True):
                if '"pc-pagination"' in line:
                    prefix,sep,body=line.partition(':')
                    try:
                        node=json.loads(body);walk(node)
                        line=prefix+sep+json.dumps(node,separators=(',',':'),ensure_ascii=False)+ ('\n' if line.endswith('\n') else '')
                    except json.JSONDecodeError: pass
                result.append(line)
            return ''.join(result)
        text=PUSH.sub(lambda m:'self.__next_f.push([1,'+json.dumps(payload(json.loads(m[1])),ensure_ascii=False)+'])',text)
        if text!=original:
            path.write_text(text);changed.append(str(path.relative_to(root)))
        for sibling in path.parent.glob('*.txt'):
            old=sibling.read_text();new=payload(old)
            if new!=old: sibling.write_text(new);changed.append(str(sibling.relative_to(root)))
    print(json.dumps({'changed_count':len(changed),'files':changed},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);update(parser.parse_args().root)
