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
from dotenv import load_dotenv
from huggingface_hub import HfFolder
from transformers import Qwen2VLForConditionalGeneration, AutoTokenizer, AutoProcessor
from qwen_vl_utils import process_vision_info

load_dotenv()
hf_token = os.getenv('HF_TOKEN')
if hf_token is None or not hf_token.strip():
    logging.error(f"No Hugging Face token was provided")
    raise
HfFolder.save_token(hf_token)

class ImageToCompraNode:
    def __init__(self, consumer: typed_messaging.PydanticQueueConsumer, publisher: typed_messaging.PydanticExchangePublisher, input_queue: str, output_endpoint: str):
        self.consumer = consumer
        self.publisher = publisher
        self.input_queue = input_queue
        self.output_endpoint = output_endpoint
        self.stop_event = threading.Event()
        self.model = Qwen2VLForConditionalGeneration.from_pretrained(
            "Qwen/Qwen2-VL-7B-Instruct", torch_dtype="auto", device_map="auto"
            )
        self.processor = AutoProcessor.from_pretrained("Qwen/Qwen2-VL-7B-Instruct")
    
    def callback(self, message: ReceiptImageLocation):
        if message.path.strip():
            logging.info(f"Processing image with path: {message.path}")
        elif message.url.strip():
            logging.info(f"Processing image with url: {message.url}")
        else:
            logging.warning("Received an empty message. Skipping...")
            return
        
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": message.path,
                    },
                    {"type": "text", "text": "Describe this image."},
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
        generated_ids = self.model.generate(**inputs, max_new_tokens=128)
        generated_ids_trimmed = [
            out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        output_text = self.processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )
        print(output_text)

        # json_data = self.donut.read_receipt_image(pixel_values)
        # if not json_data or not isinstance(json_data, dict):
        #     logging.error("Could not generate proper JSON from image")
        #     return
        # purchase = convert_data_to_purchase(json_data)
        # purchase_data = purchase.model_dump(mode='json')

        # response =  request_tools.send_request_with_retries("post", self.output_endpoint, purchase_data, stop_event= self.stop_event)
        # if response.status_code == 200:
        #     logging.info("Purchase created successfully")
        # else:
        #     logging.error(f"Failed to create purchase. Status code: {response.status_code}. Server response: {response.text}")
        
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