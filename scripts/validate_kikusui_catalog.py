from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://pharmaglobaleng.com"
DATA_PATH = ROOT / "data/kikusui-parts.csv"


def read_parts() -> list[dict[str, str]]:
    with DATA_PATH.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def has_oem(part: dict[str, str]) -> bool:
    return part["oem_number"].strip().casefold() not in {"", "n/a", "na", "none", "not available"}


parts = read_parts()
errors: list[str] = []
canonicals: set[str] = set()
image_hashes: dict[str, str] = {}
expected_sequence = [f"PGE-KIK-{number:03d}" for number in range(1, 159)]

if len(parts) != 158:
    errors.append(f"Expected 158 records, found {len(parts)}")
if [part["sku"] for part in parts] != expected_sequence:
    errors.append("Kikusui SKUs are not the exact sequence PGE-KIK-001 through PGE-KIK-158")
if len({part["sku"] for part in parts}) != len(parts):
    errors.append("Duplicate Kikusui SKU detected")
if len({(part["model"], part["catalog_part_number"], part["part_name"], part["oem_number"]) for part in parts}) != len(parts):
    errors.append("Duplicate model/catalog-part/name/OEM mapping detected")

status_counts = Counter(part["photo_status"] for part in parts)
expected_status = Counter({"Catalog photo": 136, "Photo not available": 17, "Stock photo": 5})
if status_counts != expected_status:
    errors.append(f"Photo status mismatch: {status_counts}")

for part in parts:
    slug = part["sku"].lower()
    page_path = ROOT / "parts" / slug / "index.html"
    if not page_path.is_file():
        errors.append(f"Missing landing page: {slug}")
        continue
    html = page_path.read_text(encoding="utf-8")
    expected_oem = part["oem_number"] if has_oem(part) else "Not listed in source catalog"
    required = [
        part["sku"], part["part_name"], part["model"], part["catalog_part_number"], expected_oem,
        "Kikusui", "Verified catalog mapping", "Independent supplier and trademark notice",
    ]
    for value in required:
        if value not in html:
            errors.append(f"{slug}: missing exact value {value!r}")
    if "natoli" in html.casefold():
        errors.append(f"{slug}: unrelated Natoli identifier found")
    if f'data-part-sku="{part["sku"]}"' not in html or f'data-part-model="{part["model"]}"' not in html:
        errors.append(f"{slug}: quote-cart mapping is not exact")
    canonical = f"{SITE}/parts/{slug}/"
    if f'<link rel="canonical" href="{canonical}">' not in html:
        errors.append(f"{slug}: canonical is missing or incorrect")
    elif canonical in canonicals:
        errors.append(f"{slug}: duplicate canonical")
    else:
        canonicals.add(canonical)
    schema_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    if not schema_match:
        errors.append(f"{slug}: JSON-LD missing")
    else:
        try:
            schema = json.loads(schema_match.group(1))
            graph = schema.get("@graph", [])
            types = {node.get("@type") for node in graph}
            if not {"Product", "BreadcrumbList"}.issubset(types):
                errors.append(f"{slug}: incomplete JSON-LD graph {types}")
            product = next((node for node in graph if node.get("@type") == "Product"), {})
            if product.get("sku") != part["sku"]:
                errors.append(f"{slug}: Product schema SKU mismatch")
            if bool(product.get("image")) != bool(part["image_path"]):
                errors.append(f"{slug}: Product schema image status mismatch")
        except json.JSONDecodeError as exc:
            errors.append(f"{slug}: invalid JSON-LD: {exc}")

    if part["image_path"]:
        image_path = ROOT / part["image_path"].lstrip("/")
        if not image_path.is_file():
            errors.append(f"{slug}: missing image {part['image_path']}")
        else:
            with Image.open(image_path) as image:
                if image.size != (760, 760) or image.format != "WEBP":
                    errors.append(f"{slug}: expected 760x760 WEBP, found {image.size} {image.format}")
            digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
            if digest in image_hashes:
                errors.append(f"{slug}: exact duplicate image of {image_hashes[digest]}")
            image_hashes[digest] = slug
        if part["image_path"] not in html or "Exact photograph unavailable" in html:
            errors.append(f"{slug}: page image/placeholder mismatch")
    else:
        if "Exact photograph unavailable" not in html or "No substitute image used" not in html:
            errors.append(f"{slug}: no-image record lacks the honest placeholder")
        if '<meta property="og:image"' in html:
            errors.append(f"{slug}: no-image record publishes an Open Graph image")

catalog = (ROOT / "parts/kikusui/index.html").read_text(encoding="utf-8")
if len(re.findall(r'<article class="product-card"', catalog)) != 158:
    errors.append("Kikusui catalog does not contain exactly 158 cards")
if len(re.findall(r'class="product-visual product-visual-unavailable"', catalog)) != 22:
    errors.append("Kikusui catalog does not contain exactly 22 honest no-image cards")
for part in parts:
    card_start = catalog.find(f'data-sku="{part["sku"]}"')
    card_end = catalog.find("</article>", card_start)
    card = catalog[card_start:card_end]
    expected_oem = part["oem_number"] if has_oem(part) else "Not listed in source catalog"
    if card_start < 0 or not all(value in card for value in (part["part_name"], part["model"], part["catalog_part_number"], expected_oem)):
        errors.append(f"Catalog card mapping mismatch: {part['sku']}")
    if bool(part["image_path"]) != (part["image_path"] in card if part["image_path"] else False):
        errors.append(f"Catalog card image mismatch: {part['sku']}")

sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
image_sitemap = (ROOT / "sitemap-parts-images.xml").read_text(encoding="utf-8")
if len(re.findall(r'https://pharmaglobaleng\.com/parts/pge-kik-\d{3}/', sitemap)) != 158:
    errors.append("Main sitemap does not contain exactly 158 Kikusui part URLs")
if len(re.findall(r'https://pharmaglobaleng\.com/parts/pge-kik-\d{3}/', image_sitemap)) != 136:
    errors.append("Image sitemap does not contain exactly 136 Kikusui part URLs")
if f"{SITE}/parts/kikusui/" not in sitemap:
    errors.append("Kikusui collection URL is missing from the main sitemap")

parts_index = (ROOT / "parts/index.html").read_text(encoding="utf-8")
if "Browse 3211 independently produced replacement-part records." not in parts_index:
    errors.append("Parts Store total is not 3211 after the Manesty catalog retirement")
if '<span class="status-pill">158 parts</span>' not in parts_index:
    errors.append("Kikusui Parts Store badge was not updated to 158 parts")

if errors:
    raise SystemExit("\n".join(errors))

print(json.dumps({
    "records": len(parts),
    "landing_pages": len(canonicals),
    "catalog_cards": 158,
    "verified_images": len(image_hashes),
    "no_image_placeholders": sum(not part["image_path"] for part in parts),
    "photo_status": dict(status_counts),
    "with_catalog_oem": sum(has_oem(part) for part in parts),
    "without_catalog_oem": sum(not has_oem(part) for part in parts),
    "duplicate_images": 0,
    "mapping": "make + model + part name + catalog part number + OEM preserved per record",
}, indent=2))
