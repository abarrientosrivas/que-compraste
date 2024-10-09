import argparse
import logging
import threading
import os
import sys
import json
import time
import random
from PyLib import typed_messaging, request_tools
from pydantic import ValidationError
from json.decoder import JSONDecodeError
from dotenv import load_dotenv
from pydantic import BaseModel
from bs4 import BeautifulSoup
from selenium import webdriver

load_dotenv()

TASK_DELAY = int(os.getenv("CRAWLERS_TASK_DELAY","10"))

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
    def __init__(self, node_token: str, crawl_auth_endpoint: str, consumer: typed_messaging.PydanticQueueConsumer, input_queue: str):
        self.consumer = consumer
        self.crawl_auth_endpoint = crawl_auth_endpoint
        self.node_token = node_token
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
            
        logging.info(f"Requesting crawling authorization")
        headers = {
            "Authorization": f"Bearer {self.node_token}"
        }
        wait_times = [30, 60, 90, 150, 240, 390, 630, 1800]
        retry_count = 0
        response = None
        while not response or response.status_code == 429:
            response = request_tools.send_request_with_retries('post',self.crawl_auth_endpoint, headers=headers)
            if response.status_code == 200:
                break
            if response.status_code != 200 and response.status_code != 429:
                raise Exception(f"Failed to load image from URL: {response.status_code}")
            if retry_count < len(wait_times):
                wait_time = wait_times[retry_count]
            else:
                wait_time = 3600

            logging.warning(f"No uses available, retrying in {wait_time/60} minutes...")
            time.sleep(wait_time)
            retry_count += 1

        logging.info(f"Processing a code: {received_code}")

        print(self.get_product_defails(received_code))
        
        logging.info("Complying with crawler delay")
        time.sleep(TASK_DELAY + random.uniform(0, 5))
        logging.info("Ready for next message") 

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

    broker = typed_messaging.PydanticMessageBroker(os.getenv('RABBITMQ_CONNECTION_STRING', 'amqp://guest:guest@localhost:5672/'))
    
    token = os.getenv('PRODUCT_FINDER_TOKEN','')
    if not token.strip():
        logging.error("Node token was not provided")
        sys.exit(1)
    
    crawl_endpoint = os.getenv('CRAWL_AUTH_ENDPOINT','')
    if not crawl_endpoint.strip():
        logging.error("Crawl auth endpoint was not provided")
        sys.exit(1)

    node = ProductFinderNode(
        token,
        crawl_endpoint,
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