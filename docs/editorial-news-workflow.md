# PharmaGlobalEng editorial news workflow

Use this workflow when PharmaGlobalEng selects an industry news item and wants to develop a useful, original technical article from it. This is an editorial aid, not an automated news feed or auto-publishing system.

## What to provide for each article

- The source URL and publisher.
- The article date and the date of the event, if different.
- Your own short summary of the development and why it may matter to tablet manufacturing.
- Any primary sources (regulator notice, manufacturer release, standard, study, or technical document) that support the key facts.
- The specific PharmaGlobalEng service or component category that is genuinely relevant, if any.
- A human editor to confirm sources, attribution, and company claims before publication. Use a qualified technical reviewer when the article makes engineering or operating recommendations.

Do not paste a full copyrighted article when a link and short factual notes will do. Do not use an article as a template for a sentence-by-sentence rewrite.

## Reusable drafting brief

```text
You are helping prepare a source-checked PharmaGlobalEng technical news article for pharmaceutical manufacturing, tablet compression, tooling, coatings, maintenance, or replacement parts.

I will provide a news source, my notes, and any primary references. Do not browse or invent additional facts unless I explicitly ask you to research. Do not rewrite the source article paragraph by paragraph. Use it to identify the development, then create a genuinely original article that explains the verified facts and their practical implications for tablet manufacturing.

Before drafting:
1. Separate directly supported facts from interpretation and unknowns.
2. Flag unsupported claims, missing primary references, uncertain dates, and any proposed PharmaGlobalEng experience, capability, credential, or product claim that I have not verified.
3. If the source does not support a useful technical conclusion, recommend not publishing rather than padding the article.

Draft requirements:
- Give one accurate, descriptive H1 and a concise opening that states what happened, when, and why a manufacturing reader may care.
- Use a clear H2/H3 hierarchy, short paragraphs, and a short “What manufacturers should verify” section where useful.
- Distinguish source facts from analysis. Add inline links close to the factual claims they support. Prefer primary sources for regulatory, scientific, standards, or manufacturer statements.
- Explain practical implications only when supported. Do not imply that a reported change automatically affects a specific press, formulation, tooling setup, compliance status, or production outcome.
- Use one modest call to action only when the selected PharmaGlobalEng service is directly relevant. Never suggest an unverified endorsement, authorization, stock position, compatibility, guaranteed result, or service capability.
- Do not add fabricated quotes, statistics, case studies, credentials, “50 years” claims, or claims that an item is breaking/current without a verified date.
- Avoid keyword stuffing, repetitive location or service mentions, and generic promotional filler.
- Include the confirmed author attribution; do not invent a person or qualification. Do not imply technical review unless it occurred.
- End with a source list and an editor checklist of claims that still need human confirmation.

Return:
A. Draft article in clean HTML suitable for the existing Astro page body fragment.
B. Proposed SEO title and meta description as plain text (not YAML frontmatter).
C. Proposed slug, canonical URL path, and up to 5 topical tags.
D. A claim-to-source table: claim, source URL, and whether it is fact, interpretation, or needs verification.
E. A short “publish / revise / do not publish” recommendation with reasons.

Do not create files, add schema, submit URLs for indexing, or publish unless I explicitly ask after reviewing the draft.

News source URL/publisher/date:
[Paste here]

My summary and why it matters:
[Paste here]

Primary references:
[Paste URLs or write “none supplied”]

Relevant PharmaGlobalEng service/category (if known):
[Paste here or write “none”]

Technical reviewer name/role (if needed and confirmed):
[Paste here or write “not applicable”]
```

## Site implementation notes

Industry updates are Markdown files in `astro-site/src/content/news/`. Add one `.md` file with the validated frontmatter fields, then set `status: "published"` only after a human editor checks source links, factual claims, and company claims. Astro's shared dynamic route renders the Markdown with the site's template, and the build updates the homepage card, RSS feed, and supplemental sitemap. Use qualified technical review for engineering recommendations; do not imply a review that did not occur.

The sitemap helps discovery but does not guarantee crawling or indexing. Confirm the public URL after deployment, then check indexing separately in Search Console.

## News discovery outputs

The Astro source has an RSS 2.0 feed at `/industry-news.xml` and a supplemental standard sitemap at `/industry-news-sitemap.xml`. The homepage advertises the feed and shows up to three recent news cards only when a record is published. Add a corresponding `Sitemap:` line to `robots.txt` when deploying these routes. These are discovery aids; none guarantees crawling, indexing, or ranking.

News records are Markdown files in `astro-site/src/content/news/`, validated by the Astro content collection schema. Only entries with `status: "published"` are emitted as pages, feed items, sitemap URLs, or homepage links. Keep drafts at `status: "draft"` until a human editor has checked sources, factual claims, and company statements. Do not use a Google News sitemap or the Google Indexing API as an instant-indexing shortcut.

During deployment, publish generated article pages plus both XML outputs, and separately verify that the main sitemap and article URLs are publicly accessible. Search Console URL inspection may request a crawl but cannot guarantee indexing.
