#!/usr/bin/env python3
"""Idempotent, limited corrections for independently reproduced audit findings.
Never infer a Korsch model from the legacy /korsch-300/ URL.
"""
from pathlib import Path
import re
from html import escape
import json
ROOT=Path(__file__).resolve().parents[1]

def apply():
    changed=[]
    # Resolve the homepage correctly in the independent audit itself.
    audit=ROOT/'scripts/audit_parts_site.py'
    text=audit.read_text(encoding='utf-8')
    old="name = unquote(p.path).lstrip('/')\n    candidates"
    new="name = unquote(p.path).lstrip('/')\n    if not name:\n        return 'index.html' if 'index.html' in inventory else '!missing:index.html'\n    candidates"
    if old in text:
        audit.write_text(text.replace(old,new,1),encoding='utf-8'); changed.append(str(audit.relative_to(ROOT)))
    path=ROOT/'parts/korsch/korsch-300/index.html'
    text=path.read_text(encoding='utf-8')
    original=text
    title='Korsch Component Identification Requests | PharmaGlobalEng'
    heading='Korsch Components Requiring Identification'
    description='Review 49 Korsch component records requiring identification. Exact model, part identity, dimensions and compatibility must be confirmed before quotation.'
    text=re.sub(r'<title>.*?</title>',lambda m:'<title>'+escape(title)+'</title>',text,count=1,flags=re.S)
    text=re.sub(r'<meta name="description" content="[^"]*">',lambda m:'<meta name="description" content="'+escape(description,quote=True)+'">',text,count=1)
    text=re.sub(r'<h1>.*?</h1>',lambda m:'<h1>'+heading+'</h1>',text,count=1,flags=re.S)
    def schema(match):
        data=json.loads(match.group(2))
        for node in data.get('@graph',[]):
            if node.get('@type')=='CollectionPage':
                node['name']=heading; node['description']=description
            if node.get('@type')=='BreadcrumbList':
                for item in node.get('itemListElement',[]):
                    if item.get('item')=='https://pharmaglobaleng.com/parts/korsch/korsch-300/':
                        item['name']='Component identification'
        return match.group(1)+json.dumps(data,ensure_ascii=False,separators=(',',':'))+match.group(3)
    text=re.sub(r'(<script type="application/ld\+json">)(.*?)(</script>)',schema,text,flags=re.S)
    text=text.replace('Korsch - Model Unresolved','Korsch components requiring identification')
    text=text.replace('Browse independently produced replacement components and build a technical quote cart. Pricing and compatibility are confirmed after machine and part-reference review.','These component records require identification. Supply your machine model, serial number, existing part or drawing for review before quotation.')
    text=text.replace('data-model="300" aria-current="page">300 <span>','data-model="300" aria-current="page">Identification review <span>')
    # Preserve every part-identity warning, image, SKU, URL, quote-cart control,
    # and noindex/canonical decision. Do not replace uncertainty with a model.
    if text!=original:
        path.write_text(text,encoding='utf-8'); changed.append(str(path.relative_to(ROOT)))
    print(json.dumps({'changed_files':changed,'scope':'Korsch category wording and audit homepage resolver; no product identity inferred'},indent=2))
    return changed

if __name__=='__main__': apply()
