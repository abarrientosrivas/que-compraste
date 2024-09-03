import torch
import json
import os
import logging
from PIL import Image
from pydantic import BaseModel
from pydantic import ValidationError
from json.decoder import JSONDecodeError
from transformers import DonutProcessor, VisionEncoderDecoderModel
from PyMessaging.typed_messaging import PydanticMessageBroker, PydanticExchangePublisher, PydanticQueueConsumer
from dotenv import load_dotenv

load_dotenv()

class ImageLocation(BaseModel):
    path: str

def load_and_preprocess_image(image_path: str, processor):
    """
    Load an image and preprocess it for the model.
    """
    image = Image.open(image_path).convert("RGB")
    pixel_values = processor(image, return_tensors="pt").pixel_values
    return pixel_values

class ImageToCompraNode:
    def __init__(self, consumer: PydanticQueueConsumer, publisher: PydanticExchangePublisher, input_queue: str):
        self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        self.processor = DonutProcessor.from_pretrained("AdamCodd/donut-receipts-extract")
        self.model = VisionEncoderDecoderModel.from_pretrained("AdamCodd/donut-receipts-extract")
        self.model.to(self.device)
        self.consumer = consumer
        self.publisher = publisher
        self.input_queue = input_queue

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
        result = self.read_receipt_image(message.path)
        json_result = json.dumps(result, indent=4)
        print(json_result)
        
    def error_callback(self, error: Exception):        
        if isinstance(error, JSONDecodeError):
            logging.error(f"Could not decode message: {error}")
        elif isinstance(error, ValidationError):
            logging.error(f"Received message was not of type ImageLocation: {error}")
        elif isinstance(error, FileNotFoundError):
            logging.error(f"Indicated file was not found: {error}")
        else:
            logging.error(f"An unexpected error occurred: {error}")
        
    def start(self):
        self.consumer.start(self.input_queue, self.callback, ImageLocation, self.error_callback)

    def stop(self):
        self.consumer.stop()

if __name__ == '__main__':
    broker = PydanticMessageBroker(os.getenv('RABBITMQ_CONNECTION_STRING', 'amqp://guest:guest@localhost:5672/'))

    node = ImageToCompraNode(broker.get_consumer(), broker.get_publisher(), broker.ensure_queue(os.getenv('IMAGE_TO_COMPRA_INPUT_QUEUE', '')))
    try:
        node.start()
    except KeyboardInterrupt:
        node.stop()