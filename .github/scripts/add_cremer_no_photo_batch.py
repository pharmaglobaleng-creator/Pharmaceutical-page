from pathlib import Path
from html import escape
import json, re

parts = [{'sku': 'PGE-CRE-004', 'name': 'Rack Module (by set only)', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-005', 'name': 'Gate Assembly Guider', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-006', 'name': 'Silicone Gasket', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-007', 'name': 'Pneumatic Service Unit', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-008', 'name': 'Quick Coupling KD-1/4', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-009', 'name': 'Quick Coupling Plug KS3-CK-4', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-010', 'name': 'Push-In Fitting QSF-1/4-8B', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-011', 'name': 'HHT-to-Counter Communication Cable, 9-Pin', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-012', 'name': 'Fixed HHT Mounting Bracket', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-013', 'name': 'Safety Module PNOZ-X7 24V DC/AC', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-014', 'name': 'HHT Handheld Terminal', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-015', 'name': 'AC Motor 6D22, 50 Hz, 50 rpm', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-016', 'name': 'Red LED Indicator, 24 V', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-017', 'name': 'Yellow LED Indicator, 24 V', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-018', 'name': 'Main Control PCB', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-019', 'name': 'Memory Flap Cylinder PTM 100-10-85P', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-020', 'name': 'Silicone Buffer Ring', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-021', 'name': 'Buffer Ring Nut (2005)', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-022', 'name': 'Memory Flap Buffer Strip / Silicone Foam', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-023', 'name': 'Hopper Buffer Strip / Silicone Strip Hopper Plate', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-024', 'name': 'Memory Flap Fork with Locking Ring', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-025', 'name': 'Detection Unit Assembly', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-026', 'name': 'Detection Unit Glass', 'model': 'CF1220 / CVC1220'},
 {'sku': 'PGE-CRE-027', 'name': 'Detection Unit Processor Board', 'model': 'CF1220 / CVC1220'},
 {'sku': 'PGE-CRE-028', 'name': 'Detection Unit Emitter Board', 'model': 'CF1220 / CVC1220'},
 {'sku': 'PGE-CRE-029', 'name': 'Detection Unit Receiver Board', 'model': 'CF1220 / CVC1220'},
 {'sku': 'PGE-CRE-030', 'name': 'Detection Unit Connector Board', 'model': 'CF1220 / CVC1220'},
 {'sku': 'PGE-CRE-031', 'name': 'HHT PC Board + Keyboard Full Set', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-032', 'name': 'Touch Screen Full Set', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-033', 'name': 'Infrared Emitter', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-034', 'name': 'Infrared Receiver', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-035', 'name': 'Processor PCB', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-036', 'name': 'PWM PCB', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-037', 'name': 'Keyboard PCB', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-038', 'name': 'Frequency Inverter', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-039', 'name': 'M-Type Outfeed Timing Belt 1025-5M-12', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-040', 'name': 'Dosage Flap / Hopper Gate', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-041', 'name': '16 mm Channel Inserter', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-042', 'name': '19 mm Channel Divider Insert', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-043', 'name': 'Tilt Nozzle for 750 cc / 950 cc Bottles', 'model': 'CVC1220'},
 {'sku': 'PGE-CRE-044', 'name': 'Easy-Clean Cylinder Head Nut', 'model': 'CF1220 / CVC1220'},
 {'sku': 'PGE-CRE-045', 'name': 'Precision-Fit Nut Buffer', 'model': 'CF1220 / CVC1220'},
 {'sku': 'PGE-CRE-046', 'name': 'Clevis / Rod End', 'model': 'CF1220 / CVC1220'},
 {'sku': 'PGE-CRE-047', 'name': '13-Station Valve Manifold Block', 'model': 'CF1220 / CVC1220'},
 {'sku': 'PGE-CRE-048', 'name': 'Valve Manifold PCB', 'model': 'CF1220 / CVC1220'},
 {'sku': 'PGE-CRE-049', 'name': 'Internal Cable Harness', 'model': 'CF1220 / CVC1220'},
 {'sku': 'PGE-CRE-050', 'name': 'Internal Pneumatic Push-In Connector Set', 'model': 'CF1220 / CVC1220'},
 {'sku': 'PGE-CRE-051', 'name': 'External Pneumatic Connector Set', 'model': 'CF1220 / CVC1220'},
 {'sku': 'PGE-CRE-052', 'name': '4 mm Pneumatic Tube – 15 cm', 'model': 'CF1220 / CVC1220'},
 {'sku': 'PGE-CRE-053', 'name': '4 mm Pneumatic Tube – 20 cm with Insert', 'model': 'CF1220 / CVC1220'},
 {'sku': 'PGE-CRE-054', 'name': '8 mm Pneumatic Tube', 'model': 'CF1220 / CVC1220'},
 {'sku': 'PGE-CRE-055', 'name': '4 mm Pneumatic Tube', 'model': 'CF1220 / CVC1220'},
 {'sku': 'PGE-CRE-056', 'name': 'Memory Flap Guide Block Buffer', 'model': 'CF1220 / CVC1220'},
 {'sku': 'PGE-CRE-057', 'name': 'CF1220-LTE Interface Control Board', 'model': 'CF1220 / CVC1220'},
 {'sku': 'PGE-CRE-058', 'name': 'Piggy-Back PLC', 'model': 'CF1220 / CVC1220'},
 {'sku': 'PGE-CRE-059', 'name': 'Compact HHT-Style Touchscreen', 'model': 'CF1220 / CVC1220'}]

