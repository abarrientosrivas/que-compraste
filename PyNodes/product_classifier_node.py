import chromadb
import argparse
import requests
import logging
import os
import sys
from API.schemas import Category
from typing import List
from dotenv import load_dotenv

load_dotenv()

def get_vectorizable_text(category: Category) -> str:
    text = category.original_text
    if '-' in text:
        text = text.split('-', 1)[1].strip()
    else:
        text = text.strip()
    text = text.replace('>', ' ')
    text = ' '.join(text.split())
    return text

def init(file_path: str):
    category_strs: List[str] = []
    with open(file_path, 'r') as file:
        for line in file:
            category_strs.append(line.strip())

    logging.info("Requesting taxonomy synchronization")
    taxonomy_categories_endpoint = os.getenv("TAXONOMY_CATEGORIES_ENDPOINT")
    response = requests.post(taxonomy_categories_endpoint, json=category_strs)
    if response.status_code == 200:
        logging.info("Categories synchronized successfully")
    else:
        logging.error(f"Failed to synchronize categories. Status code: {response.status_code}. Server response: {response.text}")
        sys.exit(1)

    categories = []
    response = requests.get(taxonomy_categories_endpoint)
    if response.status_code == 200:
        logging.info("Categories received successfully")
        categories_data = response.json()
        categories = [Category.model_validate(cat) for cat in categories_data]
    else:
        logging.error(f"Failed to retrieve categories. Status code: {response.status_code}. Server response: {response.text}")
        sys.exit(1)
        
    ids = [str(category.code) for category in categories]
    documents = [get_vectorizable_text(category) for category in categories]
    metadatas = [category.model_dump(exclude_none=True, include={"code","name","original_text"}) for category in categories]

    logging.info("Creating taxonomy collection")
    client = chromadb.PersistentClient(path=os.getenv("TAXONOMY_CHROMA_PATH"))
    collection_name = os.getenv("TAXONOMY_CHROMA_COLLECTION", "google_taxonomy")
    try:
        client.delete_collection(collection_name)
    except:
        pass
    collection = client.create_collection(name=collection_name)

    collection.add(
        ids= ids,
        documents= documents,
        metadatas= metadatas
    )
    
    logging.info("Taxonomy collection created successfully")

def run(product_description: str):
    product_description = product_description.strip()
    if not product_description:
        raise ValueError("Product description was null or empty")

    client = chromadb.PersistentClient(path=os.getenv("TAXONOMY_CHROMA_PATH"))
    try:
        collection = client.get_collection(name=os.getenv("TAXONOMY_CHROMA_COLLECTION", "google_taxonomy"))
    except ValueError as e:
        raise ValueError(f"Could not find taxonomy collection: {e}")

    results = collection.query(
        query_texts=[product_description],
        n_results=1
    )

    print("====FOUND====")
    print(results)
    print("====TEXT=====")
    print(results['metadatas'][0][0]['original_text'])
    print("=============")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Product classifier service.")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    init_parser = subparsers.add_parser('init', help='Initialize taxonomy synchronization')
    init_parser.add_argument('file_path', type=str, help='The path to the product taxonomy text file')

    run_parser = subparsers.add_parser('run', help='Run the taxonomy service')
    run_parser.add_argument('product_description', type=str, help='Description of the product to classify')

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.command == 'init':
        init(args.file_path)
    elif args.command == 'run':
        run(args.product_description)
    else:
        parser.print_help()