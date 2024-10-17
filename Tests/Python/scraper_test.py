from PyLib.scrapers.barcode_lookup_products import BarcodeLookupProducts
import time
import unittest

class TestScraperFunctions(unittest.TestCase):

    def setUp(self):
        self.scraper = BarcodeLookupProducts()

    def test_all_in_sequence(self):
        self._test_scraper_valid()
        self._test_scraper_invalid()
        self._test_scraper_empty()
        self._test_scraper_null()

    def _test_scraper_valid(self):
        result = self.scraper.get_product("7790790120325")
        self.assertEqual(result['product_name'], "Inca Garbanzos")
        self.assertEqual(result['product_description'], "Inca garbanzos. Country of origin: Spain.")
        self.assertEqual(result['product_category'], "Food, Beverages & Tobacco")
        time.sleep(11)

    def _test_scraper_invalid(self):
        result = self.scraper.get_product("pepe")
        self.assertEqual(result['product_name'], None)
        self.assertEqual(result['product_description'], None)
        self.assertEqual(result['product_category'], None)
        time.sleep(12)

        result = self.scraper.get_product("7798518709616")
        self.assertEqual(result['product_name'], None)
        self.assertEqual(result['product_description'], None)
        self.assertEqual(result['product_category'], None)

    def _test_scraper_empty(self):
        result = self.scraper.get_product("")
        self.assertEqual(result['product_name'], None)
        self.assertEqual(result['product_description'], None)
        self.assertEqual(result['product_category'], None)

    def _test_scraper_null(self):
        result = self.scraper.get_product(None)
        self.assertEqual(result['product_name'], None)
        self.assertEqual(result['product_description'], None)
        self.assertEqual(result['product_category'], None)
            
if __name__ == '__main__':
    unittest.main()