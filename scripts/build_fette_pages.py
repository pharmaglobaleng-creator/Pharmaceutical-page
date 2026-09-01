from __future__ import annotations

import csv
import json
import re
from collections import Counter
from html import escape
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://pharmaglobaleng.com"
DATA_PATH = ROOT / "data/fette-first-200.json"


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def equipment(part: dict) -> str:
    return f"Fette {part['model']} tablet press"


def oem_label(part: dict) -> str:
    return part["oem_number"] or "Needed"


def replacement_label(part: dict) -> str:
    if part["oem_number"]:
        return f"Replacement Part for OEM {part['oem_number']}"
    return "Replacement Part — OEM Number Needed"


def description(part: dict) -> str:
    if part["oem_number"]:
        return (
            f"Independent {part['part_name']} replacement part for OEM {part['oem_number']}, "
            f"cataloged for selected {equipment(part)} configurations. Fit is confirmed by machine "
            "configuration, dimensions, mounting, material, finish, and operating geometry."
        )
    return (
        f"Independent {part['part_name']} replacement part cataloged for selected {equipment(part)} "
        "configurations. The catalog does not list an OEM number; fit and the missing OEM cross-reference "
        "must be confirmed during engineering review."
    )


def application_guidance(part: dict) -> tuple[str, str, tuple[str, ...]]:
    name = part["part_name"].lower()
    category = part["category"].lower()
    text = f"{name} {category}"
    rules = [
        (("cam", "track"),
         "This cam or track component establishes a guided motion profile for the mechanism that follows its working surface.",
         ("Working profile and follower contact area", "Mounting pattern and installed orientation", "Clearance through the operating cycle")),
        (("turret",),
         "This turret-related component supports the indexed tooling arrangement used during the tablet-compression cycle.",
         ("Station count and tooling configuration", "Mounting and drive interfaces", "Critical runout, alignment, and clearances")),
        (("seal", "felt", "o-ring", "gasket"),
         "This sealing component helps control lubricant, product, air, or contaminant movement at its installed interface.",
         ("Cross-section and installed diameter", "Groove or mating-surface geometry", "Material compatibility with product, lubricant, and cleaning exposure")),
        (("bearing", "bush", "bushing"),
         "This bearing or bushing component supports a rotating or sliding interface while helping maintain alignment.",
         ("Bore, outside diameter, and length", "Shaft and housing fit", "Lubrication and operating environment")),
        (("belt", "gear", "wheel", "sprocket"),
         "This drive component transfers or coordinates motion between connected tablet-press mechanisms.",
         ("Tooth, groove, or pitch geometry", "Bore, keyway, and shaft connection", "Alignment with the mating drive component")),
        (("plate", "guide", "rail"),
         "This guide or plate component helps locate, support, or control the travel of a mating tablet-press mechanism.",
         ("Overall profile and critical dimensions", "Hole pattern and mounting orientation", "Mating-component clearance and wear surfaces")),
        (("feed", "paddle", "hopper", "chute"),
         "This product-handling component participates in presenting or directing material through the tablet-press feed path.",
         ("Product-contact geometry", "Rotation or travel direction and installed height", "Interfaces with adjacent feed-system components")),
        (("shaft", "pin", "stud", "screw", "bolt"),
         "This mounting or motion-transfer component locates, supports, fastens, or transmits movement between connected mechanisms.",
         ("Critical diameters, shoulders, and lengths", "Threads, keyways, or retaining features", "Mating housings and operating clearance")),
    ]
    for needles, function, checks in rules:
        if any(needle in text for needle in needles):
            return function, (
                "Visual similarity alone does not establish compatibility. Confirm the exact machine configuration, "
                "installed orientation, mating components, material, finish, and critical dimensions."
            ), checks
    return (
        f"The {part['part_name']} is cataloged in the {part['category']} group for the referenced Fette tablet-press application.",
        "Its exact function and configuration depend on its installed location and mating components; visual similarity alone is not sufficient to establish fit.",
        ("Critical dimensions and component geometry", "Mounting method and installed orientation", "Mating components and operating clearance"),
    )


