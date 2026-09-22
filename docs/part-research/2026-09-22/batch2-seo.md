# Batch 2 SEO, exact-identifier research and duplicate checks

Date: 2026-09-22 UTC. No site edits made. Parent freshly confirmed MAN1050 as Crawled - currently not indexed; remaining eligibility handled separately.

## Search record and primary verification

Before any edits, searched public web for `"Manesty" "39777"`, `"Manesty" "M4-FG1-45"`, and `"Manesty" "39383/1"`. Cross-checked the [Natoli-hosted catalog](https://natoli.com/wp-content/uploads/2018/03/Manesty-Tablet-Press-Replacement-Parts-Catalog.pdf), version 022018.

| PGE page | Source identification | Source location |
|---|---|---|
| MAN1050 | STUD IN INTER GEAR STUD; M-777; OEM 39777; Product Control | MKI, page 107 |
| MAN0394 | TABLET THICKNESS ADJUSTING SHAFT; M4-FG1-45; OEM N/A; Product Control | BETAPRESS, page 60 |
| MAN0966 | LOWER PRESSURE ROLL W/BEARING; MB1-83/WB; OEM 39383/1 | MKI, page 101 |

The stud's unusual wording is present in the source. A nearby intermediate-gear stud uses M-773/39773 and is a different entry. The roll without bearing is MB1-83/39383; another lower-roll-with-bearing entry is MD1-81/WB/39381/1. Preserve suffixes. Natoli is a replacement manufacturer; its catalog proves its own listing, not PGE specifications or physical equivalence.

## Technical and duplicate audit

Bounded local search across `work/site/parts/pge-man-*/index.html` found only MAN1050 containing 39777 and only MAN0966 containing 39383/1. The exact thickness-adjusting-shaft name appears only in MAN0394. No local same-reference duplicate was found. This does not establish absence of duplicates outside these files or Google's selected canonical.

All three current pages have one self-canonical and index/follow meta robots. The copies largely repeat the same catalog-verification narrative. Model-level breadcrumbs and links are absent despite existing model hubs. No canonical rewrite is justified by this inspection.

## MAN1050

URL: https://pharmaglobaleng.com/parts/pge-man-1050/
File: `parts/pge-man-1050/index.html`

Inferred intent: identify and quote this particular MKI stud by 39777, not a measured keyword-volume claim.

- Suggested title: `39777 Stud in Inter Gear Stud | Manesty MKI | PGE-MAN-1050`.
- Suggested meta: `PGE-MAN-1050 identifies the Manesty MKI catalog stud under reference 39777. Confirm the original stud and mounting details before quotation.`
- Retain the exact unusual designation in H1 or the visible identity table. Do not “correct” it to intermediate gear stud; that can collapse two identifiers.
- Unique content: explain identification by the exact reference and differentiation from nearby similarly named parts. Link the confirmed local feeder inter-gear bushing record `/parts/pge-man-1051/` only as a separate catalog record, without claiming a mating relationship.
- Add `/parts/manesty/mki/` to visible navigation and matching BreadcrumbList.
- Do not invent thread form, stud dimensions, load rating or fastening torque. A short identity-focused page is proportionate to the available evidence.

## MAN0394

URL: https://pharmaglobaleng.com/parts/pge-man-0394/
File: `parts/pge-man-0394/index.html`

Inferred intent: find the BETAPRESS tablet-thickness adjusting shaft when the OEM number is unavailable.

- Current title is already precise. A readable variation: `Tablet Thickness Adjusting Shaft | Manesty BETAPRESS | PGE-MAN-0394`.
- Suggested meta: `PGE-MAN-0394 tablet-thickness adjusting shaft for the Manesty BETAPRESS catalog application. OEM reference is not supplied; confirm the shaft before quotation.`
- Unique section: explain the missing OEM reference and identify the shaft separately from the tablet-thickness hand wheel, local record `/parts/pge-man-0395/`. Do not promise the two fit together solely from neighboring catalog entries.
- If publishing M4-FG1-45, label it explicitly as Natoli's catalog reference. Never encode it as Manesty OEM number or PGE MPN.
- Add `/parts/manesty/betapress/` in body/model details and BreadcrumbList.
- Do not infer gearing, adjustment range, turns-per-thickness, calibration steps, or that this individual shaft directly controls a specific pressure setting. No OEM value belongs in structured data while unresolved.

## MAN0966

URL: https://pharmaglobaleng.com/parts/pge-man-0966/
File: `parts/pge-man-0966/index.html`

Inferred intent: quote the lower pressure roll supplied with bearing under the complete 39383/1 reference.

- Suggested title: `39383/1 Lower Pressure Roll with Bearing | Manesty MKI | PGE-MAN-0966`.
- Suggested meta: `PGE-MAN-0966 lower pressure roll with bearing, cataloged for Manesty MKI under 39383/1. Distinguish the bearing-equipped record before quotation.`
- Use “with bearing” prominently in H1; retain the full suffix in all reference fields and structured data.
- Unique content: distinguish `/parts/pge-man-0965/` (39383 lower roll without the bearing designation) and `/parts/pge-man-0968/` (different 39381/1 bearing-equipped lower roll). These are comparison links, not substitutes.
- Add `/parts/manesty/mki/` and consistent breadcrumbs.
- A [Natoli pressure-roll article](https://natoli.com/pressure-roll-promo/) discusses pitting/skidding and tablet-quality consequences generally. It is not a specification or maintenance procedure for this exact 39383/1 assembly. Avoid attaching an inspection interval, acceptable wear limit, lubrication selection or replacement procedure to this SKU without exact documentation.

## Shared implementation checks

Preserve PGE identifiers, source images, responsive image variants, quote-cart attributes and current self-canonicals. Keep representative-visualization wording in alt text; it must not suggest OEM photography or verified dimensions. Replace editorial assurances with useful part-identification information. Remove unverified Product manufacturer claims where PGE's role is only established as supplier. Retain truthful brand/SKU and clearly labeled OEM-reference properties. Match Product name/description to visible content and BreadcrumbList to visible navigation; do not fabricate offers/ratings to qualify for rich results.

Check links and fragments, one H1/canonical, JSON parsing, original asset paths and rendering after editing. Confirm GSC reason/canonical per page before release. No quantity of text guarantees indexing.

SEO sources: [Google titles](https://developers.google.com/search/docs/appearance/title-link), [crawlable links](https://developers.google.com/search/docs/crawling-indexing/links-crawlable), [canonicalization](https://developers.google.com/search/docs/crawling-indexing/canonicalization), [structured-data policies](https://developers.google.com/search/docs/appearance/structured-data/sd-policies).
