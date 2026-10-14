# PharmaGlobalEng Astro migration — non-parts pages

Review preview only. Production HTML and the parts store are not changed by this branch.

## Scope

75 existing public HTML pages (including the existing coatings redirect), excluding both Google verification files, all `parts/` pages, the Next.js catalog application, and catalog data. URLs and page design are preserved. `src/content/manifest.json` is the explicit migration allowlist.

Astro renders the pages through `Document.astro` and `ContentPage.astro`. Editable per-page HTML fragments live in `src/content/pages/`; repeated headers, footers and styles live once in `src/content/shared/`. The manifest retains each page's HTML language and body attributes. All fragments are trusted source files, not visitor input.

The homepage no longer loads Next.js JavaScript or React hydration data. Its existing CSS remains available in `_next/` because the independent parts application still needs that directory. The existing native navigation script and a direct deferred analytics script remain active.

## Build and review

Use Node 22 or newer supported by the pinned Astro version.

```sh
cd astro-site
npm ci
ASTRO_TELEMETRY_DISABLED=1 npm run build
npm run preview
```

Build stages the unchanged public assets and catalog from the repository, renders Astro pages, restores the seven directory-index output paths, then validates them. `public/` and `dist/` are generated and ignored. Never edit them.

A production-like local alternative is `python3 -m http.server 8791 --bind 127.0.0.1 --directory dist`.

## Editing

Find the desired public path in `src/content/manifest.json`. Edit its named head/body fragment. Shared fragment markers expand in the layout, and a change to a shared fragment affects all pages referencing it. `src/content/shared-index.json` lists fragment type and consuming pages. Keep JSON-LD consistent with visible content. The route files in `src/pages/` make every public page explicit.

The migration validator compares content and metadata against existing production files. Intentional content changes should be handled separately from migration so regressions remain easy to detect. Existing scripts that write root HTML are not yet redirected to Astro; use this project as the source of truth only after rollout is approved and those workflows are reconciled. The parts generators remain unchanged.

## Checks

- All 75 original output paths must exist.
- Visible text, headings, metadata, canonical links, schema, forms, links and image attributes must match the existing site.
- The catalog, catalog data, `_next` assets, sitemaps, robots, CNAME and verification files must remain byte-identical.
- The homepage must not load the Next.js runtime.
- Manual preview checks cover navigation, narrow layout, contact links, FAQ expansion and the engineering diagnostic tool.

## Publishing later

Do not publish this branch as the Pages root: it deliberately retains the existing root files. Once the preview is approved, build and copy only the 75 allowlisted `dist` HTML files to their original repository paths. Keep the `parts/`, `_next/`, catalog data and shared asset files untouched. Review the final diff, disable/reconcile the old manual Next.js homepage deployment before future use, then publish through the existing GitHub Pages setup. No automatic deployment has been enabled by this migration.

Recheck origin/main before staging; changes after the migration baseline must be carried forward. Rollback is the reverse of the eventual HTML-only publication commit.

## Semantic structure

`validate-semantics.mjs` audits all content pages at build time; the original redirect is excluded. Keep one H1 and main landmark per content page. Use headings by section depth, label navigation purpose, and give table headers the correct scope. Main landmarks use `tabindex="-1"` so skip links can move keyboard focus without adding a stop to the tab sequence. The shared document layout contains the focus-only skip-link styling and a narrow card-heading compatibility rule; it does not change the site-wide assets or the parts store.