def aliases(part: dict) -> list[str]:
    values = [
        part["part_name"],
        f"Fette {part['model']} {part['part_name']}",
        part["sku"],
        part["sku"].replace("-", " "),
        part["sku"].replace("-", ""),
    ]
    if part["oem_number"]:
        values.extend([
            part["oem_number"],
            f"OEM {part['oem_number']}",
            f"replacement part {part['oem_number']}",
            f"Fette {part['model']} {part['oem_number']}",
        ])
    result = []
    for value in values:
        value = clean(str(value))
        if value and value.casefold() not in {item.casefold() for item in result}:
            result.append(value)
    return result


def inquiry_url(part: dict) -> str:
    subject = f"Fette part inquiry | {part['sku']} | {part['part_name']}"
    body = (
        "Hello PharmaGlobalEng,\n\n"
        "I would like compatibility and quotation information for this independently manufactured replacement part:\n\n"
        f"Part name: {part['part_name']}\n"
        f"PharmaGlobalEng SKU: {part['sku']}\n"
        f"OEM cross-reference: {oem_label(part)}\n"
        f"Machine: {equipment(part)}\n\n"
        "Quantity required:\nMachine serial number/configuration:\nExisting part or drawing reference:\nAdditional information:\n"
    )
    return "mailto:info@pharmaglobaleng.com?" + urlencode({"subject": subject, "body": body})


def related_parts(part: dict, parts: list[dict]) -> list[dict]:
    same = [p for p in parts if p["sku"] != part["sku"] and p["model"] == part["model"] and p["category"] == part["category"]]
    model = [p for p in parts if p["sku"] != part["sku"] and p["model"] == part["model"] and p not in same]
    return (same + model)[:4]


