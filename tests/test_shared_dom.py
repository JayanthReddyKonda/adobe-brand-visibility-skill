import unittest

from dom import UnifiedDOMParser


class TestDOM(unittest.TestCase):
    def test_dom_parsing(self):
        html = "<html><head><title>Test Title</title></head><body><h1>Heading 1</h1><p>Visible paragraph text here.</p><script>var x = 1;</script></body></html>"
        parser = UnifiedDOMParser()
        parser.feed(html)

        self.assertEqual(parser.title, "Test Title")
        self.assertEqual(len(parser.headings), 1)
        self.assertEqual(parser.headings[0]["text"], "Heading 1")
        self.assertTrue(parser.get_visible_words_count() > 0)


if __name__ == "__main__":
    unittest.main()
