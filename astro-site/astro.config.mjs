import { defineConfig } from 'astro/config';
export default defineConfig({
  site: 'https://pharmaglobaleng.com',
  output: 'static',
  build: { format: 'file' },
  compressHTML: false,
});
