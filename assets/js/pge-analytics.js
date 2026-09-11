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
}());
