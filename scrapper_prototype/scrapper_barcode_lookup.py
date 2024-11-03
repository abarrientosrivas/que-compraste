import sys
import json
from bs4 import BeautifulSoup

def get_product_details(page_source):
    soup = BeautifulSoup(page_source, 'html.parser')
    result = {}

    product_name_h4 = soup.find('h4')
    if product_name_h4:
        product_name = product_name_h4.get_text(strip=True)
        result['product_name'] = product_name
    else:
        result['product_name'] = None

    product_description_div = soup.find('div', class_='product-meta-data')
    if product_description_div:
        product_description_span = product_description_div.find('span', class_='product-text')
        if product_description_span:
            product_description = product_description_span.get_text(strip=True)
            result['product_description'] = product_description
        else:
            result['product_description'] = None
    else:
        result['product_description'] = None

    result['product_category'] = None
    product_category_divs = soup.find_all('div', class_='product-text-label')
    for div in product_category_divs:
        if div.get_text(strip=True).startswith("Category:"):
            product_category_span = div.find('span', class_='product-text')
            if product_category_span:
                product_category = product_category_span.get_text(strip=True)
                result['product_category'] = product_category
    
    return json.dumps(result, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 -m 'scrapper_prototype.scrapper_barcode_lookup' <html_path>")
        sys.exit(1)

    html_path = sys.argv[1]
    try:
        with open(html_path, 'r', encoding='utf-8') as file:
            page_source = file.read()
        
        product_details = get_product_details(page_source)
        print(product_details)
    
    except FileNotFoundError:
        print(f"File '{html_path}' not found.")
        sys.exit(1)