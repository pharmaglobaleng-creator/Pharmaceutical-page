import { escapeXml, industryNewsUrl, publishedIndustryNews } from '../lib/industry-news.js';
import { getCollection } from 'astro:content';

export const prerender = true;

export async function GET() {
  const articles = publishedIndustryNews(await getCollection('industryNews'));
  const entries = articles.map((article) => `
  <url>
    <loc>${escapeXml(industryNewsUrl(article.id))}</loc>
    <lastmod>${escapeXml(new Date(article.data.publishedAt).toISOString().slice(0, 10))}</lastmod>
  </url>`).join('');
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${entries}
</urlset>`;
  return new Response(xml, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
}
