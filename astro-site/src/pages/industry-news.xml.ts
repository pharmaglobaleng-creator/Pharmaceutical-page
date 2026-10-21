import { escapeXml, industryNewsUrl, publishedIndustryNews } from '../lib/industry-news.js';

export const prerender = true;

export function GET() {
  const latestDate = publishedIndustryNews[0]?.publishedAt;
  const lastBuildDate = latestDate ? `<lastBuildDate>${new Date(latestDate).toUTCString()}</lastBuildDate>` : '';
  const items = publishedIndustryNews.map((article) => `
    <item>
      <title>${escapeXml(article.title)}</title>
      <link>${escapeXml(industryNewsUrl(article.slug))}</link>
      <guid isPermaLink="true">${escapeXml(industryNewsUrl(article.slug))}</guid>
      <description>${escapeXml(article.summary)}</description>
      <pubDate>${new Date(article.publishedAt).toUTCString()}</pubDate>
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
