import requests

def get_page_source(product_code: str):
    url = f"https://pricely.ar/product/{product_code}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        return None
    
print(get_page_source("7790310985465"))