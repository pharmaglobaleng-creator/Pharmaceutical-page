"""Repair generated Fette guidance without regenerating product pages.

The historical generator input covers only 200 of the 769 current products.
Read the existing component details and change only the function paragraph and
its verification list. Abort before any writes if an existing block is not
recognized generated copy.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from html import escape, unescape
from pathlib import Path

from build_fette_pages import ROOT, application_guidance

FUNCTION = re.compile(r"(?P<before><h2>What does this part do\?</h2><p>)(?P<body>[^<]*)(?P<after></p>)")
CHECKS = re.compile(r"(?P<before><h2>Part-specific verification checkpoints</h2><ul>)(?P<body>(?:<li>[^<]*</li>)+)(?P<after></ul>)")


def component_details(text: str) -> dict[str, str]:
    result = {}
    for key, label in (("part_name", "Part name"), ("category", "Part category")):
        values = re.findall(r"<dt>" + label + r"</dt><dd>([^<]+)</dd>", text)
        if len(values) != 1:
            raise ValueError(f"Expected one {label} field; found {len(values)}")
        result[key] = unescape(values[0])
    return result


def rendered_guidance(part: dict[str, str]) -> tuple[str, str]:
    function, _, checks = application_guidance(part)
    return escape(function), "".join(f"<li>{escape(check)}</li>" for check in checks)


def generated_legacy_pairs(part: dict[str, str]) -> set[tuple[str, str]]:
    # These unambiguous names reproduce the historical eight generic pairs and
    # the reviewed felt pair. No arbitrary edited copy is accepted.
    result = {
        rendered_guidance({"part_name": name, "category": ""})
        for name in ("Cam", "Turret", "Seal", "Felt", "Bearing", "Belt", "Plate", "Hopper", "Shaft")
    }
    function = (
        f"The {part['part_name']} is cataloged in the {part['category']} group "
        "for the referenced Fette tablet-press application."
    )
    checks = ("Critical dimensions and component geometry", "Mounting method and installed orientation", "Mating components and operating clearance")
    result.add((escape(function), "".join(f"<li>{escape(check)}</li>" for check in checks)))
    return result


def content_blocks(text: str) -> tuple[str, str]:
    values = []
    for pattern in (FUNCTION, CHECKS):
        matches = list(pattern.finditer(text))
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one generated guidance block; found {len(matches)}")
        values.append(matches[0]["body"])
    return tuple(values)


def outside_guidance(text: str) -> str:
    for pattern in (FUNCTION, CHECKS):
        text = pattern.sub(lambda m: m["before"] + "__GUIDANCE__" + m["after"], text)
    return text


def repair_page(text: str) -> str:
    part = component_details(text)
    current = content_blocks(text)
    expected = rendered_guidance(part)
    if current == expected:
        return text
    if current not in generated_legacy_pairs(part):
        raise ValueError("Unrecognized or edited function/checkpoint copy; manual review required")
    result = text
    for pattern, replacement in zip((FUNCTION, CHECKS), expected):
        result = pattern.sub(lambda m: m["before"] + replacement + m["after"], result)
    if outside_guidance(text) != outside_guidance(result):
        raise ValueError("Content outside the authorized guidance blocks changed")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write reviewed, recognized block replacements")
    parser.add_argument("--check", action="store_true", help="Fail if guidance still needs repair")
    args = parser.parse_args()
    changes = []
    families = Counter()
    paths = sorted((ROOT / "parts").glob("pge-fet-*/index.html"))
    # Complete the preflight for every page before any write.
    for path in paths:
        before = path.read_text(encoding="utf-8")
        try:
            after = repair_page(before)
        except ValueError as error:
            raise SystemExit(f"{path.relative_to(ROOT)}: {error}") from error
        if before != after:
            changes.append((path, after))
            families[component_details(before)["category"]] += 1
    if args.apply:
        for path, text in changes:
            path.write_text(text, encoding="utf-8")
    print(json.dumps({"pages_checked": len(paths), "pages_changed" if args.apply else "pages_needing_repair": len(changes), "affected_catalog_families": dict(families), "paths": [str(path.relative_to(ROOT)) for path, _ in changes]}, indent=2))
    return int(args.check and bool(changes))


if __name__ == "__main__":
    raise SystemExit(main())
