#!/usr/bin/env python3
"""Apply reproducible crawl/indexing fixes to the static catalog."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://pharmaglobaleng.com"
LASTMOD = "2026-09-04"


def breadcrumb_json(items: list[tuple[str, str]]) -> str:
    schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": position,
                "name": name,
                "item": url,
            }
            for position, (name, url) in enumerate(items, 1)
        ],
    }
    return json.dumps(schema, ensure_ascii=False, separators=(",", ":"))


def add_breadcrumb(path: Path, items: list[tuple[str, str]]) -> bool:
    page = path.read_text(encoding="utf-8")
    if '"@type":"BreadcrumbList"' in page or '"@type": "BreadcrumbList"' in page:
        return False
    script = f'<script type="application/ld+json">{breadcrumb_json(items)}</script>'
    if "</head>" not in page:
        raise RuntimeError(f"Missing closing head tag: {path}")
    path.write_text(page.replace("</head>", script + "</head>", 1), encoding="utf-8")
    return True


def restore_manesty_page() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_part_pages as builder

    generated = builder.image_parts("manesty", "Manesty", "MAN")
    source = next(item for item in generated if item.sku == "PGE-MAN-019")
    target = builder.Part(
        sku=source.sku,
        name=source.name,
        brand=source.brand,
        brand_slug=source.brand_slug,
        model="Model unresolved",
        image=source.image,
        family=source.family,
        confirmed_copy=(
            "The part name and image record are cataloged. The exact machine model and OEM "
            "cross-reference remain unresolved and must be confirmed during quotation."
        ),
    )
    related = [target if item.sku == target.sku else item for item in generated]
    destination = ROOT / "parts/pge-man-019/index.html"
    destination.write_text(builder.build_page(target, related), encoding="utf-8")


def write_legacy_redirect() -> None:
    target = f"{SITE}/services/tablet-punch-coatings.html"
    content = f'''<!doctype html>
<html lang="en-US"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tablet Punch Coatings | PharmaGlobalEng</title>
<meta name="description" content="Tablet punch coating services from PharmaGlobalEng.">
<meta name="robots" content="index,follow"><link rel="canonical" href="{target}">
<meta http-equiv="refresh" content="0; url={target}">
<script>window.location.replace("/services/tablet-punch-coatings.html");</script>
</head><body><p>This page has moved to <a href="/services/tablet-punch-coatings.html">Tablet Punch Coatings</a>.</p></body></html>
'''
    (ROOT / "tablet-punch-coatings.html").write_text(content, encoding="utf-8")


def update_lastmod(urls: set[str]) -> int:
    path = ROOT / "sitemap.xml"
    sitemap = path.read_text(encoding="utf-8")
    changed = 0

    def replace_block(match: re.Match[str]) -> str:
        nonlocal changed
        block = match.group(0)
        location = re.search(r"<loc>([^<]+)</loc>", block)
        if not location or location.group(1) not in urls:
            return block
        if "<lastmod>" in block:
            updated = re.sub(r"<lastmod>[^<]+</lastmod>", f"<lastmod>{LASTMOD}</lastmod>", block, count=1)
        else:
            updated = block.replace("</loc>", f"</loc>\n    <lastmod>{LASTMOD}</lastmod>", 1)
        if updated != block:
            changed += 1
        return updated

    sitemap = re.sub(r"<url>.*?</url>", replace_block, sitemap, flags=re.S)
    path.write_text(sitemap, encoding="utf-8")
    return changed


def main() -> None:
    stokes_pages = sorted(
        path
        for path in (ROOT / "parts").glob("pge-stk-*/index.html")
        if re.fullmatch(r"pge-stk-\d{4}", path.parent.name)
    )
    if len(stokes_pages) != 2000:
        raise SystemExit(f"Expected 2,000 Stokes pages, found {len(stokes_pages)}")

    changed_pages = 0
    modified_urls = {f"{SITE}/parts/stokes/", f"{SITE}/parts/pge-man-019/"}
    for path in stokes_pages:
        sku = path.parent.name.upper()
        url = f"{SITE}/parts/{path.parent.name}/"
        modified_urls.add(url)
        changed_pages += int(add_breadcrumb(path, [
            ("Parts Store", f"{SITE}/parts/"),
            ("Stokes Parts", f"{SITE}/parts/stokes/"),
            (sku, url),
        ]))

    catalog_names = {
        "fette": "Fette Parts",
        "kikusui": "Kikusui Parts",
        "manesty": "Manesty Parts",
        "stokes": "Stokes Parts",
    }
    changed_catalogs = 0
    for slug, name in catalog_names.items():
        url = f"{SITE}/parts/{slug}/"
        modified_urls.add(url)
        changed_catalogs += int(add_breadcrumb(ROOT / f"parts/{slug}/index.html", [
            ("Parts Store", f"{SITE}/parts/"),
            (name, url),
        ]))

    restore_manesty_page()
    write_legacy_redirect()
    sitemap_changes = update_lastmod(modified_urls)

    print(f"Stokes breadcrumb pages updated: {changed_pages}")
    print(f"Catalog breadcrumb pages updated: {changed_catalogs}")
    print("Restored: parts/pge-man-019/index.html")
    print("Redirected legacy URL: tablet-punch-coatings.html")
    print(f"Sitemap lastmod entries updated: {sitemap_changes}")


if __name__ == "__main__":
    main()
