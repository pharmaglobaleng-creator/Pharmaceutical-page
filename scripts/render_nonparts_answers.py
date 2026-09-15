#!/usr/bin/env python3
"""Render visible answer cards and matching JSON-LD from one reviewed source.

Run after editing data/nonparts-answer-cards.json. --check verifies generated
HTML is current without writing. Does not change the surrounding article copy.
"""
from pathlib import Path
import argparse
import html
import json
import re

ROOT=Path(__file__).resolve().parents[1]
START='<!-- pge-answer-cards:start -->'
END='<!-- pge-answer-cards:end -->'
STYLE='<link rel="stylesheet" href="/assets/css/pge-guide-answers.css">'

def render(source, pairs):
    if len(pairs)!=25 or len({p['question'].casefold() for p in pairs})!=25:
        raise ValueError('Each page needs exactly 25 distinct reviewed questions')
    for p in pairs:
        if set(p)!={'question','answer'} or not all(isinstance(v,str) and v.strip() for v in p.values()):
            raise ValueError('Invalid answer record')
    canonical=re.search(r'<link\b(?=[^>]*\brel="canonical")(?=[^>]*\bhref="([^"]+)")[^>]*>',source,re.I)
    heading=re.search(r'<h1\b[^>]*>(.*?)</h1>',source,re.S|re.I)
    if not canonical or not heading or '</head>' not in source or '</main>' not in source:
        raise ValueError('Expected a canonical, H1, head and main')
    url=html.unescape(canonical.group(1))
    title=' '.join(html.unescape(re.sub('<[^>]+>',' ',heading.group(1))).split())
    body=[START,'<section class="pge-answers" id="answers" aria-labelledby="answers-heading"><div class="wrap">',
          '<h2 id="answers-heading">25 practical questions and answers</h2>',
          '<p class="pge-answers-intro">Quick answers to the questions covered in this guide. Use the detailed sections above for the evidence and context behind each answer.</p>',
          '<div class="pge-answer-grid">']
    for n,p in enumerate(pairs,1):
        body.append(f'<article class="pge-answer-card" id="answer-{n}"><span class="pge-answer-number" aria-hidden="true">{n:02d}</span><h3>{html.escape(p["question"])}</h3><p>{html.escape(p["answer"])}</p></article>')
    body.extend(['</div></div></section>',END])
    block='\n'.join(body)
    if START in source:
        source=re.sub(re.escape(START)+'.*?'+re.escape(END),lambda _:block,source,count=1,flags=re.S)
    else:
        source=source.replace('</main>',block+'\n</main>',1)
    graph={'@context':'https://schema.org','@type':'FAQPage','@id':url+'#answers','url':url+'#answers',
           'name':title+' — questions and answers','inLanguage':'en-US',
           'mainEntity':[{'@type':'Question','@id':url+f'#answer-{n}','name':p['question'],
                         'acceptedAnswer':{'@type':'Answer','text':p['answer']}} for n,p in enumerate(pairs,1)]}
    encoded=json.dumps(graph,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
    script='<script id="pge-answer-schema" type="application/ld+json">'+encoded+'</script>'
    if 'id="pge-answer-schema"' in source:
        source=re.sub(r'<script id="pge-answer-schema".*?</script>',lambda _:script,source,count=1,flags=re.S)
    else:source=source.replace('</head>',script+'\n</head>',1)
    if STYLE not in source:source=source.replace('</head>',STYLE+'\n</head>',1)
    return source

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    data=json.loads((ROOT/'data/nonparts-answer-cards.json').read_text())
    if len(data)!=27:raise SystemExit('Expected the reviewed 27-page inventory')
    changed=[]
    for relative,pairs in data.items():
        path=ROOT/relative
        if path.suffix!='.html' or '..' in Path(relative).parts or not path.is_relative_to(ROOT):raise ValueError(relative)
        source=path.read_text();updated=render(source,pairs)
        if updated!=source:
            changed.append(relative)
            if not args.check:path.write_text(updated)
    if args.check and changed:raise SystemExit('Answer cards need rendering: '+', '.join(changed))
    print(f'27 pages; 675 matching visible/structured answers; {len(changed)} '+('pending changes' if args.check else 'pages updated'))

if __name__=='__main__':main()
