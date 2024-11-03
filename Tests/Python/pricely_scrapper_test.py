from PyLib.scrapers import PricelyProductScrapper
import time
import unittest

class TestScraperFunctions(unittest.TestCase):

    def setUp(self):
        self.scraper = PricelyProductScrapper()

    def test_all_in_sequence(self):
        self._test_scraper_valid()
        self._test_scraper_invalid()
        self._test_scraper_empty()
        self._test_scraper_null()

    def _test_scraper_valid(self):
        result = self.scraper.get_product("7790790120325")
        self.assertEqual(result['product_name'], "Garbanzos Secos Remojados Inca Lat 350 Grm")
        self.assertEqual(result['product_description'], "Los garbanzos secos remojados de la marca Inca vienen listos para consumir, ofreciendo un sabor suave y una textura firme que los convierten en una excelente opción para agregar a tus platos preferidos. Son ideales para preparar guisos, ensaladas o platos vegetarianos, y se encuentran en un práctico envase de 350 gramos.")
        self.assertEqual(result['product_category'], "almacén, conservas, conservas de vegetales, legumbres al natural, enlatados y conservas, conservas de legumbres y vegetales, conservas vegetal, garbanzos, conservas de verdura y legumbres, almacen, conservas lata_brick_fco, conservas y enlatados")
        time.sleep(11)
        result = self.scraper.get_product("7790310985465")
        self.assertEqual(result['product_name'], "Papas Fritas Clásicas Lays 134g")
        self.assertEqual(result['product_description'], "Las Papas Fritas Clásicas Lays de 134g son un snack popular entre los argentinos, ideal para disfrutar en reuniones o como acompañamiento de comidas. Estas papas fritas crujientes y llenas de sabor son perfectas para satisfacer antojos y disfrutar de un momento de picada.")
        self.assertEqual(result['product_category'], "almacén, snacks, picadas, papas fritas, snacks y copetín, productos copetin, papas fritas y snacks de maíz, snack, papas fritas y nachos, snacks salados")
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