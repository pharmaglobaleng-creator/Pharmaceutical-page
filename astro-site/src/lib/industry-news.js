import content from '../content/industry-news.json';

// Only complete, explicitly published entries can reach public outputs.
export const publishedIndustryNews = content.articles
  .filter((article) => article.status === 'published'
    && /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(article.slug || '')
    && article.title
    && article.summary
    && Number.isFinite(Date.parse(article.publishedAt || ''))
    && article.authorName
    && article.bodyHtml)
  .sort((a, b) => new Date(b.publishedAt) - new Date(a.publishedAt));

export function escapeXml(value = '') {
  return String(value).replace(/[<>&'\"]/g, (character) => ({
    '<': '&lt;',
    '>': '&gt;',
    '&': '&amp;',
    "'": '&apos;',
    '"': '&quot;',
  })[character]);
}

export function escapeHtml(value = '') {
  return String(value).replace(/[&<>"']/g, (character) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  })[character]);
}

export function jsonLd(value) {
  return JSON.stringify(value).replace(/</g, '\\u003c');
}

export function industryNewsUrl(slug) {
  return `https://pharmaglobaleng.com/industry-news/${encodeURIComponent(slug)}.html`;
}
