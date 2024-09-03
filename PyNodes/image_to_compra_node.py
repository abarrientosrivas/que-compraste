import torch
import argparse
import json
import os
from PIL import Image
from transformers import DonutProcessor, VisionEncoderDecoderModel

def load_and_preprocess_image(image_path: str, processor):
    """
    Load an image and preprocess it for the model.
    """
    image = Image.open(image_path).convert("RGB")
    pixel_values = processor(image, return_tensors="pt").pixel_values
    return pixel_values

class ImageToCompraNode:
    def __init__(self):
        self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        self.processor = DonutProcessor.from_pretrained("AdamCodd/donut-receipts-extract")
        self.model = VisionEncoderDecoderModel.from_pretrained("AdamCodd/donut-receipts-extract")
        self.model.to(self.device)

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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process an image of a receipt.')
    parser.add_argument('image_path', type=str, help='The path of the receipt image file')
    args = parser.parse_args()

    node = ImageToCompraNode()
    result = node.read_receipt_image(args.image_path)
    print(result)
    print("")
    
    base_name, _ = os.path.splitext(args.image_path)
    output_file = f"{base_name}.json"
    with open(output_file, 'w') as json_file:
        json.dump(result, json_file, indent=4)
    
    print(f"Result saved to {output_file}")