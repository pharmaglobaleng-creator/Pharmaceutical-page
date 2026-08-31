from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEWED_ON = "2026-08-31"
NATOLI_CATALOGS = "https://store.natoli.com/catalogs/"

# Every row below has an exact or normalized-exact name and model match in
# PharmParts and is independently corroborated in Natoli's current print
# catalog. Third-party replacement SKUs are intentionally not stored.
MATCHES = {
    "PGE-MAN-008": ("Column Bearing Bush", "Betapress", "44344", "https://pharmparts.com/products/column-bearing-bush-for-manesty-betapress-oem-part-44344"),
    "PGE-MAN-021": ("Feeder Gear", "Betapress", "44437", "https://pharmparts.com/products/feeder-gear-oem-part-44437-for-manesty-betapress"),
    "PGE-MAN-058": ("Scraper Plate - Stainless Steel - Short", "Betapress", "44469", "https://pharmparts.com/products/scraper-plate-stainless-steel-short-for-manesty-betapress-oem-part-44469"),
    "PGE-MAN-122": ("Plate Under Feeder", "Express", "48644", "https://pharmparts.com/products/plate-under-feeder-for-manesty-express-oem-part-48644"),
    "PGE-MAN-142": ("Upper or Lower Pressure Roll", "Express", "48135", "https://pharmparts.com/products/upper-or-lower-pressure-roll-for-manesty-express-oem-part-48135"),
    "PGE-MAN-149": ("Bush in Roll", "MK I / MK II / Rotapress MK IIA", "39039", "https://pharmparts.com/products/bush-in-roll-for-manesty-mkiia-mkii-mki-oem-part-39039"),
    "PGE-MAN-150": ("Ejection Cam - Bronze", "MK I / MK II / Rotapress MK IIA", "39316", "https://pharmparts.com/products/ejection-cam-bronze-for-manesty-mkiia-mkii-mki-oem-part-39316"),
    "PGE-MAN-151": ("Ejection Cam - Steel", "MK I / MK II / Rotapress MK IIA", "39316/1", "https://pharmparts.com/products/ejection-cam-steel-for-manesty-mkiia-mkii-mki-oem-part-39316-1"),
    "PGE-MAN-164": ("Scraper Blade", "Novapress", "62223", "https://pharmparts.com/products/scraper-blade-oem-part-62223-for-manesty-novapress"),
    "PGE-MAN-185": ("Ejection Cam - B Tooling", "Unipress", "69457", "https://pharmparts.com/products/ejection-cam-b-tooling-for-manesty-unipress-oem-part-69457"),
    "PGE-STK-013": ("Lower Pull-Down Cam - 1-3/8 Inch Fill", "328", "B-236-873-009", "https://pharmparts.com/products/lower-pull-down-cam-1-3-8-fill-for-stokes-328-oem-part-b-236-873-009"),
    "PGE-STK-014": ("Lower Pull-Down Cam - 11/16 Inch Fill", "328", "D-236-864-002", "https://pharmparts.com/products/lower-pull-down-cam-11-16-fill-for-stokes-328-oem-part-d-236-864-002"),
    "PGE-STK-015": ("Lower Pull-Down Cam - 7/8 Inch Fill, Series 33", "328", "D-236-865-002", "https://pharmparts.com/products/lower-pull-down-cam-7-8-fill-ser-33-for-stokes-328-oem-part-d-236-865-002"),
    "PGE-STK-036": ("Belt Guard", "BB2", "D-200-345-13", "https://pharmparts.com/products/belt-guard-for-stokes-bb2-oem-part-d-200-345-13"),
    "PGE-STK-037": ("Rear Guard Apron - 3 Point", "BB2", "F-281-781-6", "https://pharmparts.com/products/rear-guard-apron-3-point-for-stokes-bb2-oem-part-f-281-781-6"),
    "PGE-STK-038": ("Weight Adjuster Cam", "BB2", "C-220-121-11", "https://pharmparts.com/products/weight-adjuster-cam-for-stokes-bb2-oem-part-c-220-121-11"),
}


def main() -> None:
    path = ROOT / "data/oem-cross-reference-audit.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fields = list(rows[0])
    for row in rows:
        match = MATCHES.get(row["sku"])
        if not match:
            continue
        name, model, oem, product_url = match
        row.update(
            part_name=name,
            model_reference=model,
            oem_part_number=oem,
            oem_number_status="verified",
            source_title="PharmParts product listing; Natoli current machine-parts print catalog",
            source_url=product_url,
            source_type="two-source exact name/model/OEM match",
            evidence_notes=(
                f"Exact or normalized-exact part name and model match. OEM {oem} "
                f"is independently corroborated in the Natoli catalog index at {NATOLI_CATALOGS}. "
                "No third-party replacement number is published."
            ),
            reviewed_on=REVIEWED_ON,
            approved_for_publication="yes",
        )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    content_path = ROOT / "data/part-content-audit.csv"
    with content_path.open(encoding="utf-8", newline="") as handle:
        content_rows = list(csv.DictReader(handle))
        content_fields = list(content_rows[0])
    for row in content_rows:
        match = MATCHES.get(row["sku"])
        if not match:
            continue
        name, model, oem, _ = match
        row.update(
            part_name=name,
            model_reference=model,
            identity_source="Exact name/model/OEM match in PharmParts and Natoli current print catalog",
            technical_description_status=f"Verified catalog identity; replacement part for OEM #{oem}",
            search_alias_status="Verified name, model, PGE identifier, and OEM-reference aliases",
        )
    with content_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=content_fields)
        writer.writeheader()
        writer.writerows(content_rows)


if __name__ == "__main__":
    main()
