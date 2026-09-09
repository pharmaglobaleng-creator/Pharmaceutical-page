import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { load } from 'cheerio';
import sharp from 'sharp';

const app = process.cwd();
const root = path.resolve(app, '..');
const dataFile = path.join(app, 'data/parts-catalog.json');
const names = { stokes: 'Stokes', fette: 'Fette', korsch: 'Korsch', manesty: 'Manesty', kikusui: 'Kikusui' };
const hash = value => crypto.createHash('sha256').update(value).digest('hex');
const clean = value => String(value || '').replace(/\s+/g, ' ').trim();
const slug = value => clean(value).toLowerCase().normalize('NFKD').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
const write = (file, value) => { fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, value); };
const walk = dir => fs.readdirSync(dir, { withFileTypes: true }).flatMap(e => e.isDirectory() ? walk(path.join(dir, e.name)) : [path.join(dir, e.name)]);

function localFile(url) {
  const u = new URL(url, 'https://pharmaglobaleng.com');
  if (u.origin !== 'https://pharmaglobaleng.com') throw new Error(`Unexpected external product asset: ${url}`);
  const file = path.resolve(root, '.' + decodeURIComponent(u.pathname));
  if (!file.startsWith(root + path.sep)) throw new Error('Unsafe asset path');
  return file;
}

const replaceable = new Set(['parts/index.html', ...Object.keys(names).map(b => `parts/${b}/index.html`)]);
// A byte-for-byte baseline of original images and non-catalog HTML is checked
// after assembly. New thumbnail files live in a separate directory.
const baseline = {};
for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
  if (entry.name.startsWith('.') || entry.name === 'next-app' || entry.name === '_next') continue;
  const files = entry.isDirectory() ? walk(path.join(root, entry.name)) : [path.join(root, entry.name)];
  for (const file of files) {
    const rel = path.relative(root, file).split(path.sep).join('/');
    if ((rel.endsWith('.html') && !replaceable.has(rel) && !rel.startsWith('parts/search/')) || (rel.startsWith('assets/images/') && !rel.startsWith('assets/images/catalog-thumbs/'))) baseline[rel] = hash(fs.readFileSync(file));
  }
}
write(path.join(app, '.catalog-baseline.json'), JSON.stringify(baseline));

let data;
if (fs.existsSync(dataFile)) {
  data = JSON.parse(fs.readFileSync(dataFile, 'utf8'));
  if (data.version !== 1) throw new Error('Unsupported catalog data version');
} else {
  data = { version: 1, sourceCommit: process.env.GITHUB_SHA || 'local-import', manufacturers: [], parts: [], warnings: [] };
  const seen = new Set();
  for (const [brand, brandName] of Object.entries(names)) {
    const rel = `parts/${brand}/index.html`;
    const html = fs.readFileSync(path.join(root, rel), 'utf8');
    if (html.includes('data-pge-catalog="v2"')) throw new Error('Original catalog snapshot is missing; refusing to import only a paginated subset.');
    const $ = load(html);
    const cards = $('article.product-card');
    if (!cards.length) throw new Error(`No original product cards found: ${rel}`);
    for (const element of cards.toArray()) {
      const card = $(element);
      const button = card.find('[data-pge-cart-add]').first();
      const sku = clean(card.attr('data-sku') || button.attr('data-part-sku') || card.find('.sku').text());
      const name = clean(button.attr('data-part-name') || card.attr('data-name') || card.find('h3').text());
      const model = clean(button.attr('data-part-model') || card.attr('data-model'));
      const url = button.attr('data-part-url') || card.find('h3 a').attr('href') || card.find('a.part-page-link').attr('href');
      if (!sku || !name || !model || !url || !/^\/parts\/pge-[a-z0-9-]+\/$/i.test(url)) throw new Error(`Incomplete original record: ${brand} ${sku} ${url}`);
      if (seen.has(sku)) throw new Error(`Duplicate PGE identifier: ${sku}`);
      seen.add(sku);
      if (!fs.existsSync(path.join(localFile(url), 'index.html'))) throw new Error(`Missing product landing page: ${url}`);
      const img = card.find('img').first();
      const originalImage = img.attr('src') || null;
      let image = originalImage;
      if (!image || /image-pending|placeholder|unavailable/i.test(image)) image = null;
      if (image && !fs.existsSync(localFile(image))) { data.warnings.push(`${sku}: original image file missing; no substitute used`); image = null; }
      const family = clean(card.find('.product-family').text()).split(/\s*[·|]\s*/).slice(1).join(' · ') || 'Replacement components';
      const oem = clean(card.find('.oem-reference').text()).replace(/^OEM\s*(?:number|reference|ref\.?)?\s*:\s*/i, '') || 'Not listed in source catalog';
      data.parts.push({ sku, name, brand, brandName, model, family, oem, url, originalImage, image, alt: image ? clean(img.attr('alt') || `${name} — ${brandName} ${model}`) : '', sourceCatalog: '/' + rel.replace(/index.html$/, '') });
    }
    data.manufacturers.push({ slug: brand, name: brandName, count: cards.length, sourceHash: hash(html), originalHtmlBytes: Buffer.byteLength(html) });
  }
}

