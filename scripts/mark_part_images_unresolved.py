from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW_DATE = "2026-08-31"
EVIDENCE_NOTE = (
    "Synthetic visualization has no traceable markings, dimensions, provenance, "
    "or defensible record-to-OEM mapping; current descriptive label is unverified."
)


def in_scope(sku: str) -> bool:
    return sku.startswith(("PGE-K300-", "PGE-MAN-", "PGE-KIK-", "PGE-STK-"))


def update_oem_audit() -> None:
    path = ROOT / "data/oem-cross-reference-audit.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = list(rows[0])
    for row in rows:
        if not in_scope(row["sku"]):
            continue
        if row.get("oem_number_status", "").lower() == "verified" and row.get("approved_for_publication", "").lower() == "yes":
            continue
        row.update(
            manufacturer_reference="Korsch",
            model_reference="Model unresolved",
            oem_part_number="",
            oem_number_status="unresolved",
            configuration_or_variant="",
            source_title="Internet and supplied-catalog review",
            source_url="",
            source_type="visual audit",
            evidence_notes=EVIDENCE_NOTE,
            reviewed_on=REVIEW_DATE,
            approved_for_publication="no",
        )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def update_content_audit() -> None:
    path = ROOT / "data/part-content-audit.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = list(rows[0])
    for row in rows:
        if not in_scope(row["sku"]):
            continue
        row["model_reference"] = "Model unresolved"
        row["identity_source"] = "Unverified synthetic visualization; no traceable source image or record-to-OEM mapping"
        row["technical_description_status"] = "Unverified descriptive label; identity review required"
        row["search_alias_status"] = "PGE identifier only; part-name and model aliases unverified"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def update_catalog() -> None:
    path = ROOT / "parts/korsch/korsch-300/index.html"
    page = path.read_text(encoding="utf-8")
    page = page.replace("Korsch 300 Parts", "Korsch Parts - Identification Review")
    page = page.replace("Korsch 300 Tablet Press", "Korsch Equipment - Model Unresolved")
    page = page.replace("Korsch 300", "Korsch - Model Unresolved")
    page = page.replace("Model+reference%3A+300", "Model+reference%3A+Unresolved")
    page = re.sub(
        r'alt="Representative image of ([^"]+) — confirm compatibility"',
        r'alt="Synthetic visualization labeled \1 - component identity and model unresolved"',
        page,
    )
    page = page.replace(
        '<p class="sku">PGE-K300-',
        '<p class="identity-warning">Image identity and exact model unresolved</p><p class="sku">PGE-K300-',
    )
    path.write_text(page, encoding="utf-8")


if __name__ == "__main__":
    update_oem_audit()
    update_content_audit()
    update_catalog()
