import requests

def get_page_source(product_code: str):
    url = f"https://pricely.ar/product/{product_code}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        return None
    
with open("output2.html", 'w', encoding='utf-8') as file:
    file.write(get_page_source("7790790120325"))