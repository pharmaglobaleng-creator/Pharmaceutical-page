from __future__ import annotations

import csv
import json
import re
from html import escape
from pathlib import Path
from urllib.parse import urlencode

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = Path("/Users/jimmydemetro/Documents/Codex/2026-09-01/referenced-chatgpt-conversation-this-is-an")
SOURCE_JSON = SOURCE_ROOT / "tmp/korsch_catalog/catalog_rows.json"
SOURCE_IMAGES = SOURCE_ROOT / "outputs/korsch_ai_generated/website-760"
IMAGE_ROOT = ROOT / "assets/images/parts/korsch"
DATA_PATH = ROOT / "data/korsch-parts.csv"


def slug(value: str) -> str:
    value = value.lower().replace("n/a", "na")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-") or "not-listed"


def source_image(index: int) -> Path:
    matches = list(SOURCE_IMAGES.glob(f"{index:03d}_*-760x760.png"))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one generated image for {index:03d}, found {len(matches)}")
    return matches[0]


def inquiry_url(row: dict[str, str]) -> str:
    subject = f"Part inquiry | {row['sku']} | {row['part_name']}"
    body = (
        "Hello PharmaGlobalEng,\n\nI would like compatibility and quotation information for this part:\n\n"
        f"Part name: {row['part_name']}\nPGE number: {row['sku']}\nMake: Korsch\n"
        f"Model: {row['model']}\nOEM number: {row['oem_number']}\n\n"
        "Quantity required:\nMachine serial number/configuration:\nExisting part or drawing reference:\n"
    )
    return "mailto:info@pharmaglobaleng.com?" + urlencode({"subject": subject, "body": body})


