import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { catalogRoutes, SITE } from '../lib/catalog.mjs';
const app = process.cwd(), root = path.resolve(app, '..'), out = path.join(app, 'out');
const walk = dir => fs.readdirSync(dir, { withFileTypes: true }).flatMap(e => e.isDirectory() ? walk(path.join(dir, e.name)) : [path.join(dir, e.name)]);
const rel = (base, file) => path.relative(base, file).split(path.sep).join('/');
if (!fs.existsSync(out)) throw new Error('Run next build before assembling the export.');
const routes = catalogRoutes();
const owned = new Set(routes.map(r => r.url.slice(1) + 'index.html'));
const replaceable = new Set(['parts/index.html', 'parts/stokes/index.html', 'parts/fette/index.html', 'parts/korsch/index.html', 'parts/manesty/index.html', 'parts/kikusui/index.html']);
const generated = walk(out).map(f => rel(out, f));
const publish = generated.filter(f => f.startsWith('parts/') || f.startsWith('_next/') || f.startsWith('catalog-data/') || f.startsWith('assets/images/catalog-thumbs/'));
const publicDirs = new Set(['assets','parts','about','coatings','components','services','solutions','knowledge-center','_next']);
for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
  const source = path.join(root, entry.name);
  if (entry.isDirectory() && !publicDirs.has(entry.name)) continue;
  if (!entry.isDirectory() && !(/\.(html|txt|xml|webmanifest)$/.test(entry.name) || ['CNAME','.nojekyll'].includes(entry.name))) continue;
  for (const file of entry.isDirectory() ? walk(source) : [source]) {
    const name = rel(root, file);
    if (owned.has(name)) {
      const previous = fs.readFileSync(file, 'utf8');
      if (!replaceable.has(name) && !previous.includes('data-pge-catalog="v2"')) throw new Error(`Refusing to overwrite an unrelated existing route: ${name}`);
      continue;
    }
    const dest = path.join(out, name);
    if (name.startsWith('_next/') && fs.existsSync(dest) && !fs.readFileSync(dest).equals(fs.readFileSync(file))) throw new Error(`Runtime-asset collision: ${name}`);
    fs.mkdirSync(path.dirname(dest), { recursive: true });
    fs.copyFileSync(file, dest);
  }
}
// The production homepage is deliberately retained byte for byte. The new
// catalog and its hashed runtime coexist with the existing homepage runtime.
if (!fs.readFileSync(path.join(root,'index.html')).equals(fs.readFileSync(path.join(out,'index.html')))) throw new Error('Homepage was not preserved');
let sitemap = fs.readFileSync(path.join(root, 'sitemap.xml'), 'utf8');
if (!sitemap.includes('</urlset>')) throw new Error('Expected an existing URL sitemap');
const existing = new Set([...sitemap.matchAll(/<loc>(.*?)<\/loc>/g)].map(m => m[1]));
const newEntries = routes.filter(r => r.kind !== 'search' && !existing.has(SITE + r.url)).map(r => `  <url><loc>${SITE + r.url}</loc></url>`);
if (newEntries.length) sitemap = sitemap.replace('</urlset>', newEntries.join('\n') + '\n</urlset>');
fs.writeFileSync(path.join(out, 'sitemap.xml'), sitemap);
// Manufacturer selection uses native links/search and a small optional cart.
execFileSync('python3', [path.join(root, 'scripts/optimize_catalog_entry.py'), '--root', out], { stdio: 'inherit' });
publish.push('sitemap.xml');
fs.writeFileSync(path.join(app, '.catalog-publish-files.json'), JSON.stringify([...new Set(publish)].sort()));
fs.writeFileSync(path.join(app, '.catalog-routes.json'), JSON.stringify(routes));
console.log(`Assembled ${routes.length} catalog/search pages; ${newEntries.length} new sitemap entries. Existing product pages, homepage and original assets retained.`);
