from __future__ import annotations

import json
import re
import csv
from dataclasses import dataclass
from html import escape, unescape
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://pharmaglobaleng.com"
GENERIC_MODELS = {"general", "model unconfirmed", "model unspecified", "model unresolved", "multi model"}


def load_approved_oem_references() -> dict[str, dict[str, str]]:
    source = ROOT / "data/oem-cross-reference-audit.csv"
    if not source.exists():
        return {}
    with source.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {
        row["sku"]: row
        for row in rows
        if row.get("oem_part_number", "").strip()
        and row.get("oem_number_status", "").strip().lower() == "verified"
        and row.get("approved_for_publication", "").strip().lower() == "yes"
        and row.get("source_url", "").strip()
    }


APPROVED_OEM_REFERENCES = load_approved_oem_references()


@dataclass(frozen=True)
class Part:
    sku: str
    name: str
    brand: str
    brand_slug: str
    model: str
    image: str
    family: str
    confirmed_copy: str = ""

    @property
    def slug(self) -> str:
        return self.sku.lower()

    @property
    def url(self) -> str:
        return f"{SITE}/parts/{self.slug}/"

    @property
    def catalog_url(self) -> str:
        if self.brand_slug == "korsch-300":
            return "/parts/korsch/korsch-300/"
        return f"/parts/{self.brand_slug}/"


def label(value: str) -> str:
    return value.replace("-", " ").replace("_", " ").title()


