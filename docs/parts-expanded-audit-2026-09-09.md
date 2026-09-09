# Expanded parts HTML audit — September 9, 2026

## Scope and provenance

Baseline main commit: `39ee3c4296f589aa84a0709e2917306f9c1f65ad`.
The earlier detail-page normalization was already present. This review independently checked it and extended coverage beyond product pages; it does not claim all earlier cleanup as new work.

| Inventory | Count |
|---|---:|
| All HTML files under parts | 4,566 |
| Product detail pages | 4,307 |
| Other parts HTML, including categories, pagination and support | 259 |
| URL entries in the main sitemap | 4,619 |
| Page entries in the image sitemap | 4,148 |

These are file and sitemap counts, not Google indexed-page counts.

## Corrections

### Incorrect manufacturer in legacy Stokes records

Forty-seven three-digit Stokes records were incorrectly labeled Korsch in the OEM audit CSV. The original part-content audit and the source documents' titles/URLs identify Stokes. Corrected the manufacturer field, product titles, headings, visible references and Product structured data.

Kept six existing source-approved OEM mappings and their supported machine-model references. Did not manufacture new OEM numbers or convert an unapproved value into a verified one. Removed machine-model assumptions derived only from image folders from the forty legacy Stokes records whose exact model remains unresolved. The existing BB2 reference on the additional record with an unresolved OEM mapping was retained.

### OEM references inconsistent between detail and catalog pages

Nine Kikusui OEM values were already withheld from detail-page metadata but still appeared in public catalog data and cards. The source CSV marks them reviewed-only rather than verified. Replaced those public OEM assertions with “Not verified; confirm during quotation.” Eighteen rendered card occurrences and the corresponding React server payloads were corrected. Public search data and the Next.js source snapshot now agree. Original part images, part URLs and quote-cart identities were preserved.

The catalog preparation script now applies the same source-review restriction before future exports. This is a data-consistency rule, not a claim that any particular keyword count is a Google ranking factor.

### Legacy identification and navigation

Corrected the Korsch category's unsupported “verified” wording and stopped presenting “Model unresolved” as a model name. Retained its historical URL rather than guessing that its URL proves model 300 compatibility.

Added an earlier-reference directory to the existing identification page. All 96 legacy detail records are reachable through ordinary HTML links from the parts hub. The prior scan had 12 records with no static inbound parts link, and 96 without a static path from the parts hub; both counts are now zero.

Of these 96 legacy records, 90 have no approved OEM mapping, including 89 with unresolved exact machine models. Added a visible review notice to those 90 records. The other six mappings remain source-approved. Lack of an approved OEM mapping is not proof that a component is invalid. No pages were deleted, redirected, or newly marked noindex.

## Automated validation results

All 4,566 parts HTML files pass the implemented checks for title and description presence, duplicate active titles/descriptions, one H1, expected canonicals, valid JSON-LD, Product/SKU/URL consistency, source-file availability for images/scripts/styles, internal-link targets, static product reachability, sitemap targets, and the implemented placeholder/repetition review patterns.

No remaining findings were reported by `scripts/audit_parts_site.py` after the corrections. The fixes are idempotent: a second pass makes no changes. This is a bounded automated test result, not proof that no possible content-quality issue exists.

Source robots.txt permits Googlebot, Bingbot and OAI-SearchBot. That does not independently prove that every CDN/firewall rule allows each crawler.

Nine fresh public HTTP samples returned status 200 with matching canonical URLs before the final correction batch was published. Browser test results are recorded separately in the “Parts browser smoke tests” workflow artifact; an HTML scan alone does not establish successful browser behavior.

## Search Console sample, September 9, 2026

Nine URLs were inspected directly through the connected Google Search Console property, `https://pharmaglobaleng.com/`.

| URL path | Inspection result |
|---|---|
| /parts/ | Submitted and indexed |
| /parts/pge-kik-003/ | Submitted and indexed |
| /parts/pge-stk-017/ | Submitted and indexed |
| /parts/pge-k300-001/ | Submitted and indexed |
| /parts/pge-fet-001/ | Discovered, currently not indexed |
| /parts/pge-kor-001/ | Discovered, currently not indexed |
| /parts/pge-man-0001/ | Discovered, currently not indexed |
| /parts/pge-stk-0001/ | URL unknown to Google |
| /parts/korsch/korsch-300/ | URL unknown to Google |

This is a nine-URL sample, not the website's total index count. The indexed examples' last recorded crawls were August 23, 2026, so inspection does not prove Google has processed the current edits. Discovery or non-indexing alone is not evidence of a spam penalty.

## AI search and anti-spam approach

No keyword quotas, extra mass-produced FAQ blocks, fake prices, fabricated reviews, invented dimensions, hidden keyword text or special “AI ranking” schema were added. Existing concise identifiers were retained where useful to a purchaser.

Google's AI-features guidance applies ordinary search fundamentals: helpful visible content, crawlable links, accurate structured data and index/snippet eligibility. It does not require a special AI text file or AI-specific schema. Google does not guarantee crawling, indexing or inclusion. Google's spam policies prohibit keyword stuffing and scaled content created primarily to manipulate rankings without user value.

Official references:
- https://developers.google.com/search/docs/appearance/ai-features
- https://developers.google.com/search/docs/essentials/spam-policies
- https://developers.openai.com/api/docs/bots

## Remaining evidence requirements and limits

The original identity of every illustration, every underlying OEM cross-reference and every engineering specification has not been independently certified in this HTML audit. In particular, the 90 legacy records without approved OEM mappings require source/engineering review; do not label them verified without evidence. The other catalog records retain their existing source assertions, not a new blanket engineering certification.

No sitewide manual-actions clearance, security-issues clearance, field Core Web Vitals measurement, backlink audit, accessibility certification or guarantee of Google/AI ranking is implied. Product JSON-LD syntax validity is not the same as eligibility for a Google product rich result; quote-only pages were not given invented Offer prices to silence rich-result warnings.

Original image files, the homepage, telephone number, sitemap entries and existing indexing directives were preserved. Ongoing workflow checks flag structural or reference drift; branch-protection settings were not changed, so these checks are not claimed to be an unbypassable deployment gate.
