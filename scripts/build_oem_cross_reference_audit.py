from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data/part-content-audit.csv"
DESTINATION = ROOT / "data/oem-cross-reference-audit.csv"

FIELDS = (
    "sku",
    "part_name",
    "manufacturer_reference",
    "model_reference",
    "oem_part_number",
    "oem_number_status",
    "configuration_or_variant",
    "source_title",
    "source_url",
    "source_type",
    "evidence_notes",
    "reviewed_on",
    "approved_for_publication",
)


def existing_rows() -> dict[str, dict[str, str]]:
    if not DESTINATION.exists():
        return {}
    with DESTINATION.open(encoding="utf-8", newline="") as handle:
        return {row["sku"]: row for row in csv.DictReader(handle)}


def main() -> None:
    existing = existing_rows()
    with CATALOG.open(encoding="utf-8", newline="") as handle:
        catalog = list(csv.DictReader(handle))

    with DESTINATION.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for part in catalog:
            prior = existing.get(part["sku"], {})
            row = {field: prior.get(field, "") for field in FIELDS}
            row.update(
                sku=part["sku"],
                part_name=part["part_name"],
                manufacturer_reference=part["manufacturer_reference"],
                model_reference=part["model_reference"],
            )
            if not row["oem_number_status"]:
                row["oem_number_status"] = "not researched"
            if not row["approved_for_publication"]:
                row["approved_for_publication"] = "no"
            writer.writerow(row)

    print(f"Prepared {len(catalog)} OEM cross-reference research records")


if __name__ == "__main__":
    main()