def text_only(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", unescape(value))).strip()


def write_if_changed(path: Path, content: str) -> bool:
    path.write_text(content, encoding="utf-8")
    return True


def aliases(part: Part) -> list[str]:
    values = [
        part.name,
        f"{part.model} {part.name}",
        f"{part.brand} {part.model} {part.name}",
        part.sku,
        part.sku.replace("-", " "),
        part.sku.replace("-", ""),
    ]
    oem = APPROVED_OEM_REFERENCES.get(part.sku)
    if oem:
        number = oem["oem_part_number"].strip()
        values.extend((
            number,
            f"{part.brand} {number}",
            f"{part.brand} {part.model} {number}",
            f"replacement for {number}",
        ))
    if "&" in part.name:
        values.append(part.name.replace("&", "and"))
    if "—" in part.name:
        values.append(part.name.replace("—", " "))
    replacements = (
        ("Assembly", "Assy"), ("Stainless Steel", "SS"),
        ("Left Hand", "LH"), ("Right Hand", "RH"),
        ("Upper", "Top"), ("Lower", "Bottom"),
        ("Bushing", "Bush"), ("Bushings", "Bushes"),
        ("Feed Frame", "Feeder Frame"), ("Feeder Paddle", "Feed Paddle"),
        ("Anti Vibration", "Antivibration"), ("Handwheel", "Hand Wheel"),
    )
    for original, alternative in replacements:
        if original.lower() in part.name.lower():
            values.append(re.sub(re.escape(original), alternative, part.name, flags=re.I))
    result = []
    for value in values:
        clean = re.sub(r"\s+", " ", value).strip()
        if clean and clean.lower() not in {item.lower() for item in result}:
            result.append(clean)
    return result


def equipment_reference(part: Part) -> str:
    if part.model.lower() in GENERIC_MODELS:
        return f"selected {part.brand} tablet press configurations"
    return f"selected {part.brand} {part.model} tablet press configurations"


def inquiry_url(part: Part) -> str:
    subject = f"Part inquiry | {part.sku} | {part.name}"
    body = (
        "Hello PharmaGlobalEng,\n\n"
        "I would like compatibility and quotation information for this part:\n\n"
        f"Part name: {part.name}\n"
        f"PGE number: {part.sku}\n"
        f"Manufacturer reference: {part.brand}\n"
        f"Model reference: {part.model}\n\n"
        "Quantity required:\n"
        "Machine serial number/configuration:\n"
        "Existing part or drawing reference:\n"
        "Additional information:\n"
    )
    return "mailto:info@pharmaglobaleng.com?" + urlencode({"subject": subject, "body": body})


def title_reference(part: Part) -> str:
    if part.model.lower() in GENERIC_MODELS:
        return f"{part.brand} equipment"
    return f"{part.brand} {part.model}"


def family_for(name: str) -> str:
    lower = name.lower()
    rules = [
        (("cam", "track"), "Cams and tracks"),
        (("feeder", "paddle", "feed frame", "hopper", "chute"), "Feed and discharge components"),
        (("roller", "compression"), "Compression components"),
        (("bearing", "bush", "bushing", "seal"), "Bearings, bushings, and seals"),
        (("shaft", "spindle", "pin"), "Shafts and mounting components"),
        (("guard", "cover", "door"), "Guards and covers"),
        (("gear", "sprocket", "belt"), "Drive components"),
    ]
    for needles, family in rules:
        if any(needle in lower for needle in needles):
            return family
    return "Tablet press components"


def parse_korsch() -> list[Part]:
    page = (ROOT / "parts/korsch/korsch-300/index.html").read_text(encoding="utf-8")
    cards = re.findall(r'<article class="product-card"[^>]*>.*?</article>', page, re.S)
    parts = []
    for card in cards:
        sku_match = re.search(r'data-sku="([^"]+)"', card)
        name_match = re.search(r'data-name="([^"]+)"', card)
        image_match = re.search(r'<img src="([^"]+)"', card)
        family_match = re.search(r'<p class="product-family">(.*?)</p>', card, re.S)
        copy_match = re.search(r'<p class="product-copy">(.*?)</p>', card, re.S)
        if not all((sku_match, name_match, image_match)):
            continue
        name = text_only(name_match.group(1))
        parts.append(Part(
            sku=sku_match.group(1), name=name, brand="Korsch", brand_slug="korsch-300",
            model="300", image=image_match.group(1),
            family=text_only(family_match.group(1)) if family_match else family_for(name),
            confirmed_copy=text_only(copy_match.group(1)) if copy_match else "",
        ))
    return parts


def image_parts(slug: str, brand: str, prefix: str) -> list[Part]:
    image_root = ROOT / "assets/images/parts" / slug
    parts = []
    for number, image in enumerate(sorted(image_root.rglob("*.webp")), 1):
        model = label(image.relative_to(image_root).parts[0])
        name = label(image.stem)
        parts.append(Part(
            sku=f"PGE-{prefix}-{number:03d}", name=name, brand=brand, brand_slug=slug,
            model=model, image="/" + image.relative_to(ROOT).as_posix(), family=family_for(name),
        ))
    return parts


def description(part: Part) -> str:
    text = (
        f"PharmaGlobalEng independently manufactures the {part.name} for {equipment_reference(part)}. "
        "Our engineering process establishes the correct "
        "dimensions, mounting configuration, material specification, finish, and application requirements before manufacturing."
    )
    oem = APPROVED_OEM_REFERENCES.get(part.sku)
    if oem:
        text += f" Verified OEM cross-reference {oem['oem_part_number']} is provided solely for identification and compatibility research."
    return text


def application_guidance(part: Part) -> tuple[str, str, tuple[str, ...]]:
    """Return cautious, useful guidance supported by the cataloged component name."""
    lower = part.name.lower()
    rules = [
        (("cam", "track"),
         "Cam and track components establish a guided motion path for the mechanisms that follow their working profile.",
         "Wear, profile geometry, mounting position, and the relationship to the mating follower can affect movement through the operating cycle.",
         ("Working profile and follower contact area", "Mounting-hole pattern and installed orientation", "Clearance through the complete operating path")),
        (("roller", "compression"),
         "Compression-component geometry supports the controlled loading stage used during tablet formation.",
         "The roller diameter, bearing or journal interface, installed position, and alignment with the compression mechanism must agree with the machine configuration.",
         ("Roller diameter and working-face geometry", "Bearing, journal, or shaft interface", "Installed alignment and running clearance")),
        (("bearing", "bush", "bushing"),
         "Bearing and bushing components support a rotating or sliding interface while helping maintain alignment between mating parts.",
         "Bore, outside diameter, length, fit, lubrication conditions, and the supported shaft or housing are important identification points.",
         ("Bore, outside diameter, and overall length", "Shaft and housing fit", "Lubrication and operating environment")),
        (("seal", "o-ring", "gasket"),
         "Sealing components help control material, lubricant, air, or contaminant movement at a defined equipment interface.",
         "Cross-section, sealing diameter, groove geometry, material compatibility, and the operating environment must be established before manufacture.",
         ("Seal cross-section and installed diameter", "Groove or mating-surface geometry", "Product, lubricant, and cleaning exposure")),
        (("feeder", "feed frame", "paddle", "hopper", "chute"),
         "Feed-system components participate in presenting or directing material through the tablet press product path.",
         "Installed height, product-contact geometry, rotation or travel direction, clearances, and adjacent feed-system components determine the required configuration.",
         ("Product-contact geometry and clearances", "Rotation, travel direction, and installed height", "Interfaces with the hopper, feed frame, or discharge path")),
        (("take off", "take-off", "scraper", "eject", "discharge"),
         "Take-off and discharge components help guide formed tablets away from the compression area and into the discharge path.",
         "The working edge, installed angle, height, clearance, and relationship to the turret or discharge chute must match the application.",
         ("Working-edge profile and installed angle", "Height and clearance at the tablet path", "Mounting and discharge-chute interface")),
        (("gear", "sprocket", "pulley", "belt"),
         "Drive components transfer or coordinate motion between connected tablet press mechanisms.",
         "Tooth or groove form, pitch, bore, keying, alignment, and the mating drive component are essential compatibility details.",
         ("Tooth, groove, or pitch geometry", "Bore, keyway, and shaft connection", "Alignment with the mating drive component")),
        (("shaft", "spindle", "pin", "stud"),
         "Shaft, spindle, and pin components locate, support, or transmit movement between connected mechanisms.",
         "Diameters, shoulders, lengths, threads, keyways, surface condition, and mating interfaces distinguish similar-looking configurations.",
         ("Critical diameters, shoulders, and lengths", "Threads, keyways, or retaining features", "Mating bearings, housings, and driven components")),
        (("guard", "cover", "door", "panel"),
         "Guard and cover components provide separation or controlled access around a defined machine area.",
         "Envelope dimensions, hinge or fastener locations, interlock provisions, openings, and adjacent assemblies must match the installed equipment.",
         ("Overall envelope and required openings", "Hinge, latch, and fastener locations", "Interlock and adjacent-assembly interfaces")),
        (("spring",),
         "Spring components apply or return force within a defined mechanism and operating range.",
         "Free length, coil geometry, end form, installed length, travel, and required force characteristics distinguish applications.",
         ("Free and installed length", "Coil, wire, and end-form geometry", "Working travel and force requirement")),
        (("handwheel", "hand wheel", "adjust", "knob"),
         "Adjustment components provide a manual interface for positioning or setting a tablet press mechanism.",
         "Connection geometry, direction of adjustment, available travel, scale or indicator relationship, and surrounding clearance must be confirmed.",
         ("Shaft, thread, or key connection", "Adjustment direction and usable travel", "Indicator relationship and surrounding clearance")),
    ]
    for needles, function, context, checks in rules:
        if any(needle in lower for needle in needles):
            return function, context, checks
    return (
        f"The {part.name} is a cataloged component within the {part.family.lower()} group for the referenced tablet press application.",
        "Its exact function and configuration depend on where it is installed and the components with which it interfaces; visual similarity alone is not sufficient to establish fit.",
        ("Critical dimensions and component geometry", "Mounting method and installed orientation", "Mating components and operating clearance"),
    )


def related_parts(part: Part, parts: list[Part], limit: int = 4) -> list[Part]:
    same_model = [candidate for candidate in parts if candidate.sku != part.sku and candidate.brand == part.brand and candidate.model == part.model and candidate.family == part.family]
    same_family = [candidate for candidate in parts if candidate.sku != part.sku and candidate.brand == part.brand and candidate.family == part.family and candidate not in same_model]
    same_model_other = [candidate for candidate in parts if candidate.sku != part.sku and candidate.brand == part.brand and candidate.model == part.model and candidate not in same_model]
    return (same_model + same_family + same_model_other)[:limit]


def json_ld(part: Part) -> str:
    oem = APPROVED_OEM_REFERENCES.get(part.sku)
    properties = [
        {"@type": "PropertyValue", "name": "Compatibility reference", "value": equipment_reference(part).capitalize()},
        {"@type": "PropertyValue", "name": "Engineering verification", "value": "PharmaGlobalEng verifies dimensions, mounting configuration, material specification, finish, and application requirements before manufacturing"},
        {"@type": "PropertyValue", "name": "Supplier relationship", "value": "Independent replacement-part manufacturer; not OEM affiliated or endorsed"},
    ]
    if oem:
        properties.append({
            "@type": "PropertyValue",
            "name": "Verified OEM cross-reference",
            "value": oem["oem_part_number"],
        })
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Product", "@id": part.url + "#product", "name": f"{part.name} for {title_reference(part)} compatibility",
                "alternateName": aliases(part), "sku": part.sku, "url": part.url,
                "description": description(part), "image": SITE + part.image,
                "category": part.family, "brand": {"@type": "Brand", "name": "PharmaGlobalEng"},
                "manufacturer": {"@type": "Organization", "name": "PharmaGlobalEng", "url": SITE + "/"},
                "additionalProperty": properties,
            },
            {
                "@type": "BreadcrumbList", "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Parts Store", "item": SITE + "/parts/"},
                    {"@type": "ListItem", "position": 2, "name": part.brand, "item": SITE + part.catalog_url},
                    {"@type": "ListItem", "position": 3, "name": part.sku, "item": part.url},
                ],
            },
        ],
    }
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def build_page(part: Part, parts: list[Part]) -> str:
    alias_chips = "".join(f'<span class="alias">{escape(item)}</span>' for item in aliases(part))
    confirmed = ""
    if part.confirmed_copy:
        confirmed = f'<div class="detail-box"><h2>Catalog engineering note</h2><p>{escape(part.confirmed_copy)}</p></div>'
    oem = APPROVED_OEM_REFERENCES.get(part.sku)
    oem_title = f" | OEM Ref. {oem['oem_part_number']}" if oem else ""
    oem_detail = ""
    if oem:
        oem_detail = (
            f'<div><dt>Verified OEM cross-reference</dt><dd>{escape(oem["oem_part_number"])}</dd></div>'
        )
    title = f"PGE {part.name} for {title_reference(part)} compatibility{oem_title} | PharmaGlobalEng"
    meta = description(part)
    image_url = SITE + part.image
    image_alt = f"Representative visualization of {part.name} for {title_reference(part)} tablet press compatibility"
    if part.model.lower() in GENERIC_MODELS:
        page_heading = f"{part.name} for {title_reference(part)}"
        fit_question = f"Is this {part.name} compatible with selected {part.brand} tablet press configurations?"
    else:
        page_heading = f"{part.name} for {title_reference(part)} Tablet Press"
        fit_question = f"Will this {part.name} fit a {title_reference(part)} tablet press?"
    fit_answer = (
        f"This independently manufactured {part.name} is cataloged for {equipment_reference(part)}. "
        "Compatibility is established during engineering review by confirming the machine configuration, "
        "applicable cross-reference, critical dimensions, mounting arrangement, material, finish, and operating geometry. "
        "It is not represented as a genuine OEM component."
    )
    function_note, application_note, verification_checks = application_guidance(part)
    check_items = "".join(f"<li>{escape(item)}</li>" for item in verification_checks)
    related = related_parts(part, parts)
    related_items = "".join(
        f'<li><a href="/parts/{item.slug}/">{escape(item.name)}</a> <span>({escape(item.sku)})</span></li>'
        for item in related
    )
    related_section = ""
    if related_items:
        related_section = f'''<section class="detail-section"><div class="wrap"><div class="detail-box"><h2>Related {escape(part.brand)} {escape(part.model)} components</h2><p>Compare other cataloged components in the same machine or component family:</p><ul class="related-parts">{related_items}</ul></div></div></section>'''
    return f'''<!doctype html>
<html lang="en-US"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title><meta name="description" content="{escape(meta)}"><meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{part.url}">
<meta property="og:type" content="product"><meta property="og:site_name" content="PharmaGlobalEng"><meta property="og:locale" content="en_US">
<meta property="og:title" content="{escape(title)}"><meta property="og:description" content="{escape(meta)}"><meta property="og:url" content="{part.url}">
<meta property="og:image" content="{image_url}"><meta property="og:image:alt" content="{escape(image_alt)}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{escape(title)}"><meta name="twitter:description" content="{escape(meta)}"><meta name="twitter:image" content="{image_url}"><meta name="twitter:image:alt" content="{escape(image_alt)}">
<link rel="stylesheet" href="/assets/css/pharmaglobaleng.css"><link rel="stylesheet" href="/assets/css/part-detail.css"><link rel="stylesheet" href="/assets/css/parts-quote-cart.css?v=1">
<script type="application/ld+json">{json_ld(part)}</script></head>
<body><header class="site-header"><div class="wrap nav"><a class="brand" href="/">PharmaGlobal<span>Eng</span></a><nav class="nav-links" aria-label="Primary navigation"><a href="/services/">Services</a><a href="/solutions/">Solutions</a><a href="/parts/" aria-current="page">Parts Store</a><a class="nav-cta" href="/contact.html">Contact</a></nav></div></header>
<main><div class="wrap"><div class="part-crumb"><a href="/parts/">Parts Store</a> / <a href="{part.catalog_url}">{escape(part.brand)} parts</a> / {escape(part.sku)}</div>
<section class="part-hero"><div class="part-image"><img src="{part.image}" alt="{escape(image_alt)}" width="960" height="720" loading="eager" fetchpriority="high" decoding="async"></div><div class="part-intro"><p class="eyebrow">Independent replacement component</p><h1>{escape(page_heading)}</h1><span class="sku-badge">PharmaGlobalEng SKU: {escape(part.sku)}</span><div class="store-links"><a href="{part.catalog_url}">View {escape(part.sku)} in the Parts Store →</a><a href="/parts/">Browse all parts →</a></div><p class="lead">{escape(meta)}</p><div class="compatibility"><strong>Engineered for the correct application</strong><br>Cataloged for <strong>{escape(equipment_reference(part))}</strong>. PharmaGlobalEng verifies the dimensions, mounting configuration, material specification, finish, and application requirements before manufacturing.</div><div class="part-quote-actions"><button class="btn primary quote-cta" type="button" data-pge-cart-add data-part-sku="{escape(part.sku)}" data-part-name="{escape(part.name)}" data-part-brand="{escape(part.brand)}" data-part-model="{escape(part.model)}" data-part-url="/parts/{part.slug}/">Add to Quote Cart</button><a class="btn secondary email-part-inquiry" href="{escape(inquiry_url(part))}">Email this part</a></div></div></section></div>
<section class="detail-section"><div class="wrap detail-grid"><div class="detail-box"><h2>Component details</h2><dl><div><dt>PGE number</dt><dd>{escape(part.sku)}</dd></div>{oem_detail}<div><dt>Part family</dt><dd>{escape(part.family)}</dd></div><div><dt>Compatibility reference</dt><dd>{escape(equipment_reference(part).capitalize())}</dd></div><div><dt>Manufacturing</dt><dd>Made to confirmed sample, drawing, or dimensional specification</dd></div><div><dt>Availability</dt><dd>Quotation and engineering review</dd></div></dl></div><div class="detail-box"><h2>PharmaGlobalEng fit-verification process</h2><p>Our engineering team establishes the correct:</p><ul><li>Component dimensions and critical tolerances</li><li>Mounting points and installation configuration</li><li>Material specification and required finish</li><li>Operating geometry and interface requirements</li><li>Manufacturing and inspection requirements</li></ul><p>These details are verified through the quotation and engineering-review process.</p></div>{confirmed}</div></section>
<section class="detail-section"><div class="wrap"><h2>Find this part using similar terms</h2><p class="section-copy">Parts Store search recognizes the PGE number, equipment model, punctuation and spacing variations, and small spelling differences.</p><div class="aliases">{alias_chips}</div></div></section>
<section class="detail-section"><div class="wrap detail-grid"><div class="detail-box"><h2>What does the {escape(part.name)} do?</h2><p>{escape(function_note)}</p><p>{escape(application_note)}</p></div><div class="detail-box"><h2>Part-specific verification checkpoints</h2><p>For {escape(part.sku)}, the engineering review focuses on:</p><ul>{check_items}</ul><p>The existing component, drawing, or dimensional record is used to resolve the final manufacturing configuration.</p></div></div></section>
<section class="detail-section"><div class="wrap"><div class="detail-box"><h2>{escape(fit_question)}</h2><p>{escape(fit_answer)}</p></div></div></section>
{related_section}
<section class="detail-section"><div class="wrap"><div class="notice"><strong>Independent supplier and trademark notice:</strong> PharmaGlobalEng is not affiliated with, authorized by, sponsored by, or endorsed by {escape(part.brand)} or its trademark owner. The {escape(part.brand)} name and any displayed model references are used solely to identify potential equipment compatibility. All trademarks belong to their respective owners. Product images are representative visualizations, not OEM photographs.</div></div></section></main>
<footer><div class="wrap footer"><span>© PharmaGlobalEng</span><a href="/parts/">All parts</a><a href="/contact.html">Parts inquiry</a></div></footer><script src="/assets/js/parts-quote-cart.js?v=1"></script></body></html>'''


