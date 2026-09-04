from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from collections import Counter
from html import escape
from pathlib import Path
from urllib.parse import urlencode


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://pharmaglobaleng.com"
DATA_PATH = ROOT / "data/kikusui-parts.csv"
IMAGE_DIR = ROOT / "assets/images/parts/kikusui"
TOTAL_SITE_PARTS = 3410


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", "" if value is None else str(value)).strip()


def has_oem(part: dict[str, str]) -> bool:
    return clean(part["oem_number"]).casefold() not in {"", "n/a", "na", "none", "not available"}


def oem_display(part: dict[str, str]) -> str:
    return part["oem_number"] if has_oem(part) else "Not listed in source catalog"


def has_image(part: dict[str, str]) -> bool:
    return bool(part["image_path"])


def image_status_note(part: dict[str, str]) -> str:
    if has_image(part):
        return "Representative studio visualization created from the catalog-matched part photograph."
    if part["photo_status"] == "Stock photo":
        return "Image intentionally omitted: the source workbook marks the available catalog image as a stock photo, so its exact geometry is not verified."
    return "Image intentionally omitted: the source catalog does not provide an exact part photograph for this record."


def description(part: dict[str, str]) -> str:
    oem = f"OEM cross-reference {part['oem_number']}" if has_oem(part) else "no OEM number listed in the source catalog"
    return (
        f"Independent replacement-part record for {part['part_name']}, matched to Kikusui {part['model']}, "
        f"catalog part {part['catalog_part_number']}, and {oem}. Compatibility is confirmed during quotation."
    )


def aliases(part: dict[str, str]) -> list[str]:
    values = [
        part["part_name"],
        f"Kikusui {part['model']} {part['part_name']}",
        part["model"],
        part["catalog_part_number"],
        f"catalog part {part['catalog_part_number']}",
        part["sku"],
        part["sku"].replace("-", " "),
        part["sku"].replace("-", ""),
    ]
    if has_oem(part):
        values.extend([part["oem_number"], f"OEM {part['oem_number']}"])
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        value = clean(value)
        if value and value.casefold() not in seen:
            result.append(value)
            seen.add(value.casefold())
    return result


def inquiry_url(part: dict[str, str]) -> str:
    subject = f"Kikusui part inquiry | {part['sku']} | {part['part_name']}"
    body = (
        "Hello PharmaGlobalEng,\n\n"
        "I would like compatibility and quotation information for this independently manufactured replacement part:\n\n"
        f"Part name: {part['part_name']}\n"
        f"PharmaGlobalEng SKU: {part['sku']}\n"
        f"Make: Kikusui\n"
        f"Model: {part['model']}\n"
        f"Catalog part number: {part['catalog_part_number']}\n"
        f"OEM number: {oem_display(part)}\n\n"
        "Quantity required:\nMachine serial number/configuration:\nExisting part or drawing reference:\nAdditional information:\n"
    )
    return "mailto:info@pharmaglobaleng.com?" + urlencode({"subject": subject, "body": body})


def related_parts(part: dict[str, str], parts: list[dict[str, str]]) -> list[dict[str, str]]:
    same_category = [
        candidate for candidate in parts
        if candidate["sku"] != part["sku"]
        and candidate["model"] == part["model"]
        and candidate["category"] == part["category"]
    ]
    same_model = [
        candidate for candidate in parts
        if candidate["sku"] != part["sku"]
        and candidate["model"] == part["model"]
        and candidate not in same_category
    ]
    return (same_category + same_model)[:4]


