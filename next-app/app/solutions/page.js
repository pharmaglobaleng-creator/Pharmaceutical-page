export const metadata = {
  title: 'Tablet Compression Solutions | PharmaGlobalEng',
  alternates: { canonical: '/solutions/' },
};

const solutions = [
  ['Tablet Sticking','/solutions/tablet-sticking.html'],
  ['Tablet Picking','/solutions/tablet-picking.html'],
  ['Tablet Capping','/solutions/tablet-capping.html'],
  ['Tablet Lamination','/solutions/tablet-lamination.html'],
  ['Tablet Chipping','/solutions/tablet-chipping.html'],
  ['Tablet Binding','/solutions/tablet-binding.html'],
  ['Compression Defects Guide','/solutions/tablet-compression-defects.html'],
  ['Tablet Weight Variation','/solutions/tablet-weight-variation.html'],
  ['Punch Wear','/solutions/tablet-punch-wear.html'],
  ['Punch Corrosion','/solutions/tablet-punch-corrosion.html'],
  ['Punch Cracking','/solutions/tablet-punch-cracking.html'],
  ['Punch Fatigue','/solutions/tablet-punch-fatigue.html'],
];

export default function SolutionsPage(){
  return <main className="authority-section"><div className="authority-wrap"><p className="kicker">Solutions</p><h1 className="authority-title">Tablet Compression Solutions</h1><p className="authority-lead">Engineering guidance for tablet sticking, picking, compression defects, tooling wear, corrosion, cracking, and production-performance issues.</p><div className="premium-grid">{solutions.map(([name,href])=><article className="premium-card" key={href}><h2>{name}</h2><a href={href}>Open solution →</a></article>)}</div></div></main>;
}
