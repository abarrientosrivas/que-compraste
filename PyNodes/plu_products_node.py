import argparse
import logging
import threading
import os
import sys
import pandas as pd
from PyLib import request_tools
from API.schemas import ProductCodeCreate, ProductCreate
from dotenv import load_dotenv

load_dotenv()

class ProductFinderNode:
    def __init__(self, product_codes_endpoint: str, plu_csv_path: str):
        self.product_codes_endpoint = product_codes_endpoint
        self.plu_csv_path = plu_csv_path
        self.stop_event = threading.Event()

    def start(self):
        try:
            df = pd.read_csv(self.plu_csv_path)
            logging.info("CSV file loaded successfully.")
        except FileNotFoundError:
            logging.error(f"CSV file not found at path: {self.plu_csv_path}")
            sys.exit(1)
        
        product_codes = []
        for _, row in df.iterrows():
            if not row['Plu'] or not row['Commodity']:
                continue
            description = ", ".join(
                str(value) for value in [
                    row['Variety'],
                    row['Size'],
                    row['Measures_row'],
                    row['Measures_na'],
                    row['Botanical']
                ] if pd.notna(value)
            )
            
            product = ProductCreate(
                title=row['Commodity'],
                description=description,
                read_category=row['Category']
            )
            
            product_code = ProductCodeCreate(
                format="plu",
                code=str(row['Plu']),
                product=product
            )
            product_codes.append(product_code)
        
        logging.info(f"{len(product_codes)} PLU products read.")
        product_code_jsons = [pc.model_dump(mode='json') for pc in product_codes]
        
        response = request_tools.send_request_with_retries("post", f"{self.product_codes_endpoint}bulk", product_code_jsons, stop_event=self.stop_event)
        if response is None:
            logging.error(f"There was no response from server")
        if response.status_code == 200:
            logging.info(f"Products created successfully")
        else:
            logging.error(f"Failed to create products. Status code: {response.status_code}. Server response: {response.text}")

if __name__ == '__main__':
    LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'FATAL']

    parser = argparse.ArgumentParser(description="Product data retriever service.")
    parser.add_argument('--logging', default='ERROR', choices=[level.lower() for level in LOG_LEVELS], help='Set logging level')
    args = parser.parse_args()

    logging.basicConfig(level=args.logging.upper())
    
    product_codes_endpoint = os.getenv('PRODUCT_CODES_ENDPOINT','')
    if not product_codes_endpoint.strip():
        logging.error("Product codes endpoint was not provided")
        sys.exit(1)
    
    plu_csv_path = os.getenv('PLU_CSV_PATH','')
    if not plu_csv_path.strip():
        logging.error("Path to plu products csv file was not provided")
        sys.exit(1)

    node = ProductFinderNode(product_codes_endpoint, plu_csv_path)

    try:
        logging.info("Node succesfully initialized")
        node.start()
    except KeyboardInterrupt:
        logging.info("Shutdown initiated by user (Ctrl+C)")