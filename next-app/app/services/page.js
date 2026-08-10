export const metadata = {
  title: 'Pharmaceutical Engineering Services | PharmaGlobalEng',
  alternates: { canonical: '/services/' },
};

const services = [
  ['Tablet Compression Tooling','/services/pharmaceutical-tablet-compression-tooling.html'],
  ['Tooling Evaluation','/services/tooling-evaluation.html'],
  ['Tooling Inspection','/services/tablet-tooling-inspection.html'],
  ['Failure Analysis','/services/tablet-tooling-failure-analysis.html'],
  ['Tablet Punch Restoration','/services/tablet-punch-restoration.html'],
  ['Tablet Punch Polishing','/services/tablet-punch-polishing.html'],
  ['Surface Engineering','/services/surface-engineering.html'],
  ['Tablet Punch Coatings','/services/tablet-punch-coatings.html'],
  ['Engraving Optimization','/services/engraving-optimization.html'],
  ['Tablet Press Troubleshooting','/services/tablet-press-troubleshooting.html'],
];

export default function ServicesPage(){
  return <main className="authority-section"><div className="authority-wrap"><p className="kicker">Services</p><h1 className="authority-title">Pharmaceutical Engineering Services</h1><p className="authority-lead">Explore PharmaGlobalEng tablet tooling evaluation, restoration, polishing, surface engineering, coatings, engraving optimization, and compression support.</p><div className="premium-grid">{services.map(([name,href])=><article className="premium-card" key={href}><h2>{name}</h2><a href={href}>Open service →</a></article>)}</div></div></main>;
}