def product_schema(part: dict[str, str]) -> dict:
    slug = part["sku"].lower()
    product: dict = {
        "@type": "Product",
        "@id": f"{SITE}/parts/{slug}/#product",
        "name": f"{part['part_name']} for Kikusui {part['model']}",
        "alternateName": aliases(part),
        "sku": part["sku"],
        "url": f"{SITE}/parts/{slug}/",
        "description": description(part),
        "category": part["category"],
        "brand": {"@type": "Brand", "name": "PharmaGlobalEng"},
        "manufacturer": {"@type": "Organization", "name": "PharmaGlobalEng", "url": SITE + "/"},
        "isAccessoryOrSparePartFor": {"@type": "ProductModel", "name": f"Kikusui {part['model']}"},
        "additionalProperty": [
            {"@type": "PropertyValue", "name": "Make", "value": "Kikusui"},
            {"@type": "PropertyValue", "name": "Model", "value": part["model"]},
            {"@type": "PropertyValue", "name": "Catalog part number", "value": part["catalog_part_number"]},
            {"@type": "PropertyValue", "name": "OEM cross-reference", "value": oem_display(part)},
            {"@type": "PropertyValue", "name": "Catalog page", "value": part["catalog_page"]},
            {"@type": "PropertyValue", "name": "Photo status", "value": part["photo_status"]},
            {"@type": "PropertyValue", "name": "Supplier relationship", "value": "Independent replacement-part manufacturer; not OEM affiliated or endorsed"},
        ],
    }
    if has_image(part):
        product["image"] = SITE + part["image_path"]
    if has_oem(part):
        product["identifier"] = {
            "@type": "PropertyValue",
            "propertyID": "OEM cross-reference",
            "value": part["oem_number"],
        }
    return product


