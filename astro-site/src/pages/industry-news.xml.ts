import { escapeXml, industryNewsUrl, publishedIndustryNews } from '../lib/industry-news.js';
import { getCollection } from 'astro:content';

export const prerender = true;

export async function GET() {
  const articles = publishedIndustryNews(await getCollection('industryNews'));
  const latestDate = articles[0]?.data.publishedAt;
  const lastBuildDate = latestDate ? `<lastBuildDate>${new Date(latestDate).toUTCString()}</lastBuildDate>` : '';
  const items = articles.map((entry) => `
    <item>
      <title>${escapeXml(entry.data.title)}</title>
      <link>${escapeXml(industryNewsUrl(entry.id))}</link>
      <guid isPermaLink="true">${escapeXml(industryNewsUrl(entry.id))}</guid>
      <description>${escapeXml(entry.data.description)}</description>
      <pubDate>${new Date(entry.data.publishedAt).toUTCString()}</pubDate>
    </item>`).join('');

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>PharmaGlobalEng Industry Updates</title>
    <link>https://pharmaglobaleng.com/</link>
    <description>Source-checked industry updates and practical context for pharmaceutical tablet manufacturing and tooling.</description>
    <language>en-us</language>
    ${lastBuildDate}${items}
  </channel>
</rss>`;

  return new Response(xml, {
    headers: { 'Content-Type': 'application/rss+xml; charset=utf-8' },
  });
}
