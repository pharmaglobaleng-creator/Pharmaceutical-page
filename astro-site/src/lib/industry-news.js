export function publishedIndustryNews(entries) {
  return entries
    .filter(({ data }) => data.status === 'published')
    .sort((a, b) => new Date(b.data.publishedAt) - new Date(a.data.publishedAt));
}

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
