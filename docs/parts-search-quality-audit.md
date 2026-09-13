# Parts Search / AI Quality Audit

This report is generated from the public `parts/pge-*/index.html` detail pages.
The cleanup is intentionally conservative: it removes placeholder entity data and search-engine-directed repetition without inventing specifications, prices, OEM numbers, or compatibility claims.

- Detail pages audited: **4,512**
- Pages matched to structured source records: **4,453**
- Pages changed by normalization: **0**
- Duplicate titles after normalization: **0**
- Duplicate meta descriptions after normalization: **0**

## Before / after

| Check | Before | After |
|---|---:|---:|
| Placeholder model language | 0 | 0 |
| Titles over 72 characters | 0 | 0 |
| Meta descriptions over 175 characters | 0 | 0 |
| Missing or multiple H1 | 0 | 0 |
| Missing/wrong self-canonical | 0 | 0 |
| Detail pages marked noindex | 0 | 0 |
| Missing quote-only catalog WebPage JSON-LD | 0 | 0 |
| Legacy Product rich-result markup without commerce data | 0 | 0 |
| Invalid JSON-LD | 0 | 0 |
| More than 5 visible alias chips | 0 | 0 |
| Search-engine-directed alias copy | 0 | 0 |
| Reviewed/unverified OEM value exposed | 0 | 0 |

## Publication rules enforced

- Publish only factual part name, make, verified model, PGE SKU, and verified/catalog-supported OEM cross-reference.
- Never render `Model unresolved`, `model unconfirmed`, or similar placeholders as equipment models.
- Reviewed-only Kikusui cross-references are not labeled as verified OEM numbers.
- Keep visible/schema aliases concise; punctuation-only SKU variants and repeated OEM permutations are removed.
- Product titles and descriptions are concise and user-facing rather than stuffed with repeated compatibility phrases.
- Quote-only pages use WebPage + Thing JSON-LD aligned to visible facts and one PharmaGlobalEng Organization entity.
- Product rich-result markup is omitted because quotation-only parts have no published price, purchasable offer, or visible review.
- Incomplete or fabricated Offer data is never added.
- Exact fit, dimensions, materials, finishes, and machine configuration remain subject to engineering confirmation unless a source explicitly supports them.

## AI/GEO principle

The catalog is optimized as a set of clear, factual catalog records, not as a keyword-volume system. Each page should make the relationship between part, make, model, SKU, verified cross-reference, and compatibility basis easy to extract while avoiding unsupported claims and repetitive search phrases.
