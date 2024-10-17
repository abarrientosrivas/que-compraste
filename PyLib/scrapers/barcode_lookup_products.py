from selenium import webdriver 
from bs4 import BeautifulSoup

BASE_URL = "https://www.barcodelookup.com/"

def create_driver():
    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    #chrome_options.add_argument('--enable-logging')
    #chrome_options.add_argument('--v=1') 
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def get_product_details(page_source) -> dict:
    soup = BeautifulSoup(page_source, 'html.parser')
    result = {}

    product_name_h4 = soup.find('h4')
    if product_name_h4:
        product_name = product_name_h4.get_text(strip=True)
        if product_name.strip() == 'Log in to Your API Account':
            result['product_name'] = None
        else:
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
    
    return result

class BarcodeLookupProducts:
    def __init__(self):
        self.set_driver()

    def set_driver(self):
        self.driver = create_driver()

    def get_page_html(self, product_code: str):
        try:
            search_url = f'{BASE_URL}{product_code}'
            self.driver.get(search_url)
            return self.driver.page_source
        except Exception as ex:
            print(f"error {ex} - {ex.__class__.__name__}")

    def get_product(self, product_code: str) -> dict:
        if not product_code or not product_code.strip():
            return {'product_name': None, 'product_description': None, 'product_category': None}
        return get_product_details(self.get_page_html(product_code))

    def close(self):
        self.driver.close()