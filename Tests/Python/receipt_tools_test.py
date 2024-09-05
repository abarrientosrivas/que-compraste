import unittest
from PyLib.receipt_tools import get_purchase_date, get_item_list

class TestPurchaseFunctions(unittest.TestCase):
    def test_get_purchase_date_valid(self):
        # Testing valid date extraction
        self.assertEqual(get_purchase_date({'date': '2023-09-01'}), '2023-09-01')

    def test_get_purchase_date_missing(self):
        # Testing missing date field
        with self.assertRaises(ValueError):
            get_purchase_date({})

    def test_get_purchase_date_empty(self):
        # Testing empty date string
        with self.assertRaises(ValueError):
            get_purchase_date({'date': ''})

    def test_get_item_list_valid(self):
        # Testing valid item list extraction
        self.assertEqual(get_item_list({'line_items': 'item1, item2'}), 'item1, item2')

    def test_get_item_list_missing(self):
        # Testing missing line_items field
        with self.assertRaises(ValueError):
            get_item_list({})

    def test_get_item_list_empty(self):
        # Testing empty line_items string
        with self.assertRaises(ValueError):
            get_item_list({'line_items': ''})

if __name__ == '__main__':
    unittest.main()
