from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html import escape, unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://pharmaglobaleng.com"


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


def aliases(part: Part) -> list[str]:
    values = [
        part.name,
        f"{part.model} {part.name}",
        f"{part.brand} {part.model} {part.name}",
        part.sku,
        part.sku.replace("-", " "),
        part.sku.replace("-", ""),
    ]
    if "&" in part.name:
        values.append(part.name.replace("&", "and"))
    if "—" in part.name:
        values.append(part.name.replace("—", " "))
    result = []
    for value in values:
        clean = re.sub(r"\s+", " ", value).strip()
        if clean and clean.lower() not in {item.lower() for item in result}:
            result.append(clean)
    return result


def equipment_reference(part: Part) -> str:
    generic = {"general", "model unconfirmed", "model unspecified", "multi model"}
    if part.model.lower() in generic:
        return f"selected {part.brand} tablet press configurations"
    return f"selected {part.brand} {part.model} tablet press configurations"


def title_reference(part: Part) -> str:
    generic = {"general", "model unconfirmed", "model unspecified", "multi model"}
    if part.model.lower() in generic:
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
    return (
        f"PharmaGlobalEng independently manufactures the {part.name} for {equipment_reference(part)}. "
        "Our engineering process establishes the correct "
        "dimensions, mounting configuration, material specification, finish, and application requirements before manufacturing."
    )


def json_ld(part: Part) -> str:
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Product", "@id": part.url + "#product", "name": f"PGE {part.name}",
                "alternateName": aliases(part), "sku": part.sku, "url": part.url,
                "description": description(part), "image": SITE + part.image,
                "category": part.family, "brand": {"@type": "Brand", "name": "PharmaGlobalEng"},
                "manufacturer": {"@type": "Organization", "name": "PharmaGlobalEng", "url": SITE + "/"},
                "additionalProperty": [
                    {"@type": "PropertyValue", "name": "Compatibility reference", "value": equipment_reference(part).capitalize()},
                    {"@type": "PropertyValue", "name": "Engineering verification", "value": "PharmaGlobalEng verifies dimensions, mounting configuration, material specification, finish, and application requirements before manufacturing"},
                    {"@type": "PropertyValue", "name": "Supplier relationship", "value": "Independent replacement-part manufacturer; not OEM affiliated or endorsed"},
                ],
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


def build_page(part: Part) -> str:
    alias_chips = "".join(f'<span class="alias">{escape(item)}</span>' for item in aliases(part))
    confirmed = ""
    if part.confirmed_copy:
        confirmed = f'<div class="detail-box"><h2>Catalog engineering note</h2><p>{escape(part.confirmed_copy)}</p></div>'
    title = f"PGE {part.name} for {title_reference(part)} compatibility | PharmaGlobalEng"
    meta = description(part)
    return f'''<!doctype html>
<html lang="en-US"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title><meta name="description" content="{escape(meta)}"><meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{part.url}"><link rel="stylesheet" href="/assets/css/pharmaglobaleng.css"><link rel="stylesheet" href="/assets/css/part-detail.css">
<script type="application/ld+json">{json_ld(part)}</script></head>
<body><header class="site-header"><div class="wrap nav"><a class="brand" href="/">PharmaGlobal<span>Eng</span></a><nav class="nav-links" aria-label="Primary navigation"><a href="/services/">Services</a><a href="/solutions/">Solutions</a><a href="/parts/" aria-current="page">Parts Store</a><a class="nav-cta" href="/contact.html">Contact</a></nav></div></header>
<main><div class="wrap"><div class="part-crumb"><a href="/parts/">Parts Store</a> / <a href="{part.catalog_url}">{escape(part.brand)} parts</a> / {escape(part.sku)}</div>
<section class="part-hero"><div class="part-image"><img src="{part.image}" alt="Representative visualization of PGE {escape(part.name)}, an independently manufactured replacement component for {escape(equipment_reference(part))}" width="960" height="720"></div><div class="part-intro"><p class="eyebrow">Independent replacement component</p><h1>PGE {escape(part.name)}</h1><span class="sku-badge">{escape(part.sku)}</span><div class="store-links"><a href="{part.catalog_url}">View {escape(part.sku)} in the Parts Store →</a><a href="/parts/">Browse all parts →</a></div><p class="lead">{escape(meta)}</p><div class="compatibility"><strong>Engineered for the correct application</strong><br>Cataloged for <strong>{escape(equipment_reference(part))}</strong>. PharmaGlobalEng verifies the dimensions, mounting configuration, material specification, finish, and application requirements before manufacturing.</div><a class="btn primary quote-cta" href="/contact.html?part={escape(part.sku)}">Request compatibility and quote review</a></div></section></div>
<section class="detail-section"><div class="wrap detail-grid"><div class="detail-box"><h2>Component details</h2><dl><div><dt>PGE number</dt><dd>{escape(part.sku)}</dd></div><div><dt>Part family</dt><dd>{escape(part.family)}</dd></div><div><dt>Compatibility reference</dt><dd>{escape(equipment_reference(part).capitalize())}</dd></div><div><dt>Manufacturing</dt><dd>Made to confirmed sample, drawing, or dimensional specification</dd></div><div><dt>Availability</dt><dd>Quotation and engineering review</dd></div></dl></div><div class="detail-box"><h2>PharmaGlobalEng fit-verification process</h2><p>Our engineering team establishes the correct:</p><ul><li>Component dimensions and critical tolerances</li><li>Mounting points and installation configuration</li><li>Material specification and required finish</li><li>Operating geometry and interface requirements</li><li>Manufacturing and inspection requirements</li></ul><p>These details are verified through the quotation and engineering-review process.</p></div>{confirmed}</div></section>
<section class="detail-section"><div class="wrap"><h2>Find this part using similar terms</h2><p class="section-copy">Parts Store search recognizes the PGE number, equipment model, punctuation and spacing variations, and small spelling differences.</p><div class="aliases">{alias_chips}</div></div></section>
<section class="detail-section"><div class="wrap"><div class="notice"><strong>Independent supplier and trademark notice:</strong> PharmaGlobalEng is not affiliated with, authorized by, sponsored by, or endorsed by {escape(part.brand)} or its trademark owner. The {escape(part.brand)} name and any displayed model references are used solely to identify potential equipment compatibility. All trademarks belong to their respective owners. Product images are representative visualizations, not OEM photographs.</div></div></section></main>
<footer><div class="wrap footer"><span>© PharmaGlobalEng</span><a href="/parts/">All parts</a><a href="/contact.html">Parts inquiry</a></div></footer></body></html>'''


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


def main() -> None:
    parts = parse_korsch()
    parts += image_parts("manesty", "Manesty", "MAN")
    parts += image_parts("kikusui", "Kikusui", "KIK")
    parts += image_parts("stokes", "Stokes", "STK")
    if len(parts) != 384:
        raise SystemExit(f"Expected 384 parts, found {len(parts)}")
    if len({part.sku for part in parts}) != 384:
        raise SystemExit("Duplicate SKU detected")
    for part in parts:
        destination = ROOT / "parts" / part.slug / "index.html"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(build_page(part), encoding="utf-8")
    add_detail_links_to_korsch([part for part in parts if part.brand == "Korsch"])
    update_sitemaps(parts)
    print(f"Generated {len(parts)} canonical part pages")


if __name__ == "__main__":
    main()
