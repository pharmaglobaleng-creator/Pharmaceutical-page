#!/usr/bin/env python3
"""Align only source-supplied first-200 Fette references with matching detail pages."""
import argparse
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNKNOWN = 'Not listed in source catalog'


def clean(value):
    return ' '.join(str(value or '').split())


class DetailIdentity(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.active = None
        self.values = {'h1': [], 'badge': []}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'h1':
            self.active = ('h1', tag, [])
        elif tag == 'span' and 'sku-badge' in attrs.get('class', '').split():
            self.active = ('badge', tag, [])

    def handle_data(self, data):
        if self.active:
            self.active[2].append(data)

    def handle_endtag(self, tag):
        if self.active and tag == self.active[1]:
            self.values[self.active[0]].append(clean(''.join(self.active[2])))
            self.active = None


def confirmed_references(source_rows, catalog_rows, read_detail):
    """Fail closed on identity/reference disagreements; never infer from a SKU alone."""
    if len(source_rows) != 200:
        raise ValueError('Expected the preserved first 200 Fette source records')
    source = {}
    for row in source_rows:
        sku = row.get('sku', '')
        if not re.fullmatch(r'PGE-FET-\d{3}', sku) or not 1 <= int(sku[-3:]) <= 200 or sku in source:
            raise ValueError(f'Invalid or duplicate first-200 source SKU: {sku}')
        source[sku] = row
    catalog = {}
    for row in catalog_rows:
        if row.get('brand') != 'fette':
            continue
        sku = row.get('sku')
        if sku in catalog:
            raise ValueError(f'Duplicate Fette catalog SKU: {sku}')
        catalog[sku] = row
    confirmed = {}
    for sku, original in source.items():
        if original.get('oem_status') != 'catalog-supplied' or not clean(original.get('oem_number')):
            continue
        row = catalog.get(sku)
        if (not row or clean(original.get('make')) != 'Fette'
                or clean(row.get('name')) != clean(original.get('part_name'))
                or clean(row.get('model')) != clean(original.get('model'))):
            raise ValueError(f'Source/catalog identity mismatch: {sku}')
        reference = clean(original['oem_number'])
        detail = DetailIdentity()
        detail.feed(read_detail(sku))
        expected_h1 = f"{clean(original['part_name'])} for Fette {clean(original['model'])}"
        if detail.values['h1'] != [expected_h1]:
            raise ValueError(f'Source/detail identity mismatch: {sku}')
        if detail.values['badge'] != [f'Replacement Part for OEM {reference}']:
            raise ValueError(f'Source/detail reference mismatch: {sku}')
        if clean(row.get('oem')) not in ('', UNKNOWN, reference):
            raise ValueError(f'Conflicting catalog reference: {sku}')
        confirmed[sku] = reference
    return confirmed


def serialize(data):
    if isinstance(data, list):
        return json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    return json.dumps(data, ensure_ascii=False, indent=2) + '\n'


def apply(root=ROOT, check=False):
    source = json.loads((root / 'data/fette-first-200.json').read_text(encoding='utf-8'))
    paths = [root / 'next-app/data/parts-catalog.json', root / 'catalog-data/fette.json']
    documents = {path: json.loads(path.read_text(encoding='utf-8')) for path in paths}
    read_detail = lambda sku: (root / 'parts' / sku.lower() / 'index.html').read_text(encoding='utf-8')
    references = None
    # Validate both data surfaces completely before changing either one.
    for data in documents.values():
        rows = data['parts'] if isinstance(data, dict) else data
        current = confirmed_references(source, rows, read_detail)
        if references is not None and references != current:
            raise ValueError('Catalog surfaces disagree about supported references')
        references = current
    for data in documents.values():
        rows = data['parts'] if isinstance(data, dict) else data
        for row in rows:
            if row.get('sku') in references and row.get('brand') == 'fette':
                row['oem'] = references[row['sku']]
    public_data = documents[paths[1]]
    version = hashlib.sha256(serialize(public_data).encode()).hexdigest()[:12]
    manifest_path = root / 'catalog-data/manifest.json'
    documents[manifest_path] = json.loads(manifest_path.read_text(encoding='utf-8'))
    for rows in [documents[paths[0]]['manufacturers'], documents[manifest_path]]:
        matches = [row for row in rows if row.get('slug') == 'fette']
        if len(matches) != 1:
            raise ValueError('Expected exactly one Fette manufacturer')
        matches[0]['searchVersion'] = version
    changes = {path: serialize(data) for path, data in documents.items()
               if serialize(data) != path.read_text(encoding='utf-8')}
    if check and changes:
        raise ValueError('Fette reference sync required: ' + ', '.join(str(path.relative_to(root)) for path in changes))
    if not check:
        for path, text in changes.items():
            path.write_text(text, encoding='utf-8')
    return {'source_supplied_references': len(references), 'changed_files': [str(path.relative_to(root)) for path in changes]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    print(json.dumps(apply(check=args.check), indent=2))
