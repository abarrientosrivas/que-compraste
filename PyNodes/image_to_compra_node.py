import torch
import sys
import os
import logging
import PyLib.receipt_tools as rt
import threading
import argparse
import logging
from API.schemas import PurchaseCreate, PurchaseItemCreate, ReceiptImageLocation
from PIL import Image
from io import BytesIO
from pydantic import ValidationError
from json.decoder import JSONDecodeError
from transformers import DonutProcessor, VisionEncoderDecoderModel
from PyLib import typed_messaging, request_tools
from PyLib.donut_model import DonutTrainer
from dotenv import load_dotenv
from huggingface_hub import HfFolder

load_dotenv()
hf_token = os.getenv('HF_TOKEN')
if hf_token is None or not hf_token.strip():
    logging.error(f"No Hugging Face token was provided")
    raise
HfFolder.save_token(hf_token)

def load_and_preprocess_local_image(image_path: str, processor):
    """
    Load an image and preprocess it for the model.
    """
    image = Image.open(image_path).convert("RGB")
    pixel_values = processor(image, return_tensors="pt").pixel_values
    return pixel_values

def load_and_preprocess_remote_image(image_url: str, processor):
    """
    Load an image from a URL and preprocess it for the model.
    """
    response = request_tools.send_request_with_retries('get', image_url)
    
    if response.status_code != 200:
        raise Exception(f"Failed to load image from URL: {response.status_code}")
    
    image = Image.open(BytesIO(response.content)).convert("RGB")
    pixel_values = processor(image, return_tensors="pt").pixel_values
    return pixel_values

class ImageToCompraNode:
    def __init__(self, consumer: typed_messaging.PydanticQueueConsumer, publisher: typed_messaging.PydanticExchangePublisher, input_queue: str, output_endpoint: str):
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

    def read_receipt_image(self, pixel_values):
        """
        Generate text from an image using the trained model.
        """
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
    
    def callback(self, message: ReceiptImageLocation):
        if message.path.strip():
            logging.info(f"Processing image with path: {message.path}")
            pixel_values = load_and_preprocess_local_image(message.path, self.processor)
        elif message.url.strip():
            logging.info(f"Processing image with url: {message.url}")
            pixel_values = load_and_preprocess_remote_image(message.url, self.processor)
        else:
            logging.warning("Received an empty message. Skipping...")
            return

        json_data = self.read_receipt_image(pixel_values)
        if not json_data or not isinstance(json_data, dict):
            logging.error("Could not generate proper JSON from image")
            return
        purchase = self.convert_data_to_purchase(json_data)
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