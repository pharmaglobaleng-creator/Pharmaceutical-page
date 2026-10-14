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
