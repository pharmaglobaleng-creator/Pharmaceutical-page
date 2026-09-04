#!/usr/bin/env python3
"""Validate sitemap, canonical, robots, and breadcrumb signals before publishing."""

from __future__ import annotations

import json
import urllib.parse
import xml.etree.ElementTree as ET
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://pharmaglobaleng.com"


class HeadParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.canonicals: list[str] = []
        self.robots: list[str] = []
        self.json_ld: list[str] = []
        self._json_depth = 0
        self._json_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {name.lower(): value or "" for name, value in attrs}
        if tag.lower() == "link" and "canonical" in data.get("rel", "").lower().split():
            self.canonicals.append(data.get("href", ""))
        if tag.lower() == "meta" and data.get("name", "").lower() in {"robots", "googlebot"}:
            self.robots.append(data.get("content", ""))
        if tag.lower() == "script" and data.get("type", "").lower() == "application/ld+json":
            self._json_depth += 1
            self._json_parts = []

    def handle_data(self, data: str) -> None:
        if self._json_depth:
            self._json_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._json_depth:
            self.json_ld.append("".join(self._json_parts))
            self._json_depth = 0
            self._json_parts = []


def contains_type(value, wanted: str) -> bool:
    if isinstance(value, dict):
        item_type = value.get("@type")
        if item_type == wanted or isinstance(item_type, list) and wanted in item_type:
            return True
        return any(contains_type(item, wanted) for item in value.values())
    if isinstance(value, list):
        return any(contains_type(item, wanted) for item in value)
    return False


def nodes_of_type(value, wanted: str) -> list[dict]:
    matches: list[dict] = []
    if isinstance(value, dict):
        item_type = value.get("@type")
        if item_type == wanted or isinstance(item_type, list) and wanted in item_type:
            matches.append(value)
        for item in value.values():
            matches.extend(nodes_of_type(item, wanted))
    elif isinstance(value, list):
        for item in value:
            matches.extend(nodes_of_type(item, wanted))
    return matches


def local_path(url: str) -> Path:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != "pharmaglobaleng.com":
        raise AssertionError(f"Unexpected sitemap origin: {url}")
    if parsed.path == "/":
        return ROOT / "index.html"
    if parsed.path.endswith("/"):
        return ROOT / parsed.path.lstrip("/") / "index.html"
    return ROOT / parsed.path.lstrip("/")


def main() -> None:
    sitemap_root = ET.parse(ROOT / "sitemap.xml").getroot()
    namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = [node.text.strip() for node in sitemap_root.findall("s:url/s:loc", namespace) if node.text]
    if len(urls) != len(set(urls)):
        raise AssertionError("Duplicate URL found in sitemap.xml")

    missing_files: list[str] = []
    empty_files: list[str] = []
    bad_canonicals: list[tuple[str, list[str]]] = []
    noindex_pages: list[str] = []
    invalid_json: list[str] = []
    missing_part_breadcrumbs: list[str] = []
    invalid_breadcrumbs: list[str] = []
    canonical_owners: defaultdict[str, list[str]] = defaultdict(list)

    for url in urls:
        path = local_path(url)
        if not path.exists():
            missing_files.append(url)
            continue
        if path.stat().st_size == 0:
            empty_files.append(url)
            continue
        if path.suffix.lower() != ".html":
            continue
        parser = HeadParser()
        parser.feed(path.read_text(encoding="utf-8"))
        if parser.canonicals != [url]:
            bad_canonicals.append((url, parser.canonicals))
        else:
            canonical_owners[url].append(url)
        if any("noindex" in directive.lower() for directive in parser.robots):
            noindex_pages.append(url)
        schemas = []
        for raw in parser.json_ld:
            try:
                schemas.append(json.loads(raw))
            except json.JSONDecodeError:
                invalid_json.append(url)
        if urllib.parse.urlsplit(url).path.startswith("/parts/"):
            breadcrumbs = [node for schema in schemas for node in nodes_of_type(schema, "BreadcrumbList")]
            if not breadcrumbs:
                missing_part_breadcrumbs.append(url)
            for breadcrumb in breadcrumbs:
                items = breadcrumb.get("itemListElement")
                if not isinstance(items, list) or len(items) < 2:
                    invalid_breadcrumbs.append(url)
                    continue
                positions = [item.get("position") for item in items if isinstance(item, dict)]
                valid_items = all(
                    isinstance(item, dict)
                    and item.get("@type") == "ListItem"
                    and isinstance(item.get("name"), str)
                    and item["name"].strip()
                    and isinstance(item.get("item"), str)
                    and item["item"].startswith(f"{SITE}/")
                    for item in items
                )
                if positions != list(range(1, len(items) + 1)) or not valid_items:
                    invalid_breadcrumbs.append(url)

    duplicate_canonicals = {key: owners for key, owners in canonical_owners.items() if len(owners) > 1}
    failures = {
        "missing sitemap files": missing_files,
        "empty sitemap files": empty_files,
        "bad canonicals": bad_canonicals,
        "noindex sitemap pages": noindex_pages,
        "invalid JSON-LD": invalid_json,
        "part pages missing BreadcrumbList": missing_part_breadcrumbs,
        "invalid BreadcrumbList": invalid_breadcrumbs,
        "duplicate canonical targets": duplicate_canonicals,
    }
    active_failures = {name: values for name, values in failures.items() if values}
    if active_failures:
        raise AssertionError(json.dumps(active_failures, indent=2))

    legacy = (ROOT / "tablet-punch-coatings.html").read_text(encoding="utf-8")
    expected_target = f"{SITE}/services/tablet-punch-coatings.html"
    if expected_target not in legacy or 'http-equiv="refresh"' not in legacy:
        raise AssertionError("Legacy coatings redirect is incomplete")

    print(f"Sitemap pages validated: {len(urls)}")
    print(f"Part/catalog BreadcrumbList pages validated: {sum('/parts/' in url for url in urls)}")
    print("Canonical errors: 0")
    print("Noindex sitemap pages: 0")
    print("Missing or empty sitemap pages: 0")
    print("Invalid JSON-LD pages: 0")
    print("Legacy coatings redirect: valid")


if __name__ == "__main__":
    main()
