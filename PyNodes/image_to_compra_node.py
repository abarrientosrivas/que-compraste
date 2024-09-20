import torch
import sys
import os
import logging
import PyLib.receipt_tools as rt
import requests
import time
import threading
from requests import Response
from requests.exceptions import ConnectionError, Timeout
from API.schemas import PurchaseCreate, PurchaseItemCreate
from PIL import Image
from pydantic import BaseModel, ValidationError
from json.decoder import JSONDecodeError
from transformers import DonutProcessor, VisionEncoderDecoderModel
from PyLib.typed_messaging import PydanticMessageBroker, PydanticExchangePublisher, PydanticQueueConsumer
from dotenv import load_dotenv
from huggingface_hub import HfFolder
from threading import Event

load_dotenv()
hf_token = os.getenv('HF_TOKEN')
HfFolder.save_token(hf_token)

class ImageLocation(BaseModel):
    path: str

def load_and_preprocess_image(image_path: str, processor):
    """
    Load an image and preprocess it for the model.
    """
    image = Image.open(image_path).convert("RGB")
    pixel_values = processor(image, return_tensors="pt").pixel_values
    return pixel_values

def send_request_with_retries(url: str, json_data, stop_event: Event) -> Response:
    wait_times = [0, 5, 10, 15, 30, 45, 60]
    retry_count = 0

    while not stop_event.is_set():
        try:
            return requests.post(url, json=json_data)

        except (ConnectionError, Timeout) as e:
            if retry_count < len(wait_times):
                wait_time = wait_times[retry_count]
            else:
                wait_time = 60

            print(f"Connection failed: {e}. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            retry_count += 1
    logging.warning("Stop event set before request could complete.")
    raise Exception("Operation cancelled by user.")

class ImageToCompraNode:
    def __init__(self, consumer: PydanticQueueConsumer, publisher: PydanticExchangePublisher, input_queue: str, output_endpoint: str):
        self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        self.processor = DonutProcessor.from_pretrained("AdamCodd/donut-receipts-extract")
        self.model = VisionEncoderDecoderModel.from_pretrained("AdamCodd/donut-receipts-extract")
        self.model.to(self.device)
        self.consumer = consumer
        self.publisher = publisher
        self.input_queue = input_queue
        self.output_endpoint = output_endpoint
        self.stop_event = threading.Event()

    def convert_data_to_purchase(self, json_data: dict) -> PurchaseCreate:
        entity_id = None
        try:
            entity_id = rt.normalize_entity_id(rt.get_string_field_value("entity_id", json_data))
        except Exception as e:
            logging.warning(f"Could not recover the entity's id: {e}")
        store_name = None
        try:
            store_name = rt.get_string_field_value("store_name", json_data)
        except Exception as e:
            logging.warning(f"Could not recover the store's name: {e}")
        store_branch = None
        try:
            store_branch = rt.get_string_field_value("store_branch", json_data)
        except Exception as e:
            logging.warning(f"Could not recover the store's branch name: {e}")
        store_location = None
        try:
            store_location = rt.get_string_field_value("store_location", json_data)
        except Exception as e:
            logging.warning(f"Could not recover the store's location: {e}")
        store_address = None
        try:
            store_address = rt.get_string_field_value("store_addr", json_data)
        except Exception as e:
            logging.warning(f"Could not recover the store's address: {e}")
        store_phone = None
        try:
            store_phone = rt.get_string_field_value("phone", json_data)
        except Exception as e:
            logging.warning(f"Could not recover the store's phone: {e}")
        total = None
        try:
            total = rt.normalize_value(rt.get_string_field_value("total", json_data))
        except Exception as e:
            logging.warning(f"Could not recover the purchase's total: {e}")
        subtotal = None
        try:
            subtotal = rt.normalize_value(rt.get_string_field_value("subtotal", json_data))
        except Exception as e:
            logging.warning(f"Could not recover the purchase's subtotal: {e}")
        discount = None
        try:
            discount = rt.normalize_value(rt.get_string_field_value("discount", json_data))
        except Exception as e:
            logging.warning(f"Could not recover the purchase's discount: {e}")
        tips = None
        try:
            tips = rt.normalize_value(rt.get_string_field_value("tips", json_data))
        except Exception as e:
            logging.warning(f"Could not recover the purchase's tips: {e}")
        date = None
        try:
            date = rt.get_purchase_date(json_data)
        except Exception as e:
            logging.warning(f"Could not recover the purchase's date: {e}")
        purchase = PurchaseCreate(
            read_entity_name= store_name,
            read_entity_branch= store_branch,
            read_entity_location= store_location,
            read_entity_address= store_address,
            read_entity_identification= entity_id,
            read_entity_phone= store_phone,
            date= date,
            subtotal= subtotal,
            discount= discount,
            tips= tips,
            total= total,
        )
        read_items = []
        try:
            read_items = rt.get_list_field_value("line_items", json_data)
        except Exception as e:
            logging.warning(f"Could not recover the purchase's items: {e}")
        for read_item in read_items:
            item_key = None
            try:
                item_key = rt.normalize_product_key(rt.get_string_field_value("item_key", read_item))
            except Exception as e:
                logging.warning(f"Could not recover an item's key: {e}")
            item_text = None
            try:
                item_text = rt.get_string_field_value("item_name", read_item)
            except Exception as e:
                logging.warning(f"Could not recover an item's text: {e}")
            item_quantity = None
            try:
                item_quantity = rt.normalize_quantity(rt.get_string_field_value("item_quantity", read_item))
            except Exception as e:
                logging.warning(f"Could not recover an item's quantity: {e}")
            item_value = None
            try:
                item_value = rt.normalize_value(rt.get_string_field_value("item_value", read_item))
            except Exception as e:
                logging.warning(f"Could not recover an item's value: {e}")
            item_total = None
            try:
                item_total = rt.normalize_value(rt.get_string_field_value("item_total", read_item))
            except Exception as e:
                logging.warning(f"Could not recover an item's total: {e}")
            purchase.items.append(PurchaseItemCreate(
                read_product_key= item_key,
                read_product_text= item_text,
                quantity= item_quantity,
                value= item_value,
                total= item_total,
            ))
        return purchase

    def read_receipt_image(self, image_path: str):
        """
        Generate text from an image using the trained model.
        """
        pixel_values = load_and_preprocess_image(image_path, self.processor)
        pixel_values = pixel_values.to(self.device)

        self.model.eval()
        with torch.no_grad():
            task_prompt = "<s_receipt>" # <s_cord-v2> for v1
            decoder_input_ids = self.processor.tokenizer(task_prompt, add_special_tokens=False, return_tensors="pt").input_ids
            decoder_input_ids = decoder_input_ids.to(self.device)
            generated_outputs = self.model.generate(
                pixel_values,
                decoder_input_ids=decoder_input_ids,
                max_length=self.model.decoder.config.max_position_embeddings, 
                pad_token_id=self.processor.tokenizer.pad_token_id,
                eos_token_id=self.processor.tokenizer.eos_token_id,
                early_stopping=False,
                bad_words_ids=[[self.processor.tokenizer.unk_token_id]],
                return_dict_in_generate=True
            )
            
        decoded_text = self.processor.batch_decode(generated_outputs.sequences)[0]
        # decoded_text = decoded_text.replace(self.processor.tokenizer.eos_token, "").replace(self.processor.tokenizer.pad_token, "")
        # decoded_text = re.sub(r"<.*?>", "", decoded_text, count=1).strip()  # remove first task start token
        decoded_text = self.processor.token2json(decoded_text)
        return decoded_text
    
    def callback(self, message: ImageLocation):
        logging.info(f"Processing image with path: {message.path}")

        json_data = self.read_receipt_image(message.path)
        if not json_data or not isinstance(json_data, dict):
            logging.error("Could not generate proper JSON from image")
            return
        purchase = self.convert_data_to_purchase(json_data)
        purchase_data = purchase.model_dump(mode='json')

        response = send_request_with_retries(self.output_endpoint, purchase_data, self.stop_event)
        if response.status_code == 200:
            logging.info("Purchase created successfully")
        else:
            logging.error(f"Failed to create purchase. Status code: {response.status_code}. Server response: {response.text}")
        
    def error_callback(self, error: Exception):        
        if isinstance(error, JSONDecodeError):
            logging.error(f"Could not decode message: {error}")
        elif isinstance(error, ValidationError):
            logging.error(f"Received message was not of type ImageLocation: {error}")
        elif isinstance(error, FileNotFoundError):
            logging.error(f"Indicated file was not found: {error}")
        else:
            logging.error(f"An unexpected error ({error.__class__.__name__}) occurred: {error}")
        
    def start(self):
        self.consumer.start(self.input_queue, self.callback, ImageLocation, self.error_callback)

    def stop(self):
        self.stop_event.set()
        self.consumer.stop()

if __name__ == '__main__':
    broker = PydanticMessageBroker(os.getenv('RABBITMQ_CONNECTION_STRING', 'amqp://guest:guest@localhost:5672/'))
    endpoint_url = os.getenv('IMAGE_TO_COMPRA_OUTPUT_ENDPOINT')
    if not endpoint_url:
        logging.error("Endpoint URL was not provided")
        sys.exit(1)

    node = ImageToCompraNode(
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