def json_ld(part: dict[str, str]) -> str:
    slug = part["sku"].lower()
    data = {
        "@context": "https://schema.org",
        "@graph": [
            product_schema(part),
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Parts Store", "item": SITE + "/parts/"},
                    {"@type": "ListItem", "position": 2, "name": "Kikusui parts", "item": SITE + "/parts/kikusui/"},
                    {"@type": "ListItem", "position": 3, "name": part["sku"], "item": f"{SITE}/parts/{slug}/"},
                ],
            },
        ],
    }
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def build_page(part: dict[str, str], parts: list[dict[str, str]]) -> str:
    slug = part["sku"].lower()
    url = f"{SITE}/parts/{slug}/"
    title = f"{part['part_name']} | Kikusui {part['model']} | {part['catalog_part_number']} | PharmaGlobalEng"
    meta = description(part)
    image_alt = f"Representative studio visualization of {part['part_name']} matched to Kikusui {part['model']} catalog part {part['catalog_part_number']}"
    if has_image(part):
        image_url = SITE + part["image_path"]
        social = (
            f'<meta property="og:image" content="{escape(image_url)}"><meta property="og:image:alt" content="{escape(image_alt)}">'
            f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{escape(image_url)}"><meta name="twitter:image:alt" content="{escape(image_alt)}">'
        )
        visual = (
            f'<div class="part-image"><img src="{escape(part["image_path"])}" alt="{escape(image_alt)}" '
            'width="760" height="760" loading="eager" fetchpriority="high" decoding="async"></div>'
        )
    else:
        social = '<meta name="twitter:card" content="summary">'
        visual = (
            '<div class="part-image part-image-placeholder" role="img" '
            f'aria-label="No verified photograph is available for {escape(part["part_name"])}">'
            '<span class="placeholder-mark" aria-hidden="true">KI</span><strong>Exact photograph unavailable</strong>'
            '<span>No substitute image used</span></div>'
        )
    alias_chips = "".join(f'<span class="alias">{escape(item)}</span>' for item in aliases(part))
    related = "".join(
        f'<li><a href="/parts/{candidate["sku"].lower()}/">{escape(candidate["part_name"])}</a> '
        f'<span>({escape(candidate["catalog_part_number"])})</span></li>'
        for candidate in related_parts(part, parts)
    )
    related = related or "<li>No additional matched parts in this model group.</li>"
    return f'''<!doctype html>
<html lang="en-US"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title><meta name="description" content="{escape(meta)}"><meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{url}"><meta property="og:type" content="product"><meta property="og:site_name" content="PharmaGlobalEng"><meta property="og:locale" content="en_US">
<meta property="og:title" content="{escape(title)}"><meta property="og:description" content="{escape(meta)}"><meta property="og:url" content="{url}">{social}
<meta name="twitter:title" content="{escape(title)}"><meta name="twitter:description" content="{escape(meta)}">
<link rel="stylesheet" href="/assets/css/pharmaglobaleng.css"><link rel="stylesheet" href="/assets/css/part-detail.css"><link rel="stylesheet" href="/assets/css/parts-quote-cart.css?v=1"><script type="application/ld+json">{json_ld(part)}</script></head>
<body><header class="site-header"><div class="wrap nav"><a class="brand" href="/">PharmaGlobal<span>Eng</span></a><nav class="nav-links" aria-label="Primary navigation"><a href="/services/">Services</a><a href="/solutions/">Solutions</a><a href="/parts/" aria-current="page">Parts Store</a><a class="nav-cta" href="/contact.html">Contact</a></nav></div></header>
<main><div class="wrap"><div class="part-crumb"><a href="/parts/">Parts Store</a> / <a href="/parts/kikusui/">Kikusui parts</a> / {escape(part['sku'])}</div>
<section class="part-hero">{visual}<div class="part-intro"><p class="eyebrow">Independent replacement component</p><h1>{escape(part['part_name'])} for Kikusui {escape(part['model'])}</h1><span class="sku-badge">PharmaGlobalEng SKU: {escape(part['sku'])}</span><div class="store-links"><a href="/parts/kikusui/">View in the Kikusui Parts Store →</a><a href="/parts/">Browse all parts →</a></div><p class="lead">{escape(meta)}</p><div class="compatibility"><strong>Catalog part number: {escape(part['catalog_part_number'])}</strong><br>OEM number: <strong>{escape(oem_display(part))}</strong> · Make: <strong>Kikusui</strong> · Model: <strong>{escape(part['model'])}</strong></div><div class="part-quote-actions"><button class="btn primary quote-cta" type="button" data-pge-cart-add data-part-sku="{escape(part['sku'])}" data-part-name="{escape(part['part_name'])}" data-part-brand="Kikusui" data-part-model="{escape(part['model'])}" data-part-url="/parts/{slug}/">Add to Quote Cart</button><a class="btn secondary email-part-inquiry" href="{escape(inquiry_url(part))}">Email this part</a></div></div></section></div>
<section class="detail-section"><div class="wrap detail-grid"><div class="detail-box"><h2>Verified catalog mapping</h2><dl><div><dt>Make</dt><dd>Kikusui</dd></div><div><dt>Model</dt><dd>{escape(part['model'])}</dd></div><div><dt>Part name</dt><dd>{escape(part['part_name'])}</dd></div><div><dt>Catalog part number</dt><dd>{escape(part['catalog_part_number'])}</dd></div><div><dt>OEM number</dt><dd>{escape(oem_display(part))}</dd></div><div><dt>Part category</dt><dd>{escape(part['category'])}</dd></div><div><dt>Catalog page</dt><dd>{escape(part['catalog_page'])}</dd></div></dl></div><div class="detail-box"><h2>Photo and verification status</h2><p>{escape(image_status_note(part))}</p><p><strong>Source verification:</strong> {escape(part['verification'])}.</p><p>The catalog mapping identifies this exact record. Final dimensional fit, material, finish, and machine configuration are confirmed during quotation; no unsupported specifications are published here.</p></div></div></section>
<section class="detail-section"><div class="wrap"><h2>Find this part by its catalog references</h2><p class="section-copy">Search recognizes only the matched part name, Kikusui model, catalog part number, OEM number when supplied, and PharmaGlobalEng SKU.</p><div class="aliases">{alias_chips}</div></div></section>
<section class="detail-section"><div class="wrap detail-grid"><div class="detail-box"><h2>Compatibility confirmation</h2><p>This record is mapped to Kikusui {escape(part['model'])} in the supplied catalog. Confirm the machine serial information, configuration, existing component or drawing, and critical dimensions before manufacturing or installation.</p></div><div class="detail-box"><h2>Related Kikusui {escape(part['model'])} records</h2><ul class="related-parts">{related}</ul></div></div></section>
<section class="detail-section"><div class="wrap"><div class="notice"><strong>Independent supplier and trademark notice:</strong> PharmaGlobalEng is not affiliated with, authorized by, sponsored by, or endorsed by Kikusui or its trademark owner. Kikusui names, model references, catalog numbers, and OEM numbers are used solely to identify potential equipment compatibility. All trademarks belong to their respective owners. Published product images are representative studio visualizations of independently supplied replacement components, not genuine OEM photographs.</div></div></section></main>
<footer><div class="wrap footer"><span>© PharmaGlobalEng</span><a href="/parts/">All parts</a><a href="/contact.html">Parts inquiry</a></div></footer><script src="/assets/js/parts-quote-cart.js?v=1"></script></body></html>'''


