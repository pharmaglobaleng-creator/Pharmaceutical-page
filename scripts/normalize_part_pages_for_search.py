#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import html
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTS_ROOT = ROOT / "parts"
SITE = "https://pharmaglobaleng.com"
ORG_ID = f"{SITE}/#organization"
REPORT_PATH = ROOT / "docs/parts-search-quality-audit.md"

GENERIC_MODEL_VALUES = {
    "", "general", "model unconfirmed", "model unspecified", "model unresolved",
    "multi model", "unknown", "n/a", "na", "none", "not available",
}
OEM_EMPTY_VALUES = {
    "", "n/a", "na", "none", "not available", "not listed in source catalog",
    "not listed", "unknown",
}
PLACEHOLDER_RE = re.compile(
    r"\b(?:model\s+(?:unresolved|unconfirmed|unspecified)|unknown\s+model|model\s+unknown)\b",
    re.I,
)
JSONLD_RE = re.compile(
    r'(<script[^>]+type=["\']application/ld\+json["\'][^>]*>)(.*?)(</script>)',
    re.I | re.S,
)

@dataclass
class Truth:
    sku: str
    name: str
    brand: str
    model: str | None = None
    family: str | None = None
    oem: str | None = None
    raw_oem: str | None = None
    oem_verified: bool = False
    verification: str | None = None
    source: str | None = None

def clean(value: object) -> str:
    return re.sub(r"\s+", " ", "" if value is None else str(value)).strip()

def usable_model(value: object) -> str | None:
    value = clean(value)
    return None if value.casefold() in GENERIC_MODEL_VALUES else value

def usable_oem(value: object) -> str | None:
    value = clean(value)
    return None if value.casefold() in OEM_EMPTY_VALUES else value

def load_truth() -> dict[str, Truth]:
    result: dict[str, Truth] = {}

    # Current manufacturer catalog publication records.
    catalog_dir = ROOT / "catalog-data"
    if catalog_dir.exists():
        for path in sorted(catalog_dir.glob("*.json")):
            if path.name == "manifest.json":
                continue
            try:
                rows = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                sku = clean(row.get("sku")).upper()
                if not sku:
                    continue
                oem = usable_oem(row.get("oem"))
                result[sku] = Truth(
                    sku=sku,
                    name=clean(row.get("name")) or sku,
                    brand=clean(row.get("brandName")) or clean(row.get("brand")).title(),
                    model=usable_model(row.get("model")),
                    family=clean(row.get("family")) or None,
                    oem=oem,
                    raw_oem=clean(row.get("oem")) or None,
                    oem_verified=bool(oem),
                    verification="Catalog publication record",
                    source=path.relative_to(ROOT).as_posix(),
                )

    # Kikusui has row-level verification. Reviewed-only values are not published
    # as verified OEM cross-references.
    kik = ROOT / "data/kikusui-parts.csv"
    if kik.exists():
        with kik.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                sku = clean(row.get("sku")).upper()
                if not sku:
                    continue
                verification = clean(row.get("verification"))
                raw_oem = usable_oem(row.get("oem_number"))
                verified = verification.casefold().startswith("verified")
                result[sku] = Truth(
                    sku=sku,
                    name=clean(row.get("part_name")) or sku,
                    brand="Kikusui",
                    model=usable_model(row.get("model")),
                    family=clean(row.get("category")) or None,
                    oem=raw_oem if verified else None,
                    raw_oem=raw_oem,
                    oem_verified=bool(raw_oem and verified),
                    verification=verification or None,
                    source="data/kikusui-parts.csv",
                )

    # Only cross-reference audit rows explicitly marked verified + approved may
    # add an OEM number to public pages.
    audit = ROOT / "data/oem-cross-reference-audit.csv"
    if audit.exists():
        with audit.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                sku = clean(row.get("sku")).upper()
                if not sku:
                    continue
                prior = result.get(sku)
                approved = (
                    clean(row.get("oem_number_status")).casefold() == "verified"
                    and clean(row.get("approved_for_publication")).casefold() == "yes"
                    and bool(clean(row.get("source_url")))
                )
                audited_oem = usable_oem(row.get("oem_part_number")) if approved else None
                model = usable_model(row.get("model_reference"))
                result[sku] = Truth(
                    sku=sku,
                    name=clean(row.get("part_name")) or (prior.name if prior else sku),
                    brand=clean(row.get("manufacturer_reference")) or (prior.brand if prior else "PharmaGlobalEng"),
                    model=model or (prior.model if prior and prior.source != "data/oem-cross-reference-audit.csv" else None),
                    family=prior.family if prior else None,
                    oem=audited_oem or (prior.oem if prior and prior.oem_verified else None),
                    raw_oem=clean(row.get("oem_part_number")) or (prior.raw_oem if prior else None),
                    oem_verified=bool(audited_oem or (prior and prior.oem_verified)),
                    verification=clean(row.get("oem_number_status")) or (prior.verification if prior else None),
                    source="data/oem-cross-reference-audit.csv",
                )
    return result