def json_ld(part: dict) -> str:
    fit_q = f"Will this {part['part_name']} fit a {equipment(part)}?"
    fit_a = (
        f"It is cataloged as an independent replacement component for selected {equipment(part)} configurations"
        + (f" associated with OEM cross-reference {part['oem_number']}" if part["oem_number"] else "")
        + ". Fit is not guaranteed by model name or photograph alone; confirm the machine configuration, serial information, dimensions, mounting, material, finish, and mating components before manufacture."
    )
    genuine_q = f"Is this a genuine Fette OEM part?"
    genuine_a = (
        "No. It is an independently manufactured replacement component supplied by PharmaGlobalEng. "
        "Fette names, models, and OEM cross-references are used only to identify potential compatibility."
    )
    properties = [
        {"@type": "PropertyValue", "name": "Machine compatibility reference", "value": equipment(part)},
        {"@type": "PropertyValue", "name": "OEM cross-reference", "value": oem_label(part)},
        {"@type": "PropertyValue", "name": "OEM number status", "value": "Catalog supplied" if part["oem_number"] else "Needed"},
        {"@type": "PropertyValue", "name": "Supplier relationship", "value": "Independent replacement-part manufacturer; not OEM affiliated or endorsed"},
    ]
    product = {
        "@type": "Product",
        "@id": f"{SITE}/parts/{part['sku'].lower()}/#product",
        "name": f"{part['part_name']} — {replacement_label(part)} for {equipment(part)}",
        "alternateName": aliases(part),
        "sku": part["sku"],
        "url": f"{SITE}/parts/{part['sku'].lower()}/",
        "description": description(part),
        "image": SITE + part["image"],
        "category": part["category"],
        "brand": {"@type": "Brand", "name": "PharmaGlobalEng"},
        "manufacturer": {"@type": "Organization", "name": "PharmaGlobalEng", "url": SITE + "/"},
        "isAccessoryOrSparePartFor": {"@type": "ProductModel", "name": equipment(part)},
        "additionalProperty": properties,
    }
    if part["oem_number"]:
        product["identifier"] = {"@type": "PropertyValue", "propertyID": "OEM cross-reference", "value": part["oem_number"]}
    data = {
        "@context": "https://schema.org",
        "@graph": [
            product,
            {"@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": fit_q, "acceptedAnswer": {"@type": "Answer", "text": fit_a}},
                {"@type": "Question", "name": genuine_q, "acceptedAnswer": {"@type": "Answer", "text": genuine_a}},
            ]},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Parts Store", "item": SITE + "/parts/"},
                {"@type": "ListItem", "position": 2, "name": "Fette parts", "item": SITE + "/parts/fette/"},
                {"@type": "ListItem", "position": 3, "name": part["sku"], "item": f"{SITE}/parts/{part['sku'].lower()}/"},
            ]},
        ],
    }
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def build_page(part: dict, parts: list[dict]) -> str:
    slug = part["sku"].lower()
    url = f"{SITE}/parts/{slug}/"
    title = f"{part['part_name']} | Fette {part['model']} {replacement_label(part)} | PharmaGlobalEng"
    meta = description(part)
    image_url = SITE + part["image"]
    image_alt = f"{part['part_name']} replacement component for selected {equipment(part)} configurations"
    alias_chips = "".join(f'<span class="alias">{escape(item)}</span>' for item in aliases(part))
    function_note, application_note, checks = application_guidance(part)
    check_items = "".join(f"<li>{escape(item)}</li>" for item in checks)
    related = "".join(
        f'<li><a href="/parts/{p["sku"].lower()}/">{escape(p["part_name"])}</a> <span>({escape(replacement_label(p))})</span></li>'
        for p in related_parts(part, parts)
    )
    fit_q = f"Will this {part['part_name']} fit a {equipment(part)}?"
    fit_a = (
        f"This independently manufactured {part['part_name']} is cataloged for selected {equipment(part)} configurations"
        + (f" associated with OEM cross-reference {part['oem_number']}" if part["oem_number"] else ". The catalog OEM number is currently marked as needed")
        + ". Compatibility is established during engineering review by confirming machine configuration, serial information, critical dimensions, mounting arrangement, material, finish, mating components, and operating geometry."
    )
    return f'''<!doctype html>
<html lang="en-US"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title><meta name="description" content="{escape(meta)}"><meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{url}"><meta property="og:type" content="product"><meta property="og:site_name" content="PharmaGlobalEng"><meta property="og:locale" content="en_US">
<meta property="og:title" content="{escape(title)}"><meta property="og:description" content="{escape(meta)}"><meta property="og:url" content="{url}"><meta property="og:image" content="{image_url}"><meta property="og:image:alt" content="{escape(image_alt)}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{escape(title)}"><meta name="twitter:description" content="{escape(meta)}"><meta name="twitter:image" content="{image_url}"><meta name="twitter:image:alt" content="{escape(image_alt)}">
<link rel="stylesheet" href="/assets/css/pharmaglobaleng.css"><link rel="stylesheet" href="/assets/css/part-detail.css"><link rel="stylesheet" href="/assets/css/parts-quote-cart.css?v=1"><script type="application/ld+json">{json_ld(part)}</script></head>
<body><header class="site-header"><div class="wrap nav"><a class="brand" href="/">PharmaGlobal<span>Eng</span></a><nav class="nav-links" aria-label="Primary navigation"><a href="/services/">Services</a><a href="/solutions/">Solutions</a><a href="/parts/" aria-current="page">Parts Store</a><a class="nav-cta" href="/contact.html">Contact</a></nav></div></header>
<main><div class="wrap"><div class="part-crumb"><a href="/parts/">Parts Store</a> / <a href="/parts/fette/">Fette parts</a> / {escape(part['sku'])}</div>
<section class="part-hero"><div class="part-image"><img src="{part['image']}" alt="{escape(image_alt)}" width="760" height="760" loading="eager" fetchpriority="high" decoding="async"></div><div class="part-intro"><p class="eyebrow">Independent replacement component</p><h1>{escape(part['part_name'])} for {escape(equipment(part))}</h1><span class="sku-badge">{escape(replacement_label(part))}</span><div class="store-links"><a href="/parts/fette/">View in the Fette Parts Store →</a><a href="/parts/">Browse all parts →</a></div><p class="lead">{escape(meta)}</p><div class="compatibility"><strong>OEM Number: {escape(oem_label(part))}</strong><br>Make: <strong>Fette</strong> · Model: <strong>{escape(part['model'])}</strong> · Category: <strong>{escape(part['category'])}</strong></div><div class="part-quote-actions"><button class="btn primary quote-cta" type="button" data-pge-cart-add data-part-sku="{escape(part['sku'])}" data-part-name="{escape(part['part_name'])}" data-part-brand="Fette" data-part-model="{escape(part['model'])}" data-part-url="/parts/{slug}/">Add to Quote Cart</button><a class="btn secondary email-part-inquiry" href="{escape(inquiry_url(part))}">Email this part</a></div></div></section></div>
<section class="detail-section"><div class="wrap detail-grid"><div class="detail-box"><h2>Component details</h2><dl><div><dt>OEM number</dt><dd>{escape(oem_label(part))}</dd></div><div><dt>Make</dt><dd>Fette</dd></div><div><dt>Model</dt><dd>{escape(part['model'])}</dd></div><div><dt>Part name</dt><dd>{escape(part['part_name'])}</dd></div><div><dt>Part category</dt><dd>{escape(part['category'])}</dd></div><div><dt>Catalog page</dt><dd>{part['catalog_page']}</dd></div><div><dt>Supply relationship</dt><dd>Independent replacement component; not a genuine OEM part</dd></div></dl></div><div class="detail-box"><h2>What does this part do?</h2><p>{escape(function_note)}</p><p>{escape(application_note)}</p></div></div></section>
<section class="detail-section"><div class="wrap detail-grid"><div class="detail-box"><h2>Part-specific verification checkpoints</h2><ul>{check_items}</ul><p>The existing component, OEM cross-reference, drawing, or dimensional record is used to resolve the final manufacturing configuration.</p></div><div class="detail-box"><h2>{escape(fit_q)}</h2><p>{escape(fit_a)}</p></div></div></section>
<section class="detail-section"><div class="wrap"><h2>Find this replacement part using similar terms</h2><p class="section-copy">Search recognizes the OEM cross-reference when supplied, make, model, part name, and formatting variations.</p><div class="aliases">{alias_chips}</div></div></section>
<section class="detail-section"><div class="wrap detail-grid"><div class="detail-box"><h2>Is this a genuine Fette OEM part?</h2><p>No. This is an independently manufactured replacement component supplied by PharmaGlobalEng. Fette names, models, and OEM cross-references are used only to identify potential equipment compatibility.</p></div><div class="detail-box"><h2>Related Fette {escape(part['model'])} components</h2><ul class="related-parts">{related}</ul></div></div></section>
<section class="detail-section"><div class="wrap"><div class="notice"><strong>Independent supplier and trademark notice:</strong> PharmaGlobalEng is not affiliated with, authorized by, sponsored by, or endorsed by Fette or its trademark owner. Fette names, model references, and OEM numbers are used solely to identify potential equipment compatibility. All trademarks belong to their respective owners. Product images are representative visualizations of independently manufactured replacement components, not OEM photographs.</div></div></section></main>
<footer><div class="wrap footer"><span>© PharmaGlobalEng</span><a href="/parts/">All parts</a><a href="/contact.html">Parts inquiry</a></div></footer><script src="/assets/js/parts-quote-cart.js?v=1"></script></body></html>'''


