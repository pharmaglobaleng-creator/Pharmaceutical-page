import { QuoteButton } from './QuoteCart';

export default function ProductCard({ part }) {
  const quotePart = { sku: part.sku, name: part.name, brandName: part.brandName, brand: part.brand, model: part.model, url: part.url };
  return <article className="pc-card" data-pc-sku={part.sku}>
    <a className="pc-card-image" href={part.url} tabIndex={-1} aria-hidden="true">{part.image ? <img src={part.image} srcSet={part.srcSet || undefined} sizes="(max-width: 550px) 90vw, (max-width: 800px) 44vw, (max-width: 1200px) 28vw, 22vw" alt={part.alt} width={part.imageWidth || 760} height={part.imageHeight || 760} loading="lazy" decoding="async" /> : <span className="pc-photo-unavailable"><svg viewBox="0 0 48 48" width="42" height="42" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="7" y="9" width="34" height="29" rx="3" /><circle cx="18" cy="19" r="3" /><path d="m9 35 10-9 6 6 6-13 9 16" /></svg>Photo unavailable<span>No substitute image used</span></span>}</a>
    <div className="pc-card-content"><p className="pc-card-family">{part.family}</p><h2><a href={part.url}>{part.name}</a></h2><dl className="pc-identifiers"><div><dt>Model</dt><dd>{part.brandName} {part.model}</dd></div><div><dt>PGE number</dt><dd>{part.sku}</dd></div><div><dt>OEM reference</dt><dd>{part.oem}</dd></div></dl><div className="pc-card-actions"><a href={part.url} className="pc-button pc-button-secondary">View details <span aria-hidden="true">↗</span></a><QuoteButton part={quotePart} /></div></div>
  </article>;
}