def build_card(part: dict[str, str]) -> str:
    slug = part["sku"].lower()
    search = " | ".join(aliases(part) + [part["category"], part["catalog_page"]])
    if has_image(part):
        alt = f"Representative studio visualization of {part['part_name']} matched to Kikusui {part['model']} catalog part {part['catalog_part_number']}"
        visual = (
            f'<div class="product-visual"><img src="{escape(part["image_path"])}" alt="{escape(alt)}" '
            'width="760" height="760" loading="lazy" decoding="async"></div>'
        )
    else:
        visual = (
            '<div class="product-visual product-visual-unavailable" role="img" '
            f'aria-label="No verified photograph is available for {escape(part["part_name"])}">'
            '<span class="placeholder-mark" aria-hidden="true">KI</span><strong>Exact photograph unavailable</strong>'
            '<span>No substitute image used</span></div>'
        )
    return f'''<article class="product-card" data-name="{escape(part['part_name'])}" data-model="{escape(part['model'])}" data-sku="{escape(part['sku'])}" data-search="{escape(search)}">{visual}<div class="product-content"><p class="product-family">Kikusui {escape(part['model'])} · {escape(part['category'])}</p><h3><a href="/parts/{slug}/">{escape(part['part_name'])}</a></h3><p class="catalog-reference">Catalog Part: {escape(part['catalog_part_number'])}</p><p class="oem-reference">OEM Number: {escape(oem_display(part))}</p><p class="sku">{escape(part['sku'])}</p><a class="part-page-link" href="/parts/{slug}/">View replacement part page →</a><p class="product-copy">Matched to the supplied Kikusui catalog record. {escape(image_status_note(part))}</p><div class="product-actions"><a class="btn small" href="/parts/{slug}/">View part</a><button class="btn small" type="button" data-pge-cart-add data-part-sku="{escape(part['sku'])}" data-part-name="{escape(part['part_name'])}" data-part-brand="Kikusui" data-part-model="{escape(part['model'])}" data-part-url="/parts/{slug}/">Add to Quote Cart</button></div></div></article>'''