def build_catalog(parts: list[dict]) -> None:
    total = len(parts)
    cards = []
    for part in parts:
        search = " | ".join(aliases(part))
        cards.append(f'''<article class="product-card" data-name="{escape(part['part_name'])}" data-model="{escape(part['model'])}" data-sku="{escape(part['sku'])}" data-search="{escape(search)}"><div class="product-visual"><img src="{part['image']}" alt="{escape(part['part_name'])} replacement component for {escape(equipment(part))}" width="760" height="760" loading="lazy" decoding="async"></div><div class="product-content"><p class="product-family">{escape(part['model'])} · {escape(part['category'])}</p><h3><a href="/parts/{part['sku'].lower()}/">{escape(part['part_name'])}</a></h3><p class="sku">OEM Number: {escape(oem_label(part))}</p><a class="part-page-link" href="/parts/{part['sku'].lower()}/">View replacement part page →</a><p class="product-copy">{escape(replacement_label(part))}. Independent component; fit verification required.</p><div class="product-actions"><span class="availability">Quote review</span><a class="btn small" href="/parts/{part['sku'].lower()}/">View part</a><button class="btn small" type="button" data-pge-cart-add data-part-sku="{escape(part['sku'])}" data-part-name="{escape(part['part_name'])}" data-part-brand="Fette" data-part-model="{escape(part['model'])}" data-part-url="/parts/{part['sku'].lower()}/">Add to Quote Cart</button></div></div></article>''')
    model_counts = Counter(p["model"] for p in parts)
    filters = "".join(f'<option value="{escape(model)}">{escape(model)} ({count})</option>' for model, count in sorted(model_counts.items()))
    page = f'''<!doctype html><html lang="en-US"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fette Tablet Press Replacement Parts by OEM Number | PharmaGlobalEng</title><meta name="description" content="Browse {total} independently manufactured Fette tablet press replacement parts organized by model, part name, and catalog-supplied OEM number."><meta name="robots" content="index,follow,max-image-preview:large"><link rel="canonical" href="{SITE}/parts/fette/"><link rel="stylesheet" href="/assets/css/pharmaglobaleng.css"><link rel="stylesheet" href="/assets/css/store.css"><link rel="stylesheet" href="/assets/css/parts-quote-cart.css?v=1"><script src="/assets/js/parts-search.js?v=1"></script><script type="application/ld+json">{json.dumps({'@context':'https://schema.org','@type':'CollectionPage','name':'Fette Tablet Press Replacement Parts','url':SITE + '/parts/fette/','description':'Independent replacement parts organized by Fette model and OEM cross-reference.'}, separators=(',', ':'))}</script></head><body><header class="site-header"><div class="wrap nav"><a class="brand" href="/">PharmaGlobal<span>Eng</span></a><nav class="nav-links" aria-label="Primary navigation"><a href="/services/">Services</a><a href="/solutions/">Solutions</a><a href="/parts/" aria-current="page">Parts Store</a><a href="/contact.html">Contact</a></nav></div></header><main><section class="store-hero"><div class="wrap"><div class="crumb"><a href="/parts/">Parts Store</a> / Fette</div><p class="eyebrow">Independent replacement-part library</p><h1>Replacement Parts Compatible with Selected Fette Tablet Presses</h1><p class="lead">Browse {total} independently manufactured replacement components organized by Fette model, part name, category, and catalog-supplied OEM cross-reference. Compatibility is verified during quotation.</p><div class="catalog-search"><label class="visually-hidden" for="part-search">Search Fette parts</label><input id="part-search" type="search" placeholder="Search OEM number, part name, model, or category" autocomplete="off"><label class="visually-hidden" for="model-filter">Filter by Fette model</label><select id="model-filter"><option value="">All Fette models</option>{filters}</select><span class="search-result-count"><strong id="visible-count">{total}</strong> results</span></div></div></section><section class="section" id="catalog"><div class="wrap"><div class="catalog-meta"><span><strong>{total}</strong> representative part images</span><span>Independent supplier · compatibility confirmation required</span></div><div class="product-grid" id="product-grid">{''.join(cards)}</div><p id="no-results" class="notice" hidden><strong>No matching part was found.</strong> Try an OEM number, model, or shorter part name.</p><div class="notice"><strong>Independent supplier and trademark notice:</strong> PharmaGlobalEng is not affiliated with, authorized by, sponsored by, or endorsed by Fette or its trademark owner. Fette names, model references, and OEM numbers identify potential equipment compatibility only. All trademarks belong to their respective owners. Images depict independently manufactured replacement components, not genuine OEM parts.</div></div></section></main><footer><div class="wrap footer"><span>© PharmaGlobalEng</span><a href="/parts/">All parts</a><a href="/contact.html">Parts inquiry</a></div></footer><script>(()=>{{const input=document.getElementById('part-search'),model=document.getElementById('model-filter'),cards=[...document.querySelectorAll('.product-card')],count=document.getElementById('visible-count'),empty=document.getElementById('no-results');function filter(){{const q=input.value,m=model.value;let shown=0;cards.forEach(card=>{{const matchText=window.PGEPartsSearch.matches(card.dataset.search||card.textContent,q),matchModel=!m||card.dataset.model===m,match=matchText&&matchModel;card.hidden=!match;if(match)shown++;}});count.textContent=shown;empty.hidden=shown!==0;}}input.addEventListener('input',filter);model.addEventListener('change',filter);}})();</script><script src="/assets/js/parts-quote-cart.js?v=1"></script></body></html>'''
    destination = ROOT / "parts/fette/index.html"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(page, encoding="utf-8")