repo = Path('.')
today = '2026-09-12'

def page_html(p):
    sku = p['sku']
    name = p['name']
    model = p['model']
    url = f"https://pharmaglobaleng.com/parts/{sku.lower()}/"
    title = f"{name} | Cremer {model}"
    desc = f"Cremer {model} replacement part: {name}. Contact PharmaGlobalEng for fit and availability."
    schema = {
        "@context":"https://schema.org",
        "@graph":[
            {
                "@type":"Product",
                "@id":url+"#product",
                "name":f"{name} for Cremer {model}",
                "sku":sku,
                "url":url,
                "description":desc,
                "brand":{"@type":"Brand","name":"PharmaGlobalEng"},
                "manufacturer":{"@id":"https://pharmaglobaleng.com/#organization"},
                "isAccessoryOrSparePartFor":{"@type":"ProductModel","name":f"Cremer {model}"}
            },
            {
                "@type":"BreadcrumbList",
                "itemListElement":[
                    {"@type":"ListItem","position":1,"name":"Parts Store","item":"https://pharmaglobaleng.com/parts/"},
                    {"@type":"ListItem","position":2,"name":"Creamer parts","item":"https://pharmaglobaleng.com/parts/cremer/"},
                    {"@type":"ListItem","position":3,"name":name,"item":url}
                ]
            },
            {"@type":"Organization","@id":"https://pharmaglobaleng.com/#organization","name":"PharmaGlobalEng","url":"https://pharmaglobaleng.com/"}
        ]
    }
    return f'''<!doctype html>
<html lang="en-US">
<head>
<script id="pge-analytics" src="/assets/js/pge-analytics.js" defer></script>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title>
<meta name="description" content="{escape(desc, quote=True)}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{url}">
<link rel="stylesheet" href="/assets/css/pharmaglobaleng.css">
<link rel="stylesheet" href="/assets/css/pge-header.css" data-pge-header-css="true">
<style>
.minimal-part{{padding:38px 0 70px}}.minimal-part .wrap{{max-width:920px}}
.part-crumb{{font-size:14px;color:var(--muted);margin-bottom:28px}}.part-crumb a{{color:inherit;text-decoration:none}}
.minimal-part h1{{font-size:clamp(34px,5vw,58px);line-height:1.06;margin:0 0 28px;letter-spacing:-.035em}}
.part-facts{{display:grid;gap:0;border:1px solid var(--line);border-radius:14px;overflow:hidden;background:var(--bg-alt);max-width:760px}}
.part-fact{{display:grid;grid-template-columns:140px 1fr;gap:16px;padding:18px 20px;border-bottom:1px solid var(--line)}}.part-fact:last-child{{border-bottom:0}}
.part-fact strong{{color:var(--muted)}}.part-fact span{{font-weight:800}}
.call-part{{display:inline-flex;margin-top:24px;padding:12px 18px;border-radius:8px;text-decoration:none;font-weight:800;background:linear-gradient(90deg,#6b4cff,#1aa7ff);color:#fff}}
@media(max-width:560px){{.part-fact{{grid-template-columns:1fr;gap:4px}}}}
</style>
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False, separators=(',',':'))}</script>
</head>
<body>
<header data-pge-header="v1" class="site-header"><div class="wrap nav"><div class="pge-header-identity"><a class="pge-header-brand" href="/" aria-label="PharmaGlobalEng home"><img class="pge-header-logo" src="/assets/images/pge-header-logo.webp" width="34" height="30" alt="" decoding="async"><span class="pge-header-wordmark">PharmaGlobal<span>Eng</span></span></a><a class="pge-header-phone" href="tel:+17324397849">+1 (732) 439-7849</a></div><nav class="nav-links" aria-label="Primary navigation"><a href="/services/">Services</a><a href="/solutions/">Solutions</a><a href="/parts/" aria-current="page">Parts Store</a><a class="nav-cta" href="/contact.html">Contact</a></nav></div></header>
<main class="minimal-part"><div class="wrap">
<div class="part-crumb"><a href="/parts/">Parts Store</a> / <a href="/parts/cremer/">Creamer parts</a></div>
<h1>{escape(name)}</h1>
<div class="part-facts" aria-label="Part information">
<div class="part-fact"><strong>Make</strong><span>Cremer</span></div>
<div class="part-fact"><strong>Model</strong><span>{escape(model)}</span></div>
<div class="part-fact"><strong>Part</strong><span>{escape(name)}</span></div>
</div>
<a class="call-part" href="tel:+17324397849">Call about this part: +1 (732) 439-7849</a>
</div></main>
<footer><div class="wrap footer"><span>© PharmaGlobalEng</span><a href="/parts/">All parts</a><a href="/contact.html">Parts inquiry</a></div></footer>
</body></html>'''

