#!/usr/bin/env python3
"""Add safe JSON-LD structured data to public HTML pages that do not already have it.

This script preserves existing JSON-LD (especially Product schema on parts pages) and
only injects schema where it is missing. It also validates that every public HTML page
has parseable JSON-LD after the pass.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://pharmaglobaleng.com"
ORG_ID = f"{SITE}/#organization"
WEBSITE_ID = f"{SITE}/#website"

SKIP_PREFIXES = ("_next/", "next-app/")
SKIP_FILES = {"googleb09af90219443617.html"}


def is_public_html(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    if not rel.endswith(".html"):
        return False
    if rel in SKIP_FILES:
        return False
    if any(rel.startswith(prefix) for prefix in SKIP_PREFIXES):
        return False
    return True


def extract(pattern: str, text: str) -> str | None:
    m = re.search(pattern, text, flags=re.I | re.S)
    return html.unescape(m.group(1).strip()) if m else None


def title_from_html(text: str) -> str:
    return extract(r"<title[^>]*>(.*?)</title>", text) or "PharmaGlobalEng"


def description_from_html(text: str) -> str:
    value = extract(
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', text
    )
    if value:
        return value
    value = extract(
        r'<meta[^>]+content=["\'](.*?)["\'][^>]+name=["\']description["\']', text
    )
    return value or "PharmaGlobalEng pharmaceutical tablet tooling, replacement parts, and engineering support."


def canonical_from_html(path: Path, text: str) -> str:
    value = extract(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\'](.*?)["\']', text)
    if not value:
        value = extract(r'<link[^>]+href=["\'](.*?)["\'][^>]+rel=["\']canonical["\']', text)
    if value:
        if value.startswith("http"):
            return value
        return SITE + (value if value.startswith("/") else "/" + value)

    rel = path.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return SITE + "/"
    if rel.endswith("/index.html"):
        return SITE + "/" + rel[: -len("index.html")]
    return SITE + "/" + rel


def page_name(title: str) -> str:
    return re.sub(r"\s*\|\s*PharmaGlobalEng\s*$", "", title, flags=re.I).strip() or title


def crumb_name(segment: str) -> str:
    segment = segment.replace(".html", "").replace("-", " ").replace("_", " ")
    return " ".join(word.upper() if word.lower() in {"oem", "faq"} else word.capitalize() for word in segment.split())


def breadcrumbs(url: str, title: str) -> dict | None:
    parsed = urlparse(url)
    segments = [s for s in parsed.path.split("/") if s]
    if not segments:
        return None

    items = [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"}
    ]
    current = ""
    for i, segment in enumerate(segments, start=2):
        current += "/" + segment
        is_last = i == len(segments) + 1
        name = page_name(title) if is_last else crumb_name(segment)
        item = SITE + current
        if "." not in segment:
            item += "/"
        items.append({"@type": "ListItem", "position": i, "name": name, "item": item})
    return {"@type": "BreadcrumbList", "itemListElement": items}


def og_image(text: str) -> str | None:
    value = extract(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\'](.*?)["\']', text)
    if not value:
        value = extract(r'<meta[^>]+content=["\'](.*?)["\'][^>]+property=["\']og:image["\']', text)
    if value and not value.startswith("http"):
        value = SITE + (value if value.startswith("/") else "/" + value)
    return value


def schema_for(path: Path, text: str) -> dict:
    rel = path.relative_to(ROOT).as_posix()
    title = title_from_html(text)
    name = page_name(title)
    desc = description_from_html(text)
    url = canonical_from_html(path, text)
    image = og_image(text)

    if rel == "index.html":
        graph = [
            {
                "@type": "Organization",
                "@id": ORG_ID,
                "name": "PharmaGlobalEng",
                "url": SITE + "/",
                "description": "Pharmaceutical tablet tooling, replacement parts, restoration, precision polishing, surface engineering, coatings, and tablet compression support.",
                "logo": {"@type": "ImageObject", "url": SITE + "/assets/images/about-pge-logo.svg"},
            },
            {
                "@type": "WebSite",
                "@id": WEBSITE_ID,
                "url": SITE + "/",
                "name": "PharmaGlobalEng",
                "publisher": {"@id": ORG_ID},
                "inLanguage": "en-US",
            },
            {
                "@type": "WebPage",
                "@id": url + "#webpage",
                "url": url,
                "name": title,
                "description": desc,
                "isPartOf": {"@id": WEBSITE_ID},
                "about": {"@id": ORG_ID},
                "inLanguage": "en-US",
            },
        ]
        if image:
            graph[-1]["primaryImageOfPage"] = {"@type": "ImageObject", "url": image}
        return {"@context": "https://schema.org", "@graph": graph}

    page_type = "WebPage"
    entity = None

    if rel == "about/index.html":
        page_type = "AboutPage"
    elif rel == "contact.html":
        page_type = "ContactPage"
    elif rel in {"services/index.html", "solutions/index.html", "knowledge-center/index.html"}:
        page_type = "CollectionPage"
    elif rel.startswith("knowledge-center/"):
        page_type = "TechArticle"
    elif rel.startswith("services/") or rel.startswith("coatings/"):
        entity = {
            "@type": "Service",
            "@id": url + "#service",
            "name": name,
            "description": desc,
            "url": url,
            "provider": {"@id": ORG_ID},
            "areaServed": "Worldwide",
        }
    elif rel.startswith("parts/") and "/pge-" in ("/" + rel.lower()):
        sku_match = re.search(r"pge-[a-z]+-\d+", rel, flags=re.I)
        entity = {
            "@type": "Product",
            "@id": url + "#product",
            "name": name,
            "description": desc,
            "url": url,
            "brand": {"@type": "Brand", "name": "PharmaGlobalEng"},
            "manufacturer": {"@id": ORG_ID},
        }
        if sku_match:
            entity["sku"] = sku_match.group(0).upper()
        if image:
            entity["image"] = image
    elif rel.startswith("parts/"):
        page_type = "CollectionPage"
    elif rel.startswith("solutions/"):
        page_type = "WebPage"

    page = {
        "@type": page_type,
        "@id": url + "#webpage",
        "url": url,
        "name": title,
        "description": desc,
        "isPartOf": {"@id": WEBSITE_ID},
        "about": {"@id": ORG_ID},
        "inLanguage": "en-US",
    }
    if image:
        page["primaryImageOfPage"] = {"@type": "ImageObject", "url": image}

    graph = [page]
    if page_type == "TechArticle":
        page["publisher"] = {"@id": ORG_ID}
        page["author"] = {"@id": ORG_ID}
        page["mainEntityOfPage"] = {"@id": url + "#webpage"}
    if entity:
        page["mainEntity"] = {"@id": entity["@id"]}
        graph.append(entity)
    crumb = breadcrumbs(url, title)
    if crumb:
        graph.append(crumb)
    return {"@context": "https://schema.org", "@graph": graph}


def validate_blocks(path: Path, text: str) -> None:
    blocks = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        text,
        flags=re.I | re.S,
    )
    if not blocks:
        raise ValueError(f"No JSON-LD found after processing: {path}")
    for block in blocks:
        json.loads(html.unescape(block.strip()))


def main() -> None:
    public = [p for p in ROOT.rglob("*.html") if is_public_html(p)]
    injected = 0
    preserved = 0

    for path in sorted(public):
        text = path.read_text(encoding="utf-8", errors="strict")
        if re.search(r'type=["\']application/ld\+json["\']', text, flags=re.I):
            validate_blocks(path, text)
            preserved += 1
            continue

        if "</head>" not in text.lower():
            raise ValueError(f"Public HTML page has no </head>: {path}")

        payload = json.dumps(schema_for(path, text), ensure_ascii=False, separators=(",", ":"))
        block = f'\n<script type="application/ld+json">{payload}</script>\n'
        text = re.sub(r"</head>", block + "</head>", text, count=1, flags=re.I)
        validate_blocks(path, text)
        path.write_text(text, encoding="utf-8")
        injected += 1

    # Final coverage check.
    for path in public:
        validate_blocks(path, path.read_text(encoding="utf-8"))

    print(f"Public HTML pages checked: {len(public)}")
    print(f"Existing schema preserved: {preserved}")
    print(f"Schema injected: {injected}")
    print("Coverage: 100% of public HTML pages")


if __name__ == "__main__":
    main()
