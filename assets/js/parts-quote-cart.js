(() => {
  const storageKey = 'pge-parts-quote-cart-v1';
  const readCart = () => {
    try { return JSON.parse(localStorage.getItem(storageKey) || '{}'); }
    catch (_) { return {}; }
  };
  let cart = readCart();
  const save = () => localStorage.setItem(storageKey, JSON.stringify(cart));
  const esc = value => String(value || '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));

  const shell = document.createElement('div');
  shell.className = 'pge-quote-cart';
  shell.innerHTML = `
    <button class="pge-cart-trigger" type="button" aria-expanded="false" aria-controls="pge-cart-panel">Quote Cart <span data-pge-cart-count>0</span></button>
    <aside class="pge-cart-panel" id="pge-cart-panel" hidden aria-labelledby="pge-cart-title">
      <div class="pge-cart-head"><div><small>Compatibility & price request</small><h2 id="pge-cart-title">Quote Cart</h2></div><button class="pge-cart-close" type="button" aria-label="Close quote cart">×</button></div>
      <div class="pge-cart-items"></div>
      <div class="pge-cart-actions"><button class="pge-cart-clear" type="button">Clear cart</button><a class="btn primary pge-cart-email" href="#">Email quote request</a></div>
      <p class="pge-cart-note">Compatibility, availability, lead time, and pricing are confirmed after engineering review.</p>
    </aside>`;
  document.body.appendChild(shell);

  const trigger = shell.querySelector('.pge-cart-trigger');
  const panel = shell.querySelector('.pge-cart-panel');
  const items = shell.querySelector('.pge-cart-items');
  const email = shell.querySelector('.pge-cart-email');
  const clear = shell.querySelector('.pge-cart-clear');
  const count = shell.querySelector('[data-pge-cart-count]');

  const partFromButton = button => ({
    sku: button.dataset.partSku,
    name: button.dataset.partName,
    brand: button.dataset.partBrand,
    model: button.dataset.partModel,
    url: button.dataset.partUrl,
    quantity: Number(button.dataset.partQuantity || 1)
  });

  const inquiryUrl = () => {
    const selected = Object.values(cart);
    const lines = selected.map(part => `- ${part.name} (${part.sku}) | ${part.brand} ${part.model} | Qty ${part.quantity}`);
    const subject = `Parts quote cart — ${selected.length} selected component${selected.length === 1 ? '' : 's'}`;
    const body = `Hello PharmaGlobalEng,\n\nPlease review this parts cart for compatibility, availability, lead time, and pricing:\n\n${lines.join('\n')}\n\nMachine manufacturer/model:\nMachine serial number/configuration:\nExisting part or drawing references:\nShipping destination:\nRequired timing:\nAdditional information:\n`;
    return `mailto:info@pharmaglobaleng.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  };

  const updateButtons = () => document.querySelectorAll('[data-pge-cart-add]').forEach(button => {
    const selected = Boolean(cart[button.dataset.partSku]);
    button.setAttribute('aria-pressed', selected ? 'true' : 'false');
    button.textContent = selected ? 'Remove from Quote Cart' : 'Add to Quote Cart';
  });

  const render = () => {
    const selected = Object.values(cart);
    count.textContent = selected.length;
    items.innerHTML = selected.length ? selected.map(part => `
      <div class="pge-cart-item" data-cart-sku="${esc(part.sku)}">
        <div><strong>${esc(part.name)}</strong><small>${esc(part.sku)} · ${esc(part.brand)} ${esc(part.model)}</small></div>
        <label>Qty <input type="number" min="1" max="999" value="${Number(part.quantity) || 1}" data-cart-qty></label>
        <button type="button" data-cart-remove aria-label="Remove ${esc(part.name)}">×</button>
      </div>`).join('') : '<p class="pge-cart-empty">Your quote cart is empty.</p>';
    email.href = selected.length ? inquiryUrl() : '#';
    email.setAttribute('aria-disabled', selected.length ? 'false' : 'true');
    clear.disabled = !selected.length;
    items.querySelectorAll('[data-cart-qty]').forEach(input => input.addEventListener('change', event => {
      const row = event.target.closest('[data-cart-sku]');
      cart[row.dataset.cartSku].quantity = Math.max(1, Number(event.target.value) || 1);
      save(); render();
    }));
    items.querySelectorAll('[data-cart-remove]').forEach(button => button.addEventListener('click', event => {
      const row = event.target.closest('[data-cart-sku]');
      delete cart[row.dataset.cartSku]; save(); render();
    }));
    updateButtons();
  };

  document.querySelectorAll('[data-pge-cart-add]').forEach(button => button.addEventListener('click', () => {
    const part = partFromButton(button);
    if (cart[part.sku]) delete cart[part.sku]; else cart[part.sku] = part;
    save(); render();
    if (cart[part.sku]) { panel.hidden = false; trigger.setAttribute('aria-expanded', 'true'); }
  }));
  trigger.addEventListener('click', () => { panel.hidden = !panel.hidden; trigger.setAttribute('aria-expanded', String(!panel.hidden)); });
  shell.querySelector('.pge-cart-close').addEventListener('click', () => { panel.hidden = true; trigger.setAttribute('aria-expanded', 'false'); });
  clear.addEventListener('click', () => { cart = {}; save(); render(); });
  email.addEventListener('click', event => { if (!Object.keys(cart).length) event.preventDefault(); });
  render();
})();
