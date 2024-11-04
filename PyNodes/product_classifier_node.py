import chromadb
import argparse
import requests
import logging
import threading
import os
import sys
from PyLib import request_tools, typed_messaging
from PyLib.product_classification import describe_product, translate_to_english
from API import schemas
from pydantic import ValidationError
from json.decoder import JSONDecodeError
from typing import List
from dotenv import load_dotenv

load_dotenv()

def get_vectorizable_text(category: schemas.Category) -> str:
    text = category.original_text
    if '-' in text:
        text = text.split('-', 1)[1].strip()
    else:
        text = text.strip()
    text = text.replace('>', ' ')
    text = ' '.join(text.split())
    return text

def sync_categories(file_path: str):
    category_strs: List[str] = []
    with open(file_path, 'r') as file:
        for line in file:
            category_strs.append(line.strip())

    logging.info("Requesting taxonomy synchronization")
    taxonomy_categories_endpoint = os.getenv("CATEGORIES_ENDPOINT")
    response = requests.post(taxonomy_categories_endpoint, json=category_strs)
    if response.status_code == 200:
        logging.info("Categories synchronized successfully")
    else:
        logging.error(f"Failed to synchronize categories. Status code: {response.status_code}. Server response: {response.text}")
        sys.exit(1)

def add_es_es(file_path: str):
    category_strs: List[str] = []
    with open(file_path, 'r') as file:
        for line in file:
            category_strs.append(line.strip())

    es_es_str = [(line.split("-")[0].strip(), line.split("-")[1].split(">")[-1].strip()) for line in category_strs[1:]]

    logging.info("Sending names as ES_es")
    taxonomy_categories_endpoint = os.getenv("CATEGORIES_ENDPOINT")
    response = requests.put(f"{taxonomy_categories_endpoint}es_es", json=es_es_str)
    if response.status_code == 200:
        logging.info("Categories ES_es added successfully")
    else:
        logging.error(f"Failed to add ES_es. Status code: {response.status_code}. Server response: {response.text}")
        sys.exit(1)

def init():
    taxonomy_categories_endpoint = os.getenv("CATEGORIES_ENDPOINT")
    categories = []
    response = requests.get(taxonomy_categories_endpoint)
    if response.status_code == 200:
        logging.info("Categories received successfully")
        categories_data = response.json()
        categories = [schemas.Category.model_validate(cat) for cat in categories_data]
    else:
        logging.error(f"Failed to retrieve categories. Status code: {response.status_code}. Server response: {response.text}")
        sys.exit(1)
        
    ids = [str(index) for index, _ in enumerate(categories, start=1)]
    documents = [get_vectorizable_text(category) for category in categories]
    metadatas = [category.model_dump(exclude_none=True, include={"code","name","original_text"}) for category in categories]

    logging.info("Creating taxonomy collection")
    client = chromadb.PersistentClient(path=os.getenv("TAXONOMY_CHROMA_PATH"))
    collection_name = os.getenv("TAXONOMY_CHROMA_COLLECTION", "google_taxonomy")
    try:
        client.delete_collection(collection_name)
    except:
        pass
    collection = client.create_collection(name=collection_name)

    collection.add(
        ids= ids,
        documents= documents,
        metadatas= metadatas
    )

    ids = [str(index) for index, _ in enumerate(categories, start=len(ids) + 1)]
    documents = [category.name for category in categories]
    metadatas = [category.model_dump(exclude_none=True, include={"code","name","original_text"}) for category in categories]

    collection.add(
        ids= ids,
        documents= documents,
        metadatas= metadatas
    )
    
    logging.info("Taxonomy collection created successfully")

