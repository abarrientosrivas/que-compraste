from donut_dataset_builder import generate_dataset
from donut_upload import upload_dataset
from dotenv import load_dotenv
from huggingface_hub import HfFolder
import os
import sys

load_dotenv()
hf_token = os.getenv('HF_TOKEN')
if hf_token is None or not hf_token.strip():
    print(f"No Hugging Face token was provided")
    sys.exit(1)
HfFolder.save_token(hf_token)

generate_dataset(
    "E:\\Recibos\\json",
    "E:\\Recibos\\img",
    "E:\\Recibos\\demo")

upload_dataset("E:\\Recibos\\demo","abarrientosrivas/dataset-demo")