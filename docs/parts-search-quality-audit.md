# Parts Search / AI Quality Audit

This report covers the public individual part landing pages at `parts/pge-*/index.html`. The cleanup is intentionally conservative: it removes placeholder entity data and search-engine-directed repetition without inventing specifications, prices, OEM numbers, or compatibility claims.

## Coverage and final status

- Detail pages audited: **4,307**
- Pages matched to structured source records: **4,307**
- Pages changed in the main normalization pass: **4,307**
- Pages polished for complete user-facing descriptions and residual placeholder cleanup: **4,307**
- Unique part-page titles after final validation: **4,307 / 4,307**
- Duplicate title groups after final validation: **0**
- Duplicate meta descriptions after final validation: **0**
- Critical quality gate: **PASS**

## Initial audit → final state

| Check | Initial | Final |
|---|---:|---:|
| Placeholder model language | 55 | 0 |
| Titles over 72 characters | 2,381 | 0 |
| Meta descriptions over 175 characters | 1,485 | 0 |
| Missing or multiple H1 | 0 | 0 |
| Missing/wrong self-canonical | 0 | 0 |
| Detail pages marked noindex | 0 | 0 |
| Missing Product JSON-LD | 0 | 0 |
| Invalid JSON-LD | 0 | 0 |
| More than 5 visible alias chips | 2,042 | 0 |
| Search-engine-directed alias copy | 2,307 | 0 |
| Reviewed/unverified OEM value exposed as an OEM reference | 626 | 0 |

A separate title-uniqueness gate found **1 duplicate title group** after the first normalization and corrected both affected pages. The final title check confirms all 4,307 titles are unique and no longer than 72 characters.

A final copy-quality pass also confirms every part page has a complete meta description no longer than 175 characters and no residual phrases such as `Model unresolved`, `model unconfirmed`, `model unspecified`, or `model to be confirmed`.

## Publication rules enforced

- Publish only factual part name, make, verified model, PGE SKU, and verified/catalog-supported OEM cross-reference.
- Never render internal placeholder values as equipment models.
- Reviewed-only Kikusui cross-references are not labeled or structured as verified OEM numbers.
- Keep visible and schema aliases concise; punctuation-only SKU variants and repeated OEM permutations are removed.
- Product titles and descriptions are concise and user-facing rather than stuffed with repeated compatibility phrases.
- Product JSON-LD is aligned to visible facts and points to the PharmaGlobalEng Organization entity with a logo.
- Incomplete or fabricated Offer data is never added; quotation-only parts do not receive invented prices.
- Exact fit, dimensions, materials, finishes, and machine configuration remain subject to engineering confirmation unless a source explicitly supports them.
- Source uncertainty is represented as uncertainty; the system does not infer a machine model or OEM number merely from a URL, folder name, or nearby catalog record.

## AI / GEO principle

The catalog is optimized as a set of clear product entities, not as a keyword-volume system. Each page should make the relationship between part, make, verified model, PGE SKU, verified cross-reference, and compatibility basis easy to extract while avoiding unsupported claims, repetitive search phrases, and scaled filler content.

## Persistent safeguards

The repository now runs the parts search-quality workflow whenever relevant part HTML or source data changes. It normalizes entity data, polishes user-facing metadata, enforces unique concise titles, verifies Product JSON-LD/canonicals/H1/indexability, rejects unverified OEM exposure, and fails the build when a critical issue remains.
