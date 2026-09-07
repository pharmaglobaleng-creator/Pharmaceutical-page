#!/usr/bin/env python3
"""Synchronize the verified Manesty mapping into the paginated parts catalog."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "manesty-parts.csv"
CATALOG_PATH = ROOT / "next-app" / "data" / "parts-catalog.json"
EXPECTED_ROWS = 1000


def display_oem(value: str) -> str:
    value = value.strip()
    if value.casefold() in {"", "n/a", "na", "none", "not available"}:
        return "Not listed in source catalog"
    return value


def main() -> None:
    with CSV_PATH.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))

    if len(rows) != EXPECTED_ROWS:
        raise SystemExit(f"Expected {EXPECTED_ROWS} verified Manesty rows, found {len(rows)}")

    skus = [row["sku"].strip() for row in rows]
    if len(set(skus)) != EXPECTED_ROWS:
        raise SystemExit("The Manesty mapping contains duplicate PGE identifiers")

    parts = []
    for row in rows:
        sku = row["sku"].strip()
        name = row["part_name"].strip()
        make = row["make"].strip()
        model = row["model"].strip()
        family = row["category"].strip()
        image = row["image_path"].strip()
        landing = ROOT / "parts" / sku.lower() / "index.html"
        image_file = ROOT / image.lstrip("/")

        if make != "Manesty":
            raise SystemExit(f"Unexpected make for {sku}: {make}")
        if row["verification"].strip() != "Verified":
            raise SystemExit(f"Unverified source mapping for {sku}")
        if not all((sku, name, model, family, image)):
            raise SystemExit(f"Incomplete catalog mapping for {sku or 'unknown row'}")
        if not landing.is_file():
            raise SystemExit(f"Missing landing page for {sku}: {landing}")
        if not image_file.is_file():
            raise SystemExit(f"Missing catalog image for {sku}: {image_file}")

        parts.append(
            {
                "sku": sku,
                "name": name,
                "brand": "manesty",
                "brandName": "Manesty",
                "model": model,
                "family": family,
                "oem": display_oem(row["oem_number"]),
                "url": f"/parts/{sku.lower()}/",
                "originalImage": image,
                "image": image,
                "alt": f"Representative studio visualization of {name} matched to Manesty {model}",
                "sourceCatalog": "/parts/manesty/",
            }
        )

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    existing = catalog.get("parts", [])
    first_manesty = next((i for i, part in enumerate(existing) if part.get("brand") == "manesty"), len(existing))
    non_manesty = [part for part in existing if part.get("brand") != "manesty"]
    catalog["parts"] = non_manesty[:first_manesty] + parts + non_manesty[first_manesty:]

    manufacturer = next(
        (item for item in catalog.get("manufacturers", []) if item.get("slug") == "manesty"),
        None,
    )
    if manufacturer is None:
        raise SystemExit("Manesty manufacturer record is missing from the paginated catalog")
    manufacturer["count"] = EXPECTED_ROWS
    manufacturer["sourceHash"] = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    manufacturer.pop("models", None)
    manufacturer.pop("searchVersion", None)

    catalog["warnings"] = [
        warning for warning in catalog.get("warnings", []) if not warning.startswith("PGE-MAN-")
    ]
    CATALOG_PATH.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Synchronized {EXPECTED_ROWS} verified Manesty records into the paginated catalog")


if __name__ == "__main__":
    main()
