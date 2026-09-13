#!/usr/bin/env python3
"""Structured data for quotation-only replacement-part catalog pages.

These pages do not publish a price, purchasable offer, or customer review.  A
Google Product rich result therefore cannot be completed truthfully.  Describe
the page and its catalog subject without emitting Product markup that would
create an invalid Product-snippet item.
"""

from __future__ import annotations

from typing import Any, Iterable


SITE = "https://pharmaglobaleng.com"
ORG_ID = f"{SITE}/#organization"
WEBSITE_ID = f"{SITE}/#website"


def _values(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _dedupe(values: Iterable[Any]) -> list[Any]:
    result: list[Any] = []
    seen: set[str] = set()
    for value in values:
        marker = repr(value)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(value)
    return result


def catalog_page_entity(
    *,
    url: str,
    name: str,
    description: str,
    sku: str | None = None,
    image: Any = None,
    aliases: Iterable[str] | None = None,
    identifiers: Any = None,
    language: str = "en-US",
) -> dict[str, Any]:
    """Return accurate WebPage + Thing markup for a quote-only catalog record."""

    subject: dict[str, Any] = {
        "@type": "Thing",
        "@id": url + "#catalog-entry",
        "name": name,
        "url": url,
        "description": description,
    }

    clean_aliases = [str(value).strip() for value in aliases or [] if str(value).strip()]
    if clean_aliases:
        subject["alternateName"] = _dedupe(clean_aliases)
    if image:
        subject["image"] = image

    identifier_values: list[Any] = []
    if sku:
        identifier_values.append({
            "@type": "PropertyValue",
            "propertyID": "PharmaGlobalEng SKU",
            "value": sku,
        })
    identifier_values.extend(_values(identifiers))
    identifier_values = _dedupe(identifier_values)
    if identifier_values:
        subject["identifier"] = identifier_values[0] if len(identifier_values) == 1 else identifier_values

    page: dict[str, Any] = {
        "@type": "WebPage",
        "@id": url + "#webpage",
        "url": url,
        "name": name,
        "description": description,
        "inLanguage": language,
        "isPartOf": {"@id": WEBSITE_ID},
        "publisher": {"@id": ORG_ID},
        "mainEntity": subject,
    }
    if image:
        primary = image[0] if isinstance(image, list) and image else image
        page["primaryImageOfPage"] = (
            primary if isinstance(primary, dict) else {"@type": "ImageObject", "url": primary}
        )
    return page


def catalog_page_from_product(product: dict[str, Any]) -> dict[str, Any]:
    """Convert a legacy quote-only Product node without inventing commerce data."""

    url = str(product.get("url") or "").strip()
    if not url:
        node_id = str(product.get("@id") or "")
        url = node_id.split("#", 1)[0]
    return catalog_page_entity(
        url=url,
        name=str(product.get("name") or "Replacement-part catalog record"),
        description=str(product.get("description") or "PharmaGlobalEng replacement-part catalog record."),
        sku=str(product.get("sku") or "").strip() or None,
        image=product.get("image"),
        aliases=_values(product.get("alternateName")),
        identifiers=product.get("identifier"),
    )
