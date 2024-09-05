def get_field_value(json_data: dict, field: str) -> str:
    if field not in json_data:
        raise ValueError(f"The '{field}' field is missing.")
    if not json_data[field]:
        raise ValueError(f"The '{field}' field is empty.")
    if isinstance(json_data[field], str) and not json_data[field].strip():
        raise ValueError(f"The '{field}' field is empty.")
    return json_data[field]

def get_purchase_date(json_data: dict) -> str:
    return get_field_value(json_data, "date")

def get_purchase_total(json_data: dict) -> str:
    return get_field_value(json_data, "total")

def get_entity_id(json_data: dict) -> str:
    return get_field_value(json_data, "entity_id")

def get_store_address(json_data: dict) -> str:
    return get_field_value(json_data, "store_addr")

def get_item_list(json_data: dict) -> str:
    return get_field_value(json_data, "line_items")