# Editorial product landing pages

A product page with `data-pge-content="editorial"` on its HTML element maintains its reviewed copy, metadata, and JSON-LD directly. The automatic normalization and copy-polishing steps preserve this content instead of replacing it with generic catalog copy.

These pages are still included in the normal quality audit, metadata validation, and unique-title checks. The marker does not skip checks for missing or invalid schema, canonical URLs, indexability, duplicate titles, or reviewed OEM numbers.

The channel restrictor plate uses the existing `/parts/pge-cre-001/` address and supplier SKU PGE-CRE-001. Its OEM number is unconfirmed and is not published as an MPN. The approved 500-word content uses the user's photograph, connects back to the Creamer catalog, and retains the site's analytics and quote cart.

The separate linear guide plate uses `/parts/pge-cre-002/` and supplier SKU PGE-CRE-002. Its 500-word page preserves the supplied photograph and includes CVC 1220 fit-review questions without claiming universal interchangeability or an unverified OEM number. It is the third card in the Creamer catalog. Catalog counts are synchronized in the static HTML and the Next.js navigation data; the product is listed in the general, Creamer, and image sitemaps.
