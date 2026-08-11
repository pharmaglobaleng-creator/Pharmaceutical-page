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

export default function RootLayout({ children }) {
  return (
    <html lang="en-US">
      <body>{children}</body>
    </html>
  );
}