TRUTH = load_truth()

def sku_from_path(path: Path) -> str:
    return path.parent.name.upper()

def detail_paths() -> list[Path]:
    return sorted(p for p in PARTS_ROOT.glob("pge-*/index.html") if p.is_file())

def strip_tags(value: str) -> str:
    return clean(html.unescape(re.sub(r"<[^>]+>", " ", value)))

def extract(pattern: str, text: str) -> str | None:
    m = re.search(pattern, text, re.I | re.S)
    return m.group(1) if m else None

def fallback_truth(path: Path, text: str) -> Truth:
    sku = sku_from_path(path)
    h1 = strip_tags(extract(r"<h1[^>]*>(.*?)</h1>", text) or sku)
    brand = "PharmaGlobalEng"
    for candidate in ("Korsch", "Kikusui", "Manesty", "Stokes", "Fette", "Kilian", "PTK"):
        if re.search(rf"\b{re.escape(candidate)}\b", text, re.I):
            brand = candidate
            break
    name = re.split(r"\s+(?:for|—|\|)\s+", h1, maxsplit=1, flags=re.I)[0].strip()
    return Truth(sku=sku, name=name or sku, brand=brand, source="HTML fallback")

def set_title(text: str, value: str) -> str:
    if re.search(r"<title[^>]*>.*?</title>", text, re.I | re.S):
        return re.sub(r"<title[^>]*>.*?</title>", f"<title>{html.escape(value)}</title>", text, count=1, flags=re.I | re.S)
    return re.sub(r"</head>", f"<title>{html.escape(value)}</title>\n</head>", text, count=1, flags=re.I)

def set_meta(text: str, name_or_property: str, value: str, *, prop: bool = False) -> str:
    attr = "property" if prop else "name"
    pattern = rf'<meta(?=[^>]*\b{attr}=["\']{re.escape(name_or_property)}["\'])[^>]*>'
    tag = f'<meta {attr}="{name_or_property}" content="{html.escape(value, quote=True)}">'
    if re.search(pattern, text, re.I):
        return re.sub(pattern, tag, text, count=1, flags=re.I)
    return re.sub(r"</head>", tag + "\n</head>", text, count=1, flags=re.I)

def wordsafe_truncate(value: str, limit: int) -> str:
    value = clean(value)
    if len(value) <= limit:
        return value
    cut = value[: limit + 1].rsplit(" ", 1)[0].rstrip(" |–—-:,;")
    return cut or value[:limit].rstrip()

def page_title(t: Truth) -> str:
    if t.model:
        candidate = f"{t.name} | {t.brand} {t.model} | {t.sku}"
    else:
        candidate = f"{t.name} | {t.brand} Replacement Part | {t.sku}"
    if len(candidate) <= 72:
        return candidate
    return wordsafe_truncate(f"{t.name} | {t.sku} | {t.brand}", 72)

def page_h1(t: Truth) -> str:
    if t.model:
        return f"{t.name} for {t.brand} {t.model}"
    return f"{t.name} — {t.brand} Replacement Component"

