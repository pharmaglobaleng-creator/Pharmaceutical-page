import './globals.css';
import './pge-header.css';
import Script from 'next/script';

export const metadata = {
  metadataBase: new URL('https://pharmaglobaleng.com'),
  title: 'Tablet Tooling, Polishing & Coatings | PharmaGlobalEng',
  description: 'Restore tablet punches and dies with PharmaGlobalEng. Precision polishing, coatings and tooling support to address sticking and picking. Serving manufacturers worldwide.',
  alternates: { canonical: '/' },
  icons: { icon: '/assets/images/pge-header-logo.webp' },
  openGraph: {
    type: 'website', siteName: 'PharmaGlobalEng',
    title: 'Tablet Tooling, Polishing & Coatings | PharmaGlobalEng',
    description: 'Worldwide tablet tooling restoration, precision polishing, coatings, surface engineering, and compression-performance support for pharmaceutical manufacturers.',
    url: '/',
    images: [{ url: '/assets/images/pharmaglobaleng-homepage.jpg', alt: 'PharmaGlobalEng pharmaceutical tablet tooling and surface engineering homepage' }],
  },
  twitter: { card: 'summary_large_image', title: 'Tablet Tooling, Polishing & Coatings | PharmaGlobalEng', description: 'Worldwide pharmaceutical tablet tooling restoration, precision polishing, coatings, and surface engineering support.', images: ['/assets/images/pharmaglobaleng-homepage.jpg'] },
  robots: { index: true, follow: true },
};

// Page-specific entities belong to their page, not to the shared layout.
// In particular, do not describe every catalog as the homepage.
const siteSchema = {
  '@context': 'https://schema.org',
  '@graph': [
    { '@type': 'Organization', '@id': 'https://pharmaglobaleng.com/#organization', name: 'PharmaGlobalEng', url: 'https://pharmaglobaleng.com/', description: 'Pharmaceutical tablet tooling, replacement parts, restoration, precision polishing, surface engineering, coatings, and tablet compression support.', logo: { '@type': 'ImageObject', url: 'https://pharmaglobaleng.com/assets/images/about-pge-logo.svg' } },
    { '@type': 'WebSite', '@id': 'https://pharmaglobaleng.com/#website', url: 'https://pharmaglobaleng.com/', name: 'PharmaGlobalEng', publisher: { '@id': 'https://pharmaglobaleng.com/#organization' }, inLanguage: 'en-US' },
  ],
};

export default function RootLayout({ children }) {
  return <html lang="en-US"><body><Script id="pge-analytics" src="/assets/js/pge-analytics.js" strategy="afterInteractive" /><script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(siteSchema).replace(/</g, '\\u003c') }} />{children}</body></html>;
}
