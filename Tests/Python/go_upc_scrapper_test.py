from PyLib.scrapers import GoUpcProductScrapper
import time
import unittest

class TestScraperFunctions(unittest.TestCase):

    def setUp(self):
        self.scraper = GoUpcProductScrapper()

    def test_all_in_sequence(self):
        self._test_scraper_valid()
        self._test_scraper_invalid()
        self._test_scraper_empty()
        self._test_scraper_null()

    def _test_scraper_valid(self):
        result = self.scraper.get_product("7796885059013")
        self.assertEqual(result['product_name'], "BGH Termotanque Eléctrico 40 Litros Bte-040ec15md")
        self.assertEqual(result['product_description'], "La confianza, seguridad y ahorro que su hogar necesita. Los termotanques eléctricos BGH brindan un adecuado servicio de agua caliente, son de fácil.")
        self.assertEqual(result['product_category'], None)
        self.assertEqual(result['product_images'], ["https://go-upc.s3.amazonaws.com/images/59209162.jpeg"])
        time.sleep(11)
        result = self.scraper.get_product("7792200000128")
        self.assertEqual(result['product_name'], "9 de Oro Bizcochos Agridulces 200 G")
        self.assertEqual(result['product_description'], "Encontrá increíbles ofertas y descuentos en Supermercados DIA. Comprá en nuestra tienda online productos de Almacén, Bebidas, Perfumería, Limpieza y mucho más.")
        self.assertEqual(result['product_category'], "Taco Shells & Tostadas")
        self.assertEqual(result['product_images'], ["https://go-upc.s3.amazonaws.com/images/37292219.png"])
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