def add_detail_links_to_korsch(parts: list[Part]) -> None:
    path = ROOT / "parts/korsch/korsch-300/index.html"
    page = path.read_text(encoding="utf-8")
    for part in parts:
        marker = f'<p class="sku">{part.sku}</p>'
        replacement = marker + f'<a class="part-page-link" href="/parts/{part.slug}/">View {part.sku} part page →</a>'
        if replacement not in page:
            page = page.replace(marker, replacement, 1)
        article_marker = f'data-sku="{part.sku}" data-name="{part.name}"'
        if article_marker in page and "data-search=" not in page[page.find(article_marker)-100:page.find(article_marker)+300]:
            search = " | ".join(aliases(part))
            page = page.replace(article_marker, article_marker + f' data-search="{escape(search)}"', 1)
    old = "const textMatch = !term || `${card.dataset.name} ${card.dataset.sku} ${card.dataset.family}`.toLowerCase().includes(term);"
    new = "const textMatch = !term || window.PGEPartsSearch.matches(card.dataset.search || `${card.dataset.name} ${card.dataset.sku} ${card.dataset.family}`, term);"
    page = page.replace(old, new)
    shared = '<script src="/assets/js/parts-search.js?v=1"></script>\n'
    page = page.replace('<script src="/assets/js/parts-search.js"></script>\n', shared)
    if shared not in page:
        page = page.replace('<script>\n  (() => {', shared + '<script>\n  (() => {', 1)
    path.write_text(page, encoding="utf-8")


