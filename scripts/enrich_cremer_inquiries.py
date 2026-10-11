#!/usr/bin/env python3
"""Add identification questions to minimal Cremer records; invent no specifications."""
from pathlib import Path
import html
import json
import re

ROOT = Path(__file__).resolve().parents[1]
# Questions follow the existing published component names. They are information
# requested for quotation, not verified fit, dimensions or replacement instructions.
NOTES = {
4: 'The catalog identifies this rack module as supplied by set only. State whether the enquiry concerns the complete set and photograph the installed arrangement so the required scope can be reviewed.',
5: 'For a gate assembly guider enquiry, show the guide together with the gate and its attachment points. Include a drawing or measurements of the existing guide rather than relying on its appearance alone.',
6: 'The record identifies a silicone gasket but does not specify its grade or dimensions. Supply the gasket profile, mating surfaces and any approved material specification needed for the application.',
7: 'For the pneumatic service unit, include a photograph of its label, connection arrangement and installed accessories. State whether a complete unit or a particular subcomponent is required.',
8: 'Quote the KD-1/4 marking and show both the coupling and its mating connection. The published designation alone should not be treated as confirmation of the thread standard or sealing arrangement.',
9: 'Quote KS3-CK-4 and photograph the plug alongside the mating coupling. Include any additional manufacturer markings so the connection can be distinguished from similarly shaped plugs.',
10: 'Quote QSF-1/4-8B exactly as marked. Supply photographs of the fitting, connected tubing and machine-side connection; confirm the complete fitting designation before substitution.',
11: 'This record describes the HHT-to-counter cable as 9-pin. Show both connector ends and any cable label; pin count alone does not establish wiring or communication compatibility.',
12: 'Show the fixed HHT bracket with the terminal attached and provide its mounting-hole arrangement. Identify whether the required scope is the bracket alone or includes its attachment hardware.',
13: 'The listed designation is PNOZ-X7 24V DC/AC. Supply the complete safety-module label and the approved machine documentation. Any replacement must be reviewed by personnel responsible for the machine safety system; this listing does not authorize a substitution.',
14: 'For an HHT handheld terminal enquiry, include the terminal label, connector photographs and the machine control revision if known. Distinguish a complete terminal from a keyboard, cable or mounting-bracket request.',
15: 'The record lists 6D22, 50 Hz and 50 rpm. Send a complete motor nameplate photograph, mounting details and output connection; the listing does not establish voltage, power or the full drive configuration.',
16: 'This entry is for the red 24 V indicator. Show its rear terminals and mounting opening as well as its front face; colour and nominal voltage alone do not establish a matching assembly.',
17: 'This entry is for the yellow 24 V indicator. Include the installed indicator label, terminal arrangement and mounting dimensions, and identify whether a lamp element or complete indicator is required.',
18: 'For the main control PCB, record the board number and revision and photograph the connectors. Describe the observed fault separately from the requested part; a symptom alone does not confirm that this board needs replacement.',
19: 'Quote the complete PTM 100-10-85P designation from the memory flap cylinder. Include its label, mounting arrangement and end connections so the supplied configuration can be reviewed.',
20: 'Show the silicone buffer ring and its installed position. Provide the ring profile and approved material requirements where available; the catalog name does not establish hardness or product-contact suitability.',
21: 'The published buffer ring nut name includes the identifier 2005. Retain that identifier in the enquiry and show the mating thread and buffer arrangement; do not assume that the identifier is a verified OEM part number.',
22: 'Identify the strip as the memory flap buffer strip and show where it sits. Include its section shape, required length and existing material documentation; distinguish it from the hopper buffer strip.',
23: 'Identify the hopper plate location and show the silicone strip in place. Provide the strip profile and required length, keeping this enquiry separate from the memory flap strip.',
24: 'This record names a memory flap fork with a locking ring. Show both pieces and their attachment arrangement, and state whether both are needed for the quotation.',
25: 'Clarify whether the detection unit is required as a complete assembly. Show its label and connections and distinguish the assembly request from glass or individual board enquiries.',
26: 'For detection unit glass, provide the existing panel dimensions, edge details and mounting arrangement. Do not substitute a general glass specification for an approved optical or machine-specific requirement.',
27: 'Identify this as the detection unit processor board and provide its printed board number and revision. Photograph its connectors so it is not confused with the separate general processor PCB record.',
28: 'Identify this as the detection unit emitter board. Supply its board markings and connector layout, and distinguish it from the receiver board before requesting a matched replacement.',
29: 'Identify this as the detection unit receiver board. Include its revision and connector photographs; the emitter and receiver records describe different requested components.',
30: 'For the detection unit connector board, show each connection position and all printed identifiers. State whether the enquiry includes connected cables or only the board.',
31: 'This record describes an HHT PC board and keyboard full set. Confirm that the full set is required and provide the existing terminal and board revisions to define the quotation scope.',
32: 'For the touch screen full set, provide the display label, overall mounting arrangement and connection details. Explain whether the requested set includes the housing and related interface components.',
33: 'Identify the infrared emitter with photographs and any markings. Keep the emitter request distinct from the infrared receiver and include the installed detection assembly reference.',
34: 'Identify the infrared receiver with photographs and any markings. Include the associated detection assembly reference; visual resemblance to an emitter is not a compatibility check.',
35: 'For the processor PCB, supply its board number, revision and installed location. The catalog also lists a detection unit processor board, so identify which assembly this board belongs to.',
36: 'For the PWM PCB, capture all board markings and connector locations. Describe the installed assembly and required scope without assuming that another control board is interchangeable.',
37: 'For the keyboard PCB, show the board and its connection to the keypad or terminal. State whether only the PCB is needed rather than a complete HHT board-and-keyboard set.',
38: 'Send the full frequency inverter nameplate and machine drive reference. Voltage, rating, firmware and parameter requirements must come from the approved equipment documentation, not from this general catalog entry.',
39: 'Retain the complete 1025-5M-12 marking when enquiring about the M-type outfeed timing belt. Include a photograph of the existing belt markings and drive arrangement before selecting a replacement.',
40: 'This record uses both dosage flap and hopper gate as names. Show the installed gate and its attachment points so the enquiry can be matched to the correct hopper arrangement.',
41: 'This listing names a 16 mm channel inserter. Include its profile and installed position; distinguish it from the separately listed 19 mm channel divider insert.',
42: 'This listing names a 19 mm channel divider insert. Provide its profile and mounting arrangement; the 16 mm channel inserter is a separate catalog record.',
43: 'The tilt nozzle record references 750 cc and 950 cc bottles. Supply bottle-neck geometry and the existing nozzle arrangement; nominal bottle capacity alone does not establish fit.',
44: 'For the easy-clean cylinder head nut, show the cylinder connection and nut markings. Provide an existing drawing or thread specification if available, without assuming a standard thread from the name.',
45: 'For the nut buffer, photograph the buffer separately and in its installed arrangement. Include its profile and approved material requirements; the catalog wording does not establish a tolerance.',
46: 'For the clevis or rod end, show the pin connection, attachment thread and installed orientation. Provide the existing drawing or measured geometry so the joint arrangement can be reviewed.',
47: 'This entry describes a 13-station valve manifold block. Show the complete manifold and its labels, and state whether the block alone or a populated assembly is required.',
48: 'For the valve manifold PCB, provide the board revision and connection layout alongside the manifold reference. Keep the electronics enquiry distinct from the manifold block request.',
49: 'For an internal cable harness, show both endpoints, branch layout and cable identifiers. Include a wiring reference where available; matching connector appearance does not confirm the wiring.',
50: 'Identify which internal pneumatic connectors are required and provide a marked photograph of their locations. Define the contents of the requested set instead of assuming every internal connector is included.',
51: 'Identify the external pneumatic connection locations and the mating connections. Define the required set and distinguish it from the internal push-in connector set.',
52: 'The catalog name specifies 4 mm tube and 15 cm length. Confirm how the existing tube is measured, its connection arrangement and the approved tubing material before quotation.',
53: 'The catalog name specifies 4 mm tube, 20 cm length and an insert. Show the insert and both connections; distinguish this assembly from the separate 15 cm tube entry.',
54: 'This record identifies 8 mm pneumatic tube without a stated length. Supply the required length, existing tube markings and connection details rather than assuming a complete pre-cut assembly.',
55: 'This general 4 mm pneumatic tube record has no stated length. Specify the required length and distinguish bulk or cut tubing from the separately listed 15 cm and 20 cm assemblies.',
56: 'Show the memory flap guide block buffer and its installed position. Include its profile and mounting details so it is not confused with a buffer strip or silicone ring.',
57: 'The interface control board name references CF1220-LTE. Provide the actual board label, revision and machine configuration; do not treat the broader model listing as proof of compatibility with every control system.',
58: 'For the piggy-back PLC, provide the controller label and the host assembly reference. Software and interface requirements need confirmation from the approved control documentation.',
59: 'For the compact HHT-style touchscreen, provide the display label, connectors and installed mounting arrangement. Distinguish this unit from a handheld terminal or the separate full touchscreen set.',
}
GROUPS = [[4,5,39,40,41,42,43],[6,20,21,22,23,24,44,45,46,56],[7,8,9,10,19,47,50,51,52,53,54,55],[11,12,14,31,32,37,59],[13,15,16,17,18,35,36,38,48,49,57,58],[25,26,27,28,29,30,33,34]]

