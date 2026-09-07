import fs from 'node:fs';
import path from 'node:path';

export const SITE = 'https://pharmaglobaleng.com';
export const PAGE_SIZE = 50;
export function pageSizeFor(brand) { return brand === 'manesty' ? 25 : PAGE_SIZE; }
let cached;
export function catalogData() {
  cached ??= JSON.parse(fs.readFileSync(path.join(process.cwd(), 'data/parts-catalog.json'), 'utf8'));
  return cached;
}
export function catalogPath(brand, model = null, page = 1) {
  const base = `/parts/${brand}/${model ? `${model}/` : ''}`;
  return page === 1 ? base : `${base}page/${page}/`;
}
export function catalogRoutes() {
  const data = catalogData();
  const routes = [{ segments: [], kind: 'home', url: '/parts/' }, { segments: ['search'], kind: 'search', url: '/parts/search/' }];
  for (const manufacturer of data.manufacturers) {
    const pageSize = pageSizeFor(manufacturer.slug);
    for (const model of [null, ...manufacturer.models]) {
      const rows = data.parts.filter(p => p.brand === manufacturer.slug && (!model || p.modelSlug === model.slug));
      const pages = Math.ceil(rows.length / pageSize);
      for (let page = 1; page <= pages; page++) {
        const url = catalogPath(manufacturer.slug, model?.slug, page);
        routes.push({ segments: url.slice('/parts/'.length).split('/').filter(Boolean), kind: 'catalog', url, brand: manufacturer.slug, model: model?.slug || null, page, pages, total: rows.length, skus: rows.slice((page - 1) * pageSize, page * pageSize).map(p => p.sku) });
      }
    }
  }
  return routes;
}
export function findRoute(segments = []) {
  return catalogRoutes().find(r => r.segments.join('/') === segments.join('/'));
}
export function routeDetails(route) {
  const data = catalogData();
  const manufacturer = data.manufacturers.find(b => b.slug === route.brand);
  const model = manufacturer?.models.find(m => m.slug === route.model);
  const subject = manufacturer ? `${manufacturer.name}${model ? ` ${model.name}` : ''}` : '';
  const name = route.kind === 'home' ? 'Tablet Press Replacement Parts' : route.kind === 'search' ? 'Search Replacement Parts' : `${subject} Replacement Parts`;
  const title = `${name}${route.page > 1 ? ` — Page ${route.page}` : ''} | PharmaGlobalEng`;
  const description = route.kind === 'home' ? 'Browse independent tablet press replacement components by manufacturer and machine model. View existing PGE identifiers, images, and catalog-supplied references, then request a quote.' : route.kind === 'search' ? 'Search the PharmaGlobalEng replacement-parts catalog by part name, machine model, OEM reference, or PGE number.' : `Browse ${route.total.toLocaleString('en-US')} independent replacement-part records for ${subject}.${route.page > 1 ? ` Page ${route.page} of ${route.pages}.` : ''} Compare existing part references and images; confirm compatibility during quotation.`;
  const wanted = new Set(route.skus || []);
  return { manufacturer, model, subject, name, title, description, products: data.parts.filter(p => wanted.has(p.sku)) };
}
