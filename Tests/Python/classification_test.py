from PyLib import product_classification
from API.schemas import Product
from datetime import datetime
from dateutil import tz
import unittest

class TestPurchaseFunctions(unittest.TestCase):
    def test_product_description_valid(self):
        self.assertEqual(product_classification.describe_product(
            Product(
                id=0,
                title="Seagate Expansion 2TB USB 3.0 Portable External Hard Drive (STKM2000400) - Black ",
                description="Need some extra storage space? This Seagate Expansion portable external hard drive provides an incredible 2TB of storage capacity so you have plenty of room to save and consolidate your important documents, photos, videos, and more. It features a compact design so it's easy to take with you wherever you go. | Seagate Expansion 2TB USB 3.0 Portable External Hard Drive (STKM2000400) - Black. ",
                read_category="Electronics Accessories > Computer Components > Storage Devices > Hard Drives",
                created_at=datetime.now(tz.UTC)
            )
        ), "Electronics Accessories > Computer Components > Storage Devices > Hard Drives")
        self.assertEqual(product_classification.describe_product(
            Product(
                id=0,
                title="Seagate Expansion 2TB USB 3.0 Portable External Hard Drive (STKM2000400) - Black ",
                description="Need some extra storage space? This Seagate Expansion portable external hard drive provides an incredible 2TB of storage capacity so you have plenty of room to save and consolidate your important documents, photos, videos, and more. It features a compact design so it's easy to take with you wherever you go. | Seagate Expansion 2TB USB 3.0 Portable External Hard Drive (STKM2000400) - Black. ",
                created_at=datetime.now(tz.UTC)
            )
        ), 'seagate expansion portable external hard drive provides')
        self.assertEqual(product_classification.describe_product(
            Product(
                id=0,
                title="Seagate Expansion 2TB USB 3.0 Portable External Hard Drive (STKM2000400) - Black ",
                created_at=datetime.now(tz.UTC)
            )
        ), 'seagate expansion 2tb usb 3')

    def test_product_description_empty(self):
        self.assertEqual(product_classification.describe_product(
            Product(
                id=0,
                title="",
                description="",
                created_at=datetime.now(tz.UTC)
            )
        ), None)
            
if __name__ == '__main__':
    unittest.main()