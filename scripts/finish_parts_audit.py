#!/usr/bin/env python3
"""Evidence-led fixes for catalog/detail inconsistencies and missed navigation.
No new specifications, OEM numbers, images, prices, indexing directives or URLs.
"""
from pathlib import Path
import csv
import html
import json
import re
from sync_parts_reference_status import apply as sync_references, restricted_records, STATUS
ROOT=Path(__file__).resolve().parents[1]

def save(path,text,changes):
    original=path.read_text(encoding='utf-8')
    if text!=original:
        path.write_text(text,encoding='utf-8')
        changes.add(path.relative_to(ROOT).as_posix())

def correct_stokes_source(changes):
    path=ROOT/'data/oem-cross-reference-audit.csv'
    with path.open(encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f))
    with (ROOT/'data/part-content-audit.csv').open(encoding='utf-8',newline='') as f:
        known={r['sku']:r for r in csv.DictReader(f)}
    touched=False
    for r in rows:
        if re.fullmatch(r'PGE-STK-\d{3}',r['sku']) and r['manufacturer_reference']=='Korsch':
            assert known[r['sku']]['manufacturer_reference']=='Stokes'
            assert 'stokes' in (r['source_title']+' '+r['source_url']).lower()
            r['manufacturer_reference']='Stokes'
            touched=True
    if touched:
        import io
        out=io.StringIO(newline='')
        w=csv.DictWriter(out,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
        save(path,out.getvalue(),changes)
    return rows

def polish(text,sku):
    import polish_part_page_copy as p
    description=p.complete_description(text,sku)
    text=p.clean_residual_placeholders(text)
    text=p.set_description_meta(text,'description',description)
    text=p.set_description_meta(text,'og:description',description,prop=True)
    text=p.set_description_meta(text,'twitter:description',description)
    return p.set_product_description(p.set_lead(text,description),description)

def legacy_pages(rows,changes):
    import normalize_part_pages_for_search as n
    n.TRUTH=n.load_truth()
    pending=[]
    for r in rows:
        sku=r['sku']
        if not re.fullmatch(r'PGE-(?:STK-\d{3}|K300-\d{3})',sku):
            continue
        pending.append(r)
        path=ROOT/'parts'/sku.lower()/'index.html'
        text=path.read_text(encoding='utf-8')
        if sku.startswith('PGE-STK-'):
            text=n.normalize_page(path,text)
            # Keep supported models, but do not infer a model from an image folder.
            equipment='Stokes'+(' '+n.TRUTH[sku].model if n.TRUTH[sku].model else '')
            text=re.sub(r'\bStokes\s+(?:328|747|757|BB2)\b',lambda m:equipment,text,flags=re.I)
            text=re.sub(r'Model\+reference%3A\+(?:328|747|757|BB2)%0A',lambda m:'Model+reference%3A+'+(n.TRUTH[sku].model or 'Confirm+during+quotation')+'%0A',text,flags=re.I)
            text=re.sub(r'(<dt>Compatibility reference</dt><dd>).*?(</dd>)',lambda m:m[1]+html.escape(equipment+' reference; confirm final dimensional fit')+m[2],text,count=1,flags=re.S)
            text=re.sub(r'<h2>Will this .*? fit a Stokes tablet press\?</h2>\s*<p>.*?</p>',lambda m:'<h2>How is compatibility confirmed?</h2><p>The exact machine model and OEM mapping for this record have not been verified. Supply the machine serial number, existing component or drawing, and critical dimensions before requesting a confirmed replacement.</p>',text,count=1,flags=re.S)
            text=polish(text,sku)
        notice='<section class="detail-section" data-pge-reference-review="true"><div class="wrap"><div class="notice"><strong>Identification review required.</strong> This legacy record does not have an approved OEM cross-reference. Confirm the exact machine model and component identity during review. The image is illustrative and is not evidence of dimensional fit. Use the PGE reference when <a href="/parts/identify/">requesting identification</a>; supply a photograph, drawing or sample before compatibility is confirmed.</div></div></section>\n'
        if r['approved_for_publication']!='yes' and 'data-pge-reference-review="true"' not in text:
            text=text.replace('<section class="detail-section">',notice+'<section class="detail-section">',1)
        save(path,text,changes)
    # This directory serves users with old quote references, not search phrases.
    path=ROOT/'parts/identify/index.html'
    text=path.read_text(encoding='utf-8')
    block='<section class="identify-faq" data-pge-legacy-directory="true"><div class="wrap"><h2>Find an earlier PGE reference</h2><p>Find an earlier quote or saved reference here. Review each record for its source status; an entry in this directory does not verify dimensional fit.</p>'
    for brand in ('Korsch','Stokes'):
        group=[r for r in pending if r['manufacturer_reference']==brand]
        block+='<details><summary>'+brand+' earlier reference records ('+str(len(group))+')</summary>'
        if brand=='Korsch': block+='<p><a href="/parts/korsch/korsch-300/">Korsch component identification overview</a></p>'
        block+='<ul>'+''.join('<li><a href="/parts/'+r['sku'].lower()+'/">'+html.escape(r['sku']+' — '+r['part_name'])+'</a></li>' for r in group)+'</ul></details>'
    block+='</div></section>\n'
    text=re.sub(r'<section class="identify-faq" data-pge-legacy-directory="true">.*?</section>\s*','',text,flags=re.S)
    text=text.replace('</main>',block+'</main>',1)
    save(path,text,changes)
    return len(pending)

def rewrite_flight_nodes(value,restricted):
    """Modify only a targeted product's OEM <dd> in React server output."""
    edits=0
    if isinstance(value,list):
        if len(value)>=4 and value[0]=='$' and value[1]=='article' and isinstance(value[3],dict) and value[3].get('data-pc-sku') in restricted:
            def alter(node):
                nonlocal edits
                if isinstance(node,list):
                    if len(node)>=4 and node[0]=='$' and node[1]=='div' and isinstance(node[3],dict):
                        children=node[3].get('children')
                        if isinstance(children,list) and len(children)==2 and all(isinstance(x,list) and len(x)>=4 and isinstance(x[3],dict) for x in children):
                            if children[0][1]=='dt' and children[0][3].get('children')=='OEM reference' and children[1][1]=='dd':
                                if children[1][3].get('children')!=STATUS:
                                    children[1][3]['children']=STATUS;edits+=1
                    for x in node: alter(x)
                elif isinstance(node,dict):
                    for x in node.values(): alter(x)
            alter(value)
            return edits
        for x in value: edits+=rewrite_flight_nodes(x,restricted)
    elif isinstance(value,dict):
        for x in value.values(): edits+=rewrite_flight_nodes(x,restricted)
    return edits

def patch_flight(payload,restricted):
    out=[];total=0
    for line in payload.splitlines(keepends=True):
        m=re.match(r'^([0-9a-f]+:)(\[.*)(\n?)$',line,re.S)
        if not m or not any(sku in line for sku in restricted):out.append(line);continue
        try: data=json.loads(m[2])
        except json.JSONDecodeError:out.append(line);continue
        edits=rewrite_flight_nodes(data,restricted)
        if edits:
            out.append(m[1]+json.dumps(data,ensure_ascii=False,separators=(',',':'))+('\n' if line.endswith('\n') else ''));total+=edits
        else:out.append(line)
    return ''.join(out),total

def catalog_pages(changes):
    restricted=restricted_records()
    total_cards=0;total_flight=0
    old_versions=set()
    for path in [ROOT/'catalog-data/manifest.json',ROOT/'next-app/data/parts-catalog.json']:
        data=json.loads(path.read_text(encoding='utf-8'))
        rows=data if isinstance(data,list) else data['manufacturers']
        old_versions.update(r['searchVersion'] for r in rows if r.get('slug')=='kikusui')
    changes.update(sync_references())
    version=next(r['searchVersion'] for r in json.loads((ROOT/'catalog-data/manifest.json').read_text()) if r['slug']=='kikusui')
    for path in (ROOT/'parts').rglob('*'):
        if path.suffix not in ('.html','.txt'):continue
        text=path.read_text(encoding='utf-8')
        if not any(s in text for s in restricted) and not any(v in text for v in old_versions if v!=version):continue
        for old in old_versions:
            if old!=version:text=text.replace(old,version)
        if path.suffix=='.html':
            cards=0
            def card(m):
                nonlocal cards
                if m[1] not in restricted:return m[0]
                old=m[0]
                updated=re.sub(r'(<dt>OEM reference</dt><dd>).*?(</dd>)',lambda x:x[1]+html.escape(STATUS)+x[2],old,count=1,flags=re.S)
                if updated!=old:cards+=1
                return updated
            text=re.sub(r'<article\b[^>]*data-pc-sku="([^"]+)"[^>]*>.*?</article>',card,text,flags=re.S)
            total_cards+=cards
            flights=0
            def script(m):
                nonlocal flights
                data=json.loads(m[1])
                if len(data)==2 and data[0]==1 and isinstance(data[1],str):
                    payload,count=patch_flight(data[1],restricted)
                    if count:
                        data[1]=payload;flights+=count
                        return 'self.__next_f.push('+json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')+')'
                return m[0]
            text=re.sub(r'self\.__next_f\.push\((\[.*?\])\)(?=</script>)',script,text,flags=re.S)
            # Do not publish half-fixed HTML if a future stream format changes.
            assert cards==flights, (path,cards,flights)
            total_flight+=flights
        else:
            text,count=patch_flight(text,restricted);total_flight+=count
        save(path,text,changes)
    return len(restricted),total_cards,total_flight

def preserve_build_rule(changes):
    path=ROOT/'next-app/scripts/prepare-catalogs.mjs'
    text=path.read_text(encoding='utf-8')
    marker='// PGE: enforce source-reviewed OEM restrictions before export.'
    if marker not in text:
        text="import { execFileSync } from 'node:child_process';\n"+text
        text=text.replace('const imageCache = new Map();',marker+"\nwrite(dataFile, JSON.stringify(data, null, 2) + '\\n');\nexecFileSync('python3', [path.join(root, 'scripts/sync_parts_reference_status.py')], { cwd: root, stdio: 'inherit' });\ndata = JSON.parse(fs.readFileSync(dataFile, 'utf8'));\n\nconst imageCache = new Map();",1)
    save(path,text,changes)

def apply():
    changes=set()
    rows=correct_stokes_source(changes)
    pending=legacy_pages(rows,changes)
    restricted,cards,flight=catalog_pages(changes)
    preserve_build_rule(changes)
    result={'changed_files':sorted(changes),'legacy_records_linked':pending,'restricted_oem_records':restricted,'catalog_card_occurrences_fixed_this_run':cards,'react_payload_occurrences_fixed_this_run':flight}
    print(json.dumps(result,indent=2))
    return result

if __name__=='__main__':apply()