def add_email_links_to_catalogs(parts: list[Part]) -> None:
    catalog_paths = {
        "korsch-300": ROOT / "parts/korsch/korsch-300/index.html",
        "kikusui": ROOT / "parts/kikusui/index.html",
        "stokes": ROOT / "parts/stokes/index.html",
    }
    for brand_slug, path in catalog_paths.items():
        page = path.read_text(encoding="utf-8")
        for part in (item for item in parts if item.brand_slug == brand_slug):
            article_pattern = re.compile(
                rf'(<article class="product-card"[^>]*data-sku="{re.escape(part.sku)}".*?</article>)',
                re.S,
            )
            match = article_pattern.search(page)
            if not match:
                continue
            article = match.group(1)
            email_link = (
                f'<a class="btn small email-part-inquiry" href="{escape(inquiry_url(part))}">'
                "Email inquiry</a>"
            )
            cart_button = (
                f'<button class="btn small" type="button" data-pge-cart-add '
                f'data-part-sku="{escape(part.sku)}" data-part-name="{escape(part.name)}" '
                f'data-part-brand="{escape(part.brand)}" data-part-model="{escape(part.model)}" '
                f'data-part-url="/parts/{part.slug}/">Add to Quote Cart</button>'
            )
            additions = ""
            if brand_slug != "korsch-300" and "data-pge-cart-add" not in article:
                additions += cart_button
            if "email-part-inquiry" not in article:
                additions += email_link
            if not additions:
                continue
            article = re.sub(
                r'(<div class="product-actions">.*?)(</div>)',
                rf'\1{additions}\2',
                article,
                count=1,
                flags=re.S,
            )
            page = page[:match.start()] + article + page[match.end():]
        if brand_slug != "korsch-300":
            quote_css = '<link rel="stylesheet" href="/assets/css/parts-quote-cart.css?v=1">'
            if quote_css not in page:
                page = page.replace('</head>', quote_css + '</head>', 1)
            quote_js = '<script src="/assets/js/parts-quote-cart.js?v=1"></script>'
            if quote_js not in page:
                page = page.replace('</body>', quote_js + '</body>', 1)
        path.write_text(page, encoding="utf-8")