# Rewrite the 56 no-photo pages only. The existing four photographed pages are not modified.
for p in parts:
    out = repo / 'parts' / p['sku'].lower() / 'index.html'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page_html(p), encoding='utf-8')

# Preserve the exact first four catalog cards and rebuild only the no-photo portion.
catalog_path = repo / 'parts' / 'cremer' / 'index.html'
catalog = catalog_path.read_text(encoding='utf-8')
existing_cards = re.findall(r'<article class="part-card">.*?</article>', catalog, flags=re.S)
if len(existing_cards) < 4:
    raise SystemExit('Expected at least four existing Creamer catalog cards')
first_four = existing_cards[:4]

def card(p):
    return f'''<article class="part-card">
<div class="part-card-body"><p class="part-machine">Cremer {escape(p['model'])}</p><h2>{escape(p['name'])}</h2><div class="part-card-actions"><a class="view-btn" href="/parts/{p['sku'].lower()}/">View part details <span aria-hidden="true">→</span></a></div></div>
</article>'''

new_grid = '<section class="parts-grid" aria-label="Creamer replacement parts">\n' + '\n'.join(first_four + [card(p) for p in parts]) + '\n</section>'
catalog = re.sub(r'<section class="parts-grid" aria-label="Creamer replacement parts">.*?</section>', new_grid, catalog, flags=re.S)
catalog = re.sub(r'<div class="catalog-count">\d+ parts</div>', '<div class="catalog-count">60 parts</div>', catalog)
catalog = re.sub(
    r'<meta name="description" content="[^"]*">',
    '<meta name="description" content="Browse 60 Creamer replacement-part records for Cremer CF1220 and CVC1220 equipment, including photographed components and additional part lookup pages.">',
    catalog,
    count=1
)

