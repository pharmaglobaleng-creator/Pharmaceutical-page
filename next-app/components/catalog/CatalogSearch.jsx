'use client';

import { useEffect, useState } from 'react';
import ProductCard from './ProductCard';
const normalize = value => String(value || '').normalize('NFKD').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
const compact = value => normalize(value).replace(/ /g, '');
const PAGE_SIZE = 50;

export default function CatalogSearch({ manufacturers }) {
  const [state, setState] = useState({ loading: true, rows: [], query: '', page: 1, brand: '', model: '' });
  const [sort, setSort] = useState('relevance');
  useEffect(() => {
    const controller = new AbortController();
    const query = new URLSearchParams(window.location.search);
    const q = (query.get('q') || '').trim().slice(0, 160);
    const brand = query.get('brand') || '';
    const model = query.get('model') || '';
    const page = Math.max(1, parseInt(query.get('page') || '1', 10) || 1);
    const targets = brand ? manufacturers.filter(b => b.slug === brand) : manufacturers;
    if (!q || !targets.length) { setState({ loading: false, rows: [], query: q, page: 1, brand, model }); return () => controller.abort(); }
    Promise.all(targets.map(async b => {
      const response = await fetch(`/catalog-data/${b.slug}.json?v=${b.searchVersion}`, { signal: controller.signal });
      if (!response.ok) throw new Error('Catalog search could not load.');
      return response.json();
    })).then(groups => {
      const terms = normalize(q).split(/\s+/).filter(Boolean);
      const rows = groups.flat().filter(p => {
        if (model && p.modelSlug !== model) return false;
        const haystack = normalize([p.name, p.sku, p.oem, p.brandName, p.model, p.family].join(' '));
        return terms.every(t => haystack.includes(t)) || compact(haystack).includes(compact(q));
      });
      rows.sort((a,b) => Number(compact(b.sku) === compact(q) || compact(b.oem) === compact(q)) - Number(compact(a.sku) === compact(q) || compact(a.oem) === compact(q)));
      setState({ loading: false, rows, query: q, page: Math.min(page, Math.max(1, Math.ceil(rows.length / PAGE_SIZE))), brand, model });
    }).catch(error => { if (error.name !== 'AbortError') setState({ loading: false, rows: [], query: q, page: 1, brand, model, error: 'Search is temporarily unavailable. Browse the manufacturer and model pages below, or reload to try again.' }); });
    return () => controller.abort();
  }, [manufacturers]);
  if (state.loading) return <p className="pc-search-status" role="status">Loading catalog search…</p>;
  const rows = [...state.rows];
  if (sort === 'name') rows.sort((a,b) => a.name.localeCompare(b.name, 'en', { numeric: true }));
  const pages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
  const results = rows.slice((state.page - 1) * PAGE_SIZE, state.page * PAGE_SIZE);
  function changePage(page) {
    setState(s => ({ ...s, page }));
    const u = new URL(window.location.href); u.searchParams.set('page', String(page)); window.history.replaceState(null, '', u);
    document.getElementById('pc-search-results')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
  return <section id="pc-search-results" aria-label="Search results"><div className="pc-toolbar"><h2 role="status">{state.query ? `${rows.length.toLocaleString('en-US')} results for “${state.query}”` : 'Enter a part name or reference above'}</h2><label>Sort by <select value={sort} onChange={e => { setSort(e.target.value); setState(s => ({ ...s, page: 1 })); }}><option value="relevance">Best match</option><option value="name">Part name A–Z</option></select></label></div>{state.error && <p role="alert">{state.error}</p>}{!state.error && state.query && !rows.length && <p>No matching parts found. Try the PGE number, a shorter part name, or another model. <a href="/parts/identify/">Request help identifying a part.</a></p>}<div className="pc-grid">{results.map(p => <ProductCard part={p} key={p.sku} />)}</div>{pages > 1 && <nav className="pc-pagination" aria-label="Search results pages"><button className="pc-page-number" disabled={state.page === 1} onClick={() => changePage(state.page - 1)}>← Previous</button><span>Page {state.page} of {pages}</span><button className="pc-page-number" disabled={state.page === pages} onClick={() => changePage(state.page + 1)}>Next →</button></nav>}<p className="pc-small">Search uses the complete catalog, not only the first page of products. Compatibility must be confirmed during quotation.</p></section>;
}