def build_catalog(rows: list[dict[str, str]]) -> None:
    cards = []
    for row in rows:
        oem = row["oem_number"]
        oem_display = escape(oem) if oem != "N/A" else "Not listed in source catalog"
        search = " | ".join((row["part_name"], row["model"], row["category"], row["sku"], oem if oem != "N/A" else ""))
        url = f"/parts/{row['sku'].lower()}/"
        cards.append(
            f'<article class="product-card" data-name="{escape(row["part_name"])}" data-model="{escape(row["model"])}" '
            f'data-sku="{row["sku"]}" data-search="{escape(search)}">'
            f'<div class="product-visual"><img src="{row["image_path"]}" alt="Representative visualization of {escape(row["part_name"])} for Korsch {escape(row["model"])} compatibility" width="760" height="760" loading="lazy" decoding="async"></div>'
            f'<div class="product-content"><p class="product-family">Korsch {escape(row["model"])} · {escape(row["category"])}</p>'
            f'<h3><a href="{url}">{escape(row["part_name"])}</a></h3>'
            f'<p class="oem-reference">OEM Number: {oem_display}</p><p class="sku">{row["sku"]}</p>'
            f'<a class="part-page-link" href="{url}">View replacement part page →</a>'
            f'<p class="product-copy">Independent replacement component for the listed Korsch model. Final fit is confirmed during quotation.</p>'
            f'<div class="product-actions"><a class="btn small" href="{url}">View part</a>'
            f'<button class="btn small" type="button" data-pge-cart-add data-part-sku="{row["sku"]}" data-part-name="{escape(row["part_name"])}" data-part-brand="Korsch" data-part-model="{escape(row["model"])}" data-part-url="{url}">Add to Quote Cart</button>'
            f'<a class="btn small email-part-inquiry" href="{escape(inquiry_url(row))}">Email inquiry</a></div></div></article>'
        )

    page = f'''<!doctype html>
<html lang="en-US"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Korsch Tablet Press Replacement Parts | PharmaGlobalEng</title>
<meta name="description" content="Browse {len(rows)} independently produced replacement parts organized by Korsch model and source-catalog OEM number.">
<meta name="robots" content="index,follow,max-image-preview:large"><link rel="canonical" href="https://pharmaglobaleng.com/parts/korsch/">
<link rel="stylesheet" href="/assets/css/pharmaglobaleng.css"><link rel="stylesheet" href="/assets/css/store.css"><link rel="stylesheet" href="/assets/css/parts-quote-cart.css?v=1">
<script src="/assets/js/parts-search.js?v=1"></script></head><body>
<header class="site-header"><div class="wrap nav"><a class="brand" href="/">PharmaGlobal<span>Eng</span></a><nav class="nav-links" aria-label="Primary navigation"><a href="/services/">Services</a><a href="/solutions/">Solutions</a><a href="/parts/" aria-current="page">Parts Store</a><a class="nav-cta" href="/contact.html">Contact</a></nav></div></header>
<main><section class="store-hero"><div class="wrap"><div class="crumb"><a href="/parts/">Parts Store</a> / Korsch</div><p class="eyebrow">Independent replacement-part library</p><h1>Replacement Parts Compatible with Selected Korsch Equipment</h1><p class="lead">Browse {len(rows)} independently produced replacement components matched to the part name, Korsch model, and OEM number printed in the source catalog. Entries without a catalog OEM number are clearly marked.</p><div class="catalog-search"><label class="visually-hidden" for="part-search">Search Korsch parts</label><input id="part-search" type="search" placeholder="Search part name, model, OEM, or PGE number" autocomplete="off"><span class="search-result-count"><strong id="visible-count">{len(rows)}</strong> results</span></div></div></section>
<section class="section" id="catalog"><div class="wrap"><div class="catalog-meta"><span><strong>{len(rows)}</strong> Korsch replacement-part records</span><span>Independent supplier · compatibility confirmation required</span></div><div class="product-grid" id="product-grid">{''.join(cards)}</div><p id="no-results" class="notice" hidden><strong>No matching part was found.</strong> Try a part name, model, OEM number, or PGE number.</p><div class="notice"><strong>Independent supplier and trademark notice:</strong> PharmaGlobalEng is not affiliated with, authorized by, sponsored by, or endorsed by Korsch or its trademark owner. Korsch names and OEM numbers identify equipment compatibility only. Product images are representative visualizations, not OEM photographs.</div></div></section></main>
<footer><div class="wrap footer"><span>© PharmaGlobalEng</span><a href="/parts/">All parts</a><a href="/contact.html">Parts inquiry</a></div></footer>
<script src="/assets/js/parts-quote-cart.js?v=1"></script><script>(()=>{{const input=document.getElementById('part-search'),cards=[...document.querySelectorAll('.product-card')],count=document.getElementById('visible-count'),empty=document.getElementById('no-results');function filter(){{const q=input.value;let shown=0;cards.forEach(card=>{{const match=window.PGEPartsSearch.matches(card.dataset.search||card.textContent,q);card.hidden=!match;if(match)shown++;}});count.textContent=shown;empty.hidden=shown!==0;}}input.addEventListener('input',filter);}})();</script></body></html>'''
    destination = ROOT / "parts/korsch/index.html"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(page, encoding="utf-8")


def main() -> None:
    source_rows = json.loads(SOURCE_JSON.read_text(encoding="utf-8"))
    if len(source_rows) != 284:
        raise RuntimeError(f"Expected 284 source rows, found {len(source_rows)}")
    IMAGE_ROOT.mkdir(parents=True, exist_ok=True)
    output_rows = []
    for index, source in enumerate(source_rows, start=1):
        sku = f"PGE-KOR-{index:03d}"
        image_path = IMAGE_ROOT / f"{sku.lower()}.webp"
        with Image.open(source_image(index)) as image:
            image.convert("RGB").save(image_path, "WEBP", quality=88, method=6)
        output_rows.append({
            "sku": sku, "make": "Korsch", "model": source["model"], "category": source["category"],
            "part_name": source["part_name"], "oem_number": source["oem_number"],
            "catalog_part_number": source["part_number"], "catalog_page": str(source["catalog_page"]),
            "image_status": source["image_status"], "image_path": f"/assets/images/parts/korsch/{sku.lower()}.webp",
        })
    with DATA_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output_rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(output_rows)
    build_catalog(output_rows)
    print(f"Imported {len(output_rows)} Korsch records and images")


if __name__ == "__main__":
    main()
