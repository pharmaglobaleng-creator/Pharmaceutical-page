#!/usr/bin/env python3
"""Replace incomplete Product rich-result markup on quote-only part pages."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

from catalog_page_schema import catalog_page_from_product


ROOT = Path(__file__).resolve().parents[1]
JSONLD_RE = re.compile(
    r'(<script[^>]+type=["\']application/ld\+json["\'][^>]*>)(.*?)(</script>)',
    re.I | re.S,
)


def product_node(value: object) -> bool:
    return isinstance(value, dict) and value.get("@type") == "Product"


def migrate_data(data: object) -> tuple[object, int]:
    if not isinstance(data, dict):
        return data, 0

    graph = data.get("@graph")
    if not isinstance(graph, list):
        if product_node(data):
            return {
                "@context": "https://schema.org",
                "@graph": [catalog_page_from_product(data)],
            }, 1
        return data, 0

    products = [node for node in graph if product_node(node)]
    if not products:
        return data, 0

    converted_by_url = {
        str(product.get("url") or ""): catalog_page_from_product(product)
        for product in products
    }
    existing_page_urls = {
        str(node.get("url") or "")
        for node in graph
        if isinstance(node, dict) and node.get("@type") == "WebPage"
    }
    rewritten: list[object] = []
    merged_urls: set[str] = set()

    for node in graph:
        if product_node(node):
            url = str(node.get("url") or "")
            if url in existing_page_urls:
                continue
            if url not in merged_urls:
                rewritten.append(converted_by_url[url])
                merged_urls.add(url)
            continue

        if isinstance(node, dict) and node.get("@type") == "WebPage":
            url = str(node.get("url") or "")
            converted = converted_by_url.get(url)
            if converted:
                # Preserve reviewed page-level fields (image, breadcrumb, language)
                # while replacing the Product reference and commerce-triggering node.
                merged = dict(converted)
                merged.update(node)
                merged["@type"] = "WebPage"
                merged["@id"] = converted["@id"]
                merged["url"] = converted["url"]
                merged["mainEntity"] = converted["mainEntity"]
                if "primaryImageOfPage" not in merged and "primaryImageOfPage" in converted:
                    merged["primaryImageOfPage"] = converted["primaryImageOfPage"]
                rewritten.append(merged)
                merged_urls.add(url)
                continue
        rewritten.append(node)

    # Existing WebPage nodes normally precede Product nodes. Remove any duplicate
    # page inserted when the Product appeared first.
    deduped: list[object] = []
    seen_pages: set[str] = set()
    for node in rewritten:
        if isinstance(node, dict) and node.get("@type") == "WebPage":
            url = str(node.get("url") or "")
            if url in seen_pages:
                continue
            seen_pages.add(url)
        deduped.append(node)

    result = dict(data)
    result["@graph"] = deduped
    return result, len(products)


def migrate_text(text: str) -> tuple[str, int]:
    converted = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal converted
        try:
            data = json.loads(html.unescape(match.group(2).strip()))
        except json.JSONDecodeError:
            return match.group(0)
        migrated, count = migrate_data(data)
        if not count:
            return match.group(0)
        converted += count
        payload = json.dumps(migrated, ensure_ascii=False, separators=(",", ":"))
        return match.group(1) + payload + match.group(3)

    return JSONLD_RE.sub(replace, text), converted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if legacy Product nodes remain")
    args = parser.parse_args()

    changed_pages = 0
    converted_nodes = 0
    for path in sorted((ROOT / "parts").rglob("*.html")):
        source = path.read_text(encoding="utf-8")
        rewritten, count = migrate_text(source)
        if not count:
            continue
        converted_nodes += count
        if args.check:
            continue
        path.write_text(rewritten, encoding="utf-8")
        changed_pages += 1

    if args.check and converted_nodes:
        raise SystemExit(f"Found {converted_nodes} legacy Product nodes")
    print(json.dumps({
        "changed_pages": changed_pages,
        "converted_product_nodes": converted_nodes,
        "legacy_product_nodes": 0 if not args.check else converted_nodes,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
