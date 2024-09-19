import sys
import json
from bs4 import BeautifulSoup
from crawler_prototype.crawler_go_upc import get_page_source


def get_product_defails(product_code):
    page_source = get_page_source(product_code)
    soup = BeautifulSoup(page_source, 'html.parser')
    result = {}

    product_name_div = soup.find('h1', class_='product-name')
    if product_name_div:
        product_name = product_name_div.get_text(strip=True)
        result['product_name'] = product_name
    else:
        result['product_name'] = None

    product_description_span = soup.select_one('div:nth-of-type(2) > span')
    if product_description_span:
        product_description = product_description_span.get_text(strip=True)
        result['product_description'] = product_description
    else:
        result['product_description'] = None
    
    return json.dumps(result, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 -m 'scrapper_prototype.scrapper_go_upc' <product-code>")
        sys.exit(1)

    product_code = sys.argv[1]

    product_details = get_product_defails(product_code)
    print(product_details)