// PGE: enforce source-reviewed OEM restrictions before export.
write(dataFile, JSON.stringify(data, null, 2) + '\n');
execFileSync('python3', [path.join(root, 'scripts/sync_parts_reference_status.py')], { cwd: root, stdio: 'inherit' });
data = JSON.parse(fs.readFileSync(dataFile, 'utf8'));

const imageCache = new Map();
for (const part of data.parts) {
  if (!fs.existsSync(path.join(localFile(part.url), 'index.html'))) throw new Error(`Product URL disappeared: ${part.url}`);
  part.modelSlug = /unresolved|unconfirmed|unspecified|^general$|^multi[ -]?model$/i.test(part.model) ? null : slug(part.model);
  part.srcSet = '';
  if (!part.image) continue;
  const file = localFile(part.image);
  if (!fs.existsSync(file)) throw new Error(`Original photo disappeared: ${part.sku} ${part.image}`);
  if (!imageCache.has(part.image)) {
    const bytes = fs.readFileSync(file);
    const digest = hash(bytes);
    const metadata = await sharp(bytes).metadata();
    const variants = [];
    // Never crop, recolor, regenerate or overwrite the original image.
    if (metadata.width && metadata.height && metadata.format !== 'svg') {
      for (const width of [320, 640]) {
        if (metadata.width < width) continue;
        const url = `/assets/images/catalog-thumbs/${digest.slice(0, 24)}-${width}.webp`;
        const dest = path.join(app, 'public', url);
        fs.mkdirSync(path.dirname(dest), { recursive: true });
        if (!fs.existsSync(dest)) await sharp(bytes).resize({ width, withoutEnlargement: true, fit: 'inside' }).webp({ quality: 87, effort: 3 }).toFile(dest);
        variants.push(`${url} ${width}w`);
      }
    }
    imageCache.set(part.image, { hash: digest, srcSet: variants.join(', '), width: metadata.width || 760, height: metadata.height || 760 });
  }
  const info = imageCache.get(part.image);
  part.imageHash = info.hash; part.srcSet = info.srcSet; part.imageWidth = info.width; part.imageHeight = info.height;
}
for (const manufacturer of data.manufacturers) {
  const rows = data.parts.filter(p => p.brand === manufacturer.slug);
  if (rows.length !== manufacturer.count) throw new Error(`Count mismatch: ${manufacturer.slug}`);
  const models = new Map();
  for (const row of rows) {
    if (!row.modelSlug) continue;
    const prev = models.get(row.modelSlug);
    if (prev && prev.name !== row.model) throw new Error(`Model-slug collision: ${manufacturer.name} ${row.model}`);
    models.set(row.modelSlug, { slug: row.modelSlug, name: row.model, count: (prev?.count || 0) + 1 });
  }
  manufacturer.models = [...models.values()].sort((a,b) => a.name.localeCompare(b.name, 'en', { numeric: true }));
  manufacturer.searchVersion = hash(JSON.stringify(rows)).slice(0, 12);
  write(path.join(app, `public/catalog-data/${manufacturer.slug}.json`), JSON.stringify(rows));
}
write(dataFile, JSON.stringify(data, null, 2) + '\n');
write(path.join(app, 'public/catalog-data/manifest.json'), JSON.stringify(data.manufacturers));
console.log(JSON.stringify({ importedProducts: data.parts.length, manufacturers: data.manufacturers.map(b => ({ name: b.name, parts: b.count, models: b.models.length })), originalImages: imageCache.size, productsWithoutImage: data.parts.filter(p => !p.image).length, warnings: data.warnings.length }, null, 2));
