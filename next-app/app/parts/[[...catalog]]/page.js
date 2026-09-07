import { notFound } from 'next/navigation';
import { SITE, pageSizeFor, catalogData, catalogPath, catalogRoutes, findRoute, routeDetails } from '../../../lib/catalog.mjs';
import CatalogShell, { SearchForm, SupplierNotice } from '../../../components/catalog/CatalogShell';
import ProductCard from '../../../components/catalog/ProductCard';
import CatalogSearch from '../../../components/catalog/CatalogSearch';
import '../../../components/catalog/catalog.css';

export const dynamicParams = false;
export function generateStaticParams() { return catalogRoutes().map(r => ({ catalog: r.segments })); }
export async function generateMetadata({ params }) {
  const route = findRoute((await params).catalog || []);
  if (!route) return {};
  const details = routeDetails(route);
  const photo = details.products.find(p => p.image);
  const images = photo ? [{ url: photo.image, alt: photo.alt }] : [];
  return { title: details.title, description: details.description, alternates: { canonical: SITE + route.url }, robots: { index: route.kind !== 'search', follow: true, 'max-image-preview': 'large' }, openGraph: { type: 'website', siteName: 'PharmaGlobalEng', title: details.title, description: details.description, url: SITE + route.url, images }, twitter: { card: photo ? 'summary_large_image' : 'summary', title: details.title, description: details.description, images: photo ? [photo.image] : [] } };
}

function Breadcrumbs({ route, details }) {
  return <nav className="pc-breadcrumbs" aria-label="Breadcrumb"><a href="/">Home</a><span aria-hidden="true">›</span>{route.kind === 'home' ? <span aria-current="page">Parts Store</span> : <><a href="/parts/">Parts Store</a><span aria-hidden="true">›</span>{details.manufacturer ? <>{details.model || route.page > 1 ? <a href={`/parts/${details.manufacturer.slug}/`}>{details.manufacturer.name}</a> : <span aria-current="page">{details.manufacturer.name}</span>}{details.model && <><span aria-hidden="true">›</span><a href={catalogPath(route.brand, route.model)}>{details.model.name}</a></>}{route.page > 1 && <><span aria-hidden="true">›</span><span aria-current="page">Page {route.page}</span></>}</> : <span aria-current="page">Search</span>}</>}</nav>;
}

function Schema({ route, details }) {
  if (route.kind === 'search') return null;
  const breadcrumbs = [{ '@type': 'ListItem', position: 1, name: 'Home', item: SITE + '/' }, { '@type': 'ListItem', position: 2, name: 'Parts Store', item: SITE + '/parts/' }];
  if (details.manufacturer) breadcrumbs.push({ '@type': 'ListItem', position: breadcrumbs.length + 1, name: details.manufacturer.name, item: SITE + `/parts/${route.brand}/` });
  if (details.model) breadcrumbs.push({ '@type': 'ListItem', position: breadcrumbs.length + 1, name: details.model.name, item: SITE + catalogPath(route.brand, route.model) });
  if (route.page > 1) breadcrumbs.push({ '@type': 'ListItem', position: breadcrumbs.length + 1, name: `Page ${route.page}`, item: SITE + route.url });
  const graph = [{ '@type': 'CollectionPage', '@id': SITE + route.url + '#webpage', url: SITE + route.url, name: details.title, description: details.description, isPartOf: { '@id': SITE + '/#website' }, publisher: { '@id': SITE + '/#organization' }, inLanguage: 'en-US' }, { '@type': 'BreadcrumbList', itemListElement: breadcrumbs }];
  if (details.products.length) {
    graph[0].mainEntity = { '@id': SITE + route.url + '#items' };
    graph.push({ '@type': 'ItemList', '@id': SITE + route.url + '#items', name: details.name, numberOfItems: route.total, itemListElement: details.products.map((p, i) => ({ '@type': 'ListItem', position: (route.page - 1) * pageSizeFor(route.brand) + i + 1, name: p.name, url: SITE + p.url })) });
  }
  return <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify({ '@context': 'https://schema.org', '@graph': graph }).replace(/</g, '\\u003c') }} />;
}

