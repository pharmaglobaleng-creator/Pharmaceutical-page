# PGE-MAN-0888 / PGE-MAN-0642 duplicate review

Decision: **defer URL consolidation until PGE engineering/product identity is established**. Strong evidence supports duplicate catalog identity across machine-model contexts. Available evidence does not establish that both PGE SKUs represent an identical physical manufactured item or identical quotation configuration. Do not fabricate distinct engineering content to keep both pages indexed.

## Evidence compared

| Field | PGE-MAN-0642 | PGE-MAN-0888 |
|---|---|---|
| Name | Stud for guard | Stud for guard |
| Equipment | Manesty EXPRESS | Manesty MKI |
| Category | Guarding | Guarding |
| Catalog part | M-779 | M-779 |
| OEM reference | 39779 | 39779 |
| Catalog page | 78 | 96 |
| Image position | 15 | 4 |
| PGE SKU | Separate | Separate |
| Canonical in repository | Self | Self |

Repository sources: `work/site/data/manesty-parts.csv`, `work/site/data/manesty-parts-content-audit.csv`, `work/site/catalog-data/manesty.json`, and both `work/site/parts/pge-man-*/index.html` files. The “Verified” field is catalog mapping status, not dimensional equivalence: page text explicitly reserves final material, finish, dimensions and configuration for quotation review.

## Primary source confirmation

[Natoli original Manesty catalog, version 022018](https://natoli.com/wp-content/uploads/2018/03/Manesty-Tablet-Press-Replacement-Parts-Catalog.pdf) repeats M-779 / 39779 in the EXPRESS section, page 78, and MKI section, page 96. Both entries have the same component name and category. This is compelling evidence of one Natoli catalog identity used across those equipment sections. It establishes neither PGE manufacturing drawings nor PGE SKU equivalence. No revision, dimensions, finish, material or installation-interface evidence resolves that remaining issue.

## Images

Both repository images were visually inspected. Each depicts a horizontal cylindrical stud with a reduced threaded end on the same dark studio background. They are separate files with different hashes and noticeably different displayed scale. Their proportions appear similar, but neither contains dimensional reference. Both are explicitly labeled representative studio visualizations. Image differences therefore prove neither distinct physical items nor interchangeability.

- 0642 image hash: `605dd3aef8b59caa1d4e9187cbedcf9b266ffa3c24634c834125fdab7b60b35b`.
- 0888 image hash: `d36dcd6187dade685444891ffe6aa1cccd886692d61209a4a2cdc052a8e35f47`.

## Practical disposition

Classify as **technical duplicate candidate, identity confirmation outstanding**, not a page needing a longer description. Preserve both PGE identifiers and existing images. An eventual consolidation should keep both identifiers discoverable and visibly retain both supported equipment contexts; choose the destination using fresh URL inspection, existing links and product records. A redirect/canonical change now would assert equivalence beyond the PGE records reviewed.

Confirmation needed is narrow: whether PGE supplies one identical drawing/revision and quotation configuration under these two IDs, or separate model-specific configurations. No arbitrary new engineering specifications should be added to distinguish them.

Direct public-web opens of both URLs failed through the web tool, so this comparison describes repository HTML, not independently retrieved live responses. Public exact-description/OEM research was completed in the preceding Manesty identity work; the primary catalog supports the cross-model duplication. No edits made.