def build_catalog(parts: list[dict[str, str]]) -> None:
    total = len(parts)
    image_total = sum(has_image(part) for part in parts)
    model_counts = Counter(part["model"] for part in parts)
    filters = "".join(
        f'<option value="{escape(model)}">{escape(model)} ({count})</option>'
        for model, count in sorted(model_counts.items())
    )
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "name": "Kikusui Tablet Press Replacement Parts",
                "url": SITE + "/parts/kikusui/",
                "description": f"{total} independently supplied replacement-part records matched by Kikusui model, catalog part number, and OEM cross-reference.",
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Parts Store", "item": SITE + "/parts/"},
                    {"@type": "ListItem", "position": 2, "name": "Kikusui parts", "item": SITE + "/parts/kikusui/"},
                ],
            },
        ],
    }
    page = f'''<!doctype html><html lang="en-US"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Kikusui Tablet Press Replacement Parts by Model and OEM | PharmaGlobalEng</title><meta name="description" content="Browse {total} Kikusui replacement-part records matched to model, part name, catalog part number, and catalog-supplied OEM cross-reference."><meta name="robots" content="index,follow,max-image-preview:large"><link rel="canonical" href="{SITE}/parts/kikusui/"><link rel="stylesheet" href="/assets/css/pharmaglobaleng.css"><link rel="stylesheet" href="/assets/css/store.css"><link rel="stylesheet" href="/assets/css/parts-quote-cart.css?v=1"><script src="/assets/js/parts-search.js?v=1"></script><script type="application/ld+json">{json.dumps(graph, ensure_ascii=False, separators=(',', ':'))}</script></head><body>
<header class="site-header"><div class="wrap nav"><a class="brand" href="/">PharmaGlobal<span>Eng</span></a><nav class="nav-links" aria-label="Primary navigation"><a href="/services/">Services</a><a href="/solutions/">Solutions</a><a href="/parts/" aria-current="page">Parts Store</a><a href="/contact.html">Contact</a></nav></div></header>
<main><section class="store-hero"><div class="wrap"><div class="crumb"><a href="/parts/">Parts Store</a> / Kikusui</div><p class="eyebrow">Verified catalog mapping</p><h1>Replacement Parts Compatible with Selected Kikusui Equipment</h1><p class="lead">Browse {total} independently supplied replacement-part records matched to the exact Kikusui model, part name, catalog part number, and OEM number in the supplied source. {image_total} records include catalog-matched studio images; unsupported photographs are intentionally omitted.</p><div class="catalog-search"><label class="visually-hidden" for="part-search">Search Kikusui parts</label><input id="part-search" type="search" placeholder="Search part, model, catalog number, OEM, or PGE number" autocomplete="off"><label class="visually-hidden" for="model-filter">Filter by Kikusui model</label><select id="model-filter"><option value="">All Kikusui models</option>{filters}</select><span class="search-result-count"><strong id="visible-count">{total}</strong> results</span></div></div></section>
<section class="section" id="catalog"><div class="wrap"><div class="catalog-meta"><span><strong>{total}</strong> mapped records · <strong>{image_total}</strong> verified images</span><span>Independent supplier · compatibility confirmation required</span></div><div class="product-grid" id="product-grid">{''.join(build_card(part) for part in parts)}</div><p id="no-results" class="notice" hidden><strong>No matching part was found.</strong> Try a model, part name, catalog number, OEM number, or PGE number.</p><div class="notice"><strong>Image accuracy policy:</strong> Records without an exact catalog photograph do not use a random or substitute product image. Images shown are representative studio visualizations matched to the corresponding catalog record.</div><div class="notice"><strong>Independent supplier and trademark notice:</strong> PharmaGlobalEng is not affiliated with, authorized by, sponsored by, or endorsed by Kikusui or its trademark owner. Kikusui names, model references, catalog numbers, and OEM numbers identify potential equipment compatibility only. All trademarks belong to their respective owners.</div></div></section></main>
<footer><div class="wrap footer"><span>© PharmaGlobalEng</span><a href="/parts/">All parts</a><a href="/contact.html">Parts inquiry</a></div></footer><script>(()=>{{const input=document.getElementById('part-search'),model=document.getElementById('model-filter'),cards=[...document.querySelectorAll('.product-card')],count=document.getElementById('visible-count'),empty=document.getElementById('no-results');function filter(){{const q=input.value,m=model.value;let shown=0;cards.forEach(card=>{{const matchText=window.PGEPartsSearch.matches(card.dataset.search||card.textContent,q),matchModel=!m||card.dataset.model===m,match=matchText&&matchModel;card.hidden=!match;if(match)shown++;}});count.textContent=shown;empty.hidden=shown!==0;}}input.addEventListener('input',filter);model.addEventListener('change',filter);}})();</script><script src="/assets/js/parts-quote-cart.js?v=1"></script></body></html>'''
    destination = ROOT / "parts/kikusui/index.html"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(page, encoding="utf-8")


