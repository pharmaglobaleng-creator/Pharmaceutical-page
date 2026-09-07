#!/usr/bin/env python3
"""Verify source-catalog part numbers are absent from public part HTML."""

from __future__ import annotations

import csv
import json
import re
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "kikusui": ROOT / "data/kikusui-parts.csv",
    "manesty": ROOT / "data/manesty-parts.csv",
    "stokes": ROOT / "data/stokes-catalog-parts.csv",
}
BANNED = ("catalog part number", "catalog part:", "natoli")


def public_name(row: dict[str, str]) -> str:
    name = row["part_name"].strip()
    number = row["catalog_part_number"].strip()
    return re.sub(rf"\s+-\s+NEEDS\s+{re.escape(number)}/1$", "", name)


def main() -> None:
    errors: list[str] = []
    checked = 0
    next_data_path = ROOT / "next-app/data/parts-catalog.json"
    next_parts = {}
    if next_data_path.is_file():
        next_data = json.loads(next_data_path.read_text(encoding="utf-8"))
        next_parts = {part["sku"]: part for part in next_data.get("parts", [])}
    for brand, source in SOURCES.items():
        with source.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        catalog = (ROOT / "parts" / brand / "index.html").read_text(encoding="utf-8")
        paginated = 'data-pge-catalog="v2"' in catalog
        catalog_pages = [catalog]
        if paginated:
            catalog_pages.extend(
                path.read_text(encoding="utf-8")
                for path in sorted((ROOT / "parts" / brand / "page").glob("*/index.html"))
            )
        for phrase in BANNED:
            if any(phrase in page.casefold() for page in catalog_pages):
                errors.append(f"{brand} catalog contains banned phrase: {phrase}")
        for row in rows:
            sku = row["sku"].strip()
            page_path = ROOT / "parts" / sku.lower() / "index.html"
            if not page_path.is_file():
                errors.append(f"Missing landing page: {sku}")
                continue
            html = page_path.read_text(encoding="utf-8")
            checked += 1
            for phrase in BANNED:
                if phrase in html.casefold():
                    errors.append(f"{sku} contains banned phrase: {phrase}")
            for expected in (sku, row["make"].strip(), row["model"].strip(), escape(public_name(row))):
                if expected and expected not in html:
                    errors.append(f"{sku} is missing mapped value: {expected}")
            number = row["catalog_part_number"].strip()
            oem = row["oem_number"].strip()
            if number and number != oem and number in html:
                errors.append(f"{sku} exposes source catalog-part number: {number}")

            if paginated:
                record = next_parts.get(sku)
                if record is None:
                    errors.append(f"Missing paginated catalog record: {sku}")
                else:
                    public_record = json.dumps(record, ensure_ascii=False)
                    if number and number != oem and number in public_record:
                        errors.append(f"{sku} catalog data exposes source catalog-part number: {number}")
            else:
                start = catalog.find(f'data-sku="{sku}"')
                end = catalog.find("</article>", start)
                card = catalog[start:end]
                if start < 0 or not card:
                    errors.append(f"Missing catalog card: {sku}")
                elif number and number != oem and number in card:
                    errors.append(f"{sku} catalog card exposes source catalog-part number: {number}")

    if errors:
        raise SystemExit("\n".join(errors))
    print(f"Verified {checked} landing pages and 3 catalog indexes: no public source-catalog part numbers")


if __name__ == "__main__":
    main()
