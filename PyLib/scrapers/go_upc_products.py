from selenium import webdriver 
from bs4 import BeautifulSoup

BASE_URL = "https://go-upc.com/search?q="

def create_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    #chrome_options.add_argument('--enable-logging')
    #chrome_options.add_argument('--v=1') 
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def get_product_details(page_source) -> dict:
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

    category_row = soup.find('td', text='Category')
    result['product_category'] = None
    if category_row:
        category_value_field = category_row.find_next_sibling('td')
        if category_value_field:
            result['product_category'] = category_value_field.get_text(strip=True)
    
    return result

class GoUpcProductScrapper:
    def __init__(self):
        self.set_driver()

    def set_driver(self):
        self.driver = create_driver()

    def get_page_html(self, product_code: str):
        search_url = f'{BASE_URL}{product_code}'
        self.driver.get(search_url)
        return self.driver.page_source

    def get_product(self, product_code: str) -> dict:
        if not product_code or not product_code.strip():
            return {'product_name': None, 'product_description': None, 'product_category': None}
        return get_product_details(self.get_page_html(product_code))

    def close(self):
        self.driver.close()