def load_parts() -> list[dict[str, str]]:
    with DATA_PATH.open(encoding="utf-8", newline="") as handle:
        parts = [{key: clean(value) for key, value in row.items()} for row in csv.DictReader(handle)]
    expected = {
        "record_number", "sku", "make", "model", "part_name", "category", "catalog_part_number",
        "oem_number", "catalog_page", "image_position", "photo_status", "verification", "review_notes", "image_path",
    }
    if not parts or not expected.issubset(parts[0]):
        raise SystemExit(f"Kikusui data is missing required columns: {sorted(expected - set(parts[0] if parts else {}))}")
    if len(parts) != 158 or len({part["sku"] for part in parts}) != 158:
        raise SystemExit("Kikusui dataset must contain exactly 158 unique records")
    if [int(part["record_number"]) for part in parts] != list(range(1, 159)):
        raise SystemExit("Kikusui record numbers must be the exact sequence 1 through 158")
    if any(part["make"] != "Kikusui" for part in parts):
        raise SystemExit("Every Kikusui record must retain make=Kikusui")
    status_counts = Counter(part["photo_status"] for part in parts)
    if status_counts != Counter({"Catalog photo": 136, "Photo not available": 17, "Stock photo": 5}):
        raise SystemExit(f"Unexpected Kikusui photo-status counts: {status_counts}")
    if any(has_image(part) != (part["photo_status"] == "Catalog photo") for part in parts):
        raise SystemExit("Only exact catalog-photo records may have public images")
    return parts


def import_manifest(manifest_path: Path) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if len(manifest) != 158:
        raise SystemExit(f"Expected 158 manifest records, found {len(manifest)}")
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "record_number", "sku", "make", "model", "part_name", "category", "catalog_part_number",
        "oem_number", "catalog_page", "image_position", "photo_status", "verification", "review_notes", "image_path",
    ]
    with DATA_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for item in manifest:
            record = int(item["recordNumber"])
            sku = f"PGE-KIK-{record:03d}"
            image_path = ""
            if item["photoStatus"] == "Catalog photo":
                source = Path(item["website760Path"])
                if not source.is_file():
                    raise SystemExit(f"Missing generated image for {sku}: {source}")
                destination = IMAGE_DIR / f"{sku.lower()}.webp"
                shutil.copyfile(source, destination)
                image_path = f"/assets/images/parts/kikusui/{destination.name}"
            writer.writerow({
                "record_number": record,
                "sku": sku,
                "make": clean(item["make"]),
                "model": clean(item["model"]),
                "part_name": clean(item["partName"]),
                "category": clean(item["category"]),
                "catalog_part_number": clean(item["catalogPartNumber"]),
                "oem_number": clean(item["oemNumber"]),
                "catalog_page": clean(item["catalogPage"]),
                "image_position": clean(item["imagePosition"]),
                "photo_status": clean(item["photoStatus"]),
                "verification": clean(item["verification"]),
                "review_notes": clean(item["reviewNotes"]),
                "image_path": image_path,
            })


def update_parts_index() -> None:
    path = ROOT / "parts/index.html"
    page = path.read_text(encoding="utf-8")
    page = re.sub(
        r"Browse \d+ representative visualizations of independently produced replacement parts\.",
        f"Browse {TOTAL_SITE_PARTS} independently produced replacement-part records.",
        page,
        count=1,
    )
    kikusui_card = '''<a class="machine-card" href="/parts/kikusui/">
            <span class="status-pill">158 parts</span><div class="card-mark" aria-hidden="true">KI</div>
            <h3>Replacement Parts Compatible with Selected Kikusui Equipment</h3><p>Browse independently supplied components matched to the exact Kikusui model, catalog part number, and catalog-supplied OEM reference.</p><span class="card-link">Browse compatible parts →</span>
          </a>'''
    updated, count = re.subn(r'<a class="machine-card" href="/parts/kikusui/">.*?</a>', kikusui_card, page, count=1, flags=re.S)
    if count != 1:
        raise SystemExit("Could not find the Kikusui card in parts/index.html")
    path.write_text(updated, encoding="utf-8")


