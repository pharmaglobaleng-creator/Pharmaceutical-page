import fs from 'node:fs';
import path from 'node:path';

const appDir = process.cwd();
const repoDir = path.resolve(appDir, '..');
const outDir = path.join(appDir, 'out');

function walk(dir, base = dir) {
  const files = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) files.push(...walk(full, base));
    else files.push(path.relative(base, full).replaceAll(path.sep, '/'));
  }
  return files;
}

const sourceHtml = walk(repoDir)
  .filter((p) => p.endsWith('.html'))
  .filter((p) => !p.startsWith('next-app/'))
  .filter((p) => p !== 'index.html');

const missingLegacy = sourceHtml.filter((p) => !fs.existsSync(path.join(outDir, p)));
if (missingLegacy.length) {
  throw new Error(`Missing legacy HTML routes in export:\n${missingLegacy.join('\n')}`);
}

for (const required of ['index.html', 'robots.txt', 'sitemap.xml', 'llms.txt', 'CNAME']) {
  if (!fs.existsSync(path.join(outDir, required))) {
    throw new Error(`Required production file missing: ${required}`);
  }
}

const sourceHome = fs.readFileSync(path.join(repoDir, 'index.html'), 'utf8');
const builtHome = fs.readFileSync(path.join(outDir, 'index.html'), 'utf8');
const requiredHomepageMarkers = [
  'Pharmaceutical Tablet Tooling & Surface Engineering',
  '50 Engineering Facts About Tablet Tooling',
  'Pharmaceutical Tablet Tooling FAQs',
  'Worldwide Pharmaceutical Manufacturing Support',
  'application/ld+json',
];
for (const marker of requiredHomepageMarkers) {
  if (!sourceHome.includes(marker)) throw new Error(`Source homepage marker unexpectedly missing: ${marker}`);
  if (!builtHome.includes(marker)) throw new Error(`Next.js homepage lost required marker: ${marker}`);
}

const sitemap = fs.readFileSync(path.join(outDir, 'sitemap.xml'), 'utf8');
const urls = [...sitemap.matchAll(/<loc>https?:\/\/[^/]+([^<]*)<\/loc>/g)].map((m) => m[1] || '/');
const missingSitemap = [];
for (const urlPath of urls) {
  const decoded = decodeURI(urlPath.split('?')[0].split('#')[0]);
  let candidate;
  if (decoded === '/' || decoded === '') candidate = 'index.html';
  else if (decoded.endsWith('/')) candidate = `${decoded.slice(1)}index.html`;
  else candidate = decoded.slice(1);
  if (!fs.existsSync(path.join(outDir, candidate))) missingSitemap.push(`${urlPath} -> ${candidate}`);
}
if (missingSitemap.length) {
  throw new Error(`Sitemap destinations missing from export:\n${missingSitemap.join('\n')}`);
}

console.log(`Validated ${sourceHtml.length} unchanged legacy HTML routes and ${urls.length} sitemap URLs.`);
