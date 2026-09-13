import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import { catalogData, pageSizeFor } from '../lib/catalog.mjs';
const data = catalogData();

test('manufacturer catalogs and pagination are readable without JavaScript', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  for (const brand of data.manufacturers) {
    await page.goto(`http://127.0.0.1:4173/parts/${brand.slug}/`);
    await expect(page.locator('.pc-card')).toHaveCount(Math.min(pageSizeFor(brand.slug),brand.count));
    await expect(page.locator('h1')).toContainText(brand.name);
    if (brand.count > pageSizeFor(brand.slug)) {
      await page.getByRole('link',{name:'Next →',exact:true}).click();
      await expect(page).toHaveURL(new RegExp(`/parts/${brand.slug}/page/2/`));
      await expect(page.locator('link[rel=canonical]')).toHaveAttribute('href',`https://pharmaglobaleng.com/parts/${brand.slug}/page/2/`);
    }
  }
  await context.close();
});

test('Quadro records stay in five-page order with the matched name, model, OEM and image', async ({ page }) => {
  const rows = data.parts.filter(part => part.brand === 'quadro');
  expect(rows).toHaveLength(113);
  for (let number = 1; number <= 5; number++) {
    await page.goto(number === 1 ? '/parts/quadro/' : `/parts/quadro/page/${number}/`);
    const expected = rows.slice((number - 1) * 24, number * 24);
    await expect(page.locator('.pc-card')).toHaveCount(expected.length);
    expect(await page.locator('.pc-card').evaluateAll(cards => cards.map(card => card.dataset.pcSku))).toEqual(expected.map(part => part.sku));
    await expect(page.locator('.pc-identifiers dt', { hasText: 'Replacement OEM Number' })).toHaveCount(expected.length);
  }
  const target = rows[0];
  await page.goto(target.url);
  await expect(page.locator('h1')).toContainText(target.name);
  await expect(page.locator('.compatibility')).toContainText(`Replacement OEM Number: ${target.oem}`);
  await expect(page.locator('.compatibility')).toContainText(`Model: ${target.model}`);
  await expect(page.locator('.part-image img')).toHaveAttribute('src', target.image);
  await expect(page.locator('body')).not.toContainText(/PharmParts/i);
});

test('machine model links open their own landing pages', async ({ page }) => {
  const brand = data.manufacturers.find(b => b.slug === 'kikusui');
  const model = brand.models.find(m => m.name === 'LIBRA') || brand.models[0];
  await page.goto(`/parts/kikusui/${model.slug}/`);
  await expect(page.locator('h1')).toContainText(model.name);
  await expect(page.locator('.pc-card')).toHaveCount(Math.min(pageSizeFor(brand.slug),model.count));
});

test('search finds a product beyond the first catalog page', async ({ page }) => {
  const rows = data.parts.filter(p => p.brand === 'stokes');
  const target = rows[rows.length-1];
  await page.goto('/parts/stokes/');
  await page.getByLabel('Search part name, model, OEM, or PGE number').fill(target.sku);
  await page.getByRole('button',{name:/^Search/}).click();
  await expect(page.locator(`[data-pc-sku="${target.sku}"]`)).toBeVisible();
  await expect(page.locator('.pc-card')).toHaveCount(1);
  await expect(page.locator('meta[name=robots]')).toHaveAttribute('content',/noindex/);
});

test('new quote cart preserves the existing product-page cart format', async ({ page }) => {
  const target = data.parts.find(p => p.brand === 'stokes');
  await page.goto('/parts/stokes/');
  const add = page.locator(`[data-pc-add="${target.sku}"]`);
  await expect(add).toBeEnabled();
  await add.click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.getByRole('dialog').getByLabel('Qty').fill('2');
  await page.getByRole('button',{name:'Close quote cart',exact:true}).click();
  await page.goto(target.url);
  await expect(page.locator('[data-pge-cart-count]')).toHaveText('1');
  const stored = await page.evaluate(sku => JSON.parse(localStorage.getItem('pge-parts-quote-cart-v1'))[sku],target.sku);
  expect(stored.quantity).toBe(2); expect(stored.url).toBe(target.url);
  await page.goto('/parts/stokes/page/2/');
  await expect(page.locator('[data-pc-cart-count]')).toHaveText('1');
});

test('desktop and mobile layout, image loading and screenshots', async ({ page }) => {
  const errors=[]; page.on('pageerror',e=>errors.push(e.message));
  await page.goto('/parts/stokes/');
  await expect(page.locator('.pc-cart-trigger')).toBeEnabled();
  await page.waitForTimeout(800);
  for (const img of await page.locator('.pc-card img').all()) {
    if (await img.isVisible()) {
      const box=await img.boundingBox();
      if (box && box.y < 1152) expect(await img.evaluate(e=>e.complete && e.naturalWidth>0)).toBeTruthy();
    }
  }
  fs.mkdirSync('test-results/screenshots',{recursive:true});
  await page.screenshot({path:'test-results/screenshots/catalog-desktop.png'});
  await page.setViewportSize({width:390,height:844});
  await page.waitForTimeout(300);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
  await page.screenshot({path:'test-results/screenshots/catalog-mobile.png'});
  await page.locator('.pc-mobile-nav summary').click();
  await expect(page.locator('.pc-mobile-nav nav')).toBeVisible();
  expect(errors).toEqual([]);
});