def update_parts_index() -> None:
    path = ROOT / "parts/index.html"
    page = path.read_text(encoding="utf-8")
    page = page.replace("Browse 484 representative visualizations", "Browse 584 representative visualizations")
    page = page.replace("Browse 384 representative visualizations", "Browse 584 representative visualizations")
    page = page.replace("Korsch, Manesty, Kikusui, Stokes, or", "Korsch, Fette, Manesty, Kikusui, Stokes, or")
    marker = '<a class="machine-card" href="/parts/manesty/">'
    card = '''<a class="machine-card" href="/parts/fette/"><span class="status-pill">200 parts</span><div class="card-mark" aria-hidden="true">FT</div><h3>Replacement Parts Compatible with Selected Fette Equipment</h3><p>Browse independently manufactured components organized by Fette model and catalog-supplied OEM cross-reference.</p><span class="card-link">Browse compatible parts →</span></a>'''
    page = re.sub(r'<a class="machine-card" href="/parts/fette/">.*?</a>', '', page, count=1, flags=re.S)
    page = page.replace(marker, card + marker, 1)
    path.write_text(page, encoding="utf-8")


def update_sitemaps(parts: list[dict]) -> None:
    path = ROOT / "sitemap.xml"
    xml = path.read_text(encoding="utf-8")
    xml = re.sub(r'\n\s*<url>\s*<loc>https://pharmaglobaleng\.com/parts/pge-fet-[^<]+</loc>.*?</url>', '', xml, flags=re.S)
    if f"{SITE}/parts/fette/" not in xml:
        xml = xml.replace("</urlset>", f"  <url><loc>{SITE}/parts/fette/</loc><changefreq>weekly</changefreq><priority>0.85</priority></url>\n</urlset>")
    entries = "\n".join(f'  <url><loc>{SITE}/parts/{p["sku"].lower()}/</loc><changefreq>monthly</changefreq><priority>0.75</priority></url>' for p in parts)
    xml = xml.replace("</urlset>", entries + "\n</urlset>")
    path.write_text(xml, encoding="utf-8")
    image_path = ROOT / "sitemap-parts-images.xml"
    image_xml = image_path.read_text(encoding="utf-8")
    image_xml = re.sub(r'\n\s*<url><loc>https://pharmaglobaleng\.com/parts/pge-fet-.*?</url>', '', image_xml, flags=re.S)
    image_entries = "\n".join(f'  <url><loc>{SITE}/parts/{p["sku"].lower()}/</loc><image:image><image:loc>{SITE + p["image"]}</image:loc><image:title>{escape(p["part_name"] + " — " + replacement_label(p))}</image:title><image:caption>Independent replacement component for {escape(equipment(p))}; compatibility confirmation required.</image:caption></image:image></url>' for p in parts)
    image_xml = image_xml.replace("</urlset>", image_entries + "\n</urlset>")
    image_path.write_text(image_xml, encoding="utf-8")


