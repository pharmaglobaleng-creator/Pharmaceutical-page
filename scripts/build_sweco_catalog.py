#!/usr/bin/env python3
"""Build the reviewed Sweco mapping, studio images, and landing pages.

Only public-safe catalog facts are imported. Third-party supplier identifiers,
URLs, and condition claims are deliberately excluded from tracked public data.
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

from catalog_page_schema import catalog_page_entity


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://pharmaglobaleng.com"
DATA_PATH = ROOT / "data/sweco-parts.json"
IMAGE_DIR = ROOT / "assets/images/parts/sweco"
EXPECTED_RECORDS = 33
NOT_LISTED = "Not listed in source catalog"
SAFE_REVIEW_NOTES = {
    7: ["The source title includes x4M while its description omits that designation; confirm configuration during quotation."],
    9: ["The source title identifies the screen as self-cleaning while another source field omits that wording; confirm configuration during quotation."],
    11: ["The source title and description state approximately 711 μm while another source field states 720 μm; confirm aperture during quotation."],
    12: ["This is one of two distinct source records sharing replacement OEM number 40020M013; keep the records separate pending physical verification."],
    13: ["The source title and description state that a center hole is present while another source field omits that detail; confirm configuration during quotation."],
    14: [
        "Source fields conflict between 600 μm and 1,180 μm; confirm aperture during quotation.",
        "The source title and description state that a center hole is present while another source field omits that detail; confirm configuration during quotation.",
    ],
    17: [
        "This is one of two distinct source records sharing replacement OEM number 40020M013; keep the records separate pending physical verification.",
        "Source fields differ about center-hole wording; confirm configuration during quotation.",
    ],
}


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", "" if value is None else str(value)).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def render_image(source: Path, destination: Path) -> None:
    with Image.open(source) as opened:
        rgba = opened.convert("RGBA")
        # Keep generous card-safe breathing room so circular screens and tall
        # assemblies remain fully visible at every responsive breakpoint.
        contained = ImageOps.contain(rgba, (650, 650), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (760, 760), (2, 8, 23, 255))
        offset = ((760 - contained.width) // 2, (760 - contained.height) // 2)
        canvas.alpha_composite(contained, offset)
        destination.parent.mkdir(parents=True, exist_ok=True)
        canvas.convert("RGB").save(destination, "WEBP", quality=92, method=6)


def import_inventory(inventory_path: Path, source_dir: Path, studio_dir: Path) -> None:
    source = json.loads(inventory_path.read_text(encoding="utf-8"))
    rows = source.get("records", [])
    expected_skus = [f"PGE-SWE-{number:03d}" for number in range(1, EXPECTED_RECORDS + 1)]
    if source.get("version") != 1 or len(rows) != EXPECTED_RECORDS:
        raise SystemExit(f"Expected {EXPECTED_RECORDS} version-1 inventory records")
    if [clean(row.get("sku")) for row in rows] != expected_skus:
        raise SystemExit("Sweco inventory must retain the exact PGE-SWE-001 through PGE-SWE-033 sequence")

    records = []
    source_hashes = set()
    studio_hashes = set()
    for number, row in enumerate(rows, 1):
        sku = expected_skus[number - 1]
        if clean(row.get("make")) != "Sweco":
            raise SystemExit(f"Incorrect make for {sku}")
        if clean(row.get("model")) != NOT_LISTED:
            raise SystemExit(f"A specific model was not supported by the supplied pages for {sku}")
        source_image = source_dir / f"{sku.lower()}.jpg"
        studio_image = studio_dir / f"{sku.lower()}.png"
        if not source_image.is_file():
            raise SystemExit(f"Missing matched source photo: {source_image}")
        if not studio_image.is_file():
            raise SystemExit(f"Missing approved studio photo: {studio_image}")
        source_digest = sha256(source_image)
        studio_digest = sha256(studio_image)
        if source_digest in source_hashes:
            raise SystemExit(f"Duplicate source photo for {sku}")
        if studio_digest in studio_hashes:
            raise SystemExit(f"Duplicate studio photo for {sku}")
        source_hashes.add(source_digest)
        studio_hashes.add(studio_digest)

        destination = IMAGE_DIR / f"{sku.lower()}.webp"
        render_image(studio_image, destination)
        equipment = clean(row.get("equipment_descriptor"))
        if equipment not in {"Vibratory Sieve", "Vibratory Sifter"}:
            raise SystemExit(f"Unsupported equipment descriptor for {sku}: {equipment}")
        oem = clean(row.get("replacement_oem_number")) or NOT_LISTED
        record = {
            "record_number": number,
            "sku": sku,
            "make": "Sweco",
            "model": NOT_LISTED,
            "equipment_descriptor": equipment,
            "part_name": clean(row.get("part_name")),
            "category": "Sifter Parts" if number in {3, 31} else "Screens",
            "replacement_oem_number": oem,
            "verification_note": "Catalog-listed reference; compatibility and physical dimensions have not been independently verified.",
            "review_notes": SAFE_REVIEW_NOTES.get(number, []),
            "photo_note": "AI-retouched studio image based on the matched catalog photograph; exact dimensional identity is confirmed during quotation.",
            "source_photo_sha256": source_digest,
            "full_resolution_image_sha256": studio_digest,
            "image_sha256": sha256(destination),
            "image_path": f"/assets/images/parts/sweco/{destination.name}",
            "landing_page": f"/parts/{sku.lower()}/",
        }
        if not record["part_name"]:
            raise SystemExit(f"Missing part name for {sku}")
        records.append(record)

    payload = {
        "version": 1,
        "make": "Sweco",
        "record_count": EXPECTED_RECORDS,
        "source_checked": clean(source.get("source_checked")) or "2026-09-12",
        "scope_note": "The 33 unique Sweco products visible across the user-supplied page-one and page-two surfaces were reviewed; this is not a claim that the full external collection was imported.",
        "records": records,
    }
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_parts() -> list[dict]:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    parts = payload.get("records", [])
    expected_skus = [f"PGE-SWE-{number:03d}" for number in range(1, EXPECTED_RECORDS + 1)]
    if payload.get("version") != 1 or len(parts) != EXPECTED_RECORDS:
        raise SystemExit("Sweco public data must contain exactly 33 version-1 records")
    if [part.get("sku") for part in parts] != expected_skus:
        raise SystemExit("Sweco PGE numbers must retain the exact sequence")
    if any(part.get("make") != "Sweco" or part.get("model") != NOT_LISTED for part in parts):
        raise SystemExit("Every Sweco record must keep the reviewed make and model status")
    if sum(part.get("replacement_oem_number") == NOT_LISTED for part in parts) != 10:
        raise SystemExit("Sweco source review must retain exactly 10 records without a listed OEM number")
    if Counter(part.get("equipment_descriptor") for part in parts) != Counter({"Vibratory Sieve": 29, "Vibratory Sifter": 4}):
        raise SystemExit("Sweco equipment descriptors changed from the reviewed source mapping")
    if [part["sku"] for part in parts if part.get("replacement_oem_number") == "40020M013"] != ["PGE-SWE-012", "PGE-SWE-017"]:
        raise SystemExit("The two distinct Sweco records sharing OEM 40020M013 must remain separate and ordered")
    if len({part["image_path"] for part in parts}) != EXPECTED_RECORDS:
        raise SystemExit("Every Sweco record must have a unique image path")
    image_hashes = set()
    for part in parts:
        image = ROOT / part["image_path"].lstrip("/")
        if not image.is_file() or sha256(image) != part["image_sha256"]:
            raise SystemExit(f"Missing or changed public image for {part['sku']}")
        if part["image_sha256"] in image_hashes:
            raise SystemExit(f"Duplicate public image for {part['sku']}")
        image_hashes.add(part["image_sha256"])
        with Image.open(image) as opened:
            if opened.size != (760, 760) or opened.format != "WEBP":
                raise SystemExit(f"Public image is not 760x760 WEBP for {part['sku']}")
    return parts


def equipment_name(part: dict) -> str:
    return f"Sweco {part['equipment_descriptor']}"


def page_name(part: dict) -> str:
    return f"{part['part_name']} for {equipment_name(part)}"


def description(part: dict) -> str:
    base = f"Independent replacement record for {page_name(part)}. PGE {part['sku']}."
    if part["replacement_oem_number"] == NOT_LISTED:
        oem = " Replacement OEM number is not listed in the source catalog."
    else:
        oem = f" Replacement OEM number {part['replacement_oem_number']}."
    return base + oem + " A specific machine model is not listed; confirm compatibility and critical dimensions during quotation."


def meta_description(part: dict) -> str:
    oem = part["replacement_oem_number"]
    subject = f"{part['part_name']} for {equipment_name(part)}."
    identifiers = f"PharmaGlobalEng Number: {part['sku']}. Replacement OEM Number: {oem}."
    text = f"{subject} {identifiers}"
    if len(text) <= 175:
        return text
    maximum = 175 - len(identifiers) - 1
    subject = subject[: max(30, maximum - 1)].rstrip(" ,;:-") + "…"
    return f"{subject} {identifiers}"


def seo_title(part: dict) -> str:
    suffix = f" | {part['sku']} | PGE"
    subject = f"{part['part_name']} | Sweco"
    maximum = 72 - len(suffix)
    if len(subject) > maximum:
        subject = subject[: max(12, maximum - 1)].rstrip(" ,;:-") + "…"
    return subject + suffix


def aliases(part: dict) -> list[str]:
    values = [part["part_name"], page_name(part), part["sku"]]
    if part["replacement_oem_number"] != NOT_LISTED:
        values.append(part["replacement_oem_number"])
    result = []
    for value in values:
        if value not in result:
            result.append(value)
    return result[:5]


def related_parts(part: dict, parts: list[dict]) -> list[dict]:
    same_equipment = [candidate for candidate in parts if candidate["sku"] != part["sku"] and candidate["equipment_descriptor"] == part["equipment_descriptor"]]
    same_category = [candidate for candidate in parts if candidate["sku"] != part["sku"] and candidate["category"] == part["category"] and candidate not in same_equipment]
    return (same_equipment + same_category)[:4]


def inquiry_url(part: dict) -> str:
    body = "\n".join([
        "Hello PharmaGlobalEng,", "", "Please review this replacement part for compatibility and quotation:", "",
        f"Part name: {part['part_name']}", f"PharmaGlobalEng number: {part['sku']}", "Make: Sweco",
        f"Model: {part['model']}", f"Equipment type: {part['equipment_descriptor']}",
        f"Replacement OEM Number: {part['replacement_oem_number']}", "", "Quantity required:",
        "Machine serial number/configuration:", "Existing part or drawing reference:", "Required dimensions:", "Additional information:", "",
    ])
    query = urlencode({"subject": f"Sweco part inquiry | {part['sku']} | {part['part_name']}", "body": body})
    return "mailto:info@pharmaglobaleng.com?" + query


def catalog_page_schema(part: dict) -> dict:
    identifier = None
    if part["replacement_oem_number"] != NOT_LISTED:
        identifier = {"@type": "PropertyValue", "propertyID": "Replacement OEM Number", "value": part["replacement_oem_number"]}
    return catalog_page_entity(
        url=SITE + part["landing_page"],
        name=page_name(part),
        description=description(part),
        sku=part["sku"],
        image=SITE + part["image_path"],
        aliases=aliases(part),
        identifiers=identifier,
    )


def json_ld(part: dict) -> str:
    graph = [
        catalog_page_schema(part),
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Parts Store", "item": SITE + "/parts/"},
                {"@type": "ListItem", "position": 3, "name": "Sweco parts", "item": SITE + "/parts/sweco/"},
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
    meta = meta_description(part)
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
<main><div class="wrap"><div class="part-crumb"><a href="/">Home</a> / <a href="/parts/">Parts Store</a> / <a href="/parts/sweco/">Sweco parts</a> / {escape(part['sku'])}</div>
<section class="part-hero"><div class="part-image"><img src="{escape(part['image_path'])}" alt="{escape(alt)}" width="760" height="760" loading="eager" fetchpriority="high" decoding="async"></div><div class="part-intro"><p class="eyebrow">Independent replacement component</p><h1>{escape(h1)}</h1><span class="sku-badge">PharmaGlobalEng Number: {escape(part['sku'])}</span><div class="store-links"><a href="/parts/sweco/">View in the Sweco Parts Store →</a><a href="/parts/">Browse all parts →</a></div><p class="lead">{escape(description(part))}</p><div class="compatibility"><strong>Replacement OEM Number: {escape(part['replacement_oem_number'])}</strong><br>Make: <strong>Sweco</strong> · Model: <strong>{escape(part['model'])}</strong> · Equipment type: <strong>{escape(part['equipment_descriptor'])}</strong></div><div class="part-quote-actions"><button class="btn primary quote-cta" type="button" data-pge-cart-add data-part-sku="{escape(part['sku'])}" data-part-name="{escape(part['part_name'])}" data-part-brand="Sweco" data-part-model="{escape(part['model'])}" data-part-url="{part['landing_page']}">Add to Quote Cart</button><a class="btn secondary email-part-inquiry" href="{escape(inquiry_url(part))}">Email this part</a></div></div></section></div>
<section class="detail-section"><div class="wrap detail-grid"><div class="detail-box"><h2>Catalog-matched part mapping</h2><dl><div><dt>Make</dt><dd>Sweco</dd></div><div><dt>Model</dt><dd>{escape(part['model'])}</dd></div><div><dt>Equipment type</dt><dd>{escape(part['equipment_descriptor'])}</dd></div><div><dt>Part name</dt><dd>{escape(part['part_name'])}</dd></div><div><dt>Replacement OEM Number</dt><dd>{escape(part['replacement_oem_number'])}</dd></div><div><dt>Part category</dt><dd>{escape(part['category'])}</dd></div></dl></div><div class="detail-box"><h2>Photo and verification status</h2><p>{escape(part['photo_note'])}</p><p><strong>Verification status:</strong> {escape(part['verification_note'])}</p>{notes}<p>No unsupported material, finish, function, or dimensional claim has been added. Confirm the machine configuration, existing component, drawing, and critical dimensions before manufacturing or installation.</p></div></div></section>
<section class="detail-section"><div class="wrap"><h2>Reference identifiers</h2><p class="section-copy">Use the matched part name, make, equipment type, replacement OEM number when listed, and PharmaGlobalEng number when requesting a quote.</p><div class="aliases">{alias_chips}</div></div></section>
<section class="detail-section"><div class="wrap detail-grid"><div class="detail-box"><h2>Compatibility confirmation</h2><p>This record is catalog-matched to a {escape(equipment_name(part))}. The supplied source does not state a specific model. Final compatibility is confirmed during quotation using the machine serial information, configuration, existing component or drawing, and critical dimensions.</p></div><div class="detail-box"><h2>Related Sweco records</h2><ul class="related-parts">{related}</ul></div></div></section>
<section class="detail-section"><div class="wrap"><div class="notice"><strong>Independent supplier and trademark notice:</strong> PharmaGlobalEng is not affiliated with, authorized by, sponsored by, or endorsed by Sweco or its trademark owner. Sweco names and OEM numbers are used solely to identify potential equipment compatibility. All trademarks belong to their respective owners. Published product images are AI-retouched studio representations based on catalog-matched photographs of independently supplied replacement components, not authenticated OEM product photographs.</div></div></section></main>
<footer><div class="wrap footer"><span>© PharmaGlobalEng</span><a href="/parts/">All parts</a><a href="/contact.html">Parts inquiry</a></div></footer><script src="/assets/js/parts-quote-cart.js?v=1"></script></body></html>'''


def build_pages(parts: list[dict]) -> None:
    for part in parts:
        destination = ROOT / "parts" / part["sku"].lower() / "index.html"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(build_page(part, parts), encoding="utf-8")


def update_next_catalog(parts: list[dict]) -> None:
    path = ROOT / "next-app/data/parts-catalog.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["parts"] = [part for part in data["parts"] if part.get("brand") != "sweco" and not str(part.get("sku", "")).startswith("PGE-SWE-")]
    data["manufacturers"] = [manufacturer for manufacturer in data["manufacturers"] if manufacturer.get("slug") != "sweco"]
    rows = []
    for part in parts:
        rows.append({
            "sku": part["sku"],
            "name": part["part_name"],
            "brand": "sweco",
            "brandName": "Sweco",
            "model": part["model"],
            "family": f"{part['equipment_descriptor']} · {part['category']}",
            "oem": part["replacement_oem_number"],
            "url": part["landing_page"],
            "originalImage": part["image_path"],
            "image": part["image_path"],
            "alt": f"AI-retouched studio image of {part['part_name']} matched to {equipment_name(part)}",
            "sourceCatalog": "/parts/sweco/",
        })
    source_hash = hashlib.sha256(json.dumps(parts, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    models = Counter(part["model"] for part in parts if part["model"] != NOT_LISTED)
    data["manufacturers"].append({
        "slug": "sweco",
        "name": "Sweco",
        "count": len(parts),
        "sourceHash": source_hash,
        "originalHtmlBytes": 0,
        "models": [{"slug": re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"), "name": name, "count": count} for name, count in sorted(models.items())],
        "searchVersion": source_hash[:12],
    })
    data["parts"].extend(rows)
    data["warnings"] = [warning for warning in data.get("warnings", []) if not str(warning).startswith("PGE-SWE-")]
    for part in parts:
        for note in part["review_notes"]:
            data["warnings"].append(f"{part['sku']}: {note}")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def remove_url_blocks(xml: str, pattern: str) -> str:
    block = r"\s*<url>(?:(?!</?url>).)*?<loc>" + pattern + r"</loc>(?:(?!</?url>).)*?</url>"
    return re.sub(block, "", xml, flags=re.S)


def update_sitemaps(parts: list[dict]) -> None:
    sitemap_path = ROOT / "sitemap.xml"
    xml = sitemap_path.read_text(encoding="utf-8")
    xml = remove_url_blocks(xml, re.escape(SITE) + r"/parts/pge-swe-\d{3}/")
    if SITE + "/parts/sweco/" not in xml:
        xml = xml.replace("</urlset>", f'  <url><loc>{SITE}/parts/sweco/</loc><changefreq>weekly</changefreq><priority>0.85</priority></url>\n</urlset>')
    entries = "\n".join(
        f'  <url><loc>{SITE + part["landing_page"]}</loc><lastmod>2026-09-12</lastmod><changefreq>monthly</changefreq><priority>0.75</priority></url>'
        for part in parts
    )
    xml = xml.replace("</urlset>", entries + "\n</urlset>")
    sitemap_path.write_text(xml, encoding="utf-8")

    image_path = ROOT / "sitemap-parts-images.xml"
    image_xml = image_path.read_text(encoding="utf-8")
    image_xml = remove_url_blocks(image_xml, re.escape(SITE) + r"/parts/pge-swe-\d{3}/")
    image_entries = "\n".join(
        f'  <url><loc>{SITE + part["landing_page"]}</loc><image:image><image:loc>{SITE + part["image_path"]}</image:loc><image:title>{escape(page_name(part))}</image:title><image:caption>{escape(part["photo_note"])}</image:caption></image:image></url>'
        for part in parts
    )
    image_xml = image_xml.replace("</urlset>", image_entries + "\n</urlset>")
    image_path.write_text(image_xml, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Sweco replacement-part landing pages and catalog data")
    parser.add_argument("--import-inventory", type=Path, help="Import the reviewed 33-record source inventory")
    parser.add_argument("--source-image-dir", type=Path, help="Directory containing matched pge-swe-NNN.jpg source photos")
    parser.add_argument("--studio-image-dir", type=Path, help="Directory containing approved pge-swe-NNN.png studio photos")
    args = parser.parse_args()
    if args.import_inventory:
        if not args.source_image_dir or not args.studio_image_dir:
            raise SystemExit("--source-image-dir and --studio-image-dir are required with --import-inventory")
        import_inventory(
            args.import_inventory.expanduser().resolve(),
            args.source_image_dir.expanduser().resolve(),
            args.studio_image_dir.expanduser().resolve(),
        )
    if not DATA_PATH.is_file():
        raise SystemExit("No Sweco public data found; run once with --import-inventory")
    parts = load_parts()
    build_pages(parts)
    update_next_catalog(parts)
    update_sitemaps(parts)
    print(f"Generated {len(parts)} Sweco landing pages, 760x760 images, and catalog records")


if __name__ == "__main__":
    main()
