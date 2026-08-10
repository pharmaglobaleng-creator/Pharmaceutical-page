import fs from 'node:fs';
import path from 'node:path';

const appDir = process.cwd();
const repoDir = path.resolve(appDir, '..');
const outDir = path.join(appDir, 'out');

if (!fs.existsSync(outDir)) {
  throw new Error('Next.js out/ directory does not exist. Run next build first.');
}

const excludedRootEntries = new Set([
  '.git',
  '.github',
  'next-app',
  'index.html',
  'README.md',
]);

for (const entry of fs.readdirSync(repoDir, { withFileTypes: true })) {
  if (excludedRootEntries.has(entry.name)) continue;
  const source = path.join(repoDir, entry.name);
  const destination = path.join(outDir, entry.name);
  fs.cpSync(source, destination, { recursive: true, force: true });
}

console.log('Safe export assembled: Next.js homepage + unchanged legacy routes/assets.');
