import re
from datetime import datetime
from dateutil import parser

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

def get_string_field_value(json_data: dict, field: str) -> str:
    value = get_valid_field_value(json_data, field)
    if not isinstance(value, str):
        raise TypeError(f"The value for '{field}' field is not a string.")
    return value

def get_list_field_value(json_data: dict, field: str) -> list:
    value = get_valid_field_value(json_data, field)
    if not isinstance(value, list):
        raise TypeError(f"The value for '{field}' field is not a list.")
    return value

def get_purchase_date(json_data: dict) -> str:
    return get_string_field_value(json_data, "date")

def get_purchase_total(json_data: dict) -> str:
    return get_string_field_value(json_data, "total")

def get_entity_id(json_data: dict) -> str:
    return get_string_field_value(json_data, "entity_id")

def get_store_address(json_data: dict) -> str:
    return get_string_field_value(json_data, "store_addr")

def get_item_list(json_data: dict) -> list:
    return get_list_field_value(json_data, "line_items")

def get_item_code(json_data: dict) -> str:
    return get_string_field_value(json_data, "item_key")

def get_item_quantity(json_data: dict) -> str:
    return get_string_field_value(json_data, "item_quantity")

def get_item_value(json_data: dict) -> str:
    return get_string_field_value(json_data, "item_value")

def get_item_text(json_data: dict) -> str:
    return get_string_field_value(json_data, "item_name")

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
    
if __name__ == '__main__':
    pass