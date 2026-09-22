# Batch 2: exact identity evidence

Researched 2026-09-21. No site edits. Parent reports MAN1050 freshly crawled-not-indexed; MAN0394 and MAN0966 pending inspection when research began.

Primary source: [Natoli original Manesty catalog, version 022018](https://natoli.com/wp-content/uploads/2018/03/Manesty-Tablet-Press-Replacement-Parts-Catalog.pdf). This independently corroborates catalog associations, not measured PGE component equivalence.

| URL | Verified association | Primary catalog |
|---|---|---|
| https://pharmaglobaleng.com/parts/pge-man-1050/ | MKI, Product Control, intergear-stud component M-777, OEM 39777 | Page 107; index page 18 |
| https://pharmaglobaleng.com/parts/pge-man-0394/ | Betapress, Product Control, thickness-adjusting shaft M4-FG1-45, OEM unavailable | Page 60; index page 8 |
| https://pharmaglobaleng.com/parts/pge-man-0966/ | MKI, Pressure Rolls & Components, lower pressure roll including bearing MB1-83/WB, OEM 39383/1 | Page 101; index page 17 |

## Exact-part distinctions

- MAN1050: Keep distinct from intermediate gear stud M-773 / 39773 and feeder intergear bushing M-778 / 39778. Do not infer thread dimensions, material or gear assembly arrangement from catalog adjacency.
- MAN0394: No OEM number found. M4-FG1-45 is Natoli's identifier, not an OEM number. Adjacent handwheel M4-FG1-48 is a separate item, not established as included.
- MAN0966: Preserve bearing-inclusive wording and the /1 OEM suffix. Plain MB1-83 / 39383, MD1-81/WB / 39381/1, and complete MB1-83/WB/A assembly are distinct catalog records. Bearing specification and assembly contents remain unverified.

## Duplicate screening

The repository `data/manesty-parts.csv` has only one occurrence of each exact catalog number in this batch. No same-catalog-ID duplicate PGE page was found. The original catalog repeats M-777 and MB1-83/WB under MKII/IIA, which does not establish additional PGE-page duplication or authorize expanding PGE compatibility. Similar neighboring parts are not duplicates merely because their names overlap. No consolidation is supported by this batch check.

## Public-web exact searches completed

- `Manesty "39777" stud`
- `Manesty "M4-FG1-45"`
- `Manesty "39383/1"`

The search results were cross-checked against exact entries in Natoli's original PDF. Numeric-only unrelated results were excluded. OEM unavailable remains unavailable for MAN0394; no dimensions, tolerances, materials, certifications, torque values, service intervals or detailed procedures established for these PGE items. Keep PGE identifiers and existing images.

Validation correction: the catalog index points to page 106 for intermediate gear stud 39773, but the actual printed detail page is 107. The published comparison omits that ambiguous page reference.
