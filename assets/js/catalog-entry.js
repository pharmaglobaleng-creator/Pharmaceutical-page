/* Optional quote-cart enhancement. Catalog links and search use native HTML. */
(() => {
  'use strict';
  const root = document.querySelector('[data-pge-catalog-entry="static"]');
  if (!root || root.dataset.cartReady) return;
  root.dataset.cartReady = 'true';
  const trigger = root.querySelector('.pc-cart-trigger');
  const dialog = document.querySelector('dialog.pc-quote');
  if (!trigger || !dialog) return;
  const key = 'pge-parts-quote-cart-v1';
  const items = dialog.querySelector('.pc-quote-items');
  const clear = dialog.querySelector('.pc-quote-actions button');
  const email = dialog.querySelector('.pc-quote-actions a');
  const count = trigger.querySelector('[data-pc-cart-count]');
  const warning = document.createElement('p');
  warning.setAttribute('role', 'status');
  warning.hidden = true;
  warning.textContent = 'Browser storage is unavailable. Your selection may not persist when you leave this page.';
  dialog.insertBefore(warning, items);
  const quantity = value => Math.min(999, Math.max(1, Math.floor(Number(value)) || 1));
  const valid = part => part && typeof part.sku === 'string' && typeof part.name === 'string' && /^\/parts\/pge-[a-z0-9-]+\/$/i.test(part.url || '');
  let cart = {};
  function read() {
    try {
      const stored = JSON.parse(localStorage.getItem(key) || '{}');
      cart = Object.fromEntries(Object.values(stored || {}).filter(valid).map(part => [part.sku, { ...part, quantity: quantity(part.quantity) }]));
    } catch (_) { warning.hidden = false; }
  }
  function save(refreshItems = true) {
    try { localStorage.setItem(key, JSON.stringify(cart)); }
    catch (_) { warning.hidden = false; }
    render(refreshItems);
  }
  function render(refreshItems = true) {
    const selected = Object.values(cart);
    count.textContent = selected.length;
    if (refreshItems) {
      items.replaceChildren();
      if (!selected.length) {
        const empty = document.createElement('p');
        empty.textContent = 'Your quote cart is empty. Add a part from the catalog to get started.';
        items.appendChild(empty);
      }
      selected.forEach(part => {
        const row = document.createElement('div');
        row.className = 'pc-quote-item';
        const identity = document.createElement('div');
        const link = document.createElement('a');
        link.href = part.url;
        link.textContent = part.name;
        const reference = document.createElement('small');
        reference.textContent = `${part.sku} · ${part.brand || ''} ${part.model || ''}`;
        identity.append(link, reference);
        const label = document.createElement('label');
        label.textContent = 'Qty';
        const input = document.createElement('input');
        input.type = 'number'; input.min = '1'; input.max = '999'; input.value = part.quantity;
        input.addEventListener('change', () => {
          if (!cart[part.sku]) return;
          cart[part.sku].quantity = quantity(input.value);
          input.value = cart[part.sku].quantity;
          // Keep the focused input in place; removing it can fire another change.
          save(false);
        });
        label.appendChild(input);
        const remove = document.createElement('button');
        remove.type = 'button'; remove.className = 'pc-icon-button'; remove.textContent = '×';
        remove.setAttribute('aria-label', `Remove ${part.name}`);
        remove.addEventListener('click', () => { delete cart[part.sku]; save(); });
        row.append(identity, label, remove); items.appendChild(row);
      });
    }
    clear.disabled = !selected.length;
    email.setAttribute('aria-disabled', String(!selected.length));
    const lines = selected.map(p => `- ${p.name} (${p.sku}) | ${p.brand || ''} ${p.model || ''} | Qty ${p.quantity}`);
    const body = `Hello PharmaGlobalEng,\n\nPlease review these parts for compatibility, availability, lead time, and pricing:\n\n${lines.join('\n')}\n\nMachine serial number/configuration:\nExisting part or drawing references:\nShipping destination:\nRequired timing:\nAdditional information:\n`;
    email.href = selected.length ? `mailto:info@pharmaglobaleng.com?subject=${encodeURIComponent(`Parts quote cart — ${selected.length} selected components`)}&body=${encodeURIComponent(body)}` : '#';
  }
  trigger.disabled = false;
  trigger.addEventListener('click', () => { read(); render(); if (!dialog.open) dialog.showModal(); });
  dialog.querySelector('[aria-label="Close quote cart"]').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const box = dialog.getBoundingClientRect();
    if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close();
  });
  clear.addEventListener('click', () => { cart = {}; save(); });
  email.addEventListener('click', event => { if (!Object.keys(cart).length) event.preventDefault(); });
  window.addEventListener('storage', event => { if (event.key === key) { read(); render(); } });
  read(); render();
})();
