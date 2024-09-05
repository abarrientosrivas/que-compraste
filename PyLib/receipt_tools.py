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