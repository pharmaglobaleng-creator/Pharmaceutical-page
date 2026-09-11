# Pharma Global visitor reporting

Production pages load `/assets/js/pge-analytics.js` for the **Pharma Global
Website** GA4 stream (`G-1ES31F0R1F`, property `552678192`). The loader runs only
on `pharmaglobaleng.com` and `www.pharmaglobaleng.com`, and initializes once per
document. Google Signals and advertising personalization are disabled. GA4's
enhanced measurement handles page views and browser-history changes; do not add
a second manual page-view listener.

The root Next.js layout and legacy catalog templates include this loader.
After creating or regenerating other static pages, run:

```sh
python3 scripts/apply_sitewide_analytics.py
python3 scripts/apply_sitewide_analytics.py --check
```

The installer preserves every original page byte and skips ownership
verification files and immediate redirects. The existing hosting setup,
canonical URLs, sitemap, content, and images are unchanged.

In Google Analytics, use **Reports → User attributes → Demographic details**
and select **City** or **Region** (states for US visits). Filter by **Session
source / medium = google / organic** when examining organic Google visits.
Locations are approximate; visits are not the same metric as Search Console
clicks. Reporting begins after installation and cannot recreate historical
visitors. Use Realtime to verify initial data collection.