def page_meta(t: Truth) -> str:
    equip = f"{t.brand} {t.model}" if t.model else t.brand
    base = f"{t.name} for {equip}. Independent PharmaGlobalEng replacement component {t.sku}."
    if t.oem_verified and t.oem:
        base += f" OEM cross-reference {t.oem}."
    base += " Compatibility and specifications are confirmed before quotation."
    return wordsafe_truncate(base, 175)

def factual_aliases(t: Truth) -> list[str]:
    values = [t.name]
    values.append(f"{t.brand} {t.model} {t.name}" if t.model else f"{t.brand} {t.name}")
    values.append(t.sku)
    if t.oem_verified and t.oem:
        values.append(t.oem)
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        value = clean(value)
        key = value.casefold()
        if value and key not in seen:
            out.append(value)
            seen.add(key)
    return out[:5]

def sanitize_placeholders(text: str) -> str:
    text = re.sub(r"\b([A-Za-z][A-Za-z0-9& .'-]*)\s+Model unresolved tablet press\b", r"\1 tablet press", text, flags=re.I)
    text = re.sub(r"\bselected\s+([A-Za-z][A-Za-z0-9& .'-]*)\s+Model unresolved tablet press configurations\b", r"selected \1 tablet press configurations", text, flags=re.I)
    text = re.sub(r"\bModel unresolved\b", "model to be confirmed", text, flags=re.I)
    text = re.sub(r"\bmodel unconfirmed\b", "model to be confirmed", text, flags=re.I)
    text = re.sub(r"\bmodel unspecified\b", "model to be confirmed", text, flags=re.I)
    return text

def rewrite_h1(text: str, t: Truth) -> str:
    value = html.escape(page_h1(t))
    return re.sub(r"<h1([^>]*)>.*?</h1>", rf"<h1\1>{value}</h1>", text, count=1, flags=re.I | re.S)

def rewrite_lead(text: str, t: Truth) -> str:
    value = html.escape(page_meta(t))
    return re.sub(r'(<div class="part-intro">.*?<p class="lead">).*?(</p>)', rf"\1{value}\2", text, count=1, flags=re.I | re.S)

def rewrite_compatibility(text: str, t: Truth) -> str:
    if t.model:
        ref = f"Make: <strong>{html.escape(t.brand)}</strong> · Model: <strong>{html.escape(t.model)}</strong>"
    else:
        ref = f"Manufacturer reference: <strong>{html.escape(t.brand)}</strong> · Exact model: <strong>confirm during quotation</strong>"
    if t.oem_verified and t.oem:
        content = f"<strong>OEM cross-reference: {html.escape(t.oem)}</strong><br>{ref}"
    else:
        content = f"<strong>Compatibility confirmation required</strong><br>{ref}"
    return re.sub(r'<div class="compatibility">.*?</div>', f'<div class="compatibility">{content}</div>', text, count=1, flags=re.I | re.S)

def rewrite_alias_section(text: str, t: Truth) -> str:
    chips = "".join(f'<span class="alias">{html.escape(v)}</span>' for v in factual_aliases(t))
    text = re.sub(r"<h2>Find this part (?:using similar terms|by its verified references)</h2>", "<h2>Reference identifiers</h2>", text, flags=re.I)
    text = re.sub(
        r'<p class="section-copy">(?:Parts Store search recognizes|Search recognizes).*?</p>',
        '<p class="section-copy">Use these identifiers when requesting compatibility or quotation information.</p>',
        text,
        count=1,
        flags=re.I | re.S,
    )
    return re.sub(r'<div class="aliases">.*?</div>', f'<div class="aliases">{chips}</div>', text, count=1, flags=re.I | re.S)

def remove_unverified_oem_visible(text: str, t: Truth) -> str:
    if t.oem_verified:
        return text
    text = re.sub(
        r'<div><dt>(?:OEM number|Replacement part for OEM number|Verified OEM cross-reference)</dt><dd>.*?</dd></div>',
        "",
        text,
        flags=re.I | re.S,
    )
    return re.sub(r"OEM\+number%3A\+.*?%0A", "", text, flags=re.I)

