#!/usr/bin/env python3
"""Fail-fast technical SEO regression check for every public HTML route."""

from __future__ import annotations

import csv
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urljoin, urlsplit
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://pharmaglobaleng.com"
SKIP_PREFIXES = ("_next/", "next-app/")
SKIP_FILES = {"googleb09af90219443617.html"}
JSONLD_RE = re.compile(
    r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.I | re.S,
)


class Page(HTMLParser):
    def __init__(self, source: str):
        super().__init__(convert_charrefs=True)
        self.canonicals: list[str] = []
        self.descriptions: list[str] = []
        self.h1_count = 0
        self.links: list[str] = []
        self.resources: list[str] = []
        self.robots: list[str] = []
        self.refresh = False
        self.lang = ""
        self.image_meta: list[str] = []
        self.feed(source)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag == "html":
            self.lang = values.get("lang", "")
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "a" and values.get("href"):
            self.links.append(values["href"])
        elif tag in {"img", "script"} and values.get("src"):
            self.resources.append(values["src"])
        elif tag == "link" and values.get("href"):
            rels = values.get("rel", "").lower().split()
            if "canonical" in rels:
                self.canonicals.append(values["href"])
            elif set(rels) & {"stylesheet", "icon", "manifest", "preload"}:
                self.resources.append(values["href"])
        elif tag == "meta":
            key = (values.get("name") or values.get("property") or values.get("http-equiv") or "").lower()
            content = values.get("content", "")
            if key == "description":
                self.descriptions.append(content)
            elif key in {"robots", "googlebot", "bingbot"}:
                self.robots.append(content.lower())
            elif key == "refresh":
                self.refresh = True
            elif key in {"og:image", "twitter:image"} and content:
                self.image_meta.append(content)


def public_html() -> list[Path]:
    result = []
    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT).as_posix()
        if rel in SKIP_FILES or any(rel.startswith(prefix) for prefix in SKIP_PREFIXES):
            continue
        result.append(path)
    return sorted(result)


def route(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return SITE + "/"
    if rel.endswith("/index.html"):
        return SITE + "/" + rel[:-10]
    return SITE + "/" + rel


def git_inventory() -> set[str]:
    tracked = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", "HEAD"], cwd=ROOT, text=True
    ).splitlines()
    working = [path.relative_to(ROOT).as_posix() for path in ROOT.rglob("*") if path.is_file()]
    return set(tracked) | set(working)


def local_target(value: str, base: str, inventory: set[str]) -> str | None:
    if not value or value.startswith(("#", "data:", "mailto:", "tel:", "javascript:")):
        return None
    parsed = urlsplit(urljoin(base, value))
    if parsed.scheme not in {"http", "https"}:
        return None
    if parsed.netloc.lower() not in {"pharmaglobaleng.com", "www.pharmaglobaleng.com"}:
        return None
    name = unquote(parsed.path).lstrip("/")
    if not name:
        candidates = ["index.html"]
    elif name.endswith("/"):
        candidates = [name + "index.html"]
    else:
        candidates = [name, name + "/index.html", name + ".html"]
    return next((candidate for candidate in candidates if candidate in inventory), "!missing:" + name)


def json_nodes(value: object):
    if isinstance(value, dict):
        if "@type" in value:
            yield value
        for child in value.values():
            yield from json_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from json_nodes(child)


def json_image_urls(value: object):
    if isinstance(value, dict):
        if value.get("@type") == "ImageObject":
            for key in ("url", "contentUrl"):
                if isinstance(value.get(key), str):
                    yield value[key]
        for key in ("image", "logo", "primaryImageOfPage"):
            child = value.get(key)
            if isinstance(child, str):
                yield child
        for child in value.values():
            yield from json_image_urls(child)
    elif isinstance(value, list):
        for child in value:
            yield from json_image_urls(child)


def expected_noindex() -> set[str]:
    result = {"parts/search/index.html"}
    audit = ROOT / "data/noindex-page-audit.csv"
    with audit.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("decision", "").strip().casefold() == "keep noindex":
                value = row.get("path", "").strip().lstrip("/")
                if value:
                    result.add(value)
    return result


