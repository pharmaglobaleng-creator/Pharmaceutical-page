from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parts = json.loads((ROOT / "data/fette-first-200.json").read_text(encoding="utf-8"))
errors: list[str] = []
canonicals: set[str] = set()

if len(parts) != 200:
    errors.append(f"Expected 200 records, found {len(parts)}")

for part in parts:
    slug = part["sku"].lower()
    page_path = ROOT / "parts" / slug / "index.html"
    image_path = ROOT / part["image"].lstrip("/")
    if not page_path.exists():
        errors.append(f"Missing page: {slug}")
        continue
    if not image_path.exists():
        errors.append(f"Missing image: {part['image']}")
    html = page_path.read_text(encoding="utf-8")
    required = [part["part_name"], part["model"], part["image"], "Independent supplier and trademark notice", "FAQPage", "Product"]
    required.append(f"OEM Number: {part['oem_number'] or 'Needed'}")
    if part["oem_number"]:
        required.extend([f"Replacement Part for OEM {part['oem_number']}", f"OEM {part['oem_number']}"])
    for value in required:
        if value not in html:
            errors.append(f"{slug}: missing {value!r}")
    if "natoli" in html.casefold():
        errors.append(f"{slug}: Natoli identifier leaked into page")
    canonical_match = re.search(r'<link rel="canonical" href="([^"]+)">', html)
    if not canonical_match:
        errors.append(f"{slug}: canonical missing")
    elif canonical_match.group(1) in canonicals:
        errors.append(f"{slug}: duplicate canonical")
    else:
        canonicals.add(canonical_match.group(1))
    schema_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    if not schema_match:
        errors.append(f"{slug}: JSON-LD missing")
    else:
        try:
            schema = json.loads(schema_match.group(1))
            types = {node.get("@type") for node in schema.get("@graph", [])}
            if not {"Product", "FAQPage", "BreadcrumbList"}.issubset(types):
                errors.append(f"{slug}: incomplete JSON-LD graph {types}")
        except json.JSONDecodeError as exc:
            errors.append(f"{slug}: invalid JSON-LD: {exc}")

catalog = (ROOT / "parts/fette/index.html").read_text(encoding="utf-8")
if len(re.findall(r'<article class="product-card"', catalog)) != 200:
    errors.append("Fette catalog does not contain exactly 200 cards")
if "Natoli" in catalog:
    errors.append("Natoli identifier leaked into Fette catalog")
if len(re.findall(r'https://pharmaglobaleng\.com/parts/pge-fet-\d{3}/', (ROOT / "sitemap.xml").read_text(encoding="utf-8"))) != 200:
    errors.append("Main sitemap does not contain exactly 200 Fette part URLs")
if len(re.findall(r'https://pharmaglobaleng\.com/parts/pge-fet-\d{3}/', (ROOT / "sitemap-parts-images.xml").read_text(encoding="utf-8"))) != 200:
    errors.append("Image sitemap does not contain exactly 200 Fette part URLs")

if errors:
    raise SystemExit("\n".join(errors))

print(json.dumps({
    "records": len(parts),
    "pages": len(canonicals),
    "catalog_cards": 200,
    "with_oem": sum(bool(part["oem_number"]) for part in parts),
    "oem_needed": sum(not part["oem_number"] for part in parts),
    "json_ld": "Product + FAQPage + BreadcrumbList valid on every page",
    "natoli_identifiers": 0,
}, indent=2))
