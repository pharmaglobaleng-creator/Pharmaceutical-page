#!/usr/bin/env python3
"""Remove source-catalog numbers from public Manesty image filenames."""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/manesty-parts.csv"


def slug(value: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", value.casefold())).strip("-")


def main() -> None:
    with DATA.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    renamed = 0
    for row in rows:
        old_public = row["image_path"].strip()
        if not old_public:
            continue
        suffix = Path(old_public).suffix
        oem = row["oem_number"].strip() or "not-listed"
        filename = f"{row['sku'].lower()}-{slug(row['part_name'])}-oem-{slug(oem)}{suffix}"
        new_public = f"/assets/images/parts/manesty/{filename}"
        old_path = ROOT / old_public.lstrip("/")
        new_path = ROOT / new_public.lstrip("/")
        if old_path != new_path:
            if new_path.exists() and old_path.exists():
                raise SystemExit(f"Refusing to overwrite existing image: {new_path}")
            if old_path.exists():
                old_path.rename(new_path)
                renamed += 1
            elif not new_path.exists():
                raise SystemExit(f"Missing Manesty image: {old_path}")
            row["image_path"] = new_public

    with DATA.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Renamed {renamed} Manesty images without public source-catalog numbers")


if __name__ == "__main__":
    main()
