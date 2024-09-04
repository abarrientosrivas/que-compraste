import argparse
import json

def get_purchase_date(json_data: dict) -> str:
    if 'date' not in json_data:
        raise ValueError("The 'date' field is missing.")
    if not json_data['date']:
        raise ValueError("The 'date' field is empty.")
    return json_data["date"]

# move as test
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('json_path', type=str)
    args = parser.parse_args()
    with open(args.json_path, 'r') as file:
        json_content = json.load(file)
    print(get_purchase_date(json_content))