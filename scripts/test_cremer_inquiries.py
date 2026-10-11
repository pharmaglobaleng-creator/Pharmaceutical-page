"""Check safe enrichment: complete coverage, valid local links and no identity changes."""
import json
import re
import subprocess
import unittest
from pathlib import Path
from html.parser import HTMLParser
import enrich_cremer_inquiries as build

class Links(HTMLParser):
 def __init__(self,text):
  super().__init__();self.links=[];self.feed(text)
 def handle_starttag(self,tag,attrs):
  if tag=='a':self.links.append(dict(attrs).get('href',''))

class CremerTests(unittest.TestCase):
 def test_every_record_has_specific_guidance(self):
  self.assertEqual(set(build.NOTES),set(range(4,60)))
  self.assertEqual(len(set(build.NOTES.values())),56)
  self.assertEqual(set(build.NOTES),set(sum(build.GROUPS,[])))
 def test_identity_and_links(self):
  for n in build.NOTES:
   with self.subTest(record=n):
    rel=f'parts/pge-cre-{n:03}/index.html'
    text=(build.ROOT/rel).read_text()
    base=subprocess.check_output(['git','show','HEAD:'+rel],cwd=build.ROOT,text=True)
    self.assertEqual(text.count('data-pge-cremer-inquiry="true"'),1)
    for pattern in [r'<h1[^>]*>.*?</h1>',r'<link rel="canonical"[^>]*>',r'<meta name="robots"[^>]*>',r'<script type="application/ld\+json">.*?</script>']:
     self.assertEqual(re.search(pattern,text,re.S)[0],re.search(pattern,base,re.S)[0])
    section=re.search(r'<section data-pge-cremer-inquiry="true">.*?</section>',text,re.S)[0]
    for href in Links(section).links:
     self.assertTrue(href.startswith('/'))
     target=build.ROOT/href.lstrip('/')
     if href.endswith('/'):target=target/'index.html'
     self.assertTrue(target.is_file(),href)
    self.assertNotIn('exceed cGMP',section)

if __name__=='__main__':unittest.main()
