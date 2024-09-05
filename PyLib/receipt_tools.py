def get_purchase_date(json_data: dict) -> str:
    if 'date' not in json_data:
        raise ValueError("The 'date' field is missing.")
    if not json_data['date']:
        raise ValueError("The 'date' field is empty.")
    if isinstance(json_data['date'], str) and not json_data['date'].strip():
        raise ValueError("The 'date' field is empty.")
    return json_data["date"]

def get_entity_id(json_data: dict) -> str:
    if 'entity_id' not in json_data:
        raise ValueError("The 'entity_id' field is missing.")
    if not json_data['entity_id']:
        raise ValueError("The 'entity_id' field is empty.")
    if isinstance(json_data['entity_id'], str) and not json_data['entity_id'].strip():
        raise ValueError("The 'entity_id' field is empty.")
    return json_data["entity_id"]

def get_item_list(json_data: dict) -> str:
    if 'line_items' not in json_data:
        raise ValueError("The 'line_items' field is missing.")
    if not json_data['line_items']:
        raise ValueError("The 'line_items' field is empty.")
    if isinstance(json_data['line_items'], str) and not json_data['line_items'].strip():
        raise ValueError("The 'line_items' field is empty.")
    return json_data["line_items"]