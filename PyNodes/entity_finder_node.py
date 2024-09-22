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

class EntityIdentificationMessage(BaseModel):
    identification: str

class ProductFinderNode:
    def __init__(self, consumer: PydanticQueueConsumer, publisher: PydanticExchangePublisher, input_queue: str):
        self.consumer = consumer
        self.publisher = publisher
        self.input_queue = input_queue
        self.stop_event = threading.Event()
        self.driver = create_driver()

    def callback(self, message: EntityIdentificationMessage):
        received_identification =  message.identification.strip()
        if not received_identification:
            logging.info(f"Ignoring empty message")

        logging.info(f"Processing an entity identification: {received_identification}")

    def error_callback(self, error: Exception):        
        if isinstance(error, ValueError):
            logging.error(f"Could not find entity data: {error}")
        if isinstance(error, JSONDecodeError):
            logging.error(f"Could not decode message: {error}")
        elif isinstance(error, ValidationError):
            logging.error(f"Received message format was not expected: {error}")
        else:
            logging.error(f"An unexpected error ({error.__class__.__name__}) occurred: {error}")
        
    def start(self):
        self.consumer.start(self.input_queue, self.callback, EntityIdentificationMessage, self.error_callback)

    def stop(self):
        self.stop_event.set()
        self.consumer.stop()
        if self.driver:
            self.driver.quit()

if __name__ == '__main__':
    LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'FATAL']

    parser = argparse.ArgumentParser(description="Entity data retriever service.")
    parser.add_argument('--logging', default='ERROR', choices=[level.lower() for level in LOG_LEVELS], help='Set logging level')
    args = parser.parse_args()

    logging.basicConfig(level=args.logging.upper())

    broker = PydanticMessageBroker(os.getenv('RABBITMQ_CONNECTION_STRING', 'amqp://guest:guest@localhost:5672/'))

    node = ProductFinderNode(
        broker.get_consumer(), 
        broker.get_publisher(), 
        broker.ensure_queue(os.getenv('ENTITY_FINDER_INPUT_QUEUE', '')))

    try:
        logging.info("Node succesfully initialized")
        node.start()
    except KeyboardInterrupt:
        logging.info("Shutdown initiated by user (Ctrl+C)")
    finally:
        node.stop()
        sys.exit(0)