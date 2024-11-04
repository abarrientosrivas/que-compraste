import argparse
import logging
import threading
import os
import sys
import time
import random
from API.schemas import ProductCodeBase, ProductCodeCreate, ProductCreate
from PyLib import typed_messaging, request_tools
from pydantic import ValidationError
from json.decoder import JSONDecodeError
from dotenv import load_dotenv
from PyLib.scrapers import GoUpcProductScrapper, PricelyProductScrapper

load_dotenv()

TASK_DELAY = int(os.getenv("CRAWLERS_TASK_DELAY","10"))

class ProductFinderNode:
    def __init__(self, go_upc_token: str, pricely_token: str, crawl_auth_endpoint: str, product_codes_endpoint: str, consumer: typed_messaging.PydanticQueueConsumer, input_queue: str):
        self.consumer = consumer
        self.crawl_auth_endpoint = crawl_auth_endpoint
        self.go_upc_token = go_upc_token
        self.pricely_token = pricely_token
        self.product_codes_endpoint = product_codes_endpoint
        self.input_queue = input_queue
        self.stop_event = threading.Event()
        self.pricely_scrapper = PricelyProductScrapper()
        self.go_upc_scrapper = GoUpcProductScrapper()

    def callback(self, message: ProductCodeBase):
        received_code =  message.code.strip()
        if not received_code:
            logging.info(f"Ignoring message with no code")
            return
        received_format =  message.format.strip()
        if not received_format:
            logging.info(f"Ignoring message with no format")
            return
        if received_format != 'ean13':
            logging.info(f"Ignoring message with invalid format")
            return

        logging.info(f"Checking if product exists")
        response = request_tools.send_request_with_retries('get',f"{self.product_codes_endpoint}?format={received_format}&code={received_code}")
        if response.status_code != 200:
            raise Exception(f"Failed to query products: {response.status_code}")
        entities = response.json()
        if isinstance(entities, list):
            count = len(entities)
        else:
            raise Exception("Unexpected response format: expected a JSON list")
        if count > 0:
            logging.warning(f"Product with code '{received_code}' exists, skipping...")
            return
            
        logging.info(f"Requesting crawling authorization for Pricely")
        headers = {
            "Authorization": f"Bearer {self.pricely_token}"
        }
        wait_times = [30, 60, 90, 150, 240, 390, 630, 1800]
        retry_count = 0
        response = None
        while not response or response.status_code == 429:
            response = request_tools.send_request_with_retries('post',self.crawl_auth_endpoint, headers=headers)
            if response.status_code == 200:
                break
            if response.status_code != 200 and response.status_code != 429:
                raise Exception(f"Failed to request crawling authorization: {response.status_code}")
            if retry_count < len(wait_times):
                wait_time = wait_times[retry_count]
            else:
                wait_time = 3600

            logging.warning(f"No uses available, retrying in {wait_time/60} minutes...")
            time.sleep(wait_time)
            retry_count += 1

        logging.info(f"Scrapping Pricely with code: {received_code}")
        search_result = self.pricely_scrapper.get_product(received_code)
        
        if not search_result["product_name"]:
            logging.info(f"Requesting crawling authorization for Go UPC")
            headers = {
                "Authorization": f"Bearer {self.go_upc_token}"
            }
            wait_times = [30, 60, 90, 150, 240, 390, 630, 1800]
            retry_count = 0
            response = None
            while not response or response.status_code == 429:
                response = request_tools.send_request_with_retries('post',self.crawl_auth_endpoint, headers=headers)
                if response.status_code == 200:
                    break
                if response.status_code != 200 and response.status_code != 429:
                    raise Exception(f"Failed to request crawling authorization: {response.status_code}")
                if retry_count < len(wait_times):
                    wait_time = wait_times[retry_count]
                else:
                    wait_time = 3600

                logging.warning(f"No uses available, retrying in {wait_time/60} minutes...")
                time.sleep(wait_time)
                retry_count += 1
                
            logging.info(f"Scrapping Go UPC with code: {received_code}")
            search_result = self.go_upc_scrapper.get_product(received_code)

        if not search_result["product_name"]:
            logging.error("Could not recover product's title")
            logging.info("Complying with crawler delay")
            time.sleep(TASK_DELAY + random.uniform(0, 5))
            logging.info("Ready for next message") 
            return
        
        new_product = ProductCreate(
            title=search_result['product_name'],
            description=search_result['product_description'],
            read_category=search_result['product_category']
        )

        new_product_code = ProductCodeCreate(
            format=received_format,
            code=received_code,
            product=new_product
        )
        
        response = request_tools.send_request_with_retries("post", f"{self.product_codes_endpoint}", new_product_code.model_dump(mode='json'), stop_event=self.stop_event)
        if response is None:
            logging.error(f"There was no response from server")
        if response.status_code == 200:
            logging.info(f"Product with code {received_code} created successfully")
        else:
            logging.error(f"Failed to create product code. Status code: {response.status_code}. Server response: {response.text}")
        
        logging.info("Complying with crawler delay")
        time.sleep(TASK_DELAY + random.uniform(0, 5))
        logging.info("Ready for next message") 

    def error_callback(self, error: Exception, _):        
        if isinstance(error, ValueError):
            logging.error(f"Could not find product data: {error}")
        if isinstance(error, JSONDecodeError):
            logging.error(f"Could not decode message: {error}")
        elif isinstance(error, ValidationError):
            logging.error(f"Received message format was not expected: {error}")
        else:
            logging.error(f"An unexpected error ({error.__class__.__name__}) occurred: {error}")
        
    def start(self):
        self.consumer.start(self.input_queue, self.callback, ProductCodeBase, self.error_callback)

    def stop(self):
        self.go_upc_scrapper.close()
        self.consumer.stop()

if __name__ == '__main__':
    LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'FATAL']

    parser = argparse.ArgumentParser(description="Product data retriever service.")
    parser.add_argument('--logging', default='ERROR', choices=[level.lower() for level in LOG_LEVELS], help='Set logging level')
    args = parser.parse_args()

    logging.basicConfig(level=args.logging.upper())

    broker = typed_messaging.PydanticMessageBroker(os.getenv('RABBITMQ_CONNECTION_STRING', 'amqp://guest:guest@localhost:5672/'))
    
    go_upc_token = os.getenv('GO_UPC_SCRAPPER_TOKEN','')
    if not go_upc_token.strip():
        logging.error("Go UPC scrapper token was not provided")
        sys.exit(1)
        
    pricely_token = os.getenv('PRICELY_SCRAPPER_TOKEN','')
    if not pricely_token.strip():
        logging.error("Pricely scrapper token was not provided")
        sys.exit(1)
    
    crawl_endpoint = os.getenv('CRAWL_AUTH_ENDPOINT','')
    if not crawl_endpoint.strip():
        logging.error("Crawl auth endpoint was not provided")
        sys.exit(1)
    
    product_codes_endpoint = os.getenv('PRODUCT_CODES_ENDPOINT','')
    if not product_codes_endpoint.strip():
        logging.error("Product codes endpoint was not provided")
        sys.exit(1)

    node = ProductFinderNode(
        go_upc_token,
        pricely_token,
        crawl_endpoint,
        product_codes_endpoint,
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