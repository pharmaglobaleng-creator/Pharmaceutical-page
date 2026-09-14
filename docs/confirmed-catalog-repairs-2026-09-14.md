# Confirmed catalog repairs, September 14, 2026

Shared name parsing and description shortening discarded product identity, and component guidance sometimes inferred function from an assembly word or a substring. Correct the generating rules and the reviewed affected pages without regenerating the whole catalog.

## Published content scope

- 56 Cremer pages: restore the full existing part name, Cremer machine make and existing model in titles, H1s, descriptions and equipment schema. Retain PharmaGlobalEng as the independent product supplier and preserve the existing factual fields and navigation spelling.
- 28 Fette, Korsch, Manesty and Stokes pages: retain full existing product identity and size distinctions in descriptions by shortening generic text first. Preserve source records and OEM identifiers.
- 65 component pages: correct 38 Korsch/legacy Stokes guidance mismatches and remove unsupported drive-gear assumptions from 27 Fette product-control wheels. Use neutral guidance where the source name does not establish a mechanism or subtype.
- Homepage: promote the existing primary heading to H1, including its three prebuilt navigation payloads, with the same wording and styles.
- Two service pages: remove visible SEO implementation commentary and replace implementation labels with customer-facing subject labels.

Two Korsch pages overlap the metadata and guidance groups: **150 distinct HTML pages** change. Add the existing About page to the main sitemap, bringing it to 4,843 URLs. Update lastmod only for the 150 changed pages in the main sitemap and the 56 changed Cremer entries in its companion sitemap. The unchanged About page receives no invented modification date.

## Verification

- 39 focused regression/editorial tests pass; these run in the parts audit workflow.
- Full source audit: 4,789 parts HTML files, including 4,512 numbered product pages, with no structural, canonical, sitemap, reference or internal-link findings.
- Exact normalization/polishing/title workflow run twice on independent copies: all 12 commands pass, no final HTML or audit-report differences from the reviewed source, second full pass stable.
- Existing redirects, intentional noindex pages, source identifiers, disputed dimensions, duplicate-product decisions, navigation and image assets preserved.

## Indexing interpretation

Before this change, every one of the 4,842 live sitemap URLs returned HTTP 200 HTML, allowed indexing and had a matching canonical. Search Console showed a healthy host and some recently indexed pages using the same templates as waiting pages. These repairs address demonstrated content-generation defects; they do not establish that one error blocked the entire catalog or promise indexing after deployment. Broader content differentiation and source verification remain separate work requiring facts, not mass-generated filler.
