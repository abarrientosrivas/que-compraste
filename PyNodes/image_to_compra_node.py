import sys
import os
import logging
import threading
import argparse
import logging
from API.schemas import ReceiptImageLocation
from pydantic import ValidationError
from json.decoder import JSONDecodeError
from PyLib import typed_messaging, request_tools
from PyLib.donut_model import DonutTrainer, DonutInference, convert_data_to_purchase
from dotenv import load_dotenv
from huggingface_hub import HfFolder

load_dotenv()
hf_token = os.getenv('HF_TOKEN')
if hf_token is None or not hf_token.strip():
    logging.error(f"No Hugging Face token was provided")
    raise
HfFolder.save_token(hf_token)

class ImageToCompraNode:
    def __init__(self, model_path: str, consumer: typed_messaging.PydanticQueueConsumer, publisher: typed_messaging.PydanticExchangePublisher, input_queue: str, output_endpoint: str):
        self.donut = DonutInference(model_path)
        self.consumer = consumer
        self.publisher = publisher
        self.input_queue = input_queue
        self.output_endpoint = output_endpoint
        self.stop_event = threading.Event()
    
    def callback(self, message: ReceiptImageLocation):
        if message.path.strip():
            logging.info(f"Processing image with path: {message.path}")
            pixel_values = self.donut.load_and_preprocess_local_image(message.path)
        elif message.url.strip():
            logging.info(f"Processing image with url: {message.url}")
            pixel_values = self.donut.load_and_preprocess_remote_image(message.url, os.getenv('IMAGE_TO_COMPRA_TOKEN'))
        else:
            logging.warning("Received an empty message. Skipping...")
            return

        json_data = self.donut.read_receipt_image(pixel_values)
        if not json_data or not isinstance(json_data, dict):
            logging.error("Could not generate proper JSON from image")
            return
        purchase = convert_data_to_purchase(json_data)
        purchase_data = purchase.model_dump(mode='json')

        response =  request_tools.send_request_with_retries("post", self.output_endpoint, purchase_data, stop_event= self.stop_event)
        if response.status_code == 200:
            logging.info("Purchase created successfully")
        else:
            logging.error(f"Failed to create purchase. Status code: {response.status_code}. Server response: {response.text}")
        
    def error_callback(self, error: Exception):        
        if isinstance(error, JSONDecodeError):
            logging.error(f"Could not decode message: {error}")
        elif isinstance(error, ValidationError):
            logging.error(f"Received message was not of type ReceiptImageLocation: {error}")
        elif isinstance(error, FileNotFoundError):
            logging.error(f"Indicated file was not found: {error}")
        else:
            logging.error(f"An unexpected error ({error.__class__.__name__}) occurred: {error}")
        
    def start(self):
        self.consumer.start(self.input_queue, self.callback, ReceiptImageLocation, self.error_callback)

    def stop(self):
        self.stop_event.set()
        self.consumer.stop()

if __name__ == '__main__':
    LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'FATAL']
    
    parser = argparse.ArgumentParser(description="Product classifier service.")
    parser.add_argument('--train', action='store_true', help='Train receipt reader model')
    parser.add_argument('--dev_mode', action='store_true', help='Train receipt reader model')
    parser.add_argument('--logging', default='ERROR', choices=[level.lower() for level in LOG_LEVELS], help='Set logging level')
    broker = typed_messaging.PydanticMessageBroker(os.getenv('RABBITMQ_CONNECTION_STRING', 'amqp://guest:guest@localhost:5672/'))
    args = parser.parse_args()

    logging.basicConfig(level=args.logging.upper())
    
    if args.train:
        try:
            model_path = os.getenv('IMAGE_TO_COMPRA_MODEL_PATH','')
            if not model_path.strip():
                logging.error("Model path was not provided")
                sys.exit(1)
            dataset_path = os.getenv('IMAGE_TO_COMPRA_DATASET_PATH','')
            if not dataset_path.strip():
                logging.error("Dataset path was not provided")
                sys.exit(1)
            target_path = os.getenv('IMAGE_TO_COMPRA_TARGET_PATH','')
            if not target_path.strip():
                logging.error("Target path was not provided")
                sys.exit(1)
            device = os.getenv('IMAGE_TO_COMPRA_DEVICE','')
            if not device.strip():
                logging.error("Target device was not provided")
                sys.exit(1)
            precision = os.getenv('IMAGE_TO_COMPRA_PRECISION','')
            if not precision.strip():
                logging.error("Training precision was not provided")
                sys.exit(1)
            trainer = DonutTrainer(model_path, dataset_path, target_path, 1280, 960, 768, device, precision, args.dev_mode)
            trainer.run()
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            sys.exit(1)
    else:
        endpoint_url = os.getenv('PURCHASES_ENDPOINT')
        if not endpoint_url:
            logging.error("Endpoint URL was not provided")
            sys.exit(1)
        
        model_path = os.getenv('IMAGE_TO_COMPRA_MODEL_PATH','')
        if not model_path.strip():
            logging.error("Model path was not provided")
            sys.exit(1)

        node = ImageToCompraNode(
            model_path,
            broker.get_consumer(), 
            broker.get_publisher(), 
            broker.ensure_queue(os.getenv('IMAGE_TO_COMPRA_INPUT_QUEUE', '')), 
            endpoint_url)

        try:
            logging.info("Node succesfully initialized")
            node.start()
        except KeyboardInterrupt:
            node.stop()
            sys.exit(0)