# PharmaGlobalEng Next.js migration

This folder is the staging application for migrating the existing static PharmaGlobalEng site to Next.js without changing the live `main` branch during development.

## Run locally

Requires Node.js 20.9 or newer.

```bash
cd next-app
npm install
npm run dev
```

Then open http://localhost:3000.

## Migration rules

- Preserve the current visual identity: dark background, cyan/blue/purple accents, card styling, navigation patterns, spacing, and content hierarchy.
- Preserve existing public URLs wherever possible, including current `.html` service and solution URLs.
- Preserve SEO metadata, canonical URLs, structured data, robots directives, sitemap coverage, and `llms.txt` before production cutover.
- Keep content server-rendered/static so crawlers receive meaningful HTML without requiring client JavaScript.
- Do not replace the live static site until every indexed route has a Next.js equivalent or an intentional redirect.

## Current phase

The homepage shell, shared navigation, `/services/`, and `/solutions/` hub routes have been converted. Individual legacy service/solution/component/coating/knowledge/parts pages remain on the static site and must be migrated or explicitly preserved before production cutover.
