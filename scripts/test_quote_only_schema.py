import unittest

from catalog_page_schema import catalog_page_entity
from migrate_quote_only_product_schema import migrate_data


URL = "https://pharmaglobaleng.com/parts/pge-test-001/"


class CatalogPageSchemaTests(unittest.TestCase):
    def test_catalog_page_preserves_pge_and_verified_identifiers(self):
        page = catalog_page_entity(
            url=URL,
            name="Test component",
            description="Test catalog record.",
            sku="PGE-TEST-001",
            image="https://pharmaglobaleng.com/assets/images/test.webp",
            aliases=["Test component", "PGE-TEST-001"],
            identifiers={
                "@type": "PropertyValue",
                "propertyID": "OEM cross-reference",
                "value": "VERIFIED-123",
            },
        )
        self.assertEqual(page["@type"], "WebPage")
        self.assertEqual(page["mainEntity"]["@type"], "Thing")
        values = {item["value"] for item in page["mainEntity"]["identifier"]}
        self.assertEqual(values, {"PGE-TEST-001", "VERIFIED-123"})
        self.assertNotIn("Product", repr(page))

    def test_migration_replaces_product_and_preserves_other_graph_nodes(self):
        source = {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "Product",
                    "@id": URL + "#product",
                    "url": URL,
                    "name": "Test component",
                    "description": "Test catalog record.",
                    "sku": "PGE-TEST-001",
                },
                {"@type": "BreadcrumbList", "itemListElement": []},
            ],
        }
        migrated, count = migrate_data(source)
        self.assertEqual(count, 1)
        types = [node.get("@type") for node in migrated["@graph"]]
        self.assertEqual(types, ["WebPage", "BreadcrumbList"])

    def test_existing_reviewed_webpage_is_merged_once(self):
        source = {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "WebPage",
                    "@id": URL + "#webpage",
                    "url": URL,
                    "name": "Reviewed page name",
                    "breadcrumb": {"@id": URL + "#breadcrumb"},
                    "mainEntity": {"@id": URL + "#product"},
                },
                {
                    "@type": "Product",
                    "@id": URL + "#product",
                    "url": URL,
                    "name": "Catalog subject",
                    "description": "Reviewed description.",
                    "sku": "PGE-TEST-001",
                },
            ],
        }
        migrated, count = migrate_data(source)
        self.assertEqual(count, 1)
        pages = [node for node in migrated["@graph"] if node.get("@type") == "WebPage"]
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]["name"], "Reviewed page name")
        self.assertEqual(pages[0]["mainEntity"]["@type"], "Thing")
        self.assertEqual(pages[0]["breadcrumb"], {"@id": URL + "#breadcrumb"})


if __name__ == "__main__":
    unittest.main()
