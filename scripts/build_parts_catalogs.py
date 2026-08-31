from html import escape
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BRANDS = {
    "manesty": ("Manesty", "MAN"),
    "kikusui": ("Kikusui", "KIK"),
    "stokes": ("Stokes", "STK"),
}


def label(value: str) -> str:
    return value.replace("-", " ").replace("_", " ").title()


def search_aliases(name: str, model: str, brand: str, sku: str) -> list[str]:
    values = [name, f"{model} {name}", f"{brand} {model} {name}", sku, sku.replace("-", " "), sku.replace("-", "")]
    replacements = (
        ("Assembly", "Assy"), ("Stainless Steel", "SS"),
        ("Left Hand", "LH"), ("Right Hand", "RH"),
        ("Upper", "Top"), ("Lower", "Bottom"),
        ("Bushing", "Bush"), ("Bushings", "Bushes"),
        ("Feed Frame", "Feeder Frame"), ("Feeder Paddle", "Feed Paddle"),
        ("Anti Vibration", "Antivibration"), ("Handwheel", "Hand Wheel"),
    )
    for original, alternative in replacements:
        if original.lower() in name.lower():
            values.append(re.sub(re.escape(original), alternative, name, flags=re.I))
    return list(dict.fromkeys(values))


def build_catalog(slug: str, brand: str, prefix: str) -> None:
    image_root = ROOT / "assets/images/parts" / slug
    images = sorted(image_root.rglob("*.webp"))
    cards = []
    for number, image in enumerate(images, 1):
        relative = image.relative_to(ROOT).as_posix()
        # Directory names reflect the legacy catalog classification, not an
        # independently verified image-to-machine identification.
        model = "Model unresolved"
        name = label(image.stem)
        sku = f"PGE-{prefix}-{number:03d}"
        product_url = f"/parts/{sku.lower()}/"
        search_terms = " | ".join(search_aliases(name, model, brand, sku))
        cards.append(
            f'<article class="product-card" data-name="{escape(name)}" data-model="{escape(model)}" data-sku="{sku}" data-search="{escape(search_terms)}">'
            f'<div class="product-visual"><img src="/{relative}" alt="Synthetic visualization labeled {escape(name)} - component identity and model unresolved" width="960" height="720" loading="lazy" decoding="async"></div>'
            f'<div class="product-content"><p class="product-family">{escape(model)}</p><h3><a href="{product_url}">{escape(name)}</a></h3><p class="identity-warning">Image identity and exact model unresolved</p><p class="sku">{sku}</p><a class="part-page-link" href="{product_url}">View {sku} part page →</a>'
            f'<p class="product-copy">Independently manufactured replacement component. PharmaGlobalEng verifies dimensions, mounting configuration, material, finish, and application requirements through engineering review.</p>'
            f'<div class="product-actions"><span class="availability">Quote review</span><a class="btn small" href="{product_url}">View part</a></div></div></article>'
        )

    page = f'''<!doctype html>
<html lang="en-US"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{brand} Tablet Press Replacement Parts | PharmaGlobalEng</title>
<meta name="description" content="Browse {len(images)} representative {brand} tablet press replacement-part images and request compatibility and pricing review.">
<meta name="robots" content="index,follow,max-image-preview:large"><link rel="canonical" href="https://pharmaglobaleng.com/parts/{slug}/">
<link rel="stylesheet" href="/assets/css/pharmaglobaleng.css"><link rel="stylesheet" href="/assets/css/store.css"><script src="/assets/js/parts-search.js?v=1"></script></head>
<body><header class="site-header"><div class="wrap nav"><a class="brand" href="/">PharmaGlobal<span>Eng</span></a><nav class="nav-links" aria-label="Primary navigation"><a href="/services/">Services</a><a href="/solutions/">Solutions</a><a href="/parts/" aria-current="page">Parts Store</a><a href="/contact.html">Contact</a></nav></div></header>
<main><section class="store-hero"><div class="wrap"><div class="crumb"><a href="/parts/">Parts Store</a> / {brand}</div><p class="eyebrow">Independent replacement-part library</p><h1>Replacement Parts Compatible with Selected {brand} Equipment</h1><p class="lead">Browse {len(images)} representative visualizations of independently produced parts. Every item requires model, serial, dimensional, material, availability, and compatibility review before quotation.</p><div class="catalog-search"><label class="visually-hidden" for="part-search">Search {brand} parts</label><input id="part-search" type="search" placeholder="Search part name, model, or PGE number" autocomplete="off"><span class="search-result-count"><strong id="visible-count">{len(images)}</strong> results</span></div></div></section>
<section class="section" id="catalog"><div class="wrap"><div class="catalog-meta"><span><strong>{len(images)}</strong> representative part images</span><span>Independent supplier · compatibility confirmation required</span></div><div class="product-grid" id="product-grid">{''.join(cards)}</div><p id="no-results" class="notice" hidden><strong>No matching part was found.</strong> Try a shorter search or send a photograph or drawing.</p><div class="notice"><strong>Independent supplier and trademark notice:</strong> PharmaGlobalEng is not affiliated with, authorized by, sponsored by, or endorsed by {brand} or its trademark owner. The manufacturer name identifies equipment compatibility only. All trademarks belong to their respective owners. Product images are representative visualizations, not OEM photographs.</div></div></section></main>
<footer><div class="wrap footer"><span>© PharmaGlobalEng</span><a href="/parts/">All parts</a><a href="/contact.html">Parts inquiry</a></div></footer>
<script>(()=>{{const input=document.getElementById('part-search'),cards=[...document.querySelectorAll('.product-card')],count=document.getElementById('visible-count'),empty=document.getElementById('no-results');function filter(){{const q=input.value;let shown=0;cards.forEach(card=>{{const match=window.PGEPartsSearch.matches(card.dataset.search||card.textContent,q);card.hidden=!match;if(match)shown++;}});count.textContent=shown;empty.hidden=shown!==0;}}input.addEventListener('input',filter);}})();</script></body></html>'''
    destination = ROOT / "parts" / slug / "index.html"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(page, encoding="utf-8")
    print(f"{brand}: {len(images)} cards -> {destination}")


for brand_slug, (brand_name, brand_prefix) in BRANDS.items():
    build_catalog(brand_slug, brand_name, brand_prefix)
