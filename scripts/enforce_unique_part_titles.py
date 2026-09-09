#!/usr/bin/env python3
from __future__ import annotations

import html
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTS = ROOT / "parts"
LIMIT = 72


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()


def get_title(text: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
    return clean(match.group(1)) if match else ""


def part_name(text: str, sku: str) -> str:
    match = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.I | re.S)
    value = clean(match.group(1)) if match else sku
    value = re.split(r"\s+(?:for|—)\s+", value, maxsplit=1, flags=re.I)[0].strip()
    return value or sku


def trim_words(value: str, limit: int) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) <= limit:
        return value
    cut = value[: limit + 1].rsplit(" ", 1)[0].rstrip(" |–—-:,;")
    return cut or value[:limit].rstrip()


def unique_title(text: str, sku: str) -> str:
    suffix = f" | {sku} | PGE"
    budget = max(18, LIMIT - len(suffix))
    return trim_words(part_name(text, sku), budget) + suffix


def set_title_fields(text: str, title: str) -> str:
    escaped = html.escape(title, quote=True)
    text = re.sub(r"<title[^>]*>.*?</title>", f"<title>{html.escape(title)}</title>", text, count=1, flags=re.I | re.S)
    for attr, key in (("property", "og:title"), ("name", "twitter:title")):
        pattern = rf'<meta(?=[^>]*\b{attr}=["\']{re.escape(key)}["\'])[^>]*>'
        replacement = f'<meta {attr}="{key}" content="{escaped}">'
        text = re.sub(pattern, replacement, text, count=1, flags=re.I)
    return text


def pages() -> list[Path]:
    return sorted(p for p in PARTS.glob("pge-*/index.html") if p.is_file())


def main() -> int:
    paths = pages()
    groups: dict[str, list[Path]] = defaultdict(list)
    texts: dict[Path, str] = {}
    for path in paths:
        text = path.read_text(encoding="utf-8")
        texts[path] = text
        groups[get_title(text).casefold()].append(path)

    duplicate_groups = [group for key, group in groups.items() if key and len(group) > 1]
    changed = 0
    for group in duplicate_groups:
        for path in group:
            sku = path.parent.name.upper()
            updated = set_title_fields(texts[path], unique_title(texts[path], sku))
            if updated != texts[path]:
                path.write_text(updated, encoding="utf-8")
                texts[path] = updated
                changed += 1

    final_titles: dict[str, Path] = {}
    duplicates = []
    overlong = []
    for path in paths:
        title = get_title(path.read_text(encoding="utf-8"))
        key = title.casefold()
        if key in final_titles:
            duplicates.append((final_titles[key], path, title))
        else:
            final_titles[key] = path
        if len(title) > LIMIT:
            overlong.append((path, title))

    print(f"Duplicate title groups found: {len(duplicate_groups)}; pages changed: {changed}.")
    if duplicates:
        for left, right, title in duplicates[:20]:
            print(f"DUPLICATE: {left} <> {right}: {title}")
        return 1
    if overlong:
        for path, title in overlong[:20]:
            print(f"OVERLONG: {path}: {len(title)} chars: {title}")
        return 1
    print(f"Verified {len(paths)} unique part-page titles, all <= {LIMIT} characters.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
