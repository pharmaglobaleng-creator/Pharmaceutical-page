/* Pharma Global Website GA4: visitor and traffic reporting. */
(function () {
  'use strict';

  // Navigation works independently of analytics consent, network, and hostname.
  function addSectionShortcuts() {
    if (!['/', '/index.html'].includes(window.location.pathname)) return;
    if (document.querySelector('.pge-section-shortcuts')) return;
    var target = document.querySelector('#home');
    if (!target) return;
    var nav = document.createElement('nav');
    nav.className = 'pge-section-shortcuts';
    nav.setAttribute('aria-label', 'Explore this page');
    [['/parts/', 'Find replacement parts'], ['#components', 'Components'],
      ['#evidence-and-evaluation', 'Research and evidence'],
      ['#request-evaluation-guide', 'Request an evaluation'],
      ['#technical-library', 'Technical guides'], ['#faq', 'FAQs']].forEach(function (item) {
      if (item[0][0] === '#' && !document.getElementById(item[0].slice(1))) return;
      var link = document.createElement('a');
      link.href = item[0]; link.textContent = item[1]; nav.appendChild(link);
    });
    target.prepend(nav);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', addSectionShortcuts, {once:true});
  else addSectionShortcuts();

  if (!['pharmaglobaleng.com', 'www.pharmaglobaleng.com'].includes(window.location.hostname)) return;
  if (window.pgeAnalyticsInitialized) return;
  window.pgeAnalyticsInitialized = true;

  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
  window.gtag('js', new Date());
  window.gtag('config', 'G-1ES31F0R1F', {
    allow_google_signals: false,
    allow_ad_personalization_signals: false
  });

  // Count inquiry intent, never message contents, addresses, or form values.
  document.addEventListener('click', function (event) {
    var link = event.target.closest && event.target.closest('a[href]');
    if (!link || event.defaultPrevented) return;
    var href = link.getAttribute('href') || '';
    var method = /^tel:/i.test(href) ? 'phone' : /^mailto:/i.test(href) ? 'email' : '';
    if (!method) return;
    window.gtag('event', 'inquiry_click', {
      contact_method: method,
      page_path: window.location.pathname,
      inquiry_context: link.classList.contains('pge-cart-email') ? 'quote_cart' : 'page'
    });
  });

  var tag = document.createElement('script');
  tag.async = true;
  tag.src = 'https://www.googletagmanager.com/gtag/js?id=G-1ES31F0R1F';
  document.head.appendChild(tag);

  if ((window.location.pathname === '/parts/' || window.location.pathname === '/parts') && !document.querySelector('[data-pge-catalog-entry="static"]')) {
    function setText(element, value) {
      if (element && element.textContent !== value) element.textContent = value;
    }

    function ensureCreamerCatalogCard() {
      var grid = document.querySelector('.pc-manufacturer-grid');
      if (!grid) return false;

      var identify = grid.querySelector('.pc-identify-card');
      var card = grid.querySelector('a[href="/parts/cremer/"]');

      if (!card) {
        card = document.createElement('a');
        card.className = 'pc-manufacturer-card';
        card.href = '/parts/cremer/';
        card.innerHTML = '<span class="pc-manufacturer-count">60 parts</span>' +
          '<span class="pc-manufacturer-mark" aria-hidden="true">CR</span>' +
          '<h2>Creamer</h2>' +
          '<p>Browse Creamer replacement components by machine model, part name, and reference.</p>' +
          '<strong>Browse replacement parts <span aria-hidden="true">→</span></strong>';
      } else {
        var title = card.querySelector('h2');
        setText(title, 'Creamer');
        var copy = card.querySelector('p');
        setText(copy, 'Browse Creamer replacement components by machine model, part name, and reference.');
        var partCount = card.querySelector('.pc-manufacturer-count');
        setText(partCount, '60 parts');
      }

      if (identify) {
        if (card.parentNode !== grid || card.nextElementSibling !== identify) {
          grid.insertBefore(card, identify);
        }
      } else if (card.parentNode !== grid) {
        grid.appendChild(card);
      }

      var count = document.querySelector('.pc-section-heading > span');
      setText(count, '4,271 part records');

      document.querySelectorAll('.pc-nav-menu div, .pc-mobile-nav nav').forEach(function (nav) {
        var link = nav.querySelector('a[href="/parts/cremer/"]');
        if (!link) {
          link = document.createElement('a');
          link.href = '/parts/cremer/';
          var identifyLink = nav.querySelector('a[href="/parts/identify/"]');
          if (identifyLink) nav.insertBefore(link, identifyLink);
          else nav.appendChild(link);
        }
        setText(link, 'Creamer parts');
      });

      return true;
    }

    function runCreamerFixes() {
      ensureCreamerCatalogCard();
      // Bounded retries cover hydration without observing our own DOM writes.
      [100, 300, 700, 1200, 2200, 4000].forEach(function (delay) {
        setTimeout(ensureCreamerCatalogCard, delay);
      });
    }

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', runCreamerFixes, { once: true });
    } else {
      runCreamerFixes();
    }

  }
}());
