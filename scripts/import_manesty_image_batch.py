#!/usr/bin/env python3
"""Import the verified 1,000-image Manesty batch into the public site catalog."""

from __future__ import annotations

import csv
import json
import re
import shutil
import struct
from pathlib import Path


SITE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SITE_ROOT.parent
MANIFEST_PATH = (
    PROJECT_ROOT
    / "outputs/manesty-parts-images/manifests/manesty-first-1000-catalog-photos.json"
)
SOURCE_IMAGE_DIR = PROJECT_ROOT / "outputs/manesty-parts-images/website-760"
PUBLIC_IMAGE_DIR = SITE_ROOT / "assets/images/parts/manesty"
CSV_PATH = SITE_ROOT / "data/manesty-parts.csv"
FIELDS = [
    "record_number",
    "batch_image_number",
    "sku",
    "make",
    "model",
    "part_name",
    "category",
    "catalog_part_number",
    "oem_number",
    "catalog_page",
    "image_position",
    "photo_status",
    "verification",
    "image_path",
]


def slug(value: object) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", str(value).casefold())).strip("-")


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Not a valid PNG: {path}")
    return struct.unpack(">II", header[16:24])


def required(item: dict, key: str) -> str:
    value = str(item.get(key, "")).strip()
    if not value:
        raise ValueError(f"Missing {key} in batch image {item.get('batch_image_number')}")
    return value


def main() -> None:
    raw = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    items = raw if isinstance(raw, list) else raw.get("items", [])
    if len(items) != 1000:
        raise SystemExit(f"Expected 1000 manifest rows, found {len(items)}")

    items = sorted(items, key=lambda item: int(item["batch_image_number"]))
    expected_batch = list(range(1, 1001))
    actual_batch = [int(item["batch_image_number"]) for item in items]
    if actual_batch != expected_batch:
        raise SystemExit("Manifest batch numbers are not exactly 1 through 1000")

    rows: list[dict[str, object]] = []
    expected_images: set[str] = set()
    seen_skus: set[str] = set()
    for item in items:
        sku = required(item, "sku")
        if sku in seen_skus:
            raise SystemExit(f"Duplicate SKU in manifest: {sku}")
        seen_skus.add(sku)
        if required(item, "make") != "Manesty":
            raise SystemExit(f"Unexpected make for {sku}: {item.get('make')}")

        part_name = required(item, "part_name")
        model = required(item, "model")
        oem = required(item, "oem_number")
        source = SOURCE_IMAGE_DIR / required(item, "filename")
        if not source.is_file():
            raise SystemExit(f"Missing website image for {sku}: {source}")
        if png_size(source) != (760, 760):
            raise SystemExit(f"Website image is not 760x760 for {sku}: {source}")

        public_name = f"{sku.lower()}-{slug(part_name)}-oem-{slug(oem)}.png"
        destination = PUBLIC_IMAGE_DIR / public_name
        PUBLIC_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        expected_images.add(public_name)

        rows.append(
            {
                "record_number": int(item["spreadsheet_index"]),
                "batch_image_number": int(item["batch_image_number"]),
                "sku": sku,
                "make": "Manesty",
                "model": model,
                "part_name": part_name,
                "category": required(item, "category"),
                # Preserve an empty source value; never invent a catalog-part number.
                "catalog_part_number": str(item.get("catalog_part_number", "")).strip(),
                "oem_number": oem,
                "catalog_page": int(item["source_page"]),
                "image_position": int(item["slot"]),
                "photo_status": "Catalog photo",
                "verification": required(item, "verification_status"),
                "image_path": f"/assets/images/parts/manesty/{public_name}",
            }
        )

    public_images = {path.name for path in PUBLIC_IMAGE_DIR.glob("*.png")}
    extras = sorted(public_images - expected_images)
    missing = sorted(expected_images - public_images)
    if extras or missing:
        raise SystemExit(
            f"Public Manesty image set mismatch: {len(extras)} extra, {len(missing)} missing"
        )

    temp_path = CSV_PATH.with_suffix(".csv.tmp")
    with temp_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temp_path.replace(CSV_PATH)
    print("Imported 1000 verified Manesty mappings and 1000 website images")


if __name__ == "__main__":
    main()
