import argparse
import logging
import threading
import os
import sys
import json
from PyLib.typed_messaging import PydanticMessageBroker, PydanticExchangePublisher, PydanticQueueConsumer
from pydantic import ValidationError
from json.decoder import JSONDecodeError
from dotenv import load_dotenv
from pydantic import BaseModel
from bs4 import BeautifulSoup
from selenium import webdriver

load_dotenv()

def create_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    #chrome_options.add_argument('--enable-logging')
    #chrome_options.add_argument('--v=1') 
    driver = webdriver.Chrome(options=chrome_options)
    return driver

class ProductCode(BaseModel):
    code: str

class ProductFinderNode:
    def __init__(self, consumer: PydanticQueueConsumer, input_queue: str):
        self.consumer = consumer
        self.input_queue = input_queue
        self.stop_event = threading.Event()
        self.driver = create_driver()

    def get_page_source(self, product_code):
        try:
            search_url = f'https://go-upc.com/search?q={product_code}'
            self.driver.get(search_url)
            return self.driver.page_source
        except Exception as e:
            logging.error(f"Error while fetching page source: {e}")
            raise
    
    def get_product_defails(self, product_code):
        page_source = self.get_page_source(product_code)
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

    def callback(self, message: ProductCode):
        received_code =  message.code.strip()
        if not received_code:
            logging.info(f"Ignoring empty message")

        logging.info(f"Processing a code: {received_code}")

        print(self.get_product_defails(received_code))

    def error_callback(self, error: Exception):        
        if isinstance(error, ValueError):
            logging.error(f"Could not find product data: {error}")
        if isinstance(error, JSONDecodeError):
            logging.error(f"Could not decode message: {error}")
        elif isinstance(error, ValidationError):
            logging.error(f"Received message format was not expected: {error}")
        else:
            logging.error(f"An unexpected error ({error.__class__.__name__}) occurred: {error}")
        
    def start(self):
        self.consumer.start(self.input_queue, self.callback, ProductCode, self.error_callback)

    def stop(self):
        self.stop_event.set()
        self.consumer.stop()
        if self.driver:
            self.driver.quit()

if __name__ == '__main__':
    LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'FATAL']

    parser = argparse.ArgumentParser(description="Product data retriever service.")
    parser.add_argument('--logging', default='ERROR', choices=[level.lower() for level in LOG_LEVELS], help='Set logging level')
    args = parser.parse_args()

    logging.basicConfig(level=args.logging.upper())

    broker = PydanticMessageBroker(os.getenv('RABBITMQ_CONNECTION_STRING', 'amqp://guest:guest@localhost:5672/'))

    node = ProductFinderNode(
        broker.get_consumer(), 
        broker.ensure_queue(os.getenv('PRODUCT_FINDER_INPUT_QUEUE', '')))

    try:
        logging.info("Node succesfully initialized")
        node.start()
    except KeyboardInterrupt:
        logging.info("Shutdown initiated by user (Ctrl+C)")
    finally:
        node.stop()
        sys.exit(0)