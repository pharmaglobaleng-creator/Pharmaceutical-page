import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import sharp from 'sharp';
import { load } from 'cheerio';

// Run from next-app. Originals, part identities and product URLs are never replaced.
const app = process.cwd(), root = path.resolve(app, '..');
const SITE = 'https://pharmaglobaleng.com';
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const write = (file, value) => { fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, value); };
const json = (file, value) => write(file, JSON.stringify(value, null, 2) + '\n');
const dataPath = path.join(app, 'data/parts-catalog.json');
const statePath = path.join(app, '.manesty-optimization.json');
const identity = p => Object.fromEntries(['sku','name','brand','brandName','model','modelSlug','family','oem','url','originalImage','image','alt'].map(k => [k, p[k] ?? null]));
function local(url, base = root) {
  const u = new URL(url, SITE);
  assert.equal(u.origin, SITE, 'External assets are outside this optimization');
  const result = path.resolve(base, '.' + decodeURIComponent(u.pathname));
  assert.ok(result.startsWith(base + path.sep), 'Unsafe local path');
  return result;
}
function patch(file, oldText, newText) {
  let source = fs.readFileSync(file, 'utf8');
  if (source.includes(newText)) return;
  assert.ok(source.includes(oldText), `Expected source marker not found in ${file}`);
  source = source.replace(oldText, newText);
  write(file, source);
}
function configure() {
  const lib = path.join(app, 'lib/catalog.mjs');
  patch(lib, 'export const PAGE_SIZE = 50;', "export const PAGE_SIZE = 50;\nexport function pageSizeFor(brand) { return brand === 'manesty' ? 25 : PAGE_SIZE; }");
  patch(lib, 'for (const manufacturer of data.manufacturers) {', 'for (const manufacturer of data.manufacturers) {\n    const pageSize = pageSizeFor(manufacturer.slug);');
  patch(lib, 'Math.ceil(rows.length / PAGE_SIZE)', 'Math.ceil(rows.length / pageSize)');
  patch(lib, 'rows.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)', 'rows.slice((page - 1) * pageSize, page * pageSize)');
  const pageFile = path.join(app, 'app/parts/[[...catalog]]/page.js');
  let page = fs.readFileSync(pageFile, 'utf8');
  if (page.includes('PAGE_SIZE')) {
    assert.ok(page.includes('SITE, PAGE_SIZE,'), 'Unexpected catalog page import');
    page = page.replace('SITE, PAGE_SIZE,', 'SITE, pageSizeFor,').replace(/\bPAGE_SIZE\b/g, 'pageSizeFor(route.brand)');
    write(pageFile, page);
  }
  const packageFile = path.join(app, 'package.json'), pkg = read(packageFile);
  for (const command of ['build', 'dev']) {
    if (!pkg.scripts[command].includes('optimize-manesty.mjs images')) {
      assert.ok(pkg.scripts[command].includes('node scripts/prepare-catalogs.mjs &&'), 'Unexpected build script');
      pkg.scripts[command] = pkg.scripts[command].replace('node scripts/prepare-catalogs.mjs &&', 'node scripts/prepare-catalogs.mjs && node scripts/optimize-manesty.mjs images &&');
    }
  }
  if (!pkg.scripts['build:safe'].includes('optimize-manesty.mjs details')) pkg.scripts['build:safe'] += ' && node scripts/optimize-manesty.mjs details';
  json(packageFile, pkg);
  console.log('Configured 25 products per Manesty page and persistent optimized image delivery.');
}
async function images() {
  const data = read(dataPath), parts = data.parts.filter(p => p.brand === 'manesty');
  const manufacturer = data.manufacturers.find(m => m.slug === 'manesty');
  assert.ok(manufacturer && parts.length === manufacturer.count && parts.length > 0, 'Incomplete Manesty data');
  const state = { baseCommit: process.env.MANESTY_BASE_COMMIT || null, identities: data.parts.map(identity), count: parts.length, images: {}, beforeHtmlBytes: fs.statSync(path.join(root, 'parts/manesty/index.html')).size, detailPages: [] };
  for (const part of parts) {
    assert.ok(fs.existsSync(path.join(local(part.url), 'index.html')), `Missing existing product ${part.sku}`);
    if (!part.image) continue;
    if (!state.images[part.image]) {
      const file = local(part.image), original = fs.readFileSync(file), digest = hash(original);
      const meta = await sharp(original).metadata();
      const info = { original: part.image, hash: digest, originalBytes: original.length, width: meta.width, height: meta.height, fullUrl: part.image, fullBytes: original.length, variants: [], srcSet: part.srcSet || '' };
      if (meta.width && meta.height && meta.format !== 'svg' && !(meta.pages > 1)) {
        const base = `/assets/images/catalog-thumbs/manesty-light-v1/${digest.slice(0,24)}`;
        const fullBuffer = await sharp(original).webp({ quality: 90, effort: 4, smartSubsample: true }).toBuffer();
        if (fullBuffer.length < original.length) {
          info.fullUrl = `${base}-full.webp`; info.fullBytes = fullBuffer.length;
          write(local(info.fullUrl, path.join(app, 'public')), fullBuffer);
          const converted = await sharp(fullBuffer).metadata();
          assert.equal(converted.width, meta.width); assert.equal(converted.height, meta.height);
        }
        for (const width of [...new Set([Math.min(320,meta.width), Math.min(640,meta.width)])]) {
          const buffer = await sharp(original).resize({ width, withoutEnlargement: true, fit: 'inside' }).webp({ quality: 85, effort: 4, smartSubsample: true }).toBuffer();
          const url = `${base}-${width}.webp`;
          write(local(url, path.join(app, 'public')), buffer);
          info.variants.push({ url, width, bytes: buffer.length });
        }
        info.srcSet = info.variants.map(v => `${v.url} ${v.width}w`).join(', ');
        const detailWidths = new Map(info.variants.map(v => [v.width, v.url]));
        detailWidths.set(meta.width, info.fullUrl);
        info.detailSrcSet = [...detailWidths].sort((a,b) => a[0]-b[0]).map(([width,url]) => `${url} ${width}w`).join(', ');
      }
      state.images[part.image] = info;
    }
    part.srcSet = state.images[part.image].srcSet;
  }
  assert.deepEqual(data.parts.map(identity), state.identities, 'Product identification was modified');
  manufacturer.searchVersion = hash(JSON.stringify(parts)).slice(0,12);
  json(dataPath, data);
  write(path.join(app,'public/catalog-data/manesty.json'), JSON.stringify(parts));
  write(path.join(app,'public/catalog-data/manifest.json'), JSON.stringify(data.manufacturers));
  json(statePath, state);
  console.log(`Prepared lighter copies for ${Object.keys(state.images).length} distinct images across ${parts.length} Manesty products. Originals are intact.`);
}
function stripDeliveryAttrs(html) {
  return html.replace(/<img\b[^>]*>/gi, tag => tag.replace(/\s+(?:srcset|sizes)\s*=\s*(?:"[^"]*"|'[^']*')/gi, ''));
}
async function details() {
  const state = read(statePath), data = read(dataPath), out = path.join(app,'out');
  assert.deepEqual(data.parts.map(identity), state.identities, 'Product identities changed during build');
  const publishFile = path.join(app, '.catalog-publish-files.json'), publish = new Set(read(publishFile));
  let updatedDetails = 0;
  for (const part of data.parts.filter(p => p.brand === 'manesty')) {
    const info = state.images[part.image];
    const rel = part.url.slice(1) + 'index.html', file = path.join(out, rel);
    assert.ok(fs.existsSync(file), `Missing preserved URL ${part.url}`);
    const originalHtml = fs.readFileSync(path.join(root,rel),'utf8');
    let html = fs.readFileSync(file,'utf8');
    if (info?.detailSrcSet) {
      let matches = 0;
      html = html.replace(/<img\b[^>]*>/gi, tag => {
        const img = load(tag)('img').first();
        if (new URL(img.attr('src') || '', SITE).pathname !== new URL(part.image,SITE).pathname) return tag;
        matches++;
        let clean = stripDeliveryAttrs(tag);
        clean = clean.replace(/\s*\/?\s*>$/, '');
        return `${clean} srcset="${info.detailSrcSet}" sizes="(max-width: 800px) 92vw, 46vw">`;
      });
      assert.ok(matches > 0, `Expected product photo not found: ${part.sku}`);
      // Only image delivery attributes can change, not content, schema, links or image identity.
      const normalize = h => stripDeliveryAttrs(h).replace(/<img\b[^>]*>/gi,t => t.replace(/\s*\/?\s*>$/, '>'));
      assert.equal(normalize(html), normalize(originalHtml), `Unexpected product-page edit: ${part.sku}`);
      write(file,html); publish.add(rel); updatedDetails++;
    } else assert.equal(html, originalHtml, `Image-unavailable page changed: ${part.sku}`);
    state.detailPages.push({ sku: part.sku, url: part.url, image: part.image, fullUrl: info?.fullUrl || null });
  }
  const { catalogRoutes } = await import('../lib/catalog.mjs');
  const routes = catalogRoutes().filter(r => r.brand === 'manesty'), seen = new Set();
  let maximumHtmlBytes = 0;
  for (const route of routes) {
    const html = fs.readFileSync(path.join(out,route.url.slice(1),'index.html'),'utf8'), $ = load(html);
    maximumHtmlBytes = Math.max(maximumHtmlBytes, Buffer.byteLength(html));
    const cards = $('.pc-card');
    assert.ok(cards.length <= 25); assert.equal(cards.length, route.skus.length);
    assert.equal($('link[rel="canonical"]').attr('href'), SITE + route.url);
    if (!route.model) for (const sku of route.skus) { assert.ok(!seen.has(sku)); seen.add(sku); }
    assert.ok(html.includes('25 per page') || html.includes('25<!-- --> per page'));
    for (const img of $('img[srcset]').toArray()) {
      for (const item of ($(img).attr('srcset') || '').split(',')) assert.ok(fs.existsSync(local(item.trim().split(/\s+/)[0],out)), 'Missing optimized image');
    }
  }
  assert.equal(seen.size, state.count, 'A product disappeared from pagination');
  for (const info of Object.values(state.images)) {
    assert.equal(hash(fs.readFileSync(local(info.original))), info.hash);
    assert.equal(hash(fs.readFileSync(local(info.original,out))), info.hash);
    assert.ok(info.fullBytes <= info.originalBytes);
  }
  const afterHtmlBytes = fs.statSync(path.join(out,'parts/manesty/index.html')).size;
  assert.ok(afterHtmlBytes < 180000, `Manesty HTML exceeds size budget: ${afterHtmlBytes}`);
  assert.ok(maximumHtmlBytes < 190000, `A model page exceeds the size budget: ${maximumHtmlBytes}`);
  const originals = Object.values(state.images);
  const report = { status: 'passed', baseCommit: state.baseCommit, manufacturer: 'Manesty', productsRetained: state.count, productsPerPage: 25, primaryCatalogPages: routes.filter(r => !r.model).length, modelLandingPages: routes.filter(r => r.model && r.page === 1).length, generatedManestyPages: routes.length, beforeFirstPageHtmlBytes: state.beforeHtmlBytes, afterFirstPageHtmlBytes: afterHtmlBytes, htmlReductionPercent: Number(((1-afterHtmlBytes/state.beforeHtmlBytes)*100).toFixed(2)), maximumManestyHtmlBytes: maximumHtmlBytes, uniqueOriginalImagesPreserved: originals.length, originalImageBytes: originals.reduce((n,i)=>n+i.originalBytes,0), optimizedFullSizeImageBytes: originals.reduce((n,i)=>n+i.fullBytes,0), optimizedImageDimensionsUnchanged: true, productDetailPagesWithResponsiveImages: updatedDetails, originalImageFilesUnchanged: true, partNamesOemReferencesAndUrlsUnchanged: true, allProductsReachableThroughStaticLinks: true, note: 'Image totals count distinct original images once. Optimized full-size totals are alternative serving files, not total repository storage. Original files remain stored and accessible. This is not a ranking or indexing guarantee.' };
  json(path.join(root,'docs/manesty-size-optimization-report.json'),report);
  json(path.join(app,'.manesty-final-report.json'),report);
  json(statePath,state);
  json(publishFile,[...publish].sort());
  console.log(JSON.stringify(report,null,2));
}
const mode = process.argv[2];
if (mode === 'configure') configure();
else if (mode === 'images') await images();
else if (mode === 'details') await details();
else throw new Error('Use configure, images, or details');
