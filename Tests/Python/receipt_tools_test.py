import unittest
from PyLib.receipt_tools import get_purchase_date, get_item_list, get_entity_id, get_store_address, get_purchase_total

class TestPurchaseFunctions(unittest.TestCase):
    #date
    def test_get_purchase_date_valid(self):
        self.assertEqual(get_purchase_date({'date': '01-09-2024'}), '01-09-2024')
        self.assertEqual(get_purchase_date({'date': '01/09/2024'}), '01/09/2024')

    def test_get_purchase_date_missing(self):
        with self.assertRaises(ValueError):
            get_purchase_date({})

    def test_get_purchase_date_empty(self):
        with self.assertRaises(ValueError):
            get_purchase_date({'date': ''})
            get_purchase_date({'date': '   '})

    #item list
    def test_get_item_list_valid(self):
        self.assertEqual(get_item_list({'line_items': 'item1, item2'}), 'item1, item2')

    def test_get_item_list_missing(self):
        with self.assertRaises(ValueError):
            get_item_list({})

    def test_get_item_list_empty(self):
        with self.assertRaises(ValueError):
            get_item_list({'line_items': ''})
            get_item_list({'line_items': '   '})

    #entity id
    def test_get_entity_id_valid(self):
        self.assertEqual(get_entity_id({'entity_id': '30590360763'}), '30590360763')
        self.assertEqual(get_entity_id({'entity_id': '30-50673003-8'}), '30-50673003-8')

    def test_get_entity_id_missing(self):
        with self.assertRaises(ValueError):
            get_entity_id({})

    def test_get_entity_id_empty(self):
        with self.assertRaises(ValueError):
            get_entity_id({'entity_id': ''})
            get_entity_id({'entity_id': '   '})

    #entity id
    def test_get_store_address_valid(self):
        self.assertEqual(get_store_address({'store_addr': 'Italia 500 - Pto. Madryn Provincia de Chubut'}), 'Italia 500 - Pto. Madryn Provincia de Chubut')
        self.assertEqual(get_store_address({'store_addr': 'Dr. Manuel Belgrano 372 Puerto Madryn Chubut'}), 'Dr. Manuel Belgrano 372 Puerto Madryn Chubut')

    def test_get_store_address_missing(self):
        with self.assertRaises(ValueError):
            get_store_address({})

    def test_get_store_address_empty(self):
        with self.assertRaises(ValueError):
            get_store_address({'store_addr': ''})
            get_store_address({'store_addr': '   '})

    #total
    def test_get_purchase_total_valid(self):
        self.assertEqual(get_purchase_total({'total': '18.401,37'}), '18.401,37')
        self.assertEqual(get_purchase_total({'total': '$6725.60'}), '$6725.60')

    def test_get_purchase_total_missing(self):
        with self.assertRaises(ValueError):
            get_purchase_total({})

    def test_get_purchase_total_empty(self):
        with self.assertRaises(ValueError):
            get_purchase_total({'total': ''})
            get_purchase_total({'total': '   '})

if __name__ == '__main__':
    unittest.main()