function Pagination({ route }) {
  if (route.pages <= 1) return null;
  const numbers = [...new Set([1, route.pages, ...Array.from({ length: 5 }, (_, i) => route.page + i - 2).filter(n => n > 0 && n <= route.pages)])].sort((a,b) => a-b);
  return <nav className="pc-pagination" aria-label="Catalog pages">{route.page > 1 && <a className="pc-page-number" href={catalogPath(route.brand, route.model, route.page - 1)} rel="prev">← Previous</a>}{numbers.map((n,i) => <span className="pc-page-group" key={n}>{i > 0 && n > numbers[i-1] + 1 && <span className="pc-ellipsis" aria-hidden="true">…</span>}<a className="pc-page-number" href={catalogPath(route.brand, route.model, n)} aria-current={n === route.page ? 'page' : undefined} aria-label={`Page ${n}`}>{n}</a></span>)}{route.page < route.pages && <a className="pc-page-number" href={catalogPath(route.brand, route.model, route.page + 1)} rel="next">Next →</a>}</nav>;
}

function Sidebar({ route, details, data }) {
  const { manufacturer, model } = details;
  const families = [...new Set(data.parts.filter(p => p.brand === route.brand && (!route.model || p.modelSlug === route.model)).map(p => p.family))].sort();
  return <aside className="pc-sidebar" aria-label="Catalog navigation"><details className="pc-filter" open><summary>Machine model <span aria-hidden="true">⌃</span></summary><div className="pc-filter-links"><a className={!model ? 'is-active' : ''} href={catalogPath(route.brand)} aria-current={!model && route.page === 1 ? 'page' : undefined}>All models <span>{manufacturer.count.toLocaleString('en-US')}</span></a>{manufacturer.models.map(m => <a key={m.slug} className={model?.slug === m.slug ? 'is-active' : ''} href={catalogPath(route.brand, m.slug)} aria-current={model?.slug === m.slug && route.page === 1 ? 'page' : undefined}>{m.name}<span>{m.count.toLocaleString('en-US')}</span></a>)}</div></details><details className="pc-filter"><summary>Part category <span aria-hidden="true">⌄</span></summary><div className="pc-filter-links">{families.map(f => <a key={f} href={`/parts/search/?${new URLSearchParams({ q: f, brand: route.brand, ...(route.model ? { model: route.model } : {}) })}`}>{f}</a>)}</div></details><details className="pc-filter"><summary>Other manufacturers <span aria-hidden="true">⌄</span></summary><div className="pc-filter-links">{data.manufacturers.map(b => <a key={b.slug} href={`/parts/${b.slug}/`}>{b.name}<span>{b.count.toLocaleString('en-US')}</span></a>)}</div></details><div className="pc-help"><svg viewBox="0 0 32 32" width="36" height="36" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true"><path d="M6 19v-6a10 10 0 0 1 20 0v6M6 13H3v10h5V13H6m20 0h3v10h-5V13h2m0 10v4H15" /></svg><h2>Need help finding a part?</h2><p>Send a reference, drawing, or photograph. Our team can review the match.</p><a className="pc-button pc-button-secondary" href="/parts/identify/">Identify a part <span aria-hidden="true">→</span></a></div></aside>;
}