def main() -> int:
    inventory = git_inventory()
    files = public_html()
    issues: dict[str, list[str]] = {}
    pages: dict[str, Page] = {}
    noindex_paths: set[str] = set()
    product_nodes = 0
    jsonld_blocks = 0

    def issue(kind: str, detail: str) -> None:
        issues.setdefault(kind, []).append(detail)

    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        source = path.read_text(encoding="utf-8")
        page = Page(source)
        pages[rel] = page
        url = route(path)
        redirect = page.refresh or bool(re.search(r"(?:window\.)?location(?:\.href|\.replace)?\s*[=(]", source))
        noindex = any("noindex" in value for value in page.robots)
        if noindex:
            noindex_paths.add(rel)

        if not redirect:
            if page.h1_count != 1:
                issue("h1_count", f"{rel}: {page.h1_count}")
            if page.canonicals != [url]:
                issue("canonical", f"{rel}: {page.canonicals!r}; expected {url}")
            if len(page.descriptions) != 1 or not page.descriptions[0].strip():
                issue("description", f"{rel}: {page.descriptions!r}")
            if not page.lang:
                issue("language", rel)

        decoded_blocks: list[object] = []
        for raw in JSONLD_RE.findall(source):
            jsonld_blocks += 1
            try:
                decoded_blocks.append(json.loads(html.unescape(raw.strip())))
            except json.JSONDecodeError as exc:
                issue("invalid_jsonld", f"{rel}: {exc}")
        if not decoded_blocks:
            issue("missing_jsonld", rel)

        nodes = [node for block in decoded_blocks for node in json_nodes(block)]
        product_nodes += sum(node.get("@type") == "Product" for node in nodes)
        if any(node.get("@type") == "Product" for node in nodes):
            issue("quote_only_product_schema", rel)

        if re.fullmatch(r"parts/pge-[^/]+/index\.html", rel):
            catalog_pages = [
                node for node in nodes
                if node.get("@type") == "WebPage"
                and node.get("url") == url
                and isinstance(node.get("mainEntity"), dict)
                and node["mainEntity"].get("@type") == "Thing"
            ]
            if len(catalog_pages) != 1:
                issue("catalog_schema", f"{rel}: {len(catalog_pages)} matching pages")

        for value in page.links + page.resources + page.image_meta:
            target = local_target(value, url, inventory)
            if target and target.startswith("!missing:"):
                issue("missing_internal_target", f"{rel}: {value}")
        for block in decoded_blocks:
            for value in json_image_urls(block):
                target = local_target(value, url, inventory)
                if target and target.startswith("!missing:"):
                    issue("missing_schema_image", f"{rel}: {value}")

    intended_noindex = expected_noindex()
    for rel in sorted(noindex_paths - intended_noindex):
        issue("unexpected_noindex", rel)
    for rel in sorted(intended_noindex - noindex_paths):
        issue("missing_expected_noindex", rel)

    sitemap_urls: set[str] = set()
    sitemap_counts: dict[str, int] = {}
    for name in ("sitemap.xml", "sitemap-parts-images.xml", "sitemap-cremer.xml"):
        path = ROOT / name
        try:
            root = ET.fromstring(path.read_text(encoding="utf-8"))
        except (OSError, ET.ParseError) as exc:
            issue("sitemap_parse", f"{name}: {exc}")
            continue
        urls = [node.text or "" for node in root.findall("{*}url/{*}loc")]
        sitemap_counts[name] = len(urls)
        if len(urls) != len(set(urls)):
            issue("duplicate_sitemap_url", name)
        if name == "sitemap.xml":
            sitemap_urls.update(urls)
        for value in urls:
            target = local_target(value, SITE + "/", inventory)
            if target and target.startswith("!missing:"):
                issue("sitemap_missing_target", f"{name}: {value}")
            elif target in noindex_paths:
                issue("sitemap_noindex_target", f"{name}: {value}")
        for node in root.findall(".//{http://www.google.com/schemas/sitemap-image/1.1}loc"):
            target = local_target(node.text or "", SITE + "/", inventory)
            if target and target.startswith("!missing:"):
                issue("sitemap_missing_image", f"{name}: {node.text}")

    for rel, page in pages.items():
        if rel in noindex_paths or page.refresh:
            continue
        url = route(ROOT / rel)
        if page.canonicals == [url] and url not in sitemap_urls:
            issue("indexable_page_missing_from_sitemap", rel)

    summary = {
        "public_html": len(files),
        "jsonld_blocks": jsonld_blocks,
        "legacy_product_nodes": product_nodes,
        "intentional_noindex_pages": len(noindex_paths),
        "sitemaps": sitemap_counts,
        "issues": {key: len(value) for key, value in sorted(issues.items())},
    }
    print(json.dumps(summary, indent=2))
    for kind, values in sorted(issues.items()):
        for value in values[:20]:
            print(f"FAIL {kind}: {value}")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
