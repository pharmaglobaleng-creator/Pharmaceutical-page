# Batch 3 — SEO and duplicate/source review

Date: 2026-09-22. No site edits. Parent freshly confirmed MAN1102 as Crawled - currently not indexed; MAN0575 and MAN0147 eligibility pending separately.

## Exact public research

Queries executed before editing:
- `"Manesty" "39609"`
- `"Manesty" "D3B" "TAKE OUT PLATE" "NEW"`
- `"Manesty" "38519" "BB3B"`

Primary verification: [Natoli Manesty catalog, version 022018](https://natoli.com/wp-content/uploads/2018/03/Manesty-Tablet-Press-Replacement-Parts-Catalog.pdf).

| Record | Verified catalog identity |
|---|---|
| MAN1102 | MKI insert in wear plate, MB1-609, reference 39609, Upper Cam Tracks, page 110 |
| MAN0575 | D3B take-out plate, new style, MD3-16/1, OEM N/A, Upper Cam Tracks, page73 |
| MAN0147 | BB3B lower punch retainer, M-519, reference 38519, Turret Hardware, page42 |

The insert is separately listed from slotted/unslotted wear plates 39607/39606. D3B's ordinary take-out plate is MD3-16/36016, distinct from the new-style entry. The retainer spring M-518/38518 and screw M-69/39690 are separate from the retainer. Catalog adjacency does not prove parts mate or are sold together. This source establishes replacement-catalog identities, not PGE manufacturing specifications.

## Technical/duplicate findings

All three local HTML pages currently have absolute self-canonicals and index/follow meta robots. Inspect Google-selected canonicals before treating non-indexing as a content problem.

MAN1102: local exact-reference search found no second 39609 record. The neighboring wear-plate records are separate component entries, not duplicates.

MAN0575: `/parts/pge-man-0520/` is the D3A new-style plate record. The catalog repeats the same MD3-16/1 identification across these model sections. Potential same-product model duplication warrants checking; do not manufacture different specifications to force unique copy. `/parts/pge-man-0574/` is the separate D3B ordinary-style plate.

MAN0147: four other local pages share 38519: MAN0047 (B3B), MAN0249 (BB4), MAN0514 (D3A), MAN0568 (D3B). Their catalog code is also M-519. Treat this as a potential duplicate-product cluster; determine whether one physical offer is being repeated across models. If GSC reports duplicate/canonical exclusion, handle the architecture rather than producing model-name-swapped paragraphs. Any consolidation must preserve PGE identifiers and confirmed model relationships.

## MAN1102 — ready for scoped content improvement if GSC eligible

URL: https://pharmaglobaleng.com/parts/pge-man-1102/
File: `parts/pge-man-1102/index.html`

Inferred intent: identify the insert by 39609 and distinguish it from an entire wear plate.

- Title: `39609 Wear Plate Insert | Manesty MKI | PGE-MAN-1102`.
- Meta: `PGE-MAN-1102 insert in wear plate, cataloged for Manesty MKI under reference 39609. Confirm the insert and existing wear-plate arrangement before quotation.`
- Retain exact “INSERT IN WEAR PLATE” name in H1 or identity details.
- Unique H2: “Insert versus complete wear-plate records.” Link MAN1098 and MAN1099 as separately cataloged plate forms, explicitly avoiding a claim that this insert fits both.
- Add `/parts/manesty/mki/` to visible navigation and matching BreadcrumbList.
- Do not infer material, hardness, slot geometry, retention method, wear threshold or service procedure.

## MAN0575 — identity/duplicate triage first

URL: https://pharmaglobaleng.com/parts/pge-man-0575/
File: `parts/pge-man-0575/index.html`

Inferred intent: identify the new-style D3B take-out plate, particularly where the OEM reference is absent.

- Title: `New-Style Take-Out Plate | Manesty D3B | PGE-MAN-0575`.
- Meta: `PGE-MAN-0575 new-style take-out plate for the Manesty D3B catalog application. OEM reference is not supplied; confirm the installed plate version.`
- Distinguish the ordinary-style MAN0574 record. Never transfer 36016 to the new-style page merely because both are take-out plates.
- “New style” is a catalog designation, not proof of a currently new design, model-year cutoff or retrofit compatibility.
- If publishing MD3-16/1, label it Natoli's replacement-catalog code, not OEM or PGE MPN.
- Add `/parts/manesty/d3b/` where the page remains independently indexable after duplicate review.
- Do not invent dimensions, attachment instructions, punch-removal sequence or safety procedure.

## MAN0147 — potential duplicate cluster

URL: https://pharmaglobaleng.com/parts/pge-man-0147/
File: `parts/pge-man-0147/index.html`

Inferred intent: quote the lower punch retainer by 38519 for the BB3B catalog application.

- If retained as a justified model page, title: `38519 Lower Punch Retainer | Manesty BB3B | PGE-MAN-0147`.
- Meta: `PGE-MAN-0147 lower punch retainer, cataloged for Manesty BB3B under reference 38519. Confirm the installed retainer before quotation.`
- Useful distinction: retainer versus separately identified spring and screw. Verify local related-page identifiers before adding anchors; do not imply a complete supplied assembly.
- Add `/parts/manesty/bb3b/` and matching breadcrumbs where independently indexable.
- Do not assert spring force, adjustment, retention capacity, thread details or replacement instructions.
- Avoid expanding five same-item model pages with generic prose. Use GSC evidence and confirmed offer identity to decide canonical/consolidation work.

## Shared changes/checks

Preserve assets, PGE SKUs and cart attributes. Maintain representative-image disclosure in alt text. Keep Product name/description synchronized with visible copy; omit unresolved MPNs and unsupported manufacturer/offers/ratings. Label OEM references accurately. Short identification text is justified; extensive technical or maintenance text is not supported by these searches.

Validate local links, headings, canonical, source citation, JSON-LD, unchanged image paths and rendered layout. Indexing is not guaranteed. Guidance: [Google canonicalization](https://developers.google.com/search/docs/crawling-indexing/canonicalization), [titles](https://developers.google.com/search/docs/appearance/title-link), [crawlable links](https://developers.google.com/search/docs/crawling-indexing/links-crawlable), [structured-data policies](https://developers.google.com/search/docs/appearance/structured-data/sd-policies).
