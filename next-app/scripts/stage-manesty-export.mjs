import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { catalogRoutes } from '../lib/catalog.mjs';
const root = path.resolve(process.cwd(),'..'), app = process.cwd(), out = path.join(app,'out');
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const read = f => JSON.parse(fs.readFileSync(path.join(app,f),'utf8'));
const report = read('.manesty-final-report.json');
assert.equal(report.status,'passed');
const files = read('.catalog-publish-files.json'), baseline = read('.catalog-baseline.json');
const approved = new Map();
const normalized = s => s.replace(/<img\b[^>]*>/gi, t => t.replace(/\s+(?:srcset|sizes)\s*=\s*(?:"[^"]*"|'[^']*')/gi,'').replace(/\s*\/?\s*>$/, '>'));
let changedDetails = 0;
for (const rel of files) {
  assert.ok((rel.startsWith('parts/') || rel.startsWith('_next/') || rel.startsWith('catalog-data/') || rel.startsWith('assets/images/catalog-thumbs/') || rel === 'sitemap.xml') && !rel.includes('..'), `Unapproved publish path ${rel}`);
  if (/^parts\/pge-man-[^/]+\/index\.html$/.test(rel)) {
    const before = fs.readFileSync(path.join(root,rel),'utf8'), after = fs.readFileSync(path.join(out,rel),'utf8');
    assert.equal(hash(before), baseline[rel], `Product changed after baseline: ${rel}`);
    assert.equal(normalized(before), normalized(after), `Unexpected content change: ${rel}`);
    approved.set(rel, hash(after));
    if (before !== after) changedDetails++;
  }
}
for (const rel of files) {
  const dest = path.join(root,rel);
  fs.mkdirSync(path.dirname(dest),{recursive:true});
  fs.copyFileSync(path.join(out,rel),dest);
}
const owned = new Set(catalogRoutes().map(r=>r.url.slice(1)+'index.html'));
let verifiedOriginalImages = 0, preservedDetailFiles = 0;
for (const [rel, expected] of Object.entries(baseline)) {
  if (owned.has(rel)) continue;
  const actual = hash(fs.readFileSync(path.join(root,rel)));
  assert.equal(actual, approved.get(rel) || expected, `Protected original changed: ${rel}`);
  if (rel.startsWith('assets/images/')) verifiedOriginalImages++;
  if (/^parts\/pge-[^/]+\/index\.html$/.test(rel) && actual === expected) preservedDetailFiles++;
}
const buildReport = read('.catalog-build-report.json');
buildReport.originalProductLandingPagesPreserved = preservedDetailFiles;
buildReport.productLandingPagesChangedImageDeliveryOnly = changedDetails;
buildReport.manestyProductsPerPage = 25;
buildReport.manestyProductContentPreserved = true;
buildReport.originalImageFilesPreserved = verifiedOriginalImages;
fs.writeFileSync(path.join(root,'docs/parts-catalog-migration-report.json'),JSON.stringify(buildReport,null,2)+'\n');
report.productDetailFilesChangedImageDeliveryOnly = changedDetails;
report.allSiteOriginalImagesHashVerified = verifiedOriginalImages;
fs.writeFileSync(path.join(root,'docs/manesty-size-optimization-report.json'),JSON.stringify(report,null,2)+'\n');
console.log(`Staged ${files.length} validated files. ${changedDetails} Manesty detail files changed only image delivery attributes; ${verifiedOriginalImages} original images hash-verified unchanged.`);
