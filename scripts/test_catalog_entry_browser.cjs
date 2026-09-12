// Isolated browser tests: all requests are fulfilled from this checkout.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { chromium } = require('playwright');
const root = path.resolve(__dirname, '..');
const mime = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.webp': 'image/webp', '.json': 'application/json', '.txt': 'text/plain' };
const site = 'https://pharmaglobaleng.com';
const results = [];
async function context(browser, options = {}) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, serviceWorkers: 'block', ...options });
  const requests = [];
  await ctx.route('**/*', async route => {
    const request = route.request();
    const url = new URL(request.url());
    requests.push(url.pathname);
    if (url.origin !== site || request.resourceType() === 'image') return route.abort();
    const pathname = decodeURIComponent(url.pathname) + (url.pathname.endsWith('/') ? 'index.html' : '');
    const file = path.resolve(root, '.' + pathname);
    if (!file.startsWith(root + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) return route.fulfill({ status: 404, body: 'Not found' });
    return route.fulfill({ status: 200, contentType: mime[path.extname(file)] || 'application/octet-stream', body: fs.readFileSync(file) });
  });
  return { ctx, requests };
}
(async () => {
  const browser = await chromium.launch({ headless: true, ...(process.env.PGE_TEST_CHROMIUM ? { executablePath: process.env.PGE_TEST_CHROMIUM } : {}) });
  try {
    const { ctx } = await context(browser, { javaScriptEnabled: false });
    const page = await ctx.newPage();
    await page.goto(site + '/parts/', { waitUntil: 'domcontentloaded' });
    const cards = page.locator('.pc-manufacturer-grid > a');
    assert.equal(await cards.count(), 7);
    assert.equal(await page.locator('.pc-manufacturer-grid > a[href="/parts/cremer/"]').count(), 1);
    await page.locator('.pc-manufacturer-grid > a[href="/parts/cremer/"]').click();
    assert.equal(page.url(), site + '/parts/cremer/');
    assert.equal(await page.locator('article.part-card').count(), 60);
    await page.locator('a.view-btn[href="/parts/pge-cre-003/"]').click();
    assert.equal(page.url(), site + '/parts/pge-cre-003/');
    results.push('Manufacturer cards and Creamer product cards navigate with JavaScript disabled and all images blocked.');
    await page.goto(site + '/parts/');
    await page.locator('#pc-query').fill('PGE-CRE-003');
    await page.locator('form.pc-search button').click();
    assert.equal(new URL(page.url()).pathname, '/parts/search/');
    assert.equal(new URL(page.url()).searchParams.get('q'), 'PGE-CRE-003');
    results.push('Search submits as a native form without JavaScript.');
    await ctx.close();

    const enhanced = await context(browser);
    const interactive = await enhanced.ctx.newPage();
    const errors = []; interactive.on('pageerror', error => errors.push(error.message));
    await enhanced.ctx.addInitScript(() => {
      localStorage.setItem('pge-parts-quote-cart-v1', JSON.stringify({ 'PGE-CRE-003': { sku: 'PGE-CRE-003', name: 'Set of 12 Memory Flaps', brand: 'Cremer / CVC', model: 'CF1220 / CVC1220', url: '/parts/pge-cre-003/', quantity: 2 } }));
    });
    await interactive.goto(site + '/parts/', { waitUntil: 'domcontentloaded' });
    await interactive.locator('.pc-cart-trigger').click();
    assert.equal(await interactive.locator('dialog.pc-quote').evaluate(d => d.open), true);
    assert.equal(await interactive.locator('.pc-quote-item input').inputValue(), '2');
    await interactive.locator('.pc-quote-item input').fill('3');
    await interactive.locator('.pc-quote-item input').dispatchEvent('change');
    assert.equal(await interactive.evaluate(() => JSON.parse(localStorage.getItem('pge-parts-quote-cart-v1'))['PGE-CRE-003'].quantity), 3);
    assert.match(await interactive.locator('.pc-quote-actions a').getAttribute('href'), /^mailto:info@pharmaglobaleng.com/);
    await interactive.locator('[aria-label="Close quote cart"]').click();
    assert.equal(await interactive.locator('dialog.pc-quote').evaluate(d => d.open), false);
    assert.deepEqual(enhanced.requests.filter(url => url.startsWith('/_next/') && url.endsWith('.js')), []);
    assert.deepEqual(errors, []);
    results.push('Quote cart opens, preserves saved parts, updates quantities, and prepares a mail link without loading framework JavaScript.');
    await interactive.setViewportSize({ width: 390, height: 844 });
    assert.ok(await interactive.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await interactive.locator('.pc-mobile-nav summary').click();
    await interactive.locator('.pc-mobile-nav a[href="/parts/cremer/"]').click();
    assert.equal(interactive.url(), site + '/parts/cremer/');
    assert.ok(await interactive.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    results.push('Mobile navigation and both page widths checked at 390 pixels.');
    await enhanced.ctx.close();

    const blocked = await context(browser);
    await blocked.ctx.addInitScript(() => { Object.defineProperty(window, 'localStorage', { get() { throw new Error('Storage blocked'); } }); });
    const p = await blocked.ctx.newPage();
    await p.goto(site + '/parts/');
    await p.locator('.pc-cart-trigger').click();
    assert.match(await p.locator('dialog [role="status"]').textContent(), /storage is unavailable/);
    await p.locator('[aria-label="Close quote cart"]').click();
    await p.locator('.pc-manufacturer-grid > a[href="/parts/cremer/"]').click();
    assert.equal(p.url(), site + '/parts/cremer/');
    results.push('Blocked browser storage does not disable catalog links or crash the quote cart.');
    await blocked.ctx.close();
    const out = path.join(root, 'audit-output'); fs.mkdirSync(out, { recursive: true });
    fs.writeFileSync(path.join(out, 'catalog-entry-browser.json'), JSON.stringify({ status: 'passed', results }, null, 2));
    results.forEach(result => console.log('PASS:', result));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