class ProductClassifierNode:
    def __init__(self, consumer: typed_messaging.PydanticQueueConsumer, input_queue: str, categories_endpoint: str, products_endpoint: str):
        self.consumer = consumer
        self.input_queue = input_queue
        self.categories_endpoint = categories_endpoint
        self.products_endpoint = products_endpoint
        self.stop_event = threading.Event()
        client = chromadb.PersistentClient(path=os.getenv("TAXONOMY_CHROMA_PATH"))
        try:
            self.collection = client.get_collection(name=os.getenv("TAXONOMY_CHROMA_COLLECTION", "google_taxonomy"))
        except ValueError as e:
            raise ValueError(f"Could not find taxonomy collection: {e}")

    def get_category_code(self, product_description: str) -> str:
        product_description = product_description.strip()
        if not product_description:
            raise ValueError("Product description was null or empty")

        results = self.collection.query(
            query_texts=[product_description],
            n_results=1
        )

        return results['metadatas'][0][0]['code'] 

    def callback(self, message: schemas.Product):
        logging.info(f"Processing a product: {message.title}")

        product_description = describe_product(message)
        if product_description is None:
            logging.error(f"Cannot describe product.")
            return
        
        category_str = translate_to_english(product_description)
        logging.info(f"Using keywords:{category_str}")
        category_code = self.get_category_code(category_str)
        response = request_tools.send_request_with_retries("get", self.categories_endpoint, params = {"code": category_code}, stop_event=self.stop_event)
        if response is None:
            raise Exception("No response")
        if response.status_code == 200:
            logging.info(f"Category with code {category_code} retrieved successfully")
        else:
            logging.error(f"Failed to retrieve category. Status code: {response.status_code}. Server response: {response.text}")
            return
        
        categories = [schemas.Category(**item) for item in response.json()]
        if not categories:
            logging.error(f"Failed to retrieve category with code {category_code}. Server response was empty.")
            return
        logging.info(f"Assigned category: {categories[0].original_text}")
        
        update_product = schemas.ProductUpdate(category_id=categories[0].id)
        update_product_data = update_product.model_dump(mode='json', exclude_none=True)
        response = request_tools.send_request_with_retries("put", f"{self.products_endpoint}{message.id}", update_product_data, stop_event=self.stop_event)
        if response is None:
            raise Exception("No response")
        if response.status_code == 200:
            logging.info(f"Product with id {message.id} updated successfully")
        else:
            logging.error(f"Failed to update product. Status code: {response.status_code}. Server response: {response.text}")
            return

    def error_callback(self, error: Exception, _):        
        if isinstance(error, ValueError):
            logging.error(f"Could not assign a category: {error}")
        if isinstance(error, JSONDecodeError):
            logging.error(f"Could not decode message: {error}")
        elif isinstance(error, ValidationError):
            logging.error(f"Received message was not a Product: {error}")
        else:
            logging.error(f"An unexpected error ({error.__class__.__name__}) occurred: {error}")
        
    def start(self):
        self.consumer.start(self.input_queue, self.callback, schemas.Product, self.error_callback)

    def stop(self):
        self.stop_event.set()
        self.consumer.stop()

if __name__ == '__main__':
    LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'FATAL']

    parser = argparse.ArgumentParser(description="Product classifier service.")
    parser.add_argument('--init', action='store_true', help='Initialize ChromaDB')
    parser.add_argument('--sync', action='store_true', help='Synchronize API with categories file')
    parser.add_argument('--add-es-es', action='store_true', help='Add Spanish names to API categories')
    parser.add_argument('--logging', default='ERROR', choices=[level.lower() for level in LOG_LEVELS], help='Set logging level')
    parser.add_argument('file_path', type=str, nargs='?', help='The path to the product taxonomy text file (required if --init is used)')
    parser.add_argument('product_description', type=str, nargs='?', help='Description of the product to classify (used if --init is not present)')
    args = parser.parse_args()

    logging.basicConfig(level=args.logging.upper())

    if args.init:
        init()
    elif args.add_es_es:
        if not args.file_path:
            parser.error('the following argument is required when using --add-es-es: file_path')
        add_es_es(args.file_path)
    elif args.sync:
        if not args.file_path:
            parser.error('the following argument is required when using --sync: file_path')
        sync_categories(args.file_path)
    else:
        broker = typed_messaging.PydanticMessageBroker(os.getenv('RABBITMQ_CONNECTION_STRING', 'amqp://guest:guest@localhost:5672/'))
        categories_endpoint = os.getenv('CATEGORIES_ENDPOINT')
        if not categories_endpoint:
            logging.error("Categories endpoint URL was not provided")
            sys.exit(1)
            
        products_endpoint = os.getenv('PRODUCTS_ENDPOINT')
        if not products_endpoint:
            logging.error("Products endpoint URL was not provided")
            sys.exit(1)

        node = ProductClassifierNode(
            broker.get_consumer(), 
            broker.ensure_queue(os.getenv('PRODUCT_CLASSIFIER_INPUT_QUEUE', '')), 
            categories_endpoint,
            products_endpoint)

        try:
            logging.info("Node succesfully initialized")
            node.start()
        except KeyboardInterrupt:
            node.stop()
            sys.exit(0)