import unittest
from datetime import datetime
from PyLib.receipt_tools import get_purchase_date, get_item_list, get_entity_id, get_store_address, get_purchase_total, get_item_code, get_item_quantity, get_item_value, get_item_text, normalize_date, normalize_quantity, normalize_entity_id, normalize_product_key

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
            get_purchase_date({'date': None})

    def test_get_purchase_date_type_mismatch(self):
        with self.assertRaises(TypeError):
            get_purchase_date({'date': 1})
            get_purchase_date({'date': True})

    #item list
    def test_get_item_list_valid(self):
        self.assertEqual(
            get_item_list({
                "line_items": [
                    {
                        "item_key": "75010517538",
                        "item_name": "BRIQUETA CAR",
                        "item_value": "$3250,00",
                        "item_quantity": "1"
                    },
                    {
                        "item_key": "203708700000",
                        "item_name": "PAPA",
                        "item_value": "$945.00",
                        "item_quantity": "0.756"
                    },
                    {
                        "item_key": "206848200000",
                        "item_name": "CHORIZO PARR",
                        "item_value": "$5900.00",
                        "item_quantity": "0.468"
                    }
                ]
            }),
            [
                {
                    "item_key": "75010517538",
                    "item_name": "BRIQUETA CAR",
                    "item_value": "$3250,00",
                    "item_quantity": "1"
                },
                {
                    "item_key": "203708700000",
                    "item_name": "PAPA",
                    "item_value": "$945.00",
                    "item_quantity": "0.756"
                },
                {
                    "item_key": "206848200000",
                    "item_name": "CHORIZO PARR",
                    "item_value": "$5900.00",
                    "item_quantity": "0.468"
                }
            ]
        )

        self.assertEqual(
            get_item_list({
                "line_items": [
                    {
                        "item_key": "89087",
                        "item_name": "Flautita (p)",
                        "item_value": "$156,00",
                        "item_quantity": "9"
                    },
                    {
                        "item_key": "779571100361",
                        "item_name": "Ravioles VILLA D'AGRI con Pollo y Espina",
                        "item_value": "$400,00",
                        "item_quantity": "2"
                    },
                    {
                        "item_key": "63119",
                        "item_name": "FACTURAS SURTIDAS X UN. VEA",
                        "item_value": "$269,00",
                        "item_quantity": "7"
                    },
                    {
                        "item_key": "762230074293",
                        "item_name": "Rhodesia Toonix x 88 grs",
                        "item_value": "2.300,00",
                        "item_quantity": "1"
                    }
                ]
            }),
            [
                {
                    "item_key": "89087",
                    "item_name": "Flautita (p)",
                    "item_value": "$156,00",
                    "item_quantity": "9"
                },
                {
                    "item_key": "779571100361",
                    "item_name": "Ravioles VILLA D'AGRI con Pollo y Espina",
                    "item_value": "$400,00",
                    "item_quantity": "2"
                },
                {
                    "item_key": "63119",
                    "item_name": "FACTURAS SURTIDAS X UN. VEA",
                    "item_value": "$269,00",
                    "item_quantity": "7"
                },
                {
                    "item_key": "762230074293",
                    "item_name": "Rhodesia Toonix x 88 grs",
                    "item_value": "2.300,00",
                    "item_quantity": "1"
                }
            ]
        )

    def test_get_item_list_missing(self):
        with self.assertRaises(ValueError):
            get_item_list({})

    def test_get_item_list_empty(self):
        with self.assertRaises(ValueError):
            get_item_list({'line_items': ''})
            get_item_list({'line_items': '   '})
            get_item_list({'line_items': []})
            get_item_list({'line_items': None})

    def test_get_item_list_type_mismatch(self):
        with self.assertRaises(TypeError):
            get_item_list({'line_items': 1})
            get_item_list({'line_items': True})

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
            get_entity_id({'entity_id': None})

    def test_get_entity_id_type_mismatch(self):
        with self.assertRaises(TypeError):
            get_entity_id({'entity_id': 1})
            get_entity_id({'entity_id': True})

    #store address
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
            get_store_address({'store_addr': None})

    def test_get_store_address_type_mismatch(self):
        with self.assertRaises(TypeError):
            get_store_address({'store_addr': 1})
            get_store_address({'store_addr': True})

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
            get_purchase_total({'total': None})

    def test_get_purchase_total_type_mismatch(self):
        with self.assertRaises(TypeError):
            get_purchase_total({'total': 1})
            get_purchase_total({'total': True})

    #item code
    def test_get_item_code_valid(self):
        self.assertEqual(get_item_code({"item_key": "75010517538"}), '75010517538')
        self.assertEqual(get_item_code({"item_key": "89087"}), '89087')
        self.assertEqual(get_item_code({"item_key": "779052201196"}), '779052201196')

    def test_get_item_code_missing(self):
        with self.assertRaises(ValueError):
            get_item_code({})

    def test_get_item_code_empty(self):
        with self.assertRaises(ValueError):
            get_item_code({'item_key': ''})
            get_item_code({'item_key': '   '})
            get_item_code({'item_key': None})

    def test_get_item_code_type_mismatch(self):
        with self.assertRaises(TypeError):
            get_item_code({'item_key': 1})
            get_item_code({'item_key': True})

    #item quantity
    def test_get_item_quantity_valid(self):
        self.assertEqual(get_item_quantity({"item_quantity": "1"}), '1')
        self.assertEqual(get_item_quantity({"item_quantity": "9"}), '9')
        self.assertEqual(get_item_quantity({"item_quantity": "0,216"}), '0,216')
        self.assertEqual(get_item_quantity({"item_quantity": "0.756"}), '0.756')

    def test_get_item_quantity_missing(self):
        with self.assertRaises(ValueError):
            get_item_quantity({})

    def test_get_item_quantity_empty(self):
        with self.assertRaises(ValueError):
            get_item_quantity({'item_quantity': ''})
            get_item_quantity({'item_quantity': '   '})
            get_item_quantity({'item_quantity': None})

    def test_get_item_quantity_type_mismatch(self):
        with self.assertRaises(TypeError):
            get_item_quantity({'item_quantity': 1})
            get_item_quantity({'item_quantity': True})

    #item value
    def test_get_item_value_valid(self):
        self.assertEqual(get_item_value({"item_value": "$945.00"}), '$945.00')
        self.assertEqual(get_item_value({"item_value": "2.098,99"}), '2.098,99')

    def test_get_item_value_missing(self):
        with self.assertRaises(ValueError):
            get_item_value({})

    def test_get_item_value_empty(self):
        with self.assertRaises(ValueError):
            get_item_value({'item_value': ''})
            get_item_value({'item_value': '   '})
            get_item_value({'item_value': None})

    def test_get_item_value_type_mismatch(self):
        with self.assertRaises(TypeError):
            get_item_value({'item_value': 1})
            get_item_value({'item_value': True})

    #item text
    def test_get_item_text_valid(self):
        self.assertEqual(get_item_text({"item_name": "BRIQUETA CAR"}), 'BRIQUETA CAR')
        self.assertEqual(get_item_text({"item_name": "ARVEJAS BEST x300"}), 'ARVEJAS BEST x300')
        self.assertEqual(get_item_text({"item_name": "VIGILANTES DE MANTECA BJA 6 un"}), 'VIGILANTES DE MANTECA BJA 6 un')
        self.assertEqual(get_item_text({"item_name": "Mayonesa HELLMANNS Clasica DP X475G"}), 'Mayonesa HELLMANNS Clasica DP X475G')

    def test_get_item_text_missing(self):
        with self.assertRaises(ValueError):
            get_item_text({})

    def test_get_item_text_empty(self):
        with self.assertRaises(ValueError):
            get_item_text({'item_name': ''})
            get_item_text({'item_name': '   '})
            get_item_text({'item_name': None})

    def test_get_item_text_type_mismatch(self):
        with self.assertRaises(TypeError):
            get_item_text({'item_name': 1})
            get_item_text({'item_name': True})

    #date validation
    def test_normalize_date_valid(self):
        self.assertEqual(normalize_date(" 6/7/24", True, False), datetime(2024, 7, 6))
        self.assertEqual(normalize_date("6. 8.24", True, False), datetime(2024, 8, 6))
        self.assertEqual(normalize_date("4-8-24;", True, False), datetime(2024, 8, 4))

    def test_normalize_date_invalid(self):
        with self.assertRaises(ValueError):
            normalize_date("notadate", True, False)
            normalize_date("24/24/24", True, False)

    #quantity validation
    def test_normalize_quantity_valid(self):
        self.assertEqual(normalize_quantity(" 0,2"), 0.2)
        self.assertEqual(normalize_quantity("0.03"), 0.03)
        self.assertEqual(normalize_quantity("1"), 1.0)
        self.assertEqual(normalize_quantity("2 cant."), 2.0)

    def test_normalize_quantity_invalid(self):
        with self.assertRaises(ValueError):
            normalize_quantity("notanumber")
            normalize_quantity("213-2")

    #entity id validation
    def test_normalize_entity_id_valid(self):
        self.assertEqual(normalize_entity_id("30590360763"), 30590360763)
        self.assertEqual(normalize_entity_id("30-50673003-8"), 30506730038)
        self.assertEqual(normalize_entity_id("30-68731043-4"), 30687310434)
        self.assertEqual(normalize_entity_id("30641844140"), 30641844140)

    def test_normalize_entity_id_invalid(self):
        with self.assertRaises(ValueError):
            normalize_entity_id("notacuit")
            normalize_entity_id("213-2")
            normalize_entity_id("30-50673003-7")
            normalize_entity_id("20-34823021-4")

    #product key validation
    def test_normalize_product_key_valid(self):
        self.assertEqual(normalize_product_key("779058013924"), "7790580139247")
        self.assertEqual(normalize_product_key("7790310922316"), "7790310922316")
        self.assertEqual(normalize_product_key("98169"), "98169")
        self.assertEqual(normalize_product_key("203708700000"), "2037087000003")

    def test_normalize_product_key_invalid(self):
        with self.assertRaises(ValueError):
            normalize_product_key("")
            normalize_product_key(None)


if __name__ == '__main__':
    unittest.main()