def update_sitemaps(parts: list[Part]) -> None:
    path = ROOT / "sitemap.xml"
    xml = path.read_text(encoding="utf-8")
    xml = re.sub(r'\n\s*<url>\s*<loc>https://pharmaglobaleng\.com/parts/pge-[^<]+</loc>.*?</url>', '', xml, flags=re.S)
    entries = "\n".join(f'''  <url>
    <loc>{part.url}</loc>
    <changefreq>monthly</changefreq>
    <priority>0.75</priority>
  </url>''' for part in parts)
    xml = xml.replace("</urlset>", entries + "\n</urlset>")
    path.write_text(xml, encoding="utf-8")

    image_entries = "\n".join(f'''  <url><loc>{part.url}</loc><image:image><image:loc>{SITE + part.image}</image:loc><image:title>{escape('PGE ' + part.name)}</image:title><image:caption>{escape('Representative visualization of an independently manufactured replacement component')}</image:caption></image:image></url>''' for part in parts)
    (ROOT / "sitemap-parts-images.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' + image_entries + '\n</urlset>\n', encoding="utf-8")
    robots = ROOT / "robots.txt"
    text = robots.read_text(encoding="utf-8")
    line = "Sitemap: https://pharmaglobaleng.com/sitemap-parts-images.xml"
    if line not in text:
        text = text.rstrip() + "\n" + line + "\n"
    robots.write_text(text, encoding="utf-8")


def write_content_audit(parts: list[Part]) -> None:
    destination = ROOT / "data/part-content-audit.csv"
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow((
            "sku", "part_name", "manufacturer_reference", "model_reference", "image_path",
            "identity_source", "technical_description_status", "search_alias_status", "landing_page",
        ))
        for part in parts:
            writer.writerow((
                part.sku, part.name, part.brand, part.model, part.image,
                "Existing catalog card and image-path model folder",
                "Catalog-confirmed engineering note" if part.confirmed_copy else "Identity confirmed; detailed function pending technical review",
                "Format and terminology variants generated from confirmed part name",
                f"/parts/{part.slug}/",
            ))


def main() -> None:
    parts = parse_korsch()
    parts += image_parts("kikusui", "Kikusui", "KIK")
    parts += image_parts("stokes", "Stokes", "STK")
    if len(parts) != 384:
        raise SystemExit(f"Expected 384 parts, found {len(parts)}")
    if len({part.sku for part in parts}) != 384:
        raise SystemExit("Duplicate SKU detected")
    for part in parts:
        destination = ROOT / "parts" / part.slug / "index.html"
        destination.parent.mkdir(parents=True, exist_ok=True)
        write_if_changed(destination, build_page(part, parts))
    add_detail_links_to_korsch([part for part in parts if part.brand == "Korsch"])
    add_email_links_to_catalogs(parts)
    update_sitemaps(parts)
    write_content_audit(parts)
    print(f"Generated {len(parts)} canonical part pages")


if __name__ == "__main__":
    main()
