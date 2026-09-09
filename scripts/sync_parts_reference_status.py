#!/usr/bin/env python3
"""Apply source-review restrictions to public catalog data without inventing OEMs."""
from pathlib import Path
import csv
import hashlib
import json
ROOT=Path(__file__).resolve().parents[1]
STATUS='Not verified; confirm during quotation'

def restricted_records():
    with (ROOT/'data/kikusui-parts.csv').open(encoding='utf-8',newline='') as handle:
        return {r['sku']:r for r in csv.DictReader(handle) if not r.get('verification','').lower().startswith('verified') and r.get('oem_number','').strip() not in ('','N/A','Not listed in source catalog')}

def apply():
    restricted=restricted_records()
    changed=[]
    for path in [ROOT/'catalog-data/kikusui.json',ROOT/'next-app/data/parts-catalog.json']:
        if not path.exists(): continue
        original=path.read_text(encoding='utf-8')
        data=json.loads(original)
        rows=data if isinstance(data,list) else data['parts']
        touched=False
        for row in rows:
            if row.get('sku') in restricted and row.get('oem')!=STATUS:
                row['oem']=STATUS
                touched=True
        if touched:
            compact=isinstance(data,list)
            path.write_text(json.dumps(data,ensure_ascii=False,indent=None if compact else 2,separators=(',',':') if compact else None)+('' if compact else '\n'),encoding='utf-8')
            changed.append(path.relative_to(ROOT).as_posix())
    # Invalidate the browser's manufacturer-data cache without changing images.
    version=hashlib.sha256((ROOT/'catalog-data/kikusui.json').read_bytes()).hexdigest()[:12]
    for path in [ROOT/'catalog-data/manifest.json',ROOT/'next-app/data/parts-catalog.json']:
        original=path.read_text(encoding='utf-8')
        data=json.loads(original)
        rows=data if isinstance(data,list) else data['manufacturers']
        touched=False
        for row in rows:
            if row.get('slug')=='kikusui' and row.get('searchVersion')!=version:
                row['searchVersion']=version
                touched=True
        if touched:
            compact=isinstance(data,list)
            path.write_text(json.dumps(data,ensure_ascii=False,indent=None if compact else 2,separators=(',',':') if compact else None)+('' if compact else '\n'),encoding='utf-8')
            changed.append(path.relative_to(ROOT).as_posix())
    return sorted(set(changed))

if __name__=='__main__':
    print(json.dumps({'restricted_oem_records':len(restricted_records()),'changed_files':apply()},indent=2))
