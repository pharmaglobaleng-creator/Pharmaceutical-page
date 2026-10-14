import { execFileSync } from 'node:child_process';
import { readFileSync, mkdirSync, copyFileSync, rmSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
const root = resolve('..');
const pages = new Set(JSON.parse(readFileSync('src/content/manifest.json')).map(p => p.path));
const files = execFileSync('git', ['ls-files', '-z'], { cwd: root, encoding: 'utf8' }).split('\0').filter(Boolean);
const roots = new Set(['assets','parts','catalog-data','data','resources','_next','.well-known']);
rmSync('public', { recursive: true, force: true });
for (const file of files) {
  if (pages.has(file)) continue;
  const top = file.split('/')[0];
  const rootStatic = !file.includes('/') && (/\.(html|xml|txt|ico|png|webmanifest)$/.test(file) || ['CNAME','.nojekyll'].includes(file));
  if (!roots.has(top) && !rootStatic) continue;
  const target = resolve('public', file);
  mkdirSync(dirname(target), { recursive: true });
  copyFileSync(resolve(root, file), target);
}
console.log('Staged unchanged catalog, assets, verification files and sitemaps.');
