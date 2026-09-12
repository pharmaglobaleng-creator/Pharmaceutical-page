// Run with node --test; requires jsdom (used only for the isolated DOM test).
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require('jsdom');
const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(process.env.PGE_ANALYTICS_TEST_SOURCE || path.join(root, 'assets/js/pge-analytics.js'), 'utf8');
const html = fs.readFileSync(path.join(root, 'parts/index.html'), 'utf8');

async function run({ missingCard = false, delayedGrid = false, pathname = '/parts/' } = {}) {
  const dom = new JSDOM(html, { url: 'https://pharmaglobaleng.com' + pathname, runScripts: 'outside-only' });
  const { window } = dom;
  let deliveries = 0;
  const NativeObserver = window.MutationObserver;
  // Bound the old bug's microtask loop so a regression fails rather than hangs CI.
  window.MutationObserver = class extends NativeObserver {
    constructor(callback) {
      super((records, observer) => {
        deliveries++;
        if (deliveries > 25) { observer.disconnect(); return; }
        callback(records, observer);
      });
    }
  };
  const grid = window.document.querySelector('.pc-manufacturer-grid');
  if (missingCard) grid.querySelector('a[href="/parts/cremer/"]').remove();
  if (delayedGrid) grid.remove();
  window.eval(source);
  await new Promise(resolve => setTimeout(resolve, 30));
  if (delayedGrid) {
    window.document.querySelector('main').appendChild(grid);
    await new Promise(resolve => setTimeout(resolve, 150));
  }
  return { dom, window, deliveries };
}

test('catalog startup settles and leaves the event loop responsive', async () => {
  const result = await run();
  try {
    assert.ok(result.deliveries <= 3, `Catalog kept observing its own writes (${result.deliveries} deliveries)`);
    const { document } = result.window;
    assert.equal(document.querySelectorAll('.pc-manufacturer-grid > a[href="/parts/cremer/"]').length, 1);
    assert.equal(document.querySelector('a[href="/parts/cremer/"] .pc-manufacturer-count').textContent, '60 parts');
    assert.equal(document.querySelector('.pc-section-heading > span').textContent, '4,271 part records');
    assert.equal(result.window.dataLayer.filter(args => args[0] === 'config').length, 1);
  } finally { result.dom.window.close(); }
});

test('missing card and delayed catalog still recover without a feedback loop', async () => {
  const result = await run({ missingCard: true, delayedGrid: true });
  try {
    assert.ok(result.deliveries <= 3, `Catalog kept observing its own writes (${result.deliveries} deliveries)`);
    assert.equal(result.window.document.querySelectorAll('.pc-manufacturer-grid > a[href="/parts/cremer/"]').length, 1);
    result.window.eval(source);
    assert.equal(result.window.document.querySelectorAll('script[src*="googletagmanager.com/gtag/js"]').length, 1);
  } finally { result.dom.window.close(); }
});

test('product pages initialize analytics without editing the catalog', async () => {
  const result = await run({ pathname: '/parts/pge-cre-003/' });
  try { assert.equal(result.deliveries, 0); }
  finally { result.dom.window.close(); }
});
