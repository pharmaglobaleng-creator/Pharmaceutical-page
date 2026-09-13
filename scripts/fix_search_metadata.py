#!/usr/bin/env python3
"""Apply verified metadata fixes without changing intentional index exclusions."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORG_ID = "https://pharmaglobaleng.com/#organization"
LOGO = "https://pharmaglobaleng.com/assets/images/about-pge-logo.svg"
OLD_HOMEPAGE_DESCRIPTION = "PharmaGlobalEng provides worldwide pharmaceutical tablet tooling restoration, precision polishing, surface engineering, coatings, engraving optimization, and tablet sticking and picking solutions for manufacturers across global markets."
HOMEPAGE_DESCRIPTION = "Worldwide tablet tooling restoration, replacement parts, coatings, surface engineering, and compression support for pharmaceutical manufacturers."
JSONLD_RE = re.compile(
    r'(<script[^>]+type=["\']application/ld\+json["\'][^>]*>)(.*?)(</script>)',
    re.I | re.S,
)

NOINDEX_DESCRIPTIONS = {
    "coatings/chromium-nitride-crn.html": "Planned PharmaGlobalEng technical reference for chromium nitride coating considerations in pharmaceutical tooling applications.",
    "coatings/diamond-like-carbon-dlc.html": "Planned PharmaGlobalEng technical reference for diamond-like carbon coating considerations in pharmaceutical tooling applications.",
    "coatings/titanium-carbonitride-ticn.html": "Planned PharmaGlobalEng technical reference for titanium carbonitride coating considerations in pharmaceutical tooling applications.",
    "coatings/titanium-nitride-tin.html": "Planned PharmaGlobalEng technical reference for titanium nitride coating considerations in pharmaceutical tooling applications.",
    "components/capsule-machine-components.html": "Planned PharmaGlobalEng technical reference for capsule-machine component inspection, identification, and engineering review.",
    "components/feed-frames.html": "Planned PharmaGlobalEng technical reference for pharmaceutical feed-frame inspection, wear, and engineering review.",
    "components/tablet-dies.html": "Planned PharmaGlobalEng technical reference for tablet-die inspection, maintenance, and engineering review.",
    "components/tablet-punches.html": "Planned PharmaGlobalEng technical reference for tablet-punch inspection, maintenance, and engineering review.",
    "services/engraving-optimization.html": "Planned PharmaGlobalEng technical reference for tablet-tooling engraving evaluation and optimization.",
    "solutions/compression-defects.html": "Planned PharmaGlobalEng technical reference for evaluating pharmaceutical tablet-compression defects.",
    "solutions/corrosion-and-wear.html": "Planned PharmaGlobalEng technical reference for pharmaceutical tooling corrosion and wear evaluation.",
    "solutions/poor-tablet-release.html": "Planned PharmaGlobalEng technical reference for diagnosing poor tablet release during compression.",
    "solutions/powder-adhesion.html": "Planned PharmaGlobalEng technical reference for investigating powder adhesion on tablet tooling.",
}


def set_description(text: str, value: str) -> str:
    tag = f'<meta name="description" content="{html.escape(value, quote=True)}">'
    pattern = r'<meta(?=[^>]*name=["\']description["\'])[^>]*>'
    if re.search(pattern, text, re.I):
        return re.sub(pattern, tag, text, count=1, flags=re.I)
    return re.sub(r"</title>", "</title>\n" + tag, text, count=1, flags=re.I)


def add_organization_logo(text: str) -> tuple[str, bool]:
    changed = False

    def replace(match: re.Match[str]) -> str:
        nonlocal changed
        block_changed = False
        try:
            data = json.loads(html.unescape(match.group(2).strip()))
        except json.JSONDecodeError:
            return match.group(0)

        def walk(value: object) -> None:
            nonlocal block_changed, changed
            if isinstance(value, dict):
                types = value.get("@type")
                is_organization = types == "Organization" or (
                    isinstance(types, list) and "Organization" in types
                )
                if is_organization and value.get("@id") == ORG_ID:
                    if value.get("logo") != {"@type": "ImageObject", "url": LOGO}:
                        value["logo"] = {"@type": "ImageObject", "url": LOGO}
                        block_changed = True
                        changed = True
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(data)
        if not block_changed:
            return match.group(0)
        payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        return match.group(1) + payload + match.group(3)

    return JSONLD_RE.sub(replace, text), changed


def fix_homepage() -> int:
    path = ROOT / "index.html"
    text = path.read_text(encoding="utf-8")
    original = text
    text = text.replace(
        "/assets/images/pharmaglobaleng-homepage.jpg",
        "/assets/images/pharmaglobaleng-homepage.webp",
    )
    text = text.replace("/images/logo.png", "/assets/images/about-pge-logo.svg")
    text = text.replace(OLD_HOMEPAGE_DESCRIPTION, HOMEPAGE_DESCRIPTION)
    heading = "Pharmaceutical Tablet Tooling, Replacement Parts &amp; Surface Engineering"
    actual_marker = '<main id="home">\n'
    actual_h1 = f'  <h1 class="sr-only">{heading}</h1>\n'
    if actual_marker in text and actual_h1 not in text:
        text = text.replace(actual_marker, actual_marker + actual_h1, 1)
    flight_marker = '\\u003cmain id=\\"home\\">\\n'
    flight_h1 = f'  \\u003ch1 class=\\"sr-only\\">{heading}\\u003c/h1>\\n'
    if flight_marker in text and flight_h1 not in text:
        text = text.replace(flight_marker, flight_marker + flight_h1, 1)
    text, _ = add_organization_logo(text)
    if text != original:
        path.write_text(text, encoding="utf-8")
        return 1
    return 0


def main() -> int:
    changed = fix_homepage()
    for rel, description in NOINDEX_DESCRIPTIONS.items():
        path = ROOT / rel
        source = path.read_text(encoding="utf-8")
        rewritten = set_description(source, description)
        rewritten, _ = add_organization_logo(rewritten)
        if rewritten != source:
            path.write_text(rewritten, encoding="utf-8")
            changed += 1

    for path in sorted(ROOT.rglob("*.html")):
        if ".git" in path.parts or "next-app" in path.parts:
            continue
        source = path.read_text(encoding="utf-8")
        rewritten, _ = add_organization_logo(source)
        if rewritten != source:
            path.write_text(rewritten, encoding="utf-8")
            changed += 1

    layout = ROOT / "next-app/app/layout.js"
    source = layout.read_text(encoding="utf-8")
    rewritten = source.replace(
        "/assets/images/pharmaglobaleng-homepage.jpg",
        "/assets/images/pharmaglobaleng-homepage.webp",
    )
    rewritten = rewritten.replace(OLD_HOMEPAGE_DESCRIPTION, HOMEPAGE_DESCRIPTION)
    if rewritten != source:
        layout.write_text(rewritten, encoding="utf-8")
        changed += 1

    print(json.dumps({"changed_files": changed}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
