#!/usr/bin/env python3
"""Install/check the shared Analytics loader without rewriting existing HTML.

Run after adding or regenerating legacy pages. Next.js includes the loader in
its root layout. Verification files and immediate redirects are excluded.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOADER = '<script id="pge-analytics" src="/assets/js/pge-analytics.js" defer></script>'
MARKER = b'/assets/js/pge-analytics.js'
PUBLIC_DIRS = ('about', 'coatings', 'components', 'knowledge-center', 'parts', 'services', 'solutions')


def public_pages(root):
    candidates = list(root.glob('*.html'))
    for name in PUBLIC_DIRS:
        candidates.extend((root / name).rglob('*.html'))
    for path in sorted(candidates):
        data = path.read_bytes()
        if re.search(rb'<meta\b[^>]*http-equiv=["\']refresh["\']', data, re.I):
            continue
        if not re.search(rb'<head\b[^>]*>', data, re.I):
            if b'<html' in data.lower():
                raise ValueError(f'Missing head: {path}')
            continue  # Search-engine ownership verification text, not a page.
        yield path, data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    pending = []
    count = 0
    for path, original in public_pages(args.root):
        count += 1
        occurrences = original.count(MARKER)
        if occurrences > 1:
            raise ValueError(f'Duplicate Analytics loader: {path}')
        if occurrences == 1:
            continue
        if re.search(rb'googletagmanager\.com|google-analytics\.com|\bgtag\s*\(', original):
            raise ValueError(f'Existing Google tag requires review: {path}')
        head = re.search(rb'<head\b[^>]*>', original, re.I)
        pos = head.end()
        updated = original[:pos] + LOADER.encode() + original[pos:]
        # Removing the one inserted element must restore every original byte,
        # including metadata, links, JSON-LD, images and React navigation data.
        assert updated.replace(LOADER.encode(), b'', 1) == original
        pending.append((path, updated))
    if args.check and pending:
        raise SystemExit(f'{len(pending)} of {count} public pages lack Analytics; run this script without --check.')
    for path, updated in pending:
        path.write_bytes(updated)
    print(f'{count} public pages checked; {len(pending)} updated; existing page bytes preserved.')


if __name__ == '__main__':
    main()
