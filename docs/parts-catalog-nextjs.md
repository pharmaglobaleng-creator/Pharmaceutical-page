# Next.js replacement-parts catalogs

This migration changes the Parts Store and the five manufacturer catalog browsing pages. Existing individual product pages, product URLs, homepage HTML, and original image bytes are preserved.

## Data and image preservation

The initial build imports actual product cards from the existing five HTML catalogs into `next-app/data/parts-catalog.json`. This durable data snapshot is the input for subsequent builds. Do not delete it and attempt to re-import a paginated page. It preserves existing PGE numbers, model labels, OEM-reference text, image URLs and detail-page destinations. It does not independently certify existing OEM or compatibility claims.

No catalog source images are redrawn or replaced. Resized WebP derivatives are generated in a separate `assets/images/catalog-thumbs/` directory. Missing photos remain an explicit unavailable-photo state. The original product image remains the image `src` and original detail-page image.

## Browsing and SEO

- Manufacturer catalogs and model landing pages have real addresses.
- Pagination contains at most 50 part cards in the initial HTML and uses ordinary links with self-referencing canonical URLs.
- The existing product URLs stay intact. The current individual detail pages are not rebuilt by this migration.
- Catalog metadata, CollectionPage/BreadcrumbList/ItemList JSON-LD and sitemap entries are generated from the visible records.
- Search downloads the complete selected manufacturer's search index only on the search page. Search results are noindex and excluded from the sitemap.
- Unresolved or generic model labels do not generate new model landing pages.
- The new quote cart shares the existing `pge-parts-quote-cart-v1` storage format with legacy detail pages; no payment gateway is introduced.

## Build and validation

From `next-app/`, run `npm ci`, then `npm run build:safe`. For browser tests run `npx playwright install chromium` and `npm run test:catalog`. Serve `out/` as a static site. The build retains original public files without overwriting new catalog routes with old catalog HTML. It preserves the existing homepage and keeps both old and new content-hashed runtime assets.

`npm run stage:catalog` stages only the validated catalog routes, new hashed runtime assets, search data, thumbnails, and updated sitemap into the repository's static-site root. It does not commit or publish anything itself. Commit and review the generated output before merging.

The workflow on `nextjs-parts-catalog` builds, tests and commits generated output to that branch only. It never pushes directly to main. Publishing requires merging the reviewed branch.

Checks cover product counts, photo/URL/name preservation, original-image hashes, initial HTML, internal links, canonical URLs, sitemap coverage, parseable schema and browser behavior. These tests are not certification of Google's indexing, rankings or rich-result eligibility.
