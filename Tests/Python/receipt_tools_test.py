import unittest
from PyLib.receipt_tools import get_purchase_date, get_item_list, get_entity_id

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

if __name__ == '__main__':
    unittest.main()
