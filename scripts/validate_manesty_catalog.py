#!/usr/bin/env python3
"""Validate the public Manesty catalog against its exact CSV mapping."""

from __future__ import annotations

import csv
import json
import math
import struct
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/manesty-parts.csv"


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        return (0, 0)
    return struct.unpack(">II", header[16:24])


def oem_display(value: str) -> str:
    return value if value.casefold() not in {"", "n/a", "na", "none", "not available"} else "Not listed in source catalog"


def main() -> None:
    with DATA.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    errors: list[str] = []
    if len(rows) != 1000:
        errors.append(f"Expected 1000 CSV rows, found {len(rows)}")
    if len({row["sku"] for row in rows}) != len(rows):
        errors.append("CSV contains duplicate SKUs")
    if len({row["image_path"] for row in rows}) != len(rows):
        errors.append("CSV contains duplicate image paths")

    catalog_path = ROOT / "parts/manesty/index.html"
    catalog = catalog_path.read_text(encoding="utf-8")
    paginated = 'data-pge-catalog="v2"' in catalog
    if paginated:
        pages = [catalog]
        for page_number in range(2, math.ceil(len(rows) / 50) + 1):
            page_path = ROOT / "parts" / "manesty" / "page" / str(page_number) / "index.html"
            if not page_path.is_file():
                errors.append(f"Manesty catalog page {page_number} is missing")
                continue
            pages.append(page_path.read_text(encoding="utf-8"))
        catalog = "\n".join(pages)

    next_catalog = json.loads((ROOT / "next-app/data/parts-catalog.json").read_text(encoding="utf-8"))
    next_manesty = {
        part["sku"]: part for part in next_catalog["parts"] if part.get("brand") == "manesty"
    }
    public_manesty = {
        part["sku"]: part
        for part in json.loads((ROOT / "catalog-data/manesty.json").read_text(encoding="utf-8"))
    }
    if len(next_manesty) != 1000 or len(public_manesty) != 1000:
        errors.append(
            f"Paginated data mismatch: source={len(next_manesty)}, public={len(public_manesty)}"
        )
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    image_sitemap = (ROOT / "sitemap-parts-images.xml").read_text(encoding="utf-8")
    expected_images: set[Path] = set()

    for row in rows:
        sku = row["sku"]
        if row["make"] != "Manesty":
            errors.append(f"{sku}: make is not Manesty")
        page_path = ROOT / "parts" / sku.lower() / "index.html"
        image_path = ROOT / row["image_path"].lstrip("/")
        expected_images.add(image_path)
        if not page_path.is_file():
            errors.append(f"{sku}: landing page missing")
            continue
        if not image_path.is_file() or png_size(image_path) != (760, 760):
            errors.append(f"{sku}: mapped 760x760 image missing or invalid")

        expected_record = {
            "sku": sku,
            "name": row["part_name"],
            "brand": "manesty",
            "brandName": "Manesty",
            "model": row["model"],
            "family": row["category"],
            "oem": oem_display(row["oem_number"]),
            "url": f"/parts/{sku.lower()}/",
            "originalImage": row["image_path"],
            "image": row["image_path"],
        }
        for source_name, record in (
            ("paginated source", next_manesty.get(sku)),
            ("public catalog data", public_manesty.get(sku)),
        ):
            if record is None:
                errors.append(f"{sku}: missing from {source_name}")
                continue
            for key, value in expected_record.items():
                if record.get(key) != value:
                    errors.append(
                        f"{sku}: {source_name} {key} mismatch: {record.get(key)!r} != {value!r}"
                    )

        page = page_path.read_text(encoding="utf-8")
        public_url = f"https://pharmaglobaleng.com/parts/{sku.lower()}/"
        expected_values = [
            escape(row["part_name"]),
            escape(row["model"]),
            escape(oem_display(row["oem_number"])),
            row["image_path"],
            public_url,
            'meta name="robots" content="index,follow,max-image-preview:large"',
            '"@type":"BreadcrumbList"',
        ]
        for value in expected_values:
            if value not in page:
                errors.append(f"{sku}: landing page missing mapped value {value!r}")

        card_marker = f'data-pc-sku="{sku}"' if paginated else f'data-sku="{sku}"'
        card_start = catalog.find(card_marker)
        card_end = catalog.find("</article>", card_start)
        card = catalog[card_start:card_end]
        for value in (escape(row["part_name"]), escape(row["model"]), escape(oem_display(row["oem_number"])), row["image_path"]):
            if card_start < 0 or value not in card:
                errors.append(f"{sku}: catalog card missing mapped value {value!r}")
        if public_url not in sitemap:
            errors.append(f"{sku}: missing from sitemap.xml")
        if public_url not in image_sitemap or row["image_path"] not in image_sitemap:
            errors.append(f"{sku}: missing or mismatched in image sitemap")

    actual_images = set((ROOT / "assets/images/parts/manesty").glob("*.png"))
    if actual_images != expected_images:
        errors.append(
            f"Public image inventory mismatch: expected {len(expected_images)}, found {len(actual_images)}"
        )
    if paginated:
        if '"numberOfItems":1000' not in catalog:
            errors.append("Paginated catalog schema does not report 1000 mapped records")
    elif "<strong>1000</strong> mapped records" not in catalog:
        errors.append("Catalog summary does not report 1000 mapped records")

    if errors:
        preview = "\n".join(errors[:100])
        suffix = f"\n...and {len(errors) - 100} more" if len(errors) > 100 else ""
        raise SystemExit(preview + suffix)
    print("Validated 1000 Manesty cards, landing pages, images, OEM mappings, and sitemap entries")


if __name__ == "__main__":
    main()
