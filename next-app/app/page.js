import SiteHeader from '../components/SiteHeader';

const serviceCards = [
  ['Tablet Sticking Solutions','Investigate broad punch-face adhesion, filming, buildup, moisture, lubrication, heat, compression force, dwell time, and surface-condition factors.','/solutions/tablet-sticking.html'],
  ['Tablet Picking Solutions','Evaluate localized adhesion around logos, score lines, engraving, character islands, cup geometry, and recessed punch-face features.','/solutions/tablet-picking.html'],
  ['Tablet Punch Restoration','Assess corrosion, wear, scratches, engraving condition, critical dimensions, and remaining serviceability before replacing valuable tooling.','/services/tablet-punch-restoration.html'],
  ['Precision Punch Polishing','Apply controlled surface refinement while protecting embossing, edges, score lines, punch geometry, and dimensional requirements.','/services/tablet-punch-polishing.html'],
  ['Surface Engineering','Engineer contact surfaces around release, adhesion, friction, wear, corrosion resistance, cleanability, and production demands.','/services/surface-engineering.html'],
  ['Coating Evaluation','Compare CrN, DLC, TiN, TiCN, and other PVD options based on the formulation, tooling substrate, geometry, cleaning, and operating environment.','/services/tablet-punch-coatings.html'],
];

const components = ['Tablet Punches','Tablet Dies','Feed Frames','Capsule Components','Chutes & Hoppers','Product-Contact Parts','Compression Tooling','Restoration Projects'];

export default function HomePage() {
  return (
    <>
      <SiteHeader />
      <nav className="site-breadcrumb" aria-label="Breadcrumb"><a href="/">Home</a><span>/</span><span aria-current="page">Pharmaceutical Tablet Tooling &amp; Surface Engineering</span></nav>
      <main id="home">
        <section className="visual-shell" aria-label="PharmaGlobalEng homepage">
          <img className="masterpiece" src="https://pharmaglobaleng.com/assets/images/pharmaglobaleng-homepage.webp" width="1024" height="1536" fetchPriority="high" decoding="async" alt="PharmaGlobalEng pharmaceutical tablet tooling and surface engineering homepage" />
        </section>

        <section className="authority-section" id="engineering-approach">
          <div className="authority-wrap">
            <p className="kicker">Engineering-First Pharmaceutical Tooling Support</p>
            <h1 className="authority-title">Pharmaceutical Tablet Tooling &amp; Surface Engineering</h1>
            <p className="authority-lead">PharmaGlobalEng evaluates tablet sticking, tablet picking, corrosion, product adhesion, premature wear, poor tablet release, and inconsistent embossing by considering formulation behavior, tooling geometry, engraving design, surface condition, lubrication, moisture, compression force, dwell time, press speed, cleaning procedures, and tooling history.</p>
            <div className="premium-grid">
              {serviceCards.map(([title, text, href]) => <article className="premium-card" key={href}><h2>{title}</h2><p>{text}</p><a href={href}>Explore {title.toLowerCase()} →</a></article>)}
            </div>
            <aside className="insight"><strong>Engineering Insight</strong><p>A coating is not automatically the answer to a sticky formulation. The best path may involve controlled polishing, engraving refinement, tooling restoration, formulation review, moisture control, lubrication adjustment, process changes, or a properly selected coating after the root cause is understood.</p></aside>
          </div>
        </section>

        <section className="authority-section alt" id="components">
          <div className="authority-wrap">
            <p className="kicker">Components &amp; Applications Supported</p>
            <h2 className="authority-title">Precision Components Used Across Solid-Dose Manufacturing</h2>
            <p className="authority-lead">Evaluation, restoration, surface refinement, and performance-focused engineering for pharmaceutical tooling and product-contact components.</p>
            <div className="component-grid">{components.map((name) => <article className="component-card" key={name}><strong>{name}</strong><span>Application-specific support for surface condition, wear, cleanability, restoration, and manufacturing performance.</span></article>)}</div>
          </div>
        </section>

        <section className="authority-section" id="about">
          <div className="authority-wrap two-up">
            <div><p className="kicker">Tooling Life Extension</p><h2 className="authority-title">Not Every Punch Needs to Be Replaced</h2><p className="authority-lead">Many components removed from production because of corrosion, scratching, buildup, wear, or surface damage may still have usable life when critical dimensions, geometry, engraving, structural integrity, and functional limits remain acceptable.</p></div>
            <div><p className="kicker">Engineered Surface Condition</p><h2 className="authority-title">The Surface Must Match the Operating Environment</h2><p className="authority-lead">Surface condition influences release performance, product adhesion, friction, wear, corrosion resistance, cleanability, and tooling longevity.</p><div className="cta-group"><a className="cta-button primary" href="mailto:info@pharmaglobaleng.com?subject=Tooling%20Evaluation%20Request">Request a Tooling Evaluation</a><a className="cta-button secondary" href="/services/">View Services</a></div></div>
          </div>
        </section>

        <section className="authority-section alt" id="global-support">
          <div className="authority-wrap"><p className="kicker">Worldwide Pharmaceutical Manufacturing Support</p><h2 className="authority-title">Engineering Support Across Global Markets</h2><p className="authority-lead">PharmaGlobalEng supports pharmaceutical and nutraceutical manufacturers with remote preliminary evaluation, tooling and tablet-photo review, application-specific technical guidance, restoration planning, precision polishing, surface engineering, coating evaluation, and compression-tooling support.</p></div>
        </section>
      </main>
    </>
  );
}
