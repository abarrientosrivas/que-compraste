import sys
import json
import re
from bs4 import BeautifulSoup

def get_product_details(page_source):
    soup = BeautifulSoup(page_source, 'html.parser')
    result = {}

    title_tag = soup.find('product_name')
    result['product_name'] = title_tag.get_text(strip=True) if title_tag else None
    product_name_tag = soup.find("h1", class_="text-2xl md:text-3xl font-extralight font-display text-zinc-700")
    result['product_name'] = product_name_tag.get_text(strip=True) if product_name_tag else None

    description_div = soup.find("div", class_="mb-1 text-zinc-600 text-xs mt-2")
    result['product_description'] = description_div.get_text(strip=True) if description_div else None
    result['product_description'] = ' '.join(result['product_description'].split())

    categories_div = soup.find_all('a', class_='bg-zinc-100')
    categories = [category.get_text(strip=True) for category in categories_div]
    result['product_category'] = ', '.join(categories) if categories else None
    result['product_category'] = ' '.join(result['product_category'].split())

    # Get product image link
    image_tag = soup.select_one('img.image')
    result['product_image_link'] = image_tag['src'] if image_tag else None
    
    return json.dumps(result, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 -m 'scrapper_prototype.scrapper_pricely' <html_path>")
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