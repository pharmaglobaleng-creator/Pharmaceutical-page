'use client';

import { useState } from 'react';
import Link from 'next/link';

const services = [
  ['Tablet Compression Tooling','/services/pharmaceutical-tablet-compression-tooling.html'],
  ['Tooling Evaluation','/services/tooling-evaluation.html'],
  ['Tooling Inspection','/services/tablet-tooling-inspection.html'],
  ['Failure Analysis','/services/tablet-tooling-failure-analysis.html'],
  ['Lifecycle Management','/services/tablet-tooling-lifecycle-management.html'],
  ['Preventive Maintenance','/services/tablet-tooling-preventive-maintenance.html'],
  ['Tablet Punch Restoration','/services/tablet-punch-restoration.html'],
  ['Tablet Punch Polishing','/services/tablet-punch-polishing.html'],
  ['Surface Engineering','/services/surface-engineering.html'],
  ['Tablet Punch Coatings','/services/tablet-punch-coatings.html'],
  ['Engraving Optimization','/services/engraving-optimization.html'],
  ['Tablet Press Troubleshooting','/services/tablet-press-troubleshooting.html'],
];

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

function Dropdown({ label, allHref, items }) {
  const [open, setOpen] = useState(false);
  return (
    <li className={`nav-item has-dropdown ${open ? 'dropdown-open' : ''}`}>
      <button className="dropdown-trigger" type="button" aria-expanded={open} onClick={() => setOpen(!open)}>{label}</button>
      <ul className="submenu">
        <li><Link className="view-all" href={allHref}>View All {label}</Link></li>
        {items.map(([name, href]) => <li key={href}><Link href={href}>{name}</Link></li>)}
      </ul>
    </li>
  );
}

export default function SiteHeader() {
  const [mobileOpen, setMobileOpen] = useState(false);
  return (
    <header className="site-header">
      <div className="nav-shell">
        <Link className="brand" href="/" aria-label="PharmaGlobalEng home">PharmaGlobal<span>Eng</span></Link>
        <button className="menu-toggle" type="button" aria-expanded={mobileOpen} onClick={() => setMobileOpen(!mobileOpen)}>Menu</button>
        <nav className={`primary-nav ${mobileOpen ? 'mobile-open' : ''}`} aria-label="Primary navigation">
          <ul className="nav-list">
            <li className="nav-item"><Link className="nav-link" href="/">Home</Link></li>
            <Dropdown label="Services" allHref="/services/" items={services} />
            <Dropdown label="Solutions" allHref="/solutions/" items={solutions} />
            <Dropdown label="Parts Store" allHref="/parts/" items={[["Korsch 300 Parts","/parts/korsch/korsch-300/"]]} />
            <Dropdown label="Components" allHref="/components/" items={[["Tablet Punches","/components/tablet-punches.html"],["Tablet Dies","/components/tablet-dies.html"],["Feed Frames","/components/feed-frames.html"]]} />
            <Dropdown label="Coatings" allHref="/coatings/" items={[["Chromium Nitride (CrN)","/coatings/chromium-nitride-crn.html"],["Diamond-Like Carbon (DLC)","/coatings/diamond-like-carbon-dlc.html"],["Titanium Nitride (TiN)","/coatings/titanium-nitride-tin.html"]]} />
            <li className="nav-item"><Link className="nav-link" href="/knowledge-center/">Knowledge Center</Link></li>
            <li className="nav-item"><a className="nav-link" href="#about">About Us</a></li>
            <li className="nav-item"><Link className="nav-link" href="/contact.html">Contact</Link></li>
          </ul>
        </nav>
      </div>
    </header>
  );
}
