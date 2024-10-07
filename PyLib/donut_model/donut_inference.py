import logging
import torch
import PyLib.receipt_tools as rt
from PyLib import request_tools
from transformers import DonutProcessor, VisionEncoderDecoderModel
from API.schemas import PurchaseCreate, PurchaseItemCreate
from PIL import Image
from io import BytesIO

def convert_data_to_purchase(json_data: dict) -> PurchaseCreate:
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
        read_entity_identification= str(entity_id),
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

class DonutInference:
    def __init__(self, model_path: str):
        self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        self.processor = DonutProcessor.from_pretrained(model_path)
        self.model = VisionEncoderDecoderModel.from_pretrained(model_path)
        self.model.to(self.device)

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
    
    def load_and_preprocess_local_image(self, image_path: str):
        """
        Load an image and preprocess it for the model.
        """
        image = Image.open(image_path).convert("RGB")
        pixel_values = self.processor(image, return_tensors="pt").pixel_values
        return pixel_values

    def load_and_preprocess_remote_image(self, image_url: str, node_token: str):
        """
        Load an image from a URL and preprocess it for the model.
        """
        headers = {
            "Authorization": f"Bearer {node_token}"
        }
        response = request_tools.send_request_with_retries('get', image_url, headers= headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to load image from URL: {response.status_code}")
        
        image = Image.open(BytesIO(response.content)).convert("RGB")
        pixel_values = self.processor(image, return_tensors="pt").pixel_values
        return pixel_values
        
