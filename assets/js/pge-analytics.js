/* Pharma Global Website GA4: visitor and traffic reporting. */
(function () {
  'use strict';

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

  if (window.location.pathname === '/parts/' || window.location.pathname === '/parts') {
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
        if (title) title.textContent = 'Creamer';
        var copy = card.querySelector('p');
        if (copy) copy.textContent = 'Browse Creamer replacement components by machine model, part name, and reference.';
        var partCount = card.querySelector('.pc-manufacturer-count');
        if (partCount) partCount.textContent = '60 parts';
      }

      if (identify) {
        if (card.parentNode !== grid || card.nextElementSibling !== identify) {
          grid.insertBefore(card, identify);
        }
      } else if (card.parentNode !== grid) {
        grid.appendChild(card);
      }

      var count = document.querySelector('.pc-section-heading > span');
      if (count) count.textContent = '4,271 part records';

      document.querySelectorAll('.pc-nav-menu div, .pc-mobile-nav nav').forEach(function (nav) {
        var link = nav.querySelector('a[href="/parts/cremer/"]');
        if (!link) {
          link = document.createElement('a');
          link.href = '/parts/cremer/';
          var identifyLink = nav.querySelector('a[href="/parts/identify/"]');
          if (identifyLink) nav.insertBefore(link, identifyLink);
          else nav.appendChild(link);
        }
        link.textContent = 'Creamer parts';
      });

      return true;
    }

    function runCreamerFixes() {
      ensureCreamerCatalogCard();
      [100, 300, 700, 1200, 2200, 4000].forEach(function (delay) {
        setTimeout(ensureCreamerCatalogCard, delay);
      });
    }

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', runCreamerFixes, { once: true });
    } else {
      runCreamerFixes();
    }

    var observer = new MutationObserver(function () {
      ensureCreamerCatalogCard();
    });

    function startObserver() {
      if (!document.body) return;
      observer.observe(document.body, { childList: true, subtree: true });
      setTimeout(function () { observer.disconnect(); }, 10000);
    }

    if (document.body) startObserver();
    else document.addEventListener('DOMContentLoaded', startObserver, { once: true });
  }
}());
