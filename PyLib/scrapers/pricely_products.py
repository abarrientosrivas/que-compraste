from bs4 import BeautifulSoup
import requests

BASE_URL = "https://pricely.ar/product/"

def get_product_details(page_source) -> dict:
    soup = BeautifulSoup(page_source, 'html.parser')
    result = {}

    title_tag = soup.find('title')
    result['product_name'] = title_tag.get_text(strip=True) if title_tag else None
    if result['product_name'] == "Producto no encontrado":
        result['product_name'] = None

    description_div = soup.find("div", class_="mb-1 text-zinc-600 text-xs mt-2")
    result['product_description'] = description_div.get_text(strip=True) if description_div else None
    if result['product_description']:
        result['product_description'] = ' '.join(result['product_description'].split())

    categories_div = soup.find_all('a', class_='bg-zinc-100')
    categories = [category.get_text(strip=True) for category in categories_div]
    result['product_category'] = ', '.join(categories) if categories else None
    if result['product_category']:
        result['product_category'] = ' '.join(result['product_category'].split())

    return result

class PricelyProductScrapper:
    def get_page_html(self, product_code: str):
        try:
            response = requests.get(f"{BASE_URL}{product_code}")
            response.raise_for_status()
            return response.text
        except requests.RequestException as ex:
            print(f"error {ex} - {ex.__class__.__name__}")

    def get_product(self, product_code: str) -> dict:
        if not product_code or not product_code.strip():
            return {'product_name': None, 'product_description': None, 'product_category': None}
        page_html = self.get_page_html(product_code)
        product = get_product_details(page_html)
        return product