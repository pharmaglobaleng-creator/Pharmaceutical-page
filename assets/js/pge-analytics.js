/* Pharma Global Website GA4: visitor and traffic reporting. */
(function () {
  'use strict';

  // Keep previews and repeated initialization out of production reporting.
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

  var tag = document.createElement('script');
  tag.async = true;
  tag.src = 'https://www.googletagmanager.com/gtag/js?id=G-1ES31F0R1F';
  document.head.appendChild(tag);

  // Parts catalog guard: if an edge/browser cache serves the older 4,211-part
  // catalog HTML, insert the Cremer manufacturer card into the same grid.
  // The current repository HTML already contains this card; this only repairs
  // stale rendered copies and avoids duplicate insertion.
  if (window.location.pathname === '/parts/' || window.location.pathname === '/parts') {
    function ensureCremerCatalogCard() {
      var grid = document.querySelector('.pc-manufacturer-grid');
      if (!grid || grid.querySelector('a[href="/parts/cremer/"]')) return;

      var identify = grid.querySelector('.pc-identify-card');
      var card = document.createElement('a');
      card.className = 'pc-manufacturer-card';
      card.href = '/parts/cremer/';
      card.innerHTML = '<span class="pc-manufacturer-count">1 part</span>' +
        '<span class="pc-manufacturer-mark" aria-hidden="true">CR</span>' +
        '<h2>Cremer</h2>' +
        '<p>Browse Cremer replacement components by machine model, part name, and reference.</p>' +
        '<strong>Browse replacement parts <span aria-hidden="true">→</span></strong>';

      if (identify) grid.insertBefore(card, identify);
      else grid.appendChild(card);

      var count = document.querySelector('.pc-section-heading > span');
      if (count && /4,211\s*part records/i.test(count.textContent || '')) {
        count.textContent = '4,212 part records';
      }

      document.querySelectorAll('.pc-nav-menu div, .pc-mobile-nav nav').forEach(function (nav) {
        if (!nav.querySelector('a[href="/parts/cremer/"]')) {
          var identifyLink = nav.querySelector('a[href="/parts/identify/"]');
          var link = document.createElement('a');
          link.href = '/parts/cremer/';
          link.textContent = 'Cremer parts';
          if (identifyLink) nav.insertBefore(link, identifyLink);
          else nav.appendChild(link);
        }
      });
    }

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', ensureCremerCatalogCard, { once: true });
    } else {
      ensureCremerCatalogCard();
    }
  }
}());
