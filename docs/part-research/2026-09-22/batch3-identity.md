# Batch 3 identity and duplicate evidence

Research date: 2026-09-22. No site edits. Parent reports MAN1102 freshly confirmed crawled-not-indexed; other candidates were awaiting inspection when assigned.

Primary evidence: [Natoli original Manesty replacement-parts catalog, version 022018](https://natoli.com/wp-content/uploads/2018/03/Manesty-Tablet-Press-Replacement-Parts-Catalog.pdf). Source identities independently checked against repository `data/manesty-parts.csv`.

| PGE page | Verified catalog identity | Location |
|---|---|---|
| https://pharmaglobaleng.com/parts/pge-man-1102/ | MKI wear-plate insert; Upper Cam Tracks; MB1-609; OEM 39609 | Page 110 |
| https://pharmaglobaleng.com/parts/pge-man-0575/ | D3B new-style take-out plate; Upper Cam Tracks; MD3-16/1; OEM unavailable | Page 73 |
| https://pharmaglobaleng.com/parts/pge-man-0147/ | BB3B lower-punch retainer; Turret Hardware; M-519; OEM 38519 | Page 42 |

## Distinctions and duplicate treatment

- MAN1102 has no same-catalog-ID duplicate in current PGE CSV. The insert is distinct from complete wear plates MB1-06 / 39606 and MB1-07 / 39607. Catalog adjacency does not establish which plate receives the insert or its assembly geometry. Do not claim a complete plate is included.
- MAN0575 duplicates MAN0520's catalog identity, listed for D3A on page 69. Keep this in the technical duplicate queue until PGE physical SKU equivalence is confirmed. OEM 36016 belongs to MD3-16, not the new-style MD3-16/1. Do not fill the missing OEM using that neighboring entry.
- MAN0147 shares M-519 / 38519 with MAN0047 (B3B), MAN0249 (BB4), MAN0514 (D3A), and MAN0568 (D3B). These are strong cross-model catalog duplicate candidates. No PGE drawing/revision equivalence established. Distinct nearby spring M-518 / 38518 and screw M-69 / 39690 must not be described as included.

Exact public queries completed separately before proposed edits: `Manesty "39609" "INSERT"`; `Manesty "MD3-16/1"`; `Manesty "38519" "retainer"`. Numeric-only unrelated results excluded. Exact catalog entries read directly in the primary PDF.

No dimensions, materials, tolerances, certifications, assembly instructions or maintenance intervals verified. Preserve PGE identifiers/images. Same catalog identity supports duplicate investigation, not an immediate redirect or invented cross-model physical compatibility. MAN1102 supports a short evidence-grounded page; 0575/0147 should not receive padded prose to distinguish repeat catalog records.
