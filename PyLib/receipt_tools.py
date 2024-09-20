import re
from datetime import datetime, time
from dateutil import parser, tz
from typing import List

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

def get_list_field_value(field: str, json_data: dict) -> List[dict]:
    value = get_valid_field_value(json_data, field)
    if not isinstance(value, list):
        raise TypeError(f"The value for '{field}' field is not a list.")
    return value

def normalize_date(date_str: str, day_first: bool, year_first: bool, timezone=tz.tzlocal()) -> datetime:
    date_str = date_str.strip()
    try:
        dt = parser.parse(date_str, dayfirst=day_first, yearfirst=year_first)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone)
        return dt
    except ValueError:
        raise ValueError("Invalid date format")
    
def normalize_quantity(quantity_string: str) -> float:
    match = re.search(r'([0-9]*[.,]?[0-9]+)', quantity_string)
    if not match:
        raise ValueError("Invalid number format")
    numeric_part = match.group(1)
    normalized_string = numeric_part.replace(',', '.').strip()
    try:
        return float(normalized_string)
    except ValueError:
        raise ValueError("Invalid number format")
    
def normalize_value(value_string: str) -> float:
    value_string = re.sub(r'[^\d,.-]', '', value_string).strip() # keep numbers, commas and dots
    if not value_string:
        raise ValueError(f"Invalid value format")

    if len(value_string) > 2:
        third_to_last = value_string[-3]
        if third_to_last.isdigit():
            value_string = value_string.replace(',', '').replace('.', '')
        elif third_to_last == '.':
            value_string = value_string.replace(',', '')
        elif third_to_last == ',':
            value_string = value_string.replace('.', '').replace(',', '.')

    try:
        return abs(float(value_string))
    except ValueError:
        raise ValueError(f"Invalid value format")
    
def normalize_time(time_string: str) -> time:
    normalized_time = re.sub(r'[^0-9]', ':', time_string.strip())
    if not normalized_time:
        raise ValueError("Invalid time format")
    time_parts = normalized_time.split(':')
    try:
        hours = int(time_parts[0])
        minutes = int(time_parts[1]) if len(time_parts) > 1 else 0
        seconds = int(time_parts[2]) if len(time_parts) > 2 else 0
        return time(hours, minutes, seconds)
    except ValueError:
        raise ValueError("Invalid time format")
    
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

def get_purchase_date(json_data: dict) -> datetime:
    default_timezone = tz.gettz('America/Argentina/Buenos_Aires') # TODO: provide timezone
    date = normalize_date(get_string_field_value("date", json_data), True, False, default_timezone)
    time_part = normalize_time(get_string_field_value("time", json_data))
    combined_datetime = datetime.combine(date.date(), time_part, tzinfo=date.tzinfo)
    utc_datetime = combined_datetime.astimezone(tz.UTC)
    return utc_datetime
