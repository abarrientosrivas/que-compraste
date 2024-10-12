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
        self.vea_receipt_path = os.path.abspath(".\\PyNodes\\qwen_assets\\recibo_vea.jpg")
        self.chango_receipt_path = os.path.abspath(".\\PyNodes\\qwen_assets\\recibo_chango.jpg")
        
        if not os.path.exists(self.vea_receipt_path):
            raise FileNotFoundError("Image receipt for Vea does not exist")
        
        if not os.path.exists(self.chango_receipt_path):
            raise FileNotFoundError("Image receipt for Chango Mas does not exist")
    
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
                "role": "system",
                "content": [
                    {
                        "type": "text", 
                        "text": 
'''When you receive an image, return it's text as clean JSON (and only JSON) under the following schema:
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
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": self.vea_receipt_path,
                    },
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": 
'''```json
{
  "store_name": "Vea Puerto Madryn",
  "store_addr": "Dr. Manuel Belgrano 372 Puerto Madryn Chubut",
  "entity_id": "30590360763",
  "phone": null,
  "date": "16/09/2024",
  "time": "16:56:57",
  "subtotal": "23.966,00",
  "svc": null,
  "tax": null,
  "total": "18.848,10",
  "tips": null,
  "discount": "-5.117,90",
  "line_items": [
    {
      "item_key": "7790250057048",
      "item_name": "rolcocSUSSEX200p",
      "item_value": "2.550,00",
      "item_quantity": "2",
      "item_total": "5.100,00"
    },
    {
      "item_key": "7790250054344",
      "item_name": "pandescfaELITEx90p",
      "item_value": "1.650,00",
      "item_quantity": "1",
      "item_total": "1.650,00"
    },
    {
      "item_key": "7790250097587",
      "item_name": "toafemLSOF",
      "item_value": "2.500,00",
      "item_quantity": "2",
      "item_total": "5.000,00"
    },
    {
      "item_key": "7793670000052",
      "item_name": "Yer VERDEFLORx500g",
      "item_value": "2.000,00",
      "item_quantity": "2",
      "item_total": "4.000,00"
    },
    {
      "item_key": "7797470199121",
      "item_name": "PurtomMAROLIO520",
      "item_value": "686,00",
      "item_quantity": "6",
      "item_total": "4.116,00"
    },
    {
      "item_key": "7798085681537",
      "item_name": "J.Citric Man 1L",
      "item_value": "4.100,00",
      "item_quantity": "1",
      "item_total": "4.100,00"
    }
  ]
}
```'''
                    },
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": self.chango_receipt_path,
                    },
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": 
'''```json
{
  "store_name": "Chango Más",
  "store_addr": "JUAN B. JUSTO 1855, PUERTO MADRYN (9120) - CHUBUT",
  "entity_id": "30-67813830-0",
  "phone": null,
  "date": "21/09/2024",
  "time": "21:34:38",
  "subtotal": null,
  "svc": null,
  "tax": null,
  "total": "23446.03",
  "tips": null,
  "discount": "6997.60",
  "line_items": [
    {
      "item_key": "0000000040112",
      "item_name": "BANANA",
      "item_value": "1989.00",
      "item_quantity": "1.190",
      "item_total": "2366.91"
    },
    {
      "item_key": "0000000042253",
      "item_name": "PALTA HASS",
      "item_value": "3999.00",
      "item_quantity": "0.845",
      "item_total": "3379.16"
    },
    {
      "item_key": "0000000044332",
      "item_name": "LIMON",
      "item_value": "1699.00",
      "item_quantity": "0.955",
      "item_total": "1622.55"
    },
    {
      "item_key": "7798119220183",
      "item_name": "SPEED",
      "item_value": "2206,00",
      "item_quantity": "3",
      "item_total": "6618.00"
    },
    {
      "item_key": "0000000002851",
      "item_name": "MAS CLUB",
      "item_value": null,
      "item_quantity": null,
      "item_total": "0.01"
    },
    {
      "item_key": "7798153719339",
      "item_name": "CHEK MARI SALV 220G",
      "item_value": null,
      "item_quantity": null,
      "item_total": "1343.00"
    },
    {
      "item_key": "7790380016687",
      "item_name": "GEORGALOS BANO REPOS",
      "item_value": "4143.00",
      "item_quantity": "2",
      "item_total": "8286.00"
    },
    {
      "item_key": "7799120000818",
      "item_name": "CHECK ANANA EN TROZO",
      "item_value": null,
      "item_quantity": null,
      "item_total": "2687.00"
    },
    {
      "item_key": "7799120004182",
      "item_name": "CHECK LARGUITA 150G",
      "item_value": "1399.00",
      "item_quantity": "2",
      "item_total": "2798.00"
    }
  ]
}
```'''
                    },
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": receipt_path,
                    },
                ]
            },
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