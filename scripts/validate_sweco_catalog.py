#!/usr/bin/env python3
"""Validate the Sweco source-to-image-to-page mapping and public-data hygiene."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from html import escape, unescape
from pathlib import Path
from typing import Optional

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://pharmaglobaleng.com"
EXPECTED = 33
NOT_LISTED = "Not listed in source catalog"
FORBIDDEN_KEYS = {
    "source_listing_reference", "product_url", "image_url", "source_pages",
    "supplier_sku", "supplier_variant_skus", "source_url", "catalog_image_url", "original_image_url",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def all_keys(value: object):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from all_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from all_keys(child)


def validate(source_inventory: Optional[Path], source_image_dir: Optional[Path], studio_image_dir: Optional[Path]) -> dict:
    public_path = ROOT / "data/sweco-parts.json"
    payload = json.loads(public_path.read_text(encoding="utf-8"))
    rows = payload.get("records", [])
    assert payload.get("record_count") == EXPECTED and len(rows) == EXPECTED
    assert payload.get("make") == "Sweco"
    assert not (set(all_keys(payload)) & FORBIDDEN_KEYS), "Forbidden supplier/source fields leaked into public Sweco data"
    expected_skus = [f"PGE-SWE-{number:03d}" for number in range(1, EXPECTED + 1)]
    assert [row["sku"] for row in rows] == expected_skus
    assert all(row["make"] == "Sweco" for row in rows)
    assert all(row["model"] == NOT_LISTED for row in rows)
    assert sum(row["replacement_oem_number"] == NOT_LISTED for row in rows) == 10
    assert len({row["image_path"] for row in rows}) == EXPECTED
    shared_oem = [row for row in rows if row["replacement_oem_number"] == "40020M013"]
    assert [row["sku"] for row in shared_oem] == ["PGE-SWE-012", "PGE-SWE-017"]

    catalog = json.loads((ROOT / "next-app/data/parts-catalog.json").read_text(encoding="utf-8"))
    catalog_rows = [row for row in catalog["parts"] if row.get("brand") == "sweco"]
    manufacturers = [row for row in catalog["manufacturers"] if row.get("slug") == "sweco"]
    assert len(manufacturers) == 1 and manufacturers[0]["count"] == EXPECTED
    assert manufacturers[0].get("models") == []
    assert len(catalog_rows) == EXPECTED
    by_sku = {row["sku"]: row for row in catalog_rows}

    image_hashes = set()
    meta_descriptions = set()
    page_texts = []
    for row in rows:
        sku = row["sku"]
        image = ROOT / row["image_path"].lstrip("/")
        page = ROOT / row["landing_page"].lstrip("/") / "index.html"
        assert image.is_file(), image
        assert page.is_file(), page
        with Image.open(image) as opened:
            assert opened.size == (760, 760) and opened.format == "WEBP", (sku, opened.size, opened.format)
        image_hash = digest(image)
        assert image_hash == row["image_sha256"], sku
        assert image_hash not in image_hashes, f"Duplicate Sweco website image: {sku}"
        image_hashes.add(image_hash)

        html = page.read_text(encoding="utf-8")
        page_texts.append(html)
        assert f'<link rel="canonical" href="{SITE + row["landing_page"]}">' in html
        assert '<meta name="robots" content="index,follow,max-image-preview:large">' in html
        assert '<html lang="en-US" data-pge-content="editorial">' in html
        assert f'PharmaGlobalEng Number: {sku}' in html
        meta_match = re.search(r'<meta name="description" content="([^"]*)">', html)
        assert meta_match, f"Missing meta description: {sku}"
        meta = unescape(meta_match.group(1))
        assert f"PharmaGlobalEng Number: {sku}" in meta
        assert len(meta) <= 175, f"Meta description too long: {sku} ({len(meta)})"
        assert meta not in meta_descriptions, f"Duplicate meta description: {sku}"
        meta_descriptions.add(meta)
        assert '<dt>Make</dt><dd>Sweco</dd>' in html
        assert f'<dt>Model</dt><dd>{escape(row["model"])}</dd>' in html
        assert f'<dt>Equipment type</dt><dd>{escape(row["equipment_descriptor"])}</dd>' in html
        assert f'<dt>Part name</dt><dd>{escape(row["part_name"])}</dd>' in html
        assert f'<dt>Replacement OEM Number</dt><dd>{escape(row["replacement_oem_number"])}</dd>' in html
        assert f'<img src="{row["image_path"]}"' in html
        assert f'Replacement OEM Number: {escape(row["replacement_oem_number"])}' in html
        assert "PharmParts" not in html and "pharmparts" not in html.casefold()
        product = by_sku[sku]
        assert product["name"] == row["part_name"]
        assert product["brandName"] == "Sweco"
        assert product["model"] == row["model"]
        assert product["oem"] == row["replacement_oem_number"]
        assert product["url"] == row["landing_page"]
        assert product["image"] == row["image_path"]

    public_text = public_path.read_text(encoding="utf-8") + "\n" + "\n".join(page_texts)
    assert "pharmparts" not in public_text.casefold()

    if source_inventory:
        source = json.loads(source_inventory.read_text(encoding="utf-8"))
        originals = source.get("records", [])
        assert len(originals) == EXPECTED
        for original, row in zip(originals, rows):
            assert original["sku"] == row["sku"]
            assert original["part_name"] == row["part_name"]
            assert original["make"] == row["make"]
            assert original["model"] == row["model"]
            assert original["equipment_descriptor"] == row["equipment_descriptor"]
            assert original["replacement_oem_number"] == row["replacement_oem_number"]
            supplier_reference = str(original.get("source_listing_reference", "")).strip()
            if supplier_reference:
                assert not re.search(rf"(?<![A-Za-z0-9]){re.escape(supplier_reference)}(?![A-Za-z0-9])", public_text), f"Supplier listing reference leaked: {row['sku']}"
            if source_image_dir:
                original_image = source_image_dir / f"{row['sku'].lower()}.jpg"
                assert original_image.is_file() and digest(original_image) == row["source_photo_sha256"]
            if studio_image_dir:
                studio_image = studio_image_dir / f"{row['sku'].lower()}.png"
                assert studio_image.is_file() and digest(studio_image) == row["full_resolution_image_sha256"]

    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    image_sitemap = (ROOT / "sitemap-parts-images.xml").read_text(encoding="utf-8")
    sitemap_urls = re.findall(r"<loc>(.*?)</loc>", sitemap)
    image_page_urls = re.findall(r"<url><loc>(.*?)</loc>", image_sitemap)
    image_urls = re.findall(r"<image:loc>(.*?)</image:loc>", image_sitemap)
    assert sitemap_urls.count(SITE + "/parts/sweco/") == 1
    for row in rows:
        assert sitemap_urls.count(SITE + row["landing_page"]) == 1
        assert image_page_urls.count(SITE + row["landing_page"]) == 1
        assert image_urls.count(SITE + row["image_path"]) == 1

    return {
        "status": "passed",
        "records": len(rows),
        "unique_images": len(image_hashes),
        "website_image_size": "760x760 WEBP",
        "records_without_listed_oem": 10,
        "records_without_specific_model": 33,
        "shared_oem_40020M013_records": 2,
        "matched_catalog_rows": len(catalog_rows),
        "unique_meta_descriptions": len(meta_descriptions),
        "public_supplier_identifiers": 0,
        "public_supplier_urls": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-inventory", type=Path)
    parser.add_argument("--source-image-dir", type=Path)
    parser.add_argument("--studio-image-dir", type=Path)
    args = parser.parse_args()
    source_inventory = args.source_inventory.expanduser().resolve() if args.source_inventory else None
    source_image_dir = args.source_image_dir.expanduser().resolve() if args.source_image_dir else None
    studio_image_dir = args.studio_image_dir.expanduser().resolve() if args.studio_image_dir else None
    print(json.dumps(validate(source_inventory, source_image_dir, studio_image_dir), indent=2))


if __name__ == "__main__":
    main()
