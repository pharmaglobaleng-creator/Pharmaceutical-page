import './globals.css';

export const metadata = {
  metadataBase: new URL('https://pharmaglobaleng.com'),
  title: 'Pharmaceutical Tablet Tooling & Surface Engineering | PharmaGlobalEng',
  description:
    'PharmaGlobalEng provides worldwide pharmaceutical tablet tooling restoration, precision polishing, surface engineering, coatings, engraving optimization, and tablet sticking and picking solutions for manufacturers across global markets.',
  alternates: { canonical: '/' },
  openGraph: {
    type: 'website',
    siteName: 'PharmaGlobalEng',
    title: 'Pharmaceutical Tablet Tooling & Surface Engineering | PharmaGlobalEng',
    description:
      'Worldwide tablet tooling restoration, precision polishing, coatings, surface engineering, and compression-performance support for pharmaceutical manufacturers.',
    url: '/',
    images: [{ url: '/assets/images/pharmaglobaleng-homepage.jpg', alt: 'PharmaGlobalEng pharmaceutical tablet tooling and surface engineering homepage' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Pharmaceutical Tablet Tooling & Surface Engineering | PharmaGlobalEng',
    description: 'Worldwide pharmaceutical tablet tooling restoration, precision polishing, coatings, and surface engineering support.',
    images: ['/assets/images/pharmaglobaleng-homepage.jpg'],
  },
  robots: { index: true, follow: true },
};

const siteSchema = {
  '@context': 'https://schema.org',
  '@graph': [
    {
      '@type': 'Organization',
      '@id': 'https://pharmaglobaleng.com/#organization',
      name: 'PharmaGlobalEng',
      url: 'https://pharmaglobaleng.com/',
      description:
        'Pharmaceutical tablet tooling, replacement parts, restoration, precision polishing, surface engineering, coatings, and tablet compression support.',
      logo: {
        '@type': 'ImageObject',
        url: 'https://pharmaglobaleng.com/assets/images/about-pge-logo.svg',
      },
    },
    {
      '@type': 'WebSite',
      '@id': 'https://pharmaglobaleng.com/#website',
      url: 'https://pharmaglobaleng.com/',
      name: 'PharmaGlobalEng',
      publisher: { '@id': 'https://pharmaglobaleng.com/#organization' },
      inLanguage: 'en-US',
    },
    {
      '@type': 'WebPage',
      '@id': 'https://pharmaglobaleng.com/#webpage',
      url: 'https://pharmaglobaleng.com/',
      name: 'Pharmaceutical Tablet Tooling & Surface Engineering | PharmaGlobalEng',
      description:
        'PharmaGlobalEng provides worldwide pharmaceutical tablet tooling restoration, precision polishing, surface engineering, coatings, engraving optimization, and tablet sticking and picking solutions for manufacturers across global markets.',
      isPartOf: { '@id': 'https://pharmaglobaleng.com/#website' },
      about: { '@id': 'https://pharmaglobaleng.com/#organization' },
      primaryImageOfPage: {
        '@type': 'ImageObject',
        url: 'https://pharmaglobaleng.com/assets/images/pharmaglobaleng-homepage.jpg',
      },
      inLanguage: 'en-US',
    },
  ],
};

export default function RootLayout({ children }) {
  return (
    <html lang="en-US">
      <body>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(siteSchema) }}
        />
        {children}
      </body>
    </html>
  );
}
