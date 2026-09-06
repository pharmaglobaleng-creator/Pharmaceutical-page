#!/usr/bin/env python3
"""Remove source-catalog part numbers from published Stokes HTML.

The private source mapping remains in the CSV so OEM, make, model, name, image,
and source-row relationships are not disturbed. Only public HTML is rewritten.
"""

from __future__ import annotations

import csv
from html import escape
from pathlib import Path
from urllib.parse import quote_plus


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/stokes-catalog-parts.csv"


def remove_number(html: str, row: dict[str, str]) -> str:
    sku = row["sku"].strip()
    number = row["catalog_part_number"].strip()
    if not number:
        return html

    value = escape(number, quote=True)
    json_property = (
        '{"@type": "PropertyValue", "name": "Catalog part number", '
        f'"value": "{value}"}}'
    )
    html = html.replace(json_property + ", ", "")
    html = html.replace(", " + json_property, "")
    html = html.replace(
        f'<div><dt>Catalog part number</dt><dd>{value}</dd></div>', ""
    )
    html = html.replace(f", catalog part {value}, OEM reference", ", OEM reference")
    html = html.replace(f" - NEEDS {value}/1", "")
    html = html.replace(quote_plus(f" - NEEDS {number}/1"), "")
    html = html.replace(f" · Catalog {value}</p>", "</p>")
    html = html.replace(f" | {value} | ", " | ")
    html = html.replace(quote_plus(f"Catalog part number: {number}\n"), "")
    html = html.replace(f'<span class="alias">{value}</span>', "")
    html = html.replace(f'<span class="alias">catalog part {value}</span>', "")
    return html


def clean_language(html: str) -> str:
    replacements = {
        "organized by exact model, part name, catalog part number, and OEM reference":
            "organized by exact model, part name, and OEM reference",
        "matched to the exact Stokes model, part name, catalog cross-reference, and OEM reference":
            "matched to the exact Stokes model, part name, and OEM reference",
        "matched directly to the source catalog by model, part name, catalog part number, OEM number, page, and image position":
            "matched directly to the source by model, part name, OEM number, page, and image position",
        "Search part, model, catalog number, OEM, or PGE number":
            "Search part, model, OEM, or PGE number",
        "Search part name, model, catalog number, OEM, or PGE number":
            "Search part name, model, OEM, or PGE number",
        "Try a model, part name, catalog number, OEM number, or PGE number.":
            "Try a model, part name, OEM number, or PGE number.",
        "Try a part name, model, catalog part number, OEM number, or PGE number.":
            "Try a part name, model, OEM number, or PGE number.",
        "Verified catalog cross-reference": "Verified part cross-reference",
        "Verified catalog identifiers": "Verified part identifiers",
        "Source catalog page": "Source page",
        "catalog records": "part records",
        "Catalog page ": "Source page ",
    }
    for old, new in replacements.items():
        html = html.replace(old, new)
    return html


def main() -> None:
    with DATA.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    index_path = ROOT / "parts/stokes/index.html"
    index_html = index_path.read_text(encoding="utf-8")
    for row in rows:
        index_html = remove_number(index_html, row)
    index_path.write_text(clean_language(index_html), encoding="utf-8")

    changed = 0
    for row in rows:
        page_path = ROOT / "parts" / row["sku"].lower() / "index.html"
        if not page_path.exists():
            continue
        before = page_path.read_text(encoding="utf-8")
        after = clean_language(remove_number(before, row))
        if after != before:
            page_path.write_text(after, encoding="utf-8")
            changed += 1

    print(f"Removed public catalog-part numbers from {changed} Stokes landing pages and the catalog index")


if __name__ == "__main__":
    main()
