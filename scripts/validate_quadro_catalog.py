#!/usr/bin/env python3
"""Validate the Quadro source-to-page mapping and public-data hygiene."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from html import escape
from pathlib import Path
from typing import Optional

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://pharmaglobaleng.com"
EXPECTED = 113
NOT_LISTED = "Not listed in source catalog"
FORBIDDEN_KEYS = {"supplier_sku", "supplier_variant_skus", "source_url", "catalog_image_url", "original_image_url"}


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


def validate(source_manifest: Optional[Path]) -> dict:
    public_path = ROOT / "data/quadro-parts.json"
    payload = json.loads(public_path.read_text(encoding="utf-8"))
    rows = payload.get("records", [])
    assert payload.get("record_count") == EXPECTED and len(rows) == EXPECTED
    assert not (set(all_keys(payload)) & FORBIDDEN_KEYS), "Forbidden supplier/source fields leaked into public Quadro data"
    expected_skus = [f"PGE-QUA-{number:03d}" for number in range(1, EXPECTED + 1)]
    assert [row["sku"] for row in rows] == expected_skus
    assert [row["source_record"] for row in rows] == [f"Q{number:03d}" for number in range(1, EXPECTED + 1)]
    assert len({row["image_path"] for row in rows}) == EXPECTED
    assert sum(row["replacement_oem_number"] == NOT_LISTED for row in rows) == 7

    catalog = json.loads((ROOT / "next-app/data/parts-catalog.json").read_text(encoding="utf-8"))
    catalog_rows = [row for row in catalog["parts"] if row.get("brand") == "quadro"]
    manufacturer = [row for row in catalog["manufacturers"] if row.get("slug") == "quadro"]
    assert len(manufacturer) == 1 and manufacturer[0]["count"] == EXPECTED
    assert len(catalog_rows) == EXPECTED
    by_sku = {row["sku"]: row for row in catalog_rows}

    image_hashes = set()
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
        assert image_hash not in image_hashes, f"Duplicate Quadro website image: {sku}"
        image_hashes.add(image_hash)

        html = page.read_text(encoding="utf-8")
        page_texts.append(html)
        assert f'<link rel="canonical" href="{SITE + row["landing_page"]}">' in html
        assert '<meta name="robots" content="index,follow,max-image-preview:large">' in html
        assert f'PharmaGlobalEng Number: {sku}' in html
        assert f'<dt>Make</dt><dd>Quadro</dd>' in html
        assert f'<dt>Model</dt><dd>{escape(row["model"])}</dd>' in html
        assert f'<dt>Part name</dt><dd>{escape(row["part_name"])}</dd>' in html
        assert f'<dt>Replacement OEM Number</dt><dd>{escape(row["replacement_oem_number"])}</dd>' in html
        assert f'<img src="{row["image_path"]}"' in html
        assert "Replacement OEM Number:" in html
        assert "PharmParts" not in html and "pharmparts" not in html.casefold()
        product = by_sku[sku]
        assert product["name"] == row["part_name"]
        assert product["model"] == row["model"]
        assert product["oem"] == row["replacement_oem_number"]
        assert product["url"] == row["landing_page"]
        assert product["image"] == row["image_path"]

    public_text = public_path.read_text(encoding="utf-8") + "\n" + "\n".join(page_texts)
    assert "pharmparts" not in public_text.casefold()
    assert "supplier_sku" not in public_text
    if source_manifest:
        source = json.loads(source_manifest.read_text(encoding="utf-8"))
        assert len(source) == EXPECTED
        for original, row in zip(source, rows):
            assert original["id"] == row["source_record"]
            assert original["edited_sha256"] == row["source_image_sha256"]
            assert (" / ".join(original.get("oem_numbers_listed", [])) or NOT_LISTED) == row["replacement_oem_number"]
            supplier_identifier = str(original.get("supplier_sku", "")).strip()
            if supplier_identifier:
                assert not re.search(rf"(?<![A-Za-z0-9]){re.escape(supplier_identifier)}(?![A-Za-z0-9])", public_text), f"Supplier identifier leaked: {row['source_record']}"

    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    image_sitemap = (ROOT / "sitemap-parts-images.xml").read_text(encoding="utf-8")
    sitemap_urls = re.findall(r"<loc>(.*?)</loc>", sitemap)
    image_page_urls = re.findall(r"<url><loc>(.*?)</loc>", image_sitemap)
    image_urls = re.findall(r"<image:loc>(.*?)</image:loc>", image_sitemap)
    assert sitemap_urls.count(SITE + "/parts/quadro/") == 1
    for row in rows:
        assert sitemap_urls.count(SITE + row["landing_page"]) == 1
        assert image_page_urls.count(SITE + row["landing_page"]) == 1
        assert image_urls.count(SITE + row["image_path"]) == 1

    return {
        "status": "passed",
        "records": len(rows),
        "unique_images": len(image_hashes),
        "website_image_size": "760x760 WEBP",
        "records_without_listed_oem": 7,
        "matched_catalog_rows": len(catalog_rows),
        "public_supplier_identifiers": 0,
        "public_supplier_urls": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-manifest", type=Path)
    args = parser.parse_args()
    source = args.source_manifest.expanduser().resolve() if args.source_manifest else None
    print(json.dumps(validate(source), indent=2))


if __name__ == "__main__":
    main()
