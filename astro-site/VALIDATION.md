# Migration validation — October 13, 2026

Baseline: PharmaGlobalEng production repository at `929df015`.

- Astro 7.3.8 build: 75 pages generated.
- 75 URL paths restored, including seven directory indexes and the existing redirect page.
- All page text, headings, metadata, canonicals, JSON-LD, form controls, links, image attributes, and non-Next inline/external scripts match the baseline.
- 5,948 protected catalog/support files match byte-for-byte.
- 2,370 existing local link/asset references checked: no new missing targets.
- Homepage Next.js runtime and hydration payload removed; original navigation script retained; analytics loaded directly.
- Browser checks: desktop service dropdown expanded; narrow-layout menu opened and closed; no homepage image failures or horizontal document overflow in the measured preview viewport.
- Diagnostic wizard: fictional demo inputs produced the expected conditional results.
- Contact page: existing phone, general email and sales email links present.
- Polishing page: one H1, one main landmark, no broken loaded images; visual review preserved existing design.

This validates the migration preview, not Google indexing or ranking. No production files have been published. Source content issues, existing link problems, and technical claims were not rewritten as part of the framework conversion.

## Semantic HTML pass — October 13, 2026

- Validated 74 content pages plus one preserved redirect.
- Corrected 12 introductory card headings across four pages from H3 to H2. The original card typography is explicitly retained.
- Added missing navigation labels in 33 shared fragments and three page fragments (48 rendered navigation instances).
- Added 34 table-header scope attributes and associated seven unnamed tables with their existing visible headings.
- Added 49 missing keyboard skip links; retained existing skip links elsewhere. Every main landmark has an ID and accepts focus with `tabindex="-1"`.
- Added build checks for a single main/H1, heading-level continuity, unique IDs, resolved ARIA references, named navigation/tables, header scopes, valid list children and labeled controls.
- Visible page text and existing SEO data remain unchanged except for focus-only skip-link text. The original migration content comparison ignores only these explicitly marked new links.
