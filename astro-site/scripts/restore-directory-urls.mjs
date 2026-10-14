import { readFileSync, mkdirSync, renameSync, existsSync } from 'node:fs';
import { dirname } from 'node:path';
// Astro file output emits /services.html; production uses /services/index.html.
// Move only the seven existing directory indexes, preserving their public URLs.
const pages = JSON.parse(readFileSync('src/content/manifest.json'));
for (const { path } of pages) {
  if (!path.endsWith('/index.html')) continue;
  const source = 'dist/' + path.replace(/\/index\.html$/, '.html');
  const target = 'dist/' + path;
  if (existsSync(target)) throw new Error(`Refusing to overwrite ${target}`);
  mkdirSync(dirname(target), { recursive: true });
  renameSync(source, target);
}