export default async function CatalogPage({ params }) {
  const route = findRoute((await params).catalog || []);
  if (!route) notFound();
  const data = catalogData();
  const details = routeDetails(route);
  const heroPhoto = route.kind === 'catalog' ? data.parts.find(p => p.brand === route.brand && p.image && (!route.model || p.modelSlug === route.model)) : null;
  return <CatalogShell manufacturers={data.manufacturers}><Schema route={route} details={details} /><section className="pc-hero"><div className="pc-container"><Breadcrumbs route={route} details={details} /><div className="pc-hero-layout"><div className="pc-hero-copy"><p className="pc-kicker">INDEPENDENT REPLACEMENT PARTS</p><h1>{route.kind === 'home' ? <>The right part.<br /><span>A clearer path to it.</span></> : details.name}</h1><p className="pc-lead">{route.kind === 'home' ? 'Browse tablet press components by manufacturer and model. Keep your production moving with a compatibility-led quotation.' : route.kind === 'search' ? 'Search your complete parts catalog—not just the products on one page.' : `Replacement components listed for ${details.subject} equipment. Find the right record by model, part name, or reference.`}</p><SearchForm brand={route.brand} model={route.model} /><div className="pc-hero-points"><span>✓ Existing PGE references</span><span>✓ Machine-model navigation</span><span>✓ Quote before ordering</span></div></div><div className="pc-hero-art" aria-hidden="true">{heroPhoto && <img src={heroPhoto.image} srcSet={heroPhoto.srcSet || undefined} sizes="360px" alt="" width="360" height="280" loading="eager" fetchPriority="high" />}<div className="pc-hero-tag">YOUR MACHINE.<br />YOUR COMPONENT.<br /><strong>THE RIGHT FIT.</strong></div></div></div></div></section>
    <div className="pc-container pc-content">{route.kind === 'home' ? <><div className="pc-section-heading"><div><p className="pc-kicker">EXPLORE THE CATALOG</p><h2>Choose your equipment manufacturer</h2></div><span>{data.parts.length.toLocaleString('en-US')} part records</span></div><div className="pc-manufacturer-grid">{data.manufacturers.map(b => <a className="pc-manufacturer-card" key={b.slug} href={`/parts/${b.slug}/`}><span className="pc-manufacturer-count">{b.count.toLocaleString('en-US')} parts</span><span className="pc-manufacturer-mark" aria-hidden="true">{b.name.slice(0,2).toUpperCase()}</span><h2>{b.name}</h2><p>Browse by machine model, part name, or existing reference.</p><strong>Browse replacement parts <span aria-hidden="true">→</span></strong></a>)}<a className="pc-manufacturer-card pc-identify-card" href="/parts/identify/"><span className="pc-manufacturer-mark" aria-hidden="true">+</span><h2>Not sure which part?</h2><p>Start with a photo, drawing, or machine reference.</p><strong>Get identification help <span aria-hidden="true">→</span></strong></a></div><SupplierNotice /></> : route.kind === 'search' ? <><CatalogSearch manufacturers={data.manufacturers} /><noscript><p>Interactive search needs JavaScript. All products remain accessible through the manufacturer and numbered catalog pages below.</p></noscript><div className="pc-model-shortcuts">{data.manufacturers.map(b => <a href={`/parts/${b.slug}/`} key={b.slug}>{b.name} parts →</a>)}</div><SupplierNotice /></> : <><div className="pc-catalog-layout"><Sidebar route={route} details={details} data={data} /><div className="pc-products"><div className="pc-toolbar"><p><strong>{route.total.toLocaleString('en-US')}</strong> part records{details.model ? ` · ${details.model.name}` : ''}</p><span>Catalog order <span aria-hidden="true">·</span> {pageSizeFor(route.brand)} per page</span></div><div className="pc-grid">{details.products.map(p => <ProductCard key={p.sku} part={p} />)}</div><div className="pc-pagination-row"><Pagination route={route} /><p>Showing {((route.page - 1) * pageSizeFor(route.brand) + 1).toLocaleString('en-US')}–{Math.min(route.page * pageSizeFor(route.brand), route.total).toLocaleString('en-US')} of {route.total.toLocaleString('en-US')}</p></div><SupplierNotice name={details.manufacturer.name} /></div></div></>}</div>
  </CatalogShell>;
}
