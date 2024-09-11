import re
from datetime import datetime
from dateutil import parser
from pydantic import BaseModel, Field
from typing import List, Optional

class PurchaseItem(BaseModel):
    key: Optional[str]
    text: Optional[str]
    quantity: Optional[float]
    price: Optional[float]

class Purchase(BaseModel):
    entity_id: Optional[int]
    store_name: Optional[str]
    store_address: Optional[str]
    date: Optional[datetime]
    subtotal: Optional[float]
    total: Optional[float]
    items: List[PurchaseItem] = Field(default_factory=list)

def get_field_value(json_data: dict, field: str):
    if field not in json_data:
        raise ValueError(f"The '{field}' field is missing.")
    return json_data[field]

def check_if_empty(value) -> bool:
    return value is None or (isinstance(value, str) and not value.strip()) or (isinstance(value, list) and not value)

def get_valid_field_value(json_data: dict, field: str):
    value = get_field_value(json_data, field)
    if check_if_empty(value):
        raise ValueError(f"The value for '{field}' field is empty.")
    return value

def get_string_field_value(field: str, json_data: dict) -> str:
    value = get_valid_field_value(json_data, field)
    if not isinstance(value, str):
        raise TypeError(f"The value for '{field}' field is not a string.")
    return value

def get_list_field_value(field: str, json_data: dict) -> list:
    value = get_valid_field_value(json_data, field)
    if not isinstance(value, list):
        raise TypeError(f"The value for '{field}' field is not a list.")
    return value

def normalize_date(date_str: str, day_first: bool, year_first: bool) -> datetime:
    date_str = date_str.strip()
    try:
        return parser.parse(date_str, dayfirst=day_first, yearfirst=year_first)
    except ValueError:
        raise ValueError("Invalid date format")
    
def normalize_quantity(amount_string: str) -> float:
    match = re.search(r'([0-9]*[.,]?[0-9]+)', amount_string)
    if not match:
        raise ValueError("Invalid number format")
    numeric_part = match.group(1)
    normalized_string = numeric_part.replace(',', '.').strip()
    try:
        return float(normalized_string)
    except ValueError:
        raise ValueError("Invalid number format")
    
def normalize_entity_id(entity_id_string: str) -> int:
    match = re.search(r'[0-9-]+', entity_id_string)
    if not match:
        raise ValueError("Invalid identification format")
    numeric_part = match.group(0).replace('-', '').strip()
    if not validate_cuit(numeric_part):
        raise ValueError("Invalid cuit format")
    
    try:
        return int(numeric_part)
    except ValueError:
        raise ValueError("Invalid number format")
    
def validate_cuit(cuit: str) -> bool:
    if len(cuit) != 11 or cuit[:2] not in ['30', '33', '34']:
        return False
    
    base_digits = cuit[:-1]
    actual_check_digit = int(cuit[-1])

    # Calculate the check digit
    weights = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    sum_product = sum(int(digit) * weight for digit, weight in zip(base_digits, weights))
    calculated_check_digit = 11 - (sum_product % 11)
    
    if calculated_check_digit == 11:
        calculated_check_digit = 0
    elif calculated_check_digit == 10:
        return False

    if actual_check_digit != calculated_check_digit:
        return False
    
    return True
    
def normalize_product_key(product_key_string: str) -> int:
    product_key_string = product_key_string.strip()
    if not product_key_string:
        raise ValueError("Product key was empty")
    if product_key_string.isdigit() and len(product_key_string) == 12:
        return f"{product_key_string}{calculate_ean13_check_digit(product_key_string)}"
    return product_key_string

def calculate_ean13_check_digit(ean_code: str) -> int:
    if len(ean_code) != 12 or not ean_code.isdigit():
        raise ValueError("EAN code must be 12 digits long without the check digit")

    odd_sum = sum(int(ean_code[i]) for i in range(0, 12, 2))
    even_sum = sum(int(ean_code[i]) for i in range(1, 12, 2))
    
    total_sum = odd_sum + (even_sum * 3)
    
    check_digit = (10 - (total_sum % 10)) % 10
    
    return check_digit

def validate_cuit(cuit: str) -> bool:
    if len(cuit) != 11 or cuit[:2] not in ['30', '33', '34']:
        return False
    
    base_digits = cuit[:-1]
    actual_check_digit = int(cuit[-1])

    # Calculate the check digit
    weights = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    sum_product = sum(int(digit) * weight for digit, weight in zip(base_digits, weights))
    calculated_check_digit = 11 - (sum_product % 11)
    
    if calculated_check_digit == 11:
        calculated_check_digit = 0
    elif calculated_check_digit == 10:
        return False

    if actual_check_digit != calculated_check_digit:
        return False
    
    return True

def get_purchase(json_data: dict) -> Purchase:
    entity_id = normalize_entity_id(get_string_field_value("entity_id", json_data))
    store_name = get_string_field_value("store_name", json_data)
    store_address = get_string_field_value("store_name", json_data)
    date = normalize_date(get_string_field_value("date", json_data), True, False)
    purchase = Purchase(
        entity_id = entity_id,
        store_name = store_name,
        store_address = store_address,
        date = date,
        subtotal=None,
        total=None,
    )
    return purchase
    
if __name__ == '__main__':
    purchase = get_purchase({
        "store_name": "La Anonima Sucursal 45",
        "store_addr": "Italia 500 - Puerto Madryn Provincia de Chubut",
        "entity_id": "30-50673003-8",
        "phone": "",
        "date": "11-08-24",
        "time": "10:04",
        "subtotal": "$6725.60",
        "svc": "",
        "tax": "",
        "total": "$6725.60",
        "tips": "",
        "discount": "",
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
    }
    )
    print(purchase.entity_id)
    print(purchase.store_name)
    print(purchase.store_address)
    print(purchase.date)