def update_sitemaps(parts: list[dict[str, str]]) -> None:
    sitemap_path = ROOT / "sitemap.xml"
    xml = sitemap_path.read_text(encoding="utf-8")
    xml = re.sub(
        r'\n\s*<url>\s*<loc>https://pharmaglobaleng\.com/parts/pge-kik-\d{3}/</loc>.*?</url>',
        "",
        xml,
        flags=re.S,
    )
    if f"{SITE}/parts/kikusui/" not in xml:
        xml = xml.replace(
            "</urlset>",
            f'  <url><loc>{SITE}/parts/kikusui/</loc><changefreq>weekly</changefreq><priority>0.85</priority></url>\n</urlset>',
        )
    entries = "\n".join(
        f'  <url><loc>{SITE}/parts/{part["sku"].lower()}/</loc><lastmod>2026-09-04</lastmod><changefreq>monthly</changefreq><priority>0.75</priority></url>'
        for part in parts
    )
    xml = xml.replace("</urlset>", entries + "\n</urlset>")
    sitemap_path.write_text(xml, encoding="utf-8")

    image_sitemap_path = ROOT / "sitemap-parts-images.xml"
    image_xml = image_sitemap_path.read_text(encoding="utf-8")
    image_xml = re.sub(
        r'\n\s*<url><loc>https://pharmaglobaleng\.com/parts/pge-kik-\d{3}/</loc>.*?</url>',
        "",
        image_xml,
        flags=re.S,
    )
    image_entries = "\n".join(
        f'  <url><loc>{SITE}/parts/{part["sku"].lower()}/</loc><image:image><image:loc>{SITE + part["image_path"]}</image:loc><image:title>{escape(part["part_name"] + " for Kikusui " + part["model"])}</image:title><image:caption>{escape(image_status_note(part))}</image:caption></image:image></url>'
        for part in parts if has_image(part)
    )
    image_xml = image_xml.replace("</urlset>", image_entries + "\n</urlset>")
    image_sitemap_path.write_text(image_xml, encoding="utf-8")


def write_content_audit(parts: list[dict[str, str]]) -> None:
    path = ROOT / "data/kikusui-parts-content-audit.csv"
    fields = [
        "sku", "make", "model", "part_name", "category", "catalog_part_number", "oem_number",
        "catalog_page", "photo_status", "image_path", "landing_page", "source_verification",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for part in parts:
            writer.writerow({
                "sku": part["sku"],
                "make": part["make"],
                "model": part["model"],
                "part_name": part["part_name"],
                "category": part["category"],
                "catalog_part_number": part["catalog_part_number"],
                "oem_number": oem_display(part),
                "catalog_page": part["catalog_page"],
                "photo_status": part["photo_status"],
                "image_path": part["image_path"],
                "landing_page": f"/parts/{part['sku'].lower()}/",
                "source_verification": part["verification"],
            })


def build_all(parts: list[dict[str, str]]) -> None:
    for part in parts:
        destination = ROOT / "parts" / part["sku"].lower() / "index.html"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(build_page(part, parts), encoding="utf-8")
    build_catalog(parts)
    update_parts_index()
    update_sitemaps(parts)
    write_content_audit(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the verified Kikusui catalog and landing pages")
    parser.add_argument("--import-manifest", type=Path, help="Import the verified image manifest into tracked site data")
    args = parser.parse_args()
    if args.import_manifest:
        import_manifest(args.import_manifest.expanduser().resolve())
    parts = load_parts()
    build_all(parts)
    print(
        f"Generated {len(parts)} Kikusui landing pages and catalog cards; "
        f"verified images: {sum(has_image(part) for part in parts)}; "
        f"intentional no-image records: {sum(not has_image(part) for part in parts)}"
    )


if __name__ == "__main__":
    main()
