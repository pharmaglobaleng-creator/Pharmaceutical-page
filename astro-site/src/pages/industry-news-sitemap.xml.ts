import { escapeXml, industryNewsUrl, publishedIndustryNews } from '../lib/industry-news.js';

export const prerender = true;

export function GET() {
  const entries = publishedIndustryNews.map((article) => `
  <url>
    <loc>${escapeXml(industryNewsUrl(article.slug))}</loc>
    <lastmod>${escapeXml(new Date(article.modifiedAt || article.publishedAt).toISOString().slice(0, 10))}</lastmod>
  </url>`).join('');
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${entries}
</urlset>`;
  return new Response(xml, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
}
