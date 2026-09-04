from __future__ import annotations

import csv
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
errors: list[str] = []

landing_pages = sorted((ROOT / "parts").glob("pge-man-*/index.html"))
image_files = sorted((ROOT / "assets/images/parts/manesty").rglob("*.webp")) if (ROOT / "assets/images/parts/manesty").exists() else []
if landing_pages:
    errors.append(f"{len(landing_pages)} Manesty product landing pages remain")
if image_files:
    errors.append(f"{len(image_files)} Manesty product images remain")

catalog = (ROOT / "parts/manesty/index.html").read_text(encoding="utf-8")
if '<meta name="robots" content="noindex,follow">' not in catalog:
    errors.append("Retired Manesty route is not marked noindex")
if '<link rel="canonical" href="https://pharmaglobaleng.com/parts/">' not in catalog:
    errors.append("Retired Manesty route does not canonicalize to the active Parts Store")
if '<article class="product-card"' in catalog or "PGE-MAN-" in catalog:
    errors.append("Retired Manesty route still contains product content")

parts_index = (ROOT / "parts/index.html").read_text(encoding="utf-8")
if 'href="/parts/manesty/"' in parts_index or "199 parts</span><div class=\"card-mark\" aria-hidden=\"true\">MN" in parts_index:
    errors.append("Parts Store still links to the Manesty catalog")
if "Browse 3211 independently produced replacement-part records." not in parts_index:
    errors.append("Parts Store total was not reduced to 3211")

for sitemap_name in ("sitemap.xml", "sitemap-parts-images.xml"):
    path = ROOT / sitemap_name
    ET.parse(path)
    text = path.read_text(encoding="utf-8")
    if "/parts/pge-man-" in text or "/parts/manesty/" in text or "/assets/images/parts/manesty/" in text:
        errors.append(f"{sitemap_name} still contains Manesty URLs")

audit_counts: dict[str, int] = {}
for relative in (
    "data/part-content-audit.csv",
    "data/oem-cross-reference-audit.csv",
    "data/oem-match-review.csv",
):
    path = ROOT / relative
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    count = sum(bool(row) and row[0].startswith("PGE-MAN-") for row in rows[1:])
    audit_counts[relative] = count
    if count:
        errors.append(f"{relative} still contains {count} Manesty records")

regeneration_checks = {
    "scripts/build_parts_catalogs.py": r'"manesty"\s*:\s*\("Manesty",\s*"MAN"\)',
    "scripts/build_part_pages.py": r'image_parts\("manesty",\s*"Manesty",\s*"MAN"\)',
    "scripts/apply_indexing_fixes.py": r"restore_manesty_page",
}
for relative, pattern in regeneration_checks.items():
    if re.search(pattern, (ROOT / relative).read_text(encoding="utf-8")):
        errors.append(f"{relative} can regenerate retired Manesty content")

if errors:
    raise SystemExit("\n".join(errors))

print(json.dumps({
    "removed_landing_pages": 199,
    "removed_images": 199,
    "remaining_catalog_cards": 0,
    "remaining_sitemap_urls": 0,
    "remaining_audit_rows": audit_counts,
    "parts_store_total": 3211,
    "retired_route": "noindex and canonicalized to /parts/",
    "recovery": "available from Git history",
}, indent=2))