def rewrite_model_attributes(text: str, t: Truth) -> str:
    model = t.model or "Confirm during quotation"
    text = re.sub(r'(data-part-model=")[^"]*(")', rf'\1{html.escape(model, quote=True)}\2', text, count=1, flags=re.I)
    return re.sub(
        r"Model\+reference%3A\+(?:Model\+unresolved|model\+to\+be\+confirmed)",
        "Model+reference%3A+Confirm+during+quotation",
        text,
        flags=re.I,
    )

def organization_entity() -> dict:
    return {
        "@type": "Organization",
        "@id": ORG_ID,
        "name": "PharmaGlobalEng",
        "url": SITE + "/",
        "logo": {"@type": "ImageObject", "url": SITE + "/assets/images/about-pge-logo.svg"},
    }

def normalize_product(product: dict, t: Truth, meta: str) -> dict:
    product["name"] = page_h1(t)
    product["sku"] = t.sku
    product["description"] = meta
    product["alternateName"] = factual_aliases(t)
    product["brand"] = {"@type": "Brand", "name": "PharmaGlobalEng"}
    product["manufacturer"] = {"@id": ORG_ID}
    if t.family:
        product["category"] = t.family
    if t.model:
        product["isAccessoryOrSparePartFor"] = {"@type": "ProductModel", "name": f"{t.brand} {t.model}"}
    else:
        product.pop("isAccessoryOrSparePartFor", None)

    props = [
        {"@type": "PropertyValue", "name": "Make", "value": t.brand},
        {"@type": "PropertyValue", "name": "Supplier relationship", "value": "Independent replacement-part manufacturer; not OEM affiliated or endorsed"},
    ]
    if t.model:
        props.insert(1, {"@type": "PropertyValue", "name": "Model", "value": t.model})
    if t.oem_verified and t.oem:
        props.append({"@type": "PropertyValue", "name": "OEM cross-reference", "value": t.oem})
        product["identifier"] = {"@type": "PropertyValue", "propertyID": "OEM cross-reference", "value": t.oem}
    else:
        product.pop("identifier", None)
    product["additionalProperty"] = props

    offers = product.get("offers")
    if offers:
        offer_list = offers if isinstance(offers, list) else [offers]
        complete = [
            offer for offer in offer_list
            if isinstance(offer, dict) and clean(offer.get("price")) and clean(offer.get("priceCurrency"))
        ]
        if complete:
            product["offers"] = complete if isinstance(offers, list) else complete[0]
        else:
            product.pop("offers", None)
    return product

def rewrite_jsonld(text: str, t: Truth) -> tuple[str, bool]:
    touched = False
    meta = page_meta(t)

    def repl(match: re.Match) -> str:
        nonlocal touched
        try:
            data = json.loads(html.unescape(match.group(2).strip()))
        except json.JSONDecodeError:
            return match.group(0)
        graph = data.get("@graph") if isinstance(data, dict) else None
        product_found = False
        if isinstance(graph, list):
            new_graph = []
            org_found = False
            for item in graph:
                if not isinstance(item, dict):
                    new_graph.append(item)
                    continue
                types = item.get("@type")
                is_product = types == "Product" or (isinstance(types, list) and "Product" in types)
                if is_product:
                    item = normalize_product(item, t, meta)
                    product_found = True
                if item.get("@id") == ORG_ID:
                    item = organization_entity()
                    org_found = True
                new_graph.append(item)
            if product_found and not org_found:
                new_graph.append(organization_entity())
            data["@graph"] = new_graph
        elif isinstance(data, dict) and data.get("@type") == "Product":
            data = {"@context": "https://schema.org", "@graph": [normalize_product(data, t, meta), organization_entity()]}
            product_found = True
        if not product_found:
            return match.group(0)
        touched = True
        payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        return match.group(1) + payload + match.group(3)

    return JSONLD_RE.sub(repl, text), touched

