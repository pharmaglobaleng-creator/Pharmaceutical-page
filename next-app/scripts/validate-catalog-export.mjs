import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { load } from 'cheerio';
import { catalogData, catalogRoutes, SITE, PAGE_SIZE } from '../lib/catalog.mjs';
const app = process.cwd(), out = path.join(app, 'out');
const hash = value => crypto.createHash('sha256').update(value).digest('hex');
const data = catalogData(), routes = catalogRoutes();
const owned = new Set(routes.map(r => r.url.slice(1) + 'index.html'));
const baseline = JSON.parse(fs.readFileSync(path.join(app, '.catalog-baseline.json'), 'utf8'));
let photos = 0, legacyHtml = 0, productPages = 0;
for (const [rel, expected] of Object.entries(baseline)) {
  if (owned.has(rel)) continue;
  const file = path.join(out, rel);
  assert.ok(fs.existsSync(file), `Preserved file missing: ${rel}`);
  assert.equal(hash(fs.readFileSync(file)), expected, `Original file changed: ${rel}`);
  if (rel.startsWith('assets/images/')) photos++;
  if (rel.endsWith('.html')) legacyHtml++;
  if (/^parts\/pge-[^/]+\/index\.html$/.test(rel)) productPages++;
}
const bySku = new Map(data.parts.map(p => [p.sku,p]));
const foundPrimary = new Map();
const sizes = {};
let maxBytes = 0, maxUrl = '', checkedLinks = new Set();
for (const route of routes) {
  const rel = route.url.slice(1) + 'index.html';
  const file = path.join(out, rel);
  assert.ok(fs.existsSync(file), `Generated route missing: ${rel}`);
  const source = fs.readFileSync(file, 'utf8'), $ = load(source), bytes = Buffer.byteLength(source);
  assert.ok(source.includes('data-pge-catalog="v2"'), `Missing catalog marker: ${rel}`);
  assert.equal($('h1').length, 1, `Expected one H1: ${rel}`);
  assert.equal($('link[rel="canonical"]').length, 1, `Expected one canonical: ${rel}`);
  assert.equal($('link[rel="canonical"]').attr('href'), SITE + route.url, `Wrong canonical: ${rel}`);
  assert.ok(bytes < 1900000, `Oversized HTML: ${rel} ${bytes}`);
  if (bytes > maxBytes) { maxBytes = bytes; maxUrl = route.url; }
  const types = [];
  for (const script of $('script[type="application/ld+json"]').toArray()) {
    const block = JSON.parse($(script).text());
    for (const entity of block['@graph'] || [block]) types.push(entity['@type']);
  }
  if (route.kind !== 'search') {
    assert.ok(types.includes('CollectionPage') && types.includes('BreadcrumbList'), `Missing catalog schema: ${rel}`);
    assert.ok(!/noindex/.test($('meta[name="robots"]').attr('content') || ''), `Unexpected noindex: ${rel}`);
  } else assert.ok(/noindex/.test($('meta[name="robots"]').attr('content') || ''), 'Search should be noindex');
  const cards = $('.pc-card');
  if (route.kind === 'catalog') {
    assert.equal(cards.length, route.skus.length, `Wrong SSR card count: ${rel}`);
    assert.ok(cards.length <= PAGE_SIZE, `Too many cards: ${rel}`);
    const actual = [];
    for (const element of cards.toArray()) {
      const card = $(element), sku = card.attr('data-pc-sku'), p = bySku.get(sku);
      assert.ok(p, `Unknown product: ${sku}`); actual.push(sku);
      assert.equal(card.find('h2').text(), p.name, `Changed name: ${sku}`);
      assert.equal(card.find('h2 a').attr('href'), p.url, `Changed landing URL: ${sku}`);
      assert.ok(card.find('.pc-identifiers').text().includes(p.oem), `OEM reference missing: ${sku}`);
      if (p.image) {
        assert.equal(card.find('img').attr('src'), p.image, `Replaced photo: ${sku}`);
        assert.equal(card.find('img').attr('alt'), p.alt, `Changed image identity: ${sku}`);
      } else assert.equal(card.find('img').length, 0, `Substitute photo used: ${sku}`);
      if (!route.model) foundPrimary.set(sku, (foundPrimary.get(sku) || 0) + 1);
    }
    assert.deepEqual(actual, route.skus, `Product order changed: ${rel}`);
    if (!route.model && route.page === 1) sizes[route.brand] = { beforeBytes: data.manufacturers.find(b => b.slug === route.brand).originalHtmlBytes, afterBytes: bytes, pages: route.pages, totalProducts: route.total };
  }
  for (const node of $('a[href], img[src], script[src], link[rel="stylesheet"]').toArray()) {
    const value = $(node).attr('href') || $(node).attr('src');
    if (!value || value.startsWith('#') || /^(mailto|tel|data):/.test(value)) continue;
    const u = new URL(value, SITE + route.url);
    if (u.origin !== SITE) continue;
    const target = decodeURIComponent(u.pathname).replace(/^\//, '') + (u.pathname.endsWith('/') ? 'index.html' : '');
    if (checkedLinks.has(target)) continue;
    checkedLinks.add(target);
    assert.ok(fs.existsSync(path.join(out, target)), `Broken internal link or asset: ${route.url} → ${value}`);
  }
}
assert.equal(foundPrimary.size, data.parts.length, 'Some original products are not reachable through numbered manufacturer pages');
for (const [sku, count] of foundPrimary) assert.equal(count, 1, `Repeated product across primary pagination: ${sku}`);
for (const p of data.parts.filter(p => p.image)) {
  assert.equal(hash(fs.readFileSync(path.join(out, p.image.replace(/^\//,'')))), p.imageHash, `Original product photo modified: ${p.sku}`);
  for (const candidate of p.srcSet.split(',').filter(Boolean)) assert.ok(fs.existsSync(path.join(out, candidate.trim().split(' ')[0].replace(/^\//,''))), `Missing thumbnail for ${p.sku}`);
}
const sitemap = fs.readFileSync(path.join(out,'sitemap.xml'),'utf8');
for (const route of routes.filter(r => r.kind !== 'search')) assert.ok(sitemap.includes(`<loc>${SITE + route.url}</loc>`), `Catalog missing from sitemap: ${route.url}`);
assert.ok(!sitemap.includes(`<loc>${SITE}/parts/search/</loc>`), 'Do not submit internal search results');
const report = { status: 'passed', sourceCommit: data.sourceCommit, totalCatalogRecords: data.parts.length, manufacturerCatalogs: data.manufacturers.length, modelLandingPages: data.manufacturers.reduce((n,b) => n+b.models.length,0), generatedHtmlPages: routes.length, originalProductLandingPagesPreserved: productPages, otherLegacyHtmlPreserved: legacyHtml-productPages, originalImageFilesPreserved: photos, productsWithOriginalImages: data.parts.filter(p=>p.image).length, productsWithoutImages: data.parts.filter(p=>!p.image).length, placeholderImagesNotSubstituted: true, allProductUrlsPreserved: true, allOriginalImagesByteIdentical: true, initialHtmlProductLimit: PAGE_SIZE, allProductsReachableThroughStaticLinks: true, maximumGeneratedHtmlBytes: maxBytes, maximumGeneratedHtmlUrl: maxUrl, manufacturerHtmlSizes: sizes, schemaCheck: 'JSON parsing, catalog types, canonical and visible product correspondence; not a Google rich-result certification', sourceWarnings: data.warnings };
fs.writeFileSync(path.join(app, '.catalog-build-report.json'), JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
