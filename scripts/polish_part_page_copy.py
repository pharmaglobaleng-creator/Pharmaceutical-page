#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTS = ROOT / "parts"
META_LIMIT = 175
JSONLD_RE = re.compile(r'(<script[^>]+type=["\']application/ld\+json["\'][^>]*>)(.*?)(</script>)', re.I | re.S)


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()


def trim_words(value: str, limit: int) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) <= limit:
        return value
    cut = value[: limit + 1].rsplit(" ", 1)[0].rstrip(" |–—-:,;")
    return cut or value[:limit].rstrip()


def h1(text: str) -> str:
    match = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.I | re.S)
    return clean(match.group(1)) if match else ""


def verified_oem(text: str) -> str | None:
    for match in JSONLD_RE.finditer(text):
        try:
            data = json.loads(html.unescape(match.group(2).strip()))
        except json.JSONDecodeError:
            continue
        graph = data.get("@graph", []) if isinstance(data, dict) else []
        if not isinstance(graph, list):
            graph = [data]
        for item in graph:
            if not isinstance(item, dict):
                continue
            types = item.get("@type")
            is_product = types == "Product" or (isinstance(types, list) and "Product" in types)
            if not is_product:
                continue
            identifier = item.get("identifier")
            if isinstance(identifier, dict) and identifier.get("propertyID") == "OEM cross-reference":
                value = str(identifier.get("value") or "").strip()
                if value:
                    return value
    return None


def complete_description(text: str, sku: str) -> str:
    heading = h1(text)
    if " for " in heading:
        part, equipment = heading.split(" for ", 1)
        tail = f" for {equipment}. PharmaGlobalEng replacement part {sku}."
    elif " — " in heading:
        part, context = heading.split(" — ", 1)
        tail = f" — {context}. PharmaGlobalEng SKU {sku}."
    else:
        part = heading or sku
        tail = f". PharmaGlobalEng replacement part {sku}."

    oem = verified_oem(text)
    if oem:
        tail += f" OEM cross-reference {oem}."
    tail += " Fit confirmed before quotation."

    budget = max(24, META_LIMIT - len(tail))
    description = trim_words(part, budget) + tail
    if len(description) > META_LIMIT:
        # Keep identifiers and a complete sentence even for exceptionally long names.
        short_tail = f". PharmaGlobalEng part {sku}."
        if oem:
            short_tail += f" OEM cross-reference {oem}."
        short_tail += " Fit confirmed before quotation."
        budget = max(18, META_LIMIT - len(short_tail))
        description = trim_words(part, budget) + short_tail
    return description


def set_description_meta(text: str, key: str, value: str, *, prop: bool = False) -> str:
    attr = "property" if prop else "name"
    pattern = rf'<meta(?=[^>]*\b{attr}=["\']{re.escape(key)}["\'])[^>]*>'
    replacement = f'<meta {attr}="{key}" content="{html.escape(value, quote=True)}">'
    if re.search(pattern, text, re.I):
        return re.sub(pattern, replacement, text, count=1, flags=re.I)
    return text


def set_lead(text: str, value: str) -> str:
    pattern = re.compile(r'(<div class="part-intro">.*?<p class="lead">).*?(</p>)', re.I | re.S)
    escaped = html.escape(value)
    return pattern.sub(lambda m: m.group(1) + escaped + m.group(2), text, count=1)


def set_product_description(text: str, value: str) -> str:
    def repl(match: re.Match) -> str:
        try:
            data = json.loads(html.unescape(match.group(2).strip()))
        except json.JSONDecodeError:
            return match.group(0)
        changed = False
        if isinstance(data, dict):
            graph = data.get("@graph")
            items = graph if isinstance(graph, list) else [data]
            for item in items:
                if not isinstance(item, dict):
                    continue
                types = item.get("@type")
                is_product = types == "Product" or (isinstance(types, list) and "Product" in types)
                if is_product:
                    item["description"] = value
                    changed = True
        if not changed:
            return match.group(0)
        return match.group(1) + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + match.group(3)
    return JSONLD_RE.sub(repl, text)


def clean_residual_placeholders(text: str) -> str:
    text = re.sub(
        r"(<h2>Related\s+)([^<]+?)\s+model to be confirmed\s+(components|records)(</h2>)",
        lambda m: f"{m.group(1)}{m.group(2).strip()} {m.group(3)}{m.group(4)}",
        text,
        flags=re.I,
    )
    text = re.sub(r"\bmodel to be confirmed\b", "exact model confirmed during quotation", text, flags=re.I)
    return text


def get_meta_description(text: str) -> str:
    match = re.search(r'<meta(?=[^>]*name=["\']description["\'])[^>]*content=["\'](.*?)["\']', text, re.I | re.S)
    return html.unescape(match.group(1)).strip() if match else ""


def pages() -> list[Path]:
    return sorted(p for p in PARTS.glob("pge-*/index.html") if p.is_file())


def main() -> int:
    changed = 0
    paths = pages()
    for path in paths:
        original = path.read_text(encoding="utf-8")
        sku = path.parent.name.upper()
        description = complete_description(original, sku)
        updated = clean_residual_placeholders(original)
        updated = set_description_meta(updated, "description", description)
        updated = set_description_meta(updated, "og:description", description, prop=True)
        updated = set_description_meta(updated, "twitter:description", description)
        updated = set_lead(updated, description)
        updated = set_product_description(updated, description)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed += 1

    failures = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        description = get_meta_description(text)
        if not description:
            failures.append(f"missing meta description: {path}")
        elif len(description) > META_LIMIT:
            failures.append(f"meta description too long ({len(description)}): {path}")
        elif description[-1:] not in ".!?":
            failures.append(f"meta description does not end cleanly: {path}: {description}")
        if re.search(r"\b(?:model unresolved|model unconfirmed|model unspecified|model to be confirmed)\b", text, re.I):
            failures.append(f"placeholder-style model language remains: {path}")

    print(f"Polished {len(paths)} part pages; {changed} page(s) changed.")
    if failures:
        for failure in failures[:50]:
            print("FAIL:", failure)
        print(f"Total failures: {len(failures)}")
        return 1
    print(f"Verified complete meta descriptions <= {META_LIMIT} chars and no placeholder-style model language on all {len(paths)} pages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
