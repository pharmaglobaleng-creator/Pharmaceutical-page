#!/usr/bin/env python3
"""Keep published mailto anchors intact through Cloudflare email obfuscation.
Run after HTML generation. Only public HTML is processed; script payloads and
existing email_off regions are preserved byte-for-byte.
"""
import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN = re.compile(r'<!--email_off-->.*?<!--/email_off-->|<!--.*?-->|<script\b[^>]*>.*?</script\s*>|<a\b[^>]*>.*?</a\s*>', re.I | re.S)
MAIL = re.compile(r'\bhref\s*=\s*([\"\'])mailto:[^\"\']*\1', re.I)
EXCLUDED = {'.git', 'node_modules', 'next-app', '_next', 'docs', 'scripts'}

def protect(source):
    def replace(match):
        value = match.group(0)
        if value.lower().startswith('<a') and MAIL.search(value.split('>', 1)[0]):
            return '<!--email_off-->' + value + '<!--/email_off-->'
        return value
    return TOKEN.sub(replace, source)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    changed = []
    for path in sorted(args.root.rglob('*.html')):
        if set(path.relative_to(args.root).parts) & EXCLUDED:
            continue
        source = path.read_text(encoding='utf-8')
        output = protect(source)
        if output != source:
            changed.append(str(path.relative_to(args.root)))
            if not args.check:
                path.write_text(output, encoding='utf-8')
    print(f'{len(changed)} pages ' + ('need email protection markers' if args.check else 'updated'))
    if args.check and changed:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