item_list = [
    {"name":"Dipping Nozzle Funnel Cone for Cremer CF1220","url":"https://pharmaglobaleng.com/parts/cremer-cf1220-dipping-nozzle-funnel-cone/"},
    {"name":"Channel Restrictor Plate for Cremer CF-1220","url":"https://pharmaglobaleng.com/parts/pge-cre-001/"},
    {"name":"Linear Guide Plate for Cremer CF-1220","url":"https://pharmaglobaleng.com/parts/pge-cre-002/"},
    {"name":"Set of 12 Memory Flaps for Cremer CF1220 / CVC1220","url":"https://pharmaglobaleng.com/parts/pge-cre-003/"},
] + [{"name":f"{p['name']} for Cremer {p['model']}","url":f"https://pharmaglobaleng.com/parts/{p['sku'].lower()}/"} for p in parts]

schema = {
    "@context":"https://schema.org",
    "@graph":[
        {"@type":"CollectionPage","@id":"https://pharmaglobaleng.com/parts/cremer/#webpage","url":"https://pharmaglobaleng.com/parts/cremer/","name":"Creamer Replacement Parts | PharmaGlobalEng","description":"Browse Creamer replacement-part records for Cremer CF1220 and CVC1220 equipment.","mainEntity":{"@id":"https://pharmaglobaleng.com/parts/cremer/#items"}},
        {"@type":"ItemList","@id":"https://pharmaglobaleng.com/parts/cremer/#items","name":"Creamer Replacement Parts","numberOfItems":60,"itemListElement":[{"@type":"ListItem","position":i+1,"name":x["name"],"url":x["url"]} for i,x in enumerate(item_list)]},
        {"@type":"BreadcrumbList","itemListElement":[
            {"@type":"ListItem","position":1,"name":"Home","item":"https://pharmaglobaleng.com/"},
            {"@type":"ListItem","position":2,"name":"Parts Store","item":"https://pharmaglobaleng.com/parts/"},
            {"@type":"ListItem","position":3,"name":"Creamer","item":"https://pharmaglobaleng.com/parts/cremer/"}
        ]},
        {"@type":"Organization","@id":"https://pharmaglobaleng.com/#organization","name":"PharmaGlobalEng","url":"https://pharmaglobaleng.com/"}
    ]
}
catalog = re.sub(r'<script type="application/ld\+json">.*?</script>', '<script type="application/ld+json">'+json.dumps(schema, ensure_ascii=False, separators=(',',':'))+'</script>', catalog, count=1, flags=re.S)
catalog_path.write_text(catalog, encoding='utf-8')

# Rebuild the Creamer sitemap.
urls = [
    'https://pharmaglobaleng.com/parts/cremer/',
    'https://pharmaglobaleng.com/parts/cremer-cf1220-dipping-nozzle-funnel-cone/',
    'https://pharmaglobaleng.com/parts/pge-cre-001/',
    'https://pharmaglobaleng.com/parts/pge-cre-002/',
    'https://pharmaglobaleng.com/parts/pge-cre-003/',
] + [f"https://pharmaglobaleng.com/parts/{p['sku'].lower()}/" for p in parts]
sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(
    f'  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n' for u in urls
) + '</urlset>\n'
(repo / 'sitemap-cremer.xml').write_text(sitemap, encoding='utf-8')

# Update the root Parts Store hydration repair count/card count without touching the four photographed part pages.
analytics_path = repo / 'assets' / 'js' / 'pge-analytics.js'
analytics = analytics_path.read_text(encoding='utf-8')
analytics = re.sub(r"'\d+ parts'", "'60 parts'", analytics)
analytics = re.sub(r"'[\d,]+ part records'", "'4,271 part records'", analytics)
analytics_path.write_text(analytics, encoding='utf-8')
