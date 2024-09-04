import argparse
import json

def get_purchase_date(json_data: dict) -> str:
    if 'date' not in json_data:
        raise ValueError("The 'date' field is missing.")
    if isinstance(json_data['date'], str) and not json_data['date'].strip():
        raise ValueError("The 'date' field is empty.")
    if not json_data['date']:
        raise ValueError("The 'date' field is empty.")
    return json_data["date"]

def get_item_list(json_data: dict) -> str:
    if 'line_items' not in json_data:
        raise ValueError("The 'line_items' field is missing.")
    if isinstance(json_data['line_items'], str) and not json_data['line_items'].strip():
        raise ValueError("The 'line_items' field is empty.")
    if not json_data['line_items']:
        raise ValueError("The 'line_items' field is empty.")
    return json_data["line_items"]

# move as test
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('json_path', type=str)
    args = parser.parse_args()
    with open(args.json_path, 'r') as file:
        json_content = json.load(file)
    print("date:")
    print(get_purchase_date(json_content))
    print("line items:")
    print(get_item_list(json_content))