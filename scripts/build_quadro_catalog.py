#!/usr/bin/env python3
"""Build the public Quadro mapping, images, and part landing pages.

Only reviewed fields from the supplied manifest are imported. Third-party
supplier identifiers and URLs are deliberately excluded from every public or
tracked Quadro record.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from html import escape
from pathlib import Path
from urllib.parse import urlencode

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://pharmaglobaleng.com"
DATA_PATH = ROOT / "data/quadro-parts.json"
IMAGE_DIR = ROOT / "assets/images/parts/quadro"
EXPECTED_RECORDS = 113
MISSING_OEM = "Not listed in source catalog"
CONFLICT_SIZE_COPY = {
    "Q004": '0.018\" aperture listed; mesh designation conflicts in the source record',
    "Q063": "Conflicting aperture values in the source record; confirm during quotation",
    "Q067": "Conflicting decimal and fractional size values in the source record; confirm during quotation",
}


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", "" if value is None else str(value)).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def public_part_name(title: str, source_id: str) -> str:
    name = re.split(r"\s*for\s+Quadro\b", clean(title), maxsplit=1, flags=re.I)[0]
    name = re.sub(r"\*modified\*", "(Modified)", name, flags=re.I).strip(" ,.")
    if source_id == "Q004":
        return re.sub(r"\s*\(35-Mesh\)", "", name, flags=re.I)
    if source_id == "Q063":
        return "Round Hole Screen"
    if source_id == "Q067":
        return "Square Hole Screen"
    return name


def public_model(values: list[object]) -> str:
    models = [clean(value) for value in values if clean(value)]
    if not models:
        return MISSING_OEM
    if models == ["SLS", "U5"]:
        return "SLS-U5"
    return " / ".join(models)


def public_oem(values: list[object]) -> str:
    numbers = [clean(value) for value in values if clean(value)]
    return " / ".join(numbers) if numbers else MISSING_OEM


def equipment_name(part: dict) -> str:
    if part["model"] == MISSING_OEM:
        return "Quadro Comil"
    return f"Quadro {part['model']} Comil"


def page_name(part: dict) -> str:
    return f"{part['part_name']} for {equipment_name(part)}"


def safe_size(item: dict) -> str:
    if item["id"] in CONFLICT_SIZE_COPY:
        return CONFLICT_SIZE_COPY[item["id"]]
    value = clean(item.get("listed_sizes"))
    return value if value and value.casefold() != "not listed" else MISSING_OEM


def render_image(source: Path, destination: Path) -> None:
    with Image.open(source) as opened:
        rgba = opened.convert("RGBA")
        contained = ImageOps.contain(rgba, (760, 760), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (760, 760), (2, 8, 23, 255))
        offset = ((760 - contained.width) // 2, (760 - contained.height) // 2)
        canvas.alpha_composite(contained, offset)
        destination.parent.mkdir(parents=True, exist_ok=True)
        canvas.convert("RGB").save(destination, "WEBP", quality=91, method=6)


def import_manifest(manifest_path: Path) -> None:
    source_root = manifest_path.parent
    source = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(source, list) or len(source) != EXPECTED_RECORDS:
        raise SystemExit(f"Expected {EXPECTED_RECORDS} manifest records, found {len(source) if isinstance(source, list) else 'invalid data'}")
    expected_ids = [f"Q{number:03d}" for number in range(1, EXPECTED_RECORDS + 1)]
    if [clean(item.get("id")) for item in source] != expected_ids:
        raise SystemExit("Quadro manifest IDs must be the exact Q001 through Q113 sequence")

    records = []
    for number, item in enumerate(source, 1):
        source_id = f"Q{number:03d}"
        source_image = source_root / clean(item.get("edited_file"))
        if not source_image.is_file():
            raise SystemExit(f"Missing edited image for {source_id}: {source_image}")
        expected_hash = clean(item.get("edited_sha256"))
        if expected_hash and sha256(source_image) != expected_hash:
            raise SystemExit(f"Edited-image hash mismatch for {source_id}")

        sku = f"PGE-QUA-{number:03d}"
        destination = IMAGE_DIR / f"{sku.lower()}.webp"
        render_image(source_image, destination)
        notes = [clean(note) for note in item.get("notes", []) if clean(note)]
        record = {
            "record_number": number,
            "source_record": source_id,
            "sku": sku,
            "make": "Quadro",
            "model": public_model(item.get("model_reference", [])),
            "part_name": public_part_name(clean(item.get("product_title") or item.get("title")), source_id),
            "category": clean(item.get("category")) or "Replacement components",
            "replacement_oem_number": public_oem(item.get("oem_numbers_listed", [])),
            "listed_size": safe_size(item),
            "listed_dimensions": clean(item.get("listed_dimensions")) or MISSING_OEM,
            "catalog_page": int(item.get("catalog_page") or 0),
            "verification_note": "Catalog-listed reference; compatibility and physical dimensions have not been independently verified.",
            "review_notes": notes,
            "photo_note": "AI-retouched studio image based on the matched catalog photograph; exact dimensional identity is confirmed during quotation.",
            "source_image_sha256": sha256(source_image),
            "image_sha256": sha256(destination),
            "image_path": f"/assets/images/parts/quadro/{destination.name}",
            "landing_page": f"/parts/{sku.lower()}/",
        }
        if not record["part_name"]:
            raise SystemExit(f"Missing public part name for {source_id}")
        records.append(record)

    payload = {
        "version": 1,
        "make": "Quadro",
        "record_count": EXPECTED_RECORDS,
        "source_checked": clean(source[0].get("source_checked")) or "2026-09-12",
        "records": records,
    }
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_parts() -> list[dict]:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    parts = payload.get("records", [])
    if payload.get("version") != 1 or len(parts) != EXPECTED_RECORDS:
        raise SystemExit("Quadro public data must contain exactly 113 version-1 records")
    if [part.get("sku") for part in parts] != [f"PGE-QUA-{number:03d}" for number in range(1, 114)]:
        raise SystemExit("Quadro PGE numbers must be the exact PGE-QUA-001 through PGE-QUA-113 sequence")
    if any(part.get("make") != "Quadro" for part in parts):
        raise SystemExit("Every Quadro public record must retain make=Quadro")
    if len({part["image_path"] for part in parts}) != EXPECTED_RECORDS:
        raise SystemExit("Every Quadro record must have a unique image path")
    for part in parts:
        image = ROOT / part["image_path"].lstrip("/")
        if not image.is_file() or sha256(image) != part["image_sha256"]:
            raise SystemExit(f"Missing or changed public image for {part['sku']}")
        with Image.open(image) as opened:
            if opened.size != (760, 760) or opened.format != "WEBP":
                raise SystemExit(f"Public image is not 760x760 WEBP for {part['sku']}")
    return parts


def description(part: dict) -> str:
    base = f"{page_name(part)}. PGE {part['sku']}."
    if part["replacement_oem_number"] == MISSING_OEM:
        return base + " Replacement OEM number not listed in the source catalog. Confirm compatibility during quotation."
    return base + f" Replacement OEM number {part['replacement_oem_number']}. Confirm compatibility during quotation."


def seo_title(part: dict) -> str:
    suffix = f" | {part['sku']} | PGE"
    subject = f"{part['part_name']} | Quadro {part['model']}"
    maximum = 72 - len(suffix)
    if len(subject) > maximum:
        subject = subject[: max(12, maximum - 1)].rstrip(" ,;:-") + "…"
    return subject + suffix


def aliases(part: dict) -> list[str]:
    values = [part["part_name"], page_name(part), part["sku"]]
    if part["replacement_oem_number"] != MISSING_OEM:
        values.append(part["replacement_oem_number"])
    result = []
    for value in values:
        if value not in result:
            result.append(value)
    return result[:5]


def related_parts(part: dict, parts: list[dict]) -> list[dict]:
    same_model = [candidate for candidate in parts if candidate["sku"] != part["sku"] and candidate["model"] == part["model"]]
    same_category = [candidate for candidate in parts if candidate["sku"] != part["sku"] and candidate["category"] == part["category"] and candidate not in same_model]
    return (same_model + same_category)[:4]


def inquiry_url(part: dict) -> str:
    body = "\n".join([
        "Hello PharmaGlobalEng,", "", "Please review this replacement part for compatibility and quotation:", "",
        f"Part name: {part['part_name']}", f"PharmaGlobalEng number: {part['sku']}", "Make: Quadro",
        f"Model: {part['model']}", f"Replacement OEM Number: {part['replacement_oem_number']}", "",
        "Quantity required:", "Machine serial number/configuration:", "Existing part or drawing reference:",
        "Required dimensions:", "Additional information:", "",
    ])
    query = urlencode({"subject": f"Quadro part inquiry | {part['sku']} | {part['part_name']}", "body": body})
    return "mailto:info@pharmaglobaleng.com?" + query


def product_schema(part: dict) -> dict:
    product = {
        "@type": "Product",
        "@id": SITE + part["landing_page"] + "#product",
        "name": page_name(part),
        "alternateName": aliases(part),
        "sku": part["sku"],
        "url": SITE + part["landing_page"],
        "description": description(part),
        "category": part["category"],
        "image": SITE + part["image_path"],
        "brand": {"@type": "Brand", "name": "PharmaGlobalEng"},
        "manufacturer": {"@id": SITE + "/#organization"},
        "isAccessoryOrSparePartFor": {"@type": "ProductModel", "name": equipment_name(part)},
        "additionalProperty": [
            {"@type": "PropertyValue", "name": "Make", "value": "Quadro"},
            {"@type": "PropertyValue", "name": "Model", "value": part["model"]},
            {"@type": "PropertyValue", "name": "Replacement OEM Number", "value": part["replacement_oem_number"]},
            {"@type": "PropertyValue", "name": "Listed size", "value": part["listed_size"]},
            {"@type": "PropertyValue", "name": "Supplier relationship", "value": "Independent replacement-part supplier; not OEM affiliated or endorsed"},
        ],
    }
    if part["replacement_oem_number"] != MISSING_OEM:
        product["identifier"] = {"@type": "PropertyValue", "propertyID": "Replacement OEM Number", "value": part["replacement_oem_number"]}
    return product


def json_ld(part: dict) -> str:
    graph = [
        product_schema(part),
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Parts Store", "item": SITE + "/parts/"},
                {"@type": "ListItem", "position": 3, "name": "Quadro parts", "item": SITE + "/parts/quadro/"},
                {"@type": "ListItem", "position": 4, "name": part["sku"], "item": SITE + part["landing_page"]},
            ],
        },
        {
            "@type": "Organization",
            "@id": SITE + "/#organization",
            "name": "PharmaGlobalEng",
            "url": SITE + "/",
            "logo": {"@type": "ImageObject", "url": SITE + "/assets/images/about-pge-logo.svg"},
        },
    ]
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":"))


def build_page(part: dict, parts: list[dict]) -> str:
    url = SITE + part["landing_page"]
    title = seo_title(part)
    meta = description(part)
    h1 = page_name(part)
    alt = f"AI-retouched studio image of {part['part_name']} matched to {equipment_name(part)}"
    alias_chips = "".join(f'<span class="alias">{escape(value)}</span>' for value in aliases(part))
    related = "".join(
        f'<li><a href="{candidate["landing_page"]}">{escape(candidate["part_name"])}</a> <span>({escape(candidate["sku"])})</span></li>'
        for candidate in related_parts(part, parts)
    ) or "<li>No additional matched records in this group.</li>"
    notes = "".join(f'<p><strong>Review note:</strong> {escape(note)}</p>' for note in part["review_notes"])
    return f'''<!doctype html>
<html lang="en-US" data-pge-content="editorial"><head><script id="pge-analytics" src="/assets/js/pge-analytics.js" defer></script><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title><meta name="description" content="{escape(meta)}"><meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{url}"><meta property="og:type" content="product"><meta property="og:site_name" content="PharmaGlobalEng"><meta property="og:locale" content="en_US">
<meta property="og:title" content="{escape(title)}"><meta property="og:description" content="{escape(meta)}"><meta property="og:url" content="{url}"><meta property="og:image" content="{SITE + part['image_path']}"><meta property="og:image:alt" content="{escape(alt)}"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{SITE + part['image_path']}"><meta name="twitter:image:alt" content="{escape(alt)}">
<meta name="twitter:title" content="{escape(title)}"><meta name="twitter:description" content="{escape(meta)}">
<link rel="stylesheet" href="/assets/css/pharmaglobaleng.css"><link rel="stylesheet" href="/assets/css/part-detail.css"><link rel="stylesheet" href="/assets/css/parts-quote-cart.css?v=1"><link rel="stylesheet" href="/assets/css/pge-header.css" data-pge-header-css="true"><script type="application/ld+json">{json_ld(part)}</script></head>
<body><header data-pge-header="v1" class="site-header"><div class="wrap nav"><div class="pge-header-identity"><a class="pge-header-brand" href="/" aria-label="PharmaGlobalEng home"><img class="pge-header-logo" src="/assets/images/pge-header-logo.webp" width="34" height="30" alt="" decoding="async"><span class="pge-header-wordmark">PharmaGlobal<span>Eng</span></span></a><a class="pge-header-phone" href="tel:+17324397849" aria-label="Call PharmaGlobalEng at +1 (732) 439-7849">+1 (732) 439-7849</a></div><nav class="nav-links" aria-label="Primary navigation"><a href="/services/">Services</a><a href="/solutions/">Solutions</a><a href="/parts/" aria-current="page">Parts Store</a><a class="nav-cta" href="/contact.html">Contact</a></nav></div></header>
<main><div class="wrap"><div class="part-crumb"><a href="/">Home</a> / <a href="/parts/">Parts Store</a> / <a href="/parts/quadro/">Quadro parts</a> / {escape(part['sku'])}</div>
<section class="part-hero"><div class="part-image"><img src="{escape(part['image_path'])}" alt="{escape(alt)}" width="760" height="760" loading="eager" fetchpriority="high" decoding="async"></div><div class="part-intro"><p class="eyebrow">Independent replacement component</p><h1>{escape(h1)}</h1><span class="sku-badge">PharmaGlobalEng Number: {escape(part['sku'])}</span><div class="store-links"><a href="/parts/quadro/">View in the Quadro Parts Store →</a><a href="/parts/">Browse all parts →</a></div><p class="lead">{escape(meta)}</p><div class="compatibility"><strong>Replacement OEM Number: {escape(part['replacement_oem_number'])}</strong><br>Make: <strong>Quadro</strong> · Model: <strong>{escape(part['model'])}</strong> · Category: <strong>{escape(part['category'])}</strong></div><div class="part-quote-actions"><button class="btn primary quote-cta" type="button" data-pge-cart-add data-part-sku="{escape(part['sku'])}" data-part-name="{escape(part['part_name'])}" data-part-brand="Quadro" data-part-model="{escape(part['model'])}" data-part-url="{part['landing_page']}">Add to Quote Cart</button><a class="btn secondary email-part-inquiry" href="{escape(inquiry_url(part))}">Email this part</a></div></div></section></div>
<section class="detail-section"><div class="wrap detail-grid"><div class="detail-box"><h2>Catalog-matched part mapping</h2><dl><div><dt>Make</dt><dd>Quadro</dd></div><div><dt>Model</dt><dd>{escape(part['model'])}</dd></div><div><dt>Part name</dt><dd>{escape(part['part_name'])}</dd></div><div><dt>Replacement OEM Number</dt><dd>{escape(part['replacement_oem_number'])}</dd></div><div><dt>Part category</dt><dd>{escape(part['category'])}</dd></div><div><dt>Listed size</dt><dd>{escape(part['listed_size'])}</dd></div><div><dt>Listed overall dimensions</dt><dd>{escape(part['listed_dimensions'])}</dd></div></dl></div><div class="detail-box"><h2>Photo and verification status</h2><p>{escape(part['photo_note'])}</p><p><strong>Verification status:</strong> {escape(part['verification_note'])}</p>{notes}<p>No unsupported material, finish, function, or dimensional claim has been added. Confirm the machine configuration, existing component, drawing, and critical dimensions before manufacturing or installation.</p></div></div></section>
<section class="detail-section"><div class="wrap"><h2>Reference identifiers</h2><p class="section-copy">Use the matched part name, make, model, replacement OEM number when listed, and PharmaGlobalEng number when requesting a quote.</p><div class="aliases">{alias_chips}</div></div></section>
<section class="detail-section"><div class="wrap detail-grid"><div class="detail-box"><h2>Compatibility confirmation</h2><p>This record is catalog-matched to {escape(equipment_name(part))}. Final compatibility is confirmed during quotation using the machine serial information, configuration, existing component or drawing, and critical dimensions.</p></div><div class="detail-box"><h2>Related Quadro records</h2><ul class="related-parts">{related}</ul></div></div></section>
<section class="detail-section"><div class="wrap"><div class="notice"><strong>Independent supplier and trademark notice:</strong> PharmaGlobalEng is not affiliated with, authorized by, sponsored by, or endorsed by Quadro or its trademark owner. Quadro names, model references, and OEM numbers are used solely to identify potential equipment compatibility. All trademarks belong to their respective owners. Published product images are AI-retouched studio representations based on catalog-matched photographs of independently supplied replacement components, not authenticated OEM product photographs.</div></div></section></main>
<footer><div class="wrap footer"><span>© PharmaGlobalEng</span><a href="/parts/">All parts</a><a href="/contact.html">Parts inquiry</a></div></footer><script src="/assets/js/parts-quote-cart.js?v=1"></script></body></html>'''


def build_pages(parts: list[dict]) -> None:
    for part in parts:
        destination = ROOT / "parts" / part["sku"].lower() / "index.html"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(build_page(part, parts), encoding="utf-8")


def update_next_catalog(parts: list[dict]) -> None:
    path = ROOT / "next-app/data/parts-catalog.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["parts"] = [part for part in data["parts"] if part.get("brand") != "quadro" and not str(part.get("sku", "")).startswith("PGE-QUA-")]
    data["manufacturers"] = [manufacturer for manufacturer in data["manufacturers"] if manufacturer.get("slug") != "quadro"]
    rows = []
    for part in parts:
        rows.append({
            "sku": part["sku"],
            "name": part["part_name"],
            "brand": "quadro",
            "brandName": "Quadro",
            "model": part["model"],
            "family": part["category"],
            "oem": part["replacement_oem_number"],
            "url": part["landing_page"],
            "originalImage": part["image_path"],
            "image": part["image_path"],
            "alt": f"AI-retouched studio image of {part['part_name']} matched to {equipment_name(part)}",
            "sourceCatalog": "/parts/quadro/",
        })
    source_hash = hashlib.sha256(json.dumps(parts, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    models = Counter(part["model"] for part in parts if part["model"] != MISSING_OEM)
    data["manufacturers"].append({
        "slug": "quadro",
        "name": "Quadro",
        "count": len(parts),
        "sourceHash": source_hash,
        "originalHtmlBytes": 0,
        "models": [{"slug": re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"), "name": name, "count": count} for name, count in sorted(models.items())],
        "searchVersion": source_hash[:12],
    })
    data["parts"].extend(rows)
    data["warnings"] = [warning for warning in data.get("warnings", []) if not str(warning).startswith("PGE-QUA-")]
    for part in parts:
        for note in part["review_notes"]:
            data["warnings"].append(f"{part['sku']}: {note}")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def remove_url_blocks(xml: str, pattern: str) -> str:
    # Keep the match inside one <url> block. A plain `.*?` here can begin at an
    # earlier block and erase unrelated sitemap entries on a repeat build.
    block = r"\s*<url>(?:(?!</?url>).)*?<loc>" + pattern + r"</loc>(?:(?!</?url>).)*?</url>"
    return re.sub(block, "", xml, flags=re.S)


def update_sitemaps(parts: list[dict]) -> None:
    sitemap_path = ROOT / "sitemap.xml"
    xml = sitemap_path.read_text(encoding="utf-8")
    xml = remove_url_blocks(xml, re.escape(SITE) + r"/parts/pge-qua-\d{3}/")
    if SITE + "/parts/quadro/" not in xml:
        xml = xml.replace("</urlset>", f'  <url><loc>{SITE}/parts/quadro/</loc><changefreq>weekly</changefreq><priority>0.85</priority></url>\n</urlset>')
    entries = [
        f'  <url><loc>{SITE + part["landing_page"]}</loc><lastmod>2026-09-12</lastmod><changefreq>monthly</changefreq><priority>0.75</priority></url>'
        for part in parts
    ]
    existing = set(re.findall(r"<loc>(.*?)</loc>", xml))
    for page in sorted((ROOT / "parts").glob("pge-cre-*/index.html")):
        text = page.read_text(encoding="utf-8")
        match = re.search(r'<link rel="canonical" href="([^"]+)"', text)
        if match and match.group(1) not in existing:
            entries.append(f'  <url><loc>{escape(match.group(1))}</loc><lastmod>2026-09-12</lastmod><changefreq>monthly</changefreq><priority>0.75</priority></url>')
            existing.add(match.group(1))
    xml = xml.replace("</urlset>", "\n".join(entries) + "\n</urlset>")
    sitemap_path.write_text(xml, encoding="utf-8")

    image_path = ROOT / "sitemap-parts-images.xml"
    image_xml = image_path.read_text(encoding="utf-8")
    image_xml = remove_url_blocks(image_xml, re.escape(SITE) + r"/parts/pge-qua-\d{3}/")
    image_entries = "\n".join(
        f'  <url><loc>{SITE + part["landing_page"]}</loc><image:image><image:loc>{SITE + part["image_path"]}</image:loc><image:title>{escape(page_name(part))}</image:title><image:caption>{escape(part["photo_note"])}</image:caption></image:image></url>'
        for part in parts
    )
    image_xml = image_xml.replace("</urlset>", image_entries + "\n</urlset>")
    image_path.write_text(image_xml, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Quadro replacement-part landing pages and catalog data")
    parser.add_argument("--import-manifest", type=Path, help="Import the reviewed 113-record image manifest")
    args = parser.parse_args()
    if args.import_manifest:
        import_manifest(args.import_manifest.expanduser().resolve())
    if not DATA_PATH.is_file():
        raise SystemExit("No Quadro public data found; run once with --import-manifest")
    parts = load_parts()
    build_pages(parts)
    update_next_catalog(parts)
    update_sitemaps(parts)
    print(f"Generated {len(parts)} Quadro landing pages, 760x760 images, and catalog records")


if __name__ == "__main__":
    main()
