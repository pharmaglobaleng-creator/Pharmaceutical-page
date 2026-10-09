#!/usr/bin/env python3
"""Generate a source-linked plain-text homepage reference without dependencies."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
import re

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://pharmaglobaleng.com/'

class HomepageText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.active = False
        self.parts = []
        self.links = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'main':
            self.active = True
        if not self.active:
            return
        if tag in ('script', 'style'):
            self.skip += 1
        if self.skip:
            return
        if tag in ('h1', 'h2', 'h3', 'h4'):
            self.parts.append('\n\n' + '#' * int(tag[1]) + ' ')
        elif tag in ('p', 'section', 'article', 'details', 'div', 'tr', 'caption'):
            self.parts.append('\n\n')
        elif tag == 'li':
            self.parts.append('\n- ')
        elif tag in ('td', 'th'):
            self.parts.append(' | ')
        elif tag == 'summary':
            self.parts.append('\n\n### ')
        elif tag == 'br':
            self.parts.append('\n')
        elif tag == 'a':
            self.links.append(urljoin(ORIGIN, a.get('href', '')))
        elif tag == 'img' and a.get('alt'):
            self.parts.append('[Image: ' + a['alt'] + ']')

    def handle_endtag(self, tag):
        if tag in ('script', 'style') and self.skip:
            self.skip -= 1
            return
        if not self.active or self.skip:
            return
        if tag == 'a' and self.links:
            self.parts.append(' (' + self.links.pop() + ') ')
        if tag in ('p', 'h1', 'h2', 'h3', 'h4', 'article', 'details', 'section', 'div', 'tr'):
            self.parts.append('\n\n')
        if tag == 'main':
            self.active = False

    def handle_data(self, text):
        if self.active and not self.skip:
            self.parts.append(re.sub(r'\s+', ' ', text))


def build():
    parser = HomepageText()
    parser.feed((ROOT / 'index.html').read_text())
    lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in ''.join(parser.parts).splitlines()]
    body = re.sub(r'\n{3,}', '\n\n', '\n'.join(lines)).strip()
    assert 'What pharmaceutical tooling services do we provide?' in body
    assert 'pubmed.ncbi.nlm.nih.gov/29751009/' in body
    assert '<script' not in body and '__next_f' not in body
    header = '''# PharmaGlobalEng - Expanded Homepage Reference

Source: https://pharmaglobaleng.com/
Navigation index: https://pharmaglobaleng.com/llms.txt

Scope: This file contains the homepage's published main content and source links.
It is not an export of the complete replacement-parts catalog or every service page.
The linked web pages remain the sources for current details. Engineering guidance
is application-specific; this file adds no specifications, guarantees, or endorsements.
Generated from index.html by scripts/build_llms_full.py. Regenerate when homepage content changes.

---

'''
    (ROOT / 'llms-full.txt').write_text(header + body + '\n')
    print('Generated llms-full.txt:', len((header + body).encode()), 'bytes')

if __name__ == '__main__':
    build()