def main():
 assert set(NOTES) == set(sum(GROUPS, [])), "Every record needs related-page context"
 records={}
 for n in NOTES:
  path=ROOT/f'parts/pge-cre-{n:03}/index.html'
  text=path.read_text()
  graph=json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>',text,re.S)[1])
  product=next(x for x in graph['@graph'] if x['@type']=='Product')
  records[n]=(path,text,product)
 for n,(path,text,p) in records.items():
  text=re.sub(r'\s*<section data-pge-cremer-inquiry="true">.*?</section>\s*(?=</div></main>)','',text,flags=re.S)
  if '[data-pge-cremer-inquiry]' not in text:
   text=text.replace('</style>','[data-pge-cremer-inquiry]{margin-top:36px;max-width:760px}[data-pge-cremer-inquiry] h2{font-size:clamp(26px,4vw,36px);line-height:1.2}[data-pge-cremer-inquiry] h3{margin-top:28px}\n</style>',1)
  peers=next(g for g in GROUPS if n in g)
  others=sorted((x for x in peers if x!=n),key=lambda x:abs(x-n))[:3]
  e=html.escape
  block='\n<section data-pge-cremer-inquiry="true"><h2>Identify the component before ordering</h2>'
  block+=f'<p>Use supplier reference <strong>{e(p["sku"])}</strong> when enquiring about {e(p["name"])}. Final compatibility is confirmed during quotation.</p>'
  block+=f'<h3>What to include for this part</h3><p>{e(NOTES[n])}</p>'
  block+='<p>Include the machine serial number, quantity needed and photographs of the existing component or an approved drawing. Do not dismantle equipment solely to obtain a photograph; use available records or have qualified personnel collect details under your site procedures.</p>'
  block+='<h3>Request an identification review</h3><p><a href="/contact.html">Send a parts enquiry</a> with the supplier reference above. The listing does not establish current stock, lead time or a certified material grade; ask for those details to be confirmed in the quotation.</p>'
  block+='<h3>Related catalog records to distinguish</h3><p>These links help identify the requested component; they are not statements of interchangeability.</p><ul>'
  block+=''.join(f'<li><a href="/parts/pge-cre-{x:03}/">{e(records[x][2]["name"])}</a></li>' for x in others)
  block+='</ul><p>PharmaGlobalEng is an independent supplier, not affiliated with or endorsed by Cremer. Equipment names identify the catalog application; exact fit requires review.</p></section>\n'
  assert '</div></main>' in text
  path.write_text(text.replace('</div></main>',block+'</div></main>',1))
 urls={p['url'] for _,_,p in records.values()}
 for sitemap in ROOT.glob('sitemap*.xml'):
  original=sitemap.read_text()
  def refresh(match):
   block=match[0]
   loc=re.search(r'<loc>(.*?)</loc>',block)
   if not loc or loc[1] not in urls:return block
   if '<lastmod>' in block:return re.sub(r'<lastmod>.*?</lastmod>','<lastmod>2026-10-10</lastmod>',block)
   return block.replace('</loc>','</loc><lastmod>2026-10-10</lastmod>',1)
  updated=re.sub(r'<url\b[^>]*>.*?</url>',refresh,original,flags=re.S)
  if updated!=original:sitemap.write_text(updated)
 print(f'Updated {len(records)} existing Cremer pages; identifiers and indexing directives preserved.')

if __name__=='__main__':main()
