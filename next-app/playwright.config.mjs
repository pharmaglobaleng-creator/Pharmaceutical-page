import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests', timeout: 45000, retries: 0, workers: 1,
  reporter: [['list']],
  use: { baseURL: 'http://127.0.0.1:4173', browserName: 'chromium', viewport: { width: 1536, height: 1152 }, trace: 'retain-on-failure' },
  webServer: { command: 'python3 -m http.server 4173 --bind 127.0.0.1 --directory out', url: 'http://127.0.0.1:4173/parts/stokes/', timeout: 20000, reuseExistingServer: !process.env.CI },
});