def write_audit(parts: list[dict]) -> None:
    path = ROOT / "data/fette-first-200-content-audit.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("position", "sku", "make", "model", "part_name", "category", "oem_number", "oem_status", "catalog_page", "image_path", "landing_page"))
        for p in parts:
            writer.writerow((p["position"], p["sku"], p["make"], p["model"], p["part_name"], p["category"], p["oem_number"] or "Needed", p["oem_status"], p["catalog_page"], p["image"], f"/parts/{p['sku'].lower()}/"))


def main() -> None:
    parts = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if len(parts) != 200 or len({p["sku"] for p in parts}) != 200:
        raise SystemExit("Fette dataset must contain exactly 200 unique records")
    if any("natoli" in json.dumps(p).lower() for p in parts):
        raise SystemExit("Natoli identifier found in public Fette dataset")
    for part in parts:
        destination = ROOT / "parts" / part["sku"].lower() / "index.html"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(build_page(part, parts), encoding="utf-8")
    build_catalog(parts)
    update_parts_index()
    update_sitemaps(parts)
    write_audit(parts)
    print(f"Generated {len(parts)} Fette landing pages; OEM supplied: {sum(bool(p['oem_number']) for p in parts)}; OEM needed: {sum(not p['oem_number'] for p in parts)}")


if __name__ == "__main__":
    main()
