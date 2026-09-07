import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { catalogRoutes } from '../lib/catalog.mjs';
const app = process.cwd(), root = path.resolve(app,'..'), out = path.join(app,'out');
const files = JSON.parse(fs.readFileSync(path.join(app,'.catalog-publish-files.json'),'utf8'));
const report = JSON.parse(fs.readFileSync(path.join(app,'.catalog-build-report.json'),'utf8'));
if (report.status !== 'passed') throw new Error('Only a validated export can be staged.');
for (const rel of files) {
  if (!(rel.startsWith('parts/') || rel.startsWith('_next/') || rel.startsWith('catalog-data/') || rel.startsWith('assets/images/catalog-thumbs/') || rel === 'sitemap.xml') || rel.includes('..')) throw new Error(`Unapproved output path: ${rel}`);
  const dest = path.join(root, rel);
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.copyFileSync(path.join(out,rel), dest);
}
const owned = new Set(catalogRoutes().map(r=>r.url.slice(1)+'index.html'));
const baseline = JSON.parse(fs.readFileSync(path.join(app,'.catalog-baseline.json'),'utf8'));
for (const [rel, expected] of Object.entries(baseline)) {
  if (owned.has(rel)) continue;
  const actual = crypto.createHash('sha256').update(fs.readFileSync(path.join(root,rel))).digest('hex');
  if (actual !== expected) throw new Error(`Staging changed a protected original: ${rel}`);
}
fs.mkdirSync(path.join(root,'docs'), {recursive:true});
fs.copyFileSync(path.join(app,'.catalog-build-report.json'),path.join(root,'docs/parts-catalog-migration-report.json'));
console.log(`Staged ${files.length} validated files. Original photos and product landing pages remain untouched.`);
