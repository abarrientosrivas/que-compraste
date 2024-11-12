import argparse
import logging
import threading
import os
import sys
from API.schemas import Purchase
from PyLib import typed_messaging, request_tools
from pydantic import ValidationError
from json.decoder import JSONDecodeError
from dotenv import load_dotenv

load_dotenv()

TASK_DELAY = int(os.getenv("CRAWLERS_TASK_DELAY","10"))

class PurchasePredictorNode:
    def __init__(self, restockables_endpoint: str, consumer: typed_messaging.PydanticQueueConsumer, input_queue: str):
        self.consumer = consumer
        self.restockables_endpoint = restockables_endpoint
        self.input_queue = input_queue
        self.stop_event = threading.Event()

    def callback(self, message: Purchase):
        if not message.items:
            logging.info(f"Ignoring purchase with no items")
            return
        
        response = request_tools.send_request_with_retries("get", f"{self.restockables_endpoint}", stop_event=self.stop_event)
        if response is None:
            logging.error(f"There was no response from server")
        if response.status_code != 200:
            logging.error(f"Failed to retrieve restockables. Status code: {response.status_code}. Server response: {response.text}")
        restockable_keys: list = response.json()

        purchase_product_keys = list({item.read_product_key for item in message.items})

        for product_key in purchase_product_keys:
            if product_key in restockable_keys:
                logging.info(f"Generating predictions for {product_key}")
        
        # response = request_tools.send_request_with_retries("post", f"{self.product_codes_endpoint}", new_product_code.model_dump(mode='json'), stop_event=self.stop_event)
        # if response is None:
        #     logging.error(f"There was no response from server")
        # if response.status_code == 200:
        #     logging.info(f"Product with code {received_code} created successfully")
        # else:
        #     logging.error(f"Failed to create product code. Status code: {response.status_code}. Server response: {response.text}")
        
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
        self.consumer.start(self.input_queue, self.callback, Purchase, self.error_callback)

    def stop(self):
        self.consumer.stop()

if __name__ == '__main__':
    LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'FATAL']

    parser = argparse.ArgumentParser(description="Purchase prediction service.")
    parser.add_argument('--logging', default='ERROR', choices=[level.lower() for level in LOG_LEVELS], help='Set logging level')
    args = parser.parse_args()

    logging.basicConfig(level=args.logging.upper())

    broker = typed_messaging.PydanticMessageBroker(os.getenv('RABBITMQ_CONNECTION_STRING', 'amqp://guest:guest@localhost:5672/'))
    
    restockables_endpoint = os.getenv('RESTOCKABLES_ENDPOINT','')
    if not restockables_endpoint.strip():
        logging.error("Product codes endpoint was not provided")
        sys.exit(1)

    node = PurchasePredictorNode(
        restockables_endpoint,
        broker.get_consumer(), 
        broker.ensure_queue(os.getenv('PURCHASE_PREDICTOR_INPUT_QUEUE', '')))

    try:
        logging.info("Node succesfully initialized")
        node.start()
    except KeyboardInterrupt:
        logging.info("Shutdown initiated by user (Ctrl+C)")
    finally:
        node.stop()
        sys.exit(0)