def normalize_page(path: Path, text: str) -> str:
    t = TRUTH.get(sku_from_path(path)) or fallback_truth(path, text)
    new = sanitize_placeholders(text)
    title = page_title(t)
    meta = page_meta(t)
    new = set_title(new, title)
    new = set_meta(new, "description", meta)
    new = set_meta(new, "og:title", title, prop=True)
    new = set_meta(new, "og:description", meta, prop=True)
    new = set_meta(new, "twitter:title", title)
    new = set_meta(new, "twitter:description", meta)
    new = rewrite_h1(new, t)
    new = rewrite_lead(new, t)
    new = rewrite_compatibility(new, t)
    new = rewrite_alias_section(new, t)
    new = remove_unverified_oem_visible(new, t)
    new = rewrite_model_attributes(new, t)
    new, _ = rewrite_jsonld(new, t)
    new = sanitize_placeholders(new)
    if t.source == "data/kikusui-parts.csv" and not (t.verification or "").casefold().startswith("verified"):
        new = new.replace("<h2>Verified part mapping</h2>", "<h2>Part record</h2>")
        new = new.replace("<strong>Source verification:</strong>", "<strong>Source review:</strong>")
    return new

def audit_page(path: Path, text: str) -> dict[str, bool | int | str]:
    sku = sku_from_path(path)
    t = TRUTH.get(sku) or fallback_truth(path, text)
    title = strip_tags(extract(r"<title[^>]*>(.*?)</title>", text) or "")
    meta = html.unescape(extract(r'<meta(?=[^>]*name=["\']description["\'])[^>]*content=["\'](.*?)["\']', text) or "")
    canonical = html.unescape(extract(r'<link(?=[^>]*rel=["\']canonical["\'])[^>]*href=["\'](.*?)["\']', text) or "")
    h1s = re.findall(r"<h1[^>]*>(.*?)</h1>", text, re.I | re.S)
    aliases = re.findall(r'<span class="alias">.*?</span>', text, re.I | re.S)
    json_blocks = re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', text, re.I | re.S)
    product_schema = False
    json_valid = True
    for block in json_blocks:
        try:
            data = json.loads(html.unescape(block.strip()))
        except json.JSONDecodeError:
            json_valid = False
            continue
        if '"Product"' in json.dumps(data, ensure_ascii=False):
            product_schema = True
    expected = f"{SITE}/parts/{sku.lower()}/"
    unverified_oem_exposed = bool(t.raw_oem and not t.oem_verified and re.search(re.escape(t.raw_oem), text, re.I))
    return {
        "placeholder": bool(PLACEHOLDER_RE.search(text)),
        "title_long": len(title) > 72,
        "meta_long": len(meta) > 175,
        "missing_h1": len(h1s) != 1,
        "missing_canonical": canonical != expected,
        "noindex": bool(re.search(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex', text, re.I)),
        "missing_product_schema": not product_schema,
        "invalid_jsonld": not json_valid,
        "alias_excess": len(aliases) > 5,
        "search_directed_copy": bool(re.search(r"Search recognizes|search recognizes|Find this part using similar terms", text)),
        "unverified_oem_exposed": unverified_oem_exposed,
        "title": title,
        "meta": meta,
    }

def totals(rows: list[dict]) -> Counter:
    keys = [
        "placeholder", "title_long", "meta_long", "missing_h1", "missing_canonical",
        "noindex", "missing_product_schema", "invalid_jsonld", "alias_excess",
        "search_directed_copy", "unverified_oem_exposed",
    ]
    return Counter({key: sum(bool(row.get(key)) for row in rows) for key in keys})

def duplicate_count(rows: list[dict], key: str) -> int:
    counts = Counter(clean(row.get(key)) for row in rows if clean(row.get(key)))
    return sum(count - 1 for count in counts.values() if count > 1)

def render_report(before_rows: list[dict], after_rows: list[dict], changed: int, source_coverage: int) -> str:
    b = totals(before_rows)
    a = totals(after_rows)
    lines = [
        "# Parts Search / AI Quality Audit", "",
        "This report is generated from the public `parts/pge-*/index.html` detail pages.",
        "The cleanup is intentionally conservative: it removes placeholder entity data and search-engine-directed repetition without inventing specifications, prices, OEM numbers, or compatibility claims.", "",
        f"- Detail pages audited: **{len(after_rows):,}**",
        f"- Pages matched to structured source records: **{source_coverage:,}**",
        f"- Pages changed by normalization: **{changed:,}**",
        f"- Duplicate titles after normalization: **{duplicate_count(after_rows, 'title'):,}**",
        f"- Duplicate meta descriptions after normalization: **{duplicate_count(after_rows, 'meta'):,}**", "",
        "## Before / after", "", "| Check | Before | After |", "|---|---:|---:|",
    ]
    labels = {
        "placeholder": "Placeholder model language",
        "title_long": "Titles over 72 characters",
        "meta_long": "Meta descriptions over 175 characters",
        "missing_h1": "Missing or multiple H1",
        "missing_canonical": "Missing/wrong self-canonical",
        "noindex": "Detail pages marked noindex",
        "missing_product_schema": "Missing Product JSON-LD",
        "invalid_jsonld": "Invalid JSON-LD",
        "alias_excess": "More than 5 visible alias chips",
        "search_directed_copy": "Search-engine-directed alias copy",
        "unverified_oem_exposed": "Reviewed/unverified OEM value exposed",
    }
    for key, label in labels.items():
        lines.append(f"| {label} | {b[key]:,} | {a[key]:,} |")
    lines += [
        "", "## Publication rules enforced", "",
        "- Publish only factual part name, make, verified model, PGE SKU, and verified/catalog-supported OEM cross-reference.",
        "- Never render `Model unresolved`, `model unconfirmed`, or similar placeholders as equipment models.",
        "- Reviewed-only Kikusui cross-references are not labeled as verified OEM numbers.",
        "- Keep visible/schema aliases concise; punctuation-only SKU variants and repeated OEM permutations are removed.",
        "- Product titles and descriptions are concise and user-facing rather than stuffed with repeated compatibility phrases.",
        "- Product JSON-LD is aligned to visible facts and points to one PharmaGlobalEng Organization entity with a logo.",
        "- Incomplete/fabricated Offer data is never added; quotation-only parts do not receive invented prices.",
        "- Exact fit, dimensions, materials, finishes, and machine configuration remain subject to engineering confirmation unless a source explicitly supports them.",
        "", "## AI/GEO principle", "",
        "The catalog is optimized as a set of clear product entities, not as a keyword-volume system. Each page should make the relationship between part, make, model, SKU, verified cross-reference, and compatibility basis easy to extract while avoiding unsupported claims and repetitive search phrases.", "",
    ]
    return "\n".join(lines)

def run(fix: bool, check: bool) -> int:
    paths = detail_paths()
    before_rows = []
    originals: dict[Path, str] = {}
    for path in paths:
        text = path.read_text(encoding="utf-8")
        originals[path] = text
        before_rows.append(audit_page(path, text))

    changed = 0
    if fix:
        for path in paths:
            original = originals[path]
            updated = normalize_page(path, original)
            if updated != original:
                path.write_text(updated, encoding="utf-8")
                changed += 1

    after_rows = [audit_page(path, path.read_text(encoding="utf-8")) for path in paths]
    source_coverage = sum(sku_from_path(path) in TRUTH for path in paths)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(render_report(before_rows, after_rows, changed, source_coverage), encoding="utf-8")

    b = totals(before_rows)
    a = totals(after_rows)
    print(f"Audited {len(paths)} part detail pages; {changed} changed; source coverage {source_coverage}.")
    print("Before:", dict(b))
    print("After:", dict(a))

    critical_keys = [
        "placeholder", "missing_h1", "missing_canonical", "noindex",
        "missing_product_schema", "invalid_jsonld", "unverified_oem_exposed",
    ]
    remaining = {key: a[key] for key in critical_keys if a[key]}
    if check and remaining:
        print("CRITICAL PART QUALITY ISSUES REMAIN:", remaining)
        return 1
    return 0

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true", help="Normalize part pages in place.")
    parser.add_argument("--check", action="store_true", help="Exit non-zero when critical issues remain.")
    args = parser.parse_args()
    return run(args.fix, args.check)

if __name__ == "__main__":
    raise SystemExit(main())
