'use client';

import { createContext, useContext, useEffect, useRef, useState } from 'react';
const Context = createContext(null);
const STORAGE_KEY = 'pge-parts-quote-cart-v1';
const safePart = p => p && typeof p.sku === 'string' && typeof p.name === 'string' && /^\/parts\/pge-[a-z0-9-]+\/$/i.test(p.url || '');

export function QuoteProvider({ children }) {
  const [cart, setCart] = useState({});
  const [ready, setReady] = useState(false);
  const [storageWarning, setStorageWarning] = useState(false);
  const dialog = useRef(null);
  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
      setCart(Object.fromEntries(Object.values(saved || {}).filter(safePart).map(p => [p.sku, { ...p, quantity: Math.min(999, Math.max(1, Number(p.quantity) || 1)) }])));
    } catch { setStorageWarning(true); }
    setReady(true);
  }, []);
  function save(next) {
    setCart(next);
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(next)); }
    catch { setStorageWarning(true); }
  }
  function open() { if (dialog.current && !dialog.current.open) dialog.current.showModal(); }
  function toggle(part) {
    if (!ready || !safePart(part)) return;
    const next = { ...cart };
    if (next[part.sku]) delete next[part.sku];
    else next[part.sku] = { sku: part.sku, name: part.name, brand: part.brandName || part.brand, model: part.model, url: part.url, quantity: 1 };
    save(next);
    if (next[part.sku]) open();
  }
  const selected = Object.values(cart);
  const lines = selected.map(p => `- ${p.name} (${p.sku}) | ${p.brand} ${p.model} | Qty ${p.quantity}`);
  const emailBody = `Hello PharmaGlobalEng,\n\nPlease review these parts for compatibility, availability, lead time, and pricing:\n\n${lines.join('\n')}\n\nMachine serial number/configuration:\nExisting part or drawing references:\nShipping destination:\nRequired timing:\nAdditional information:\n`;
  const emailUrl = `mailto:info@pharmaglobaleng.com?subject=${encodeURIComponent(`Parts quote cart — ${selected.length} selected components`)}&body=${encodeURIComponent(emailBody)}`;
  return <Context.Provider value={{ cart, toggle, open, ready }}>
    {children}
    <dialog className="pc-quote" ref={dialog} aria-labelledby="pc-quote-title" onClick={event => { if (event.target === dialog.current) { const r = dialog.current.getBoundingClientRect(); if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) dialog.current.close(); } }}>
      <div className="pc-quote-head"><div><span className="pc-kicker">COMPATIBILITY & PRICE REQUEST</span><h2 id="pc-quote-title">Your quote cart</h2></div><button type="button" className="pc-icon-button" aria-label="Close quote cart" onClick={() => dialog.current.close()}>×</button></div>
      {storageWarning && <p role="status">Browser storage is unavailable. Your selection may not persist when you leave this page.</p>}
      <div className="pc-quote-items">{selected.length ? selected.map(p => <div className="pc-quote-item" key={p.sku}><div><a href={p.url}>{p.name}</a><small>{p.sku} · {p.brand} {p.model}</small></div><label>Qty<input type="number" min="1" max="999" value={p.quantity} onChange={e => save({ ...cart, [p.sku]: { ...p, quantity: Math.min(999, Math.max(1, Number(e.target.value) || 1)) } })} /></label><button type="button" className="pc-icon-button" aria-label={`Remove ${p.name}`} onClick={() => { const next = { ...cart }; delete next[p.sku]; save(next); }}>×</button></div>) : <p>Your quote cart is empty. Add a part from the catalog to get started.</p>}</div>
      <div className="pc-quote-actions"><button type="button" className="pc-button pc-button-secondary" disabled={!selected.length} onClick={() => save({})}>Clear cart</button><a className="pc-button pc-button-primary" aria-disabled={!selected.length} href={selected.length ? emailUrl : '#'} onClick={e => { if (!selected.length) e.preventDefault(); }}>Email quote request</a></div>
      <p className="pc-small">Compatibility, availability, lead time, and pricing are confirmed after review. No payment is collected here.</p>
    </dialog>
  </Context.Provider>;
}

export function QuoteTrigger() {
  const { cart, open, ready } = useContext(Context);
  return <button type="button" className="pc-button pc-button-primary pc-cart-trigger" onClick={open} disabled={!ready} aria-haspopup="dialog"><svg viewBox="0 0 24 24" width="19" height="19" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="M3 3h2l3 12h11l2-8H6M9 21h.01M18 21h.01" strokeLinecap="round" /></svg>Quote cart <span data-pc-cart-count>{Object.keys(cart).length}</span></button>;
}

export function QuoteButton({ part }) {
  const { cart, toggle, ready } = useContext(Context);
  return <button type="button" className="pc-button pc-button-primary pc-add" disabled={!ready} aria-pressed={Boolean(cart[part.sku])} data-pc-add={part.sku} onClick={() => toggle(part)}>{cart[part.sku] ? 'Added ✓' : '+ Add to quote'}</button>;
}
