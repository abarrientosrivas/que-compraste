from selenium import webdriver 

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

class BarcodeLookupProducts:
    def __init__(self):
        self.driver = create_driver()

    def get_page_html(self, product_code: str):
        try:
            search_url = f'{BASE_URL}{product_code}'
            self.driver.get(search_url)
            return self.driver.page_source
        except Exception as ex:
            print(f"error {ex} - {ex.__class__.__name__}")

    def close(self):
        self.driver.close()