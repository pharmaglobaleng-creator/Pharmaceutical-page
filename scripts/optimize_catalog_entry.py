#!/usr/bin/env python3
"""Keep the Parts Store entry usable without a client application startup.

Run against the static repository or after assembling a Next export. Metadata,
catalog links, styles, native navigation/search, and the quote dialog survive.
"""
import argparse
import re
from pathlib import Path

def optimize(root):
    page = root / 'parts/index.html'
    original = page.read_text()
    text = re.sub(r'<script\b[^>]*>.*?</script>', lambda match: '' if '/_next/' in match[0] or 'self.__next_f' in match[0] else match[0], original, flags=re.S)
    text = re.sub(r'<link\b[^>]*>', lambda match: '' if '/_next/' in match[0] and 'as="script"' in match[0] else match[0], text)
    text = re.sub(r'<script id="pge-creamer-selection-fix">.*?</script>', '', text, flags=re.S)
    original_cards = len(re.findall('class="pc-manufacturer-card', original))
    added_card = False
    cremer = root / 'parts/cremer/index.html'
    if cremer.exists():
        count = re.search(r'<div class="catalog-count">([\d,]+) parts</div>', cremer.read_text())
        if count:
            card_pattern = r'<a class="pc-manufacturer-card" href="/parts/cremer/">.*?</a>'
            if not re.search(card_pattern, text, re.S):
                card = '<a class="pc-manufacturer-card" href="/parts/cremer/"><span class="pc-manufacturer-count">'+count[1]+' parts</span><span class="pc-manufacturer-mark" aria-hidden="true">CR</span><h2>Creamer</h2><p>Browse Creamer replacement components by machine model, part name, and reference.</p><strong>Browse replacement parts <span aria-hidden="true">→</span></strong></a>'
                text = text.replace('<a class="pc-manufacturer-card pc-identify-card"', card+'<a class="pc-manufacturer-card pc-identify-card"', 1)
                added_card = True
            def update_count(match):
                return re.sub(r'(<span class="pc-manufacturer-count">).*?(</span>)', lambda m:m[1]+count[1]+' parts'+m[2], match[0])
            text = re.sub(card_pattern, update_count, text, flags=re.S)
            total = sum(int(n.replace(',', '')) for n in re.findall(r'<span class="pc-manufacturer-count">([\d,]+)', text))
            text = re.sub(r'(<span>)[\d,]+(?:<!-- -->)? part records(</span>)', lambda m:m[1]+f'{total:,} part records'+m[2], text)
    text = text.replace('data-pge-catalog="v2"', 'data-pge-catalog="v2" data-pge-catalog-entry="static"') if 'data-pge-catalog-entry="static"' not in text else text
    # Include the independently maintained Cremer catalog in both native menus.
    for pattern in [r'(<details class="pc-nav-menu">.*?<div>)(.*?)(</div>)', r'(<details class="pc-mobile-nav">.*?<nav[^>]*>)(.*?)(</nav>)']:
        def navigation(match):
            if '/parts/cremer/' in match[2]: return match[0]
            return match[1] + match[2] + '<a href="/parts/cremer/">Creamer parts</a>' + match[3]
        text = re.sub(pattern, navigation, text, flags=re.S)
    if 'src="/assets/js/catalog-entry.js?v=20260912"' not in text:
        text = text.replace('</body>', '<script src="/assets/js/catalog-entry.js?v=20260912" defer></script></body>')
    text = text.replace('/assets/js/pge-analytics.js?v=catalog-freeze-20260912', '/assets/js/pge-analytics.js?v=catalog-entry-20260912')
    assert 'self.__next_f' not in text
    assert not re.search(r'<script[^>]+src="/_next/', text)
    assert len(re.findall('class="pc-manufacturer-card', text)) == original_cards + int(added_card)
    for pattern in [r'<title>.*?</title>', r'<link rel="canonical"[^>]*>', r'<h1[^>]*>.*?</h1>', r'<script type="application/ld\+json">.*?</script>']:
        assert re.findall(pattern, original, re.S) == re.findall(pattern, text, re.S)
    page.write_text(text)
    print(f'Catalog entry: {len(original.encode()):,} → {len(text.encode()):,} HTML bytes; native links/search preserved.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    optimize(parser.parse_args().root)
