"""Regression checks for verification files in the header automation."""
import tempfile
import unittest
from pathlib import Path
from apply_sitewide_header import public_pages, transform_html


class PageSelectionTests(unittest.TestCase):
    def test_verification_file_is_not_a_landing_page(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            name = 'google0123456789abcdef.html'
            (root / name).write_text(f'google-site-verification: {name}\n')
            page = root / 'index.html'
            page.write_text('<html><head><title>Guide</title></head><body><main>Keep this</main></body></html>')
            pages, excluded = public_pages(root)
            self.assertEqual(pages, [page])
            self.assertEqual(excluded, [name])
            result = transform_html(page.read_text())
            self.assertIn('<main>Keep this</main>', result)
            self.assertEqual(transform_html(result), result)

    def test_google_named_content_is_not_silently_excluded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            page = root / 'google0123456789abcdef.html'
            page.write_text('<html><head></head><body><main>A real page</main></body></html>')
            pages, excluded = public_pages(root)
            self.assertEqual(pages, [page])
            self.assertEqual(excluded, [])


if __name__ == '__main__':
    unittest.main()
