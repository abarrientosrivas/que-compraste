import sys
import os
import logging
import threading
import argparse
import logging
import json
import torch
from API.schemas import ReceiptImageLocation
from pydantic import ValidationError
from json.decoder import JSONDecodeError
from PyLib import typed_messaging, request_tools
from dotenv import load_dotenv
from transformers import Qwen2VLForConditionalGeneration, AutoTokenizer, AutoProcessor
from qwen_vl_utils import process_vision_info
from PyLib.donut_model import convert_data_to_purchase

load_dotenv()

class ImageToCompraNode:
    def __init__(self, node_token: str, receipt_output_path: str, consumer: typed_messaging.PydanticQueueConsumer, input_queue: str, output_endpoint: str):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.consumer = consumer
        self.input_queue = input_queue
        self.output_endpoint = output_endpoint
        self.node_token = node_token
        self.receipt_output_path = receipt_output_path
        self.stop_event = threading.Event()
        self.min_pixels = 256 * 28 * 28
        self.max_pixels = 1280 * 28 * 28
        self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                "Qwen/Qwen2-VL-7B-Instruct", 
                torch_dtype="auto",
                # torch_dtype=torch.bfloat16,
                # attn_implementation='flash_attention_2',
            ).to(self.device)
        self.processor = AutoProcessor.from_pretrained(
                "Qwen/Qwen2-VL-7B-Instruct",
                min_pixels = self.min_pixels,
                max_pixels = self.max_pixels,
            )
    
    def callback(self, message: ReceiptImageLocation):
        if message.path.strip():
            logging.info(f"Processing image with path: {message.path}")
            receipt_path = message.path
        elif message.url.strip():
            logging.info(f"Processing image with url: {message.url}")
            headers = {
                "Authorization": f"Bearer {self.node_token}"
            }
            response = request_tools.send_request_with_retries('get', message.url, headers= headers)
            if response.status_code != 200:
                raise Exception(f"Failed to load image from URL: {response.status_code}")
            
            receipt_path = self.receipt_output_path

            with open(receipt_path, 'wb') as f:
                f.write(response.content)
        else:
            logging.warning("Received an empty message. Skipping...")
            return
        
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": receipt_path,
                    },
                    {
                        "type": "text", 
                        "text": 
'''Read the following receipt image and return it's text as clean JSON, and only JSON, under the following schema:
{
    "type": "object",
    "properties": {
        "store_name": {
            "type": "string",
            "description": "The brand name of the store where the purchase was made."
        },
        "store_addr": {
            "type": "string",
            "description": "The address of the store."
        },
        "entity_id": {
            "type": "string",
            "description": "The tax or business identification number of the store."
        },
        "phone": {
            "type": "string",
            "description": "The contact phone number of the store."
        },
        "date": {
            "type": "string",
            "description": "The date of the transaction."
        },
        "time": {
            "type": "string",
            "description": "The time of the transaction."
        },
        "subtotal": {
            "type": "string",
            "description": "The subtotal amount of the purchase."
        },
        "svc": {
            "type": "string",
            "description": "Service charges if applicable."
        },
        "tax": {
            "type": "string",
            "description": "The tax amount."
        },
        "total": {
            "type": "string",
            "description": "The total amount paid."
        },
        "tips": {
            "type": "string",
            "description": "The tips amount if any."
        },
        "discount": {
            "type": "string",
            "description": "Total discount applied to the transaction."
        },
        "line_items": {
            "type": "array",
            "description": "List of items purchased.",
            "items": {
                "type": "object",
                "properties": {
                    "item_key": {
                        "type": "string",
                        "description": "Unique identifier for the item."
                    },
                    "item_name": {
                        "type": "string",
                        "description": "Text description of the item."
                    },
                    "item_value": {
                        "type": "string",
                        "description": "Price of a single unit of the item."
                    },
                    "item_quantity": {
                        "type": "string",
                        "description": "Quantity of the item purchased."
                    },
                    "item_total": {
                        "type": "string",
                        "description": "Total amount charged for this purchase's item."
                    }
                }
            }
        }
    }
}
'''
                    },
                ],
            }
        ]

        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )
        inputs = inputs.to("cuda")

        # Inference: Generation of the output
        generated_ids = self.model.generate(**inputs, max_new_tokens=2048)
        generated_ids_trimmed = [
            out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        output_text = self.processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )
        json_str = output_text[0].removeprefix("```json").removesuffix("```").strip()
        try:
            json_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON: {e}")
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
    
    parser = argparse.ArgumentParser(description="Receipt reader service.")
    parser.add_argument('--logging', default='ERROR', choices=[level.lower() for level in LOG_LEVELS], help='Set logging level')
    broker = typed_messaging.PydanticMessageBroker(os.getenv('RABBITMQ_CONNECTION_STRING', 'amqp://guest:guest@localhost:5672/'))
    args = parser.parse_args()

    logging.basicConfig(level=args.logging.upper())
    
    endpoint_url = os.getenv('PURCHASES_ENDPOINT')
    if not endpoint_url:
        logging.error("Endpoint URL was not provided")
        sys.exit(1)
    
    node_token = os.getenv('IMAGE_TO_COMPRA_TOKEN')
    if not node_token:
        logging.error("Node token was not provided")
        sys.exit(1)
    
    receipt_path = os.getenv('IMAGE_TO_COMPRA_RECEIPT_PATH')
    if not receipt_path:
        logging.error("Receipt path was not provided")
        sys.exit(1)

    node = ImageToCompraNode(
        node_token,
        receipt_path,
        broker.get_consumer(), 
        broker.ensure_queue(os.getenv('IMAGE_TO_COMPRA_INPUT_QUEUE', '')), 
        endpoint_url)

    try:
        logging.info("Node succesfully initialized")
        node.start()
    except KeyboardInterrupt:
        node.stop()
        sys.exit(0)