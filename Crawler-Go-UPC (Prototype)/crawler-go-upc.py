import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def create_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    #chrome_options.add_argument('--enable-logging')
    #chrome_options.add_argument('--v=1') 
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def get_page_source(driver, url):
    driver.get(url)
    return driver.page_source

def main(product_code):
    driver = create_driver()
    try:
        search_url = f'https://go-upc.com/search?q={product_code}'
        html_content = get_page_source(driver, search_url)
        return html_content
    finally:
        driver.quit()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python crawler.py <product-code>")
        sys.exit(1)

    product_code = sys.argv[1]

    html_content = main(product_code)
    print(html_content)
