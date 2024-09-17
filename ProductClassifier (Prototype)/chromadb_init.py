from pydantic import BaseModel
from typing import List
import chromadb

class Category(BaseModel):
    code: int
    name: str
    full_text: str

def get_categories_from_file(file_path: str) -> List[Category]:
    categories: List[Category] = []
    with open(file_path, 'r') as file:
        for line in file:
            full_text = line.strip()
            if full_text:
                code_str = line.split('-')[0].strip()
                name = line.split('>').pop().strip()
                if code_str and name and code_str.isdigit():
                    code = int(code_str)
                    categories.append(Category(code=code, name=name, full_text=full_text))
    return categories

def get_vectorizable_text(category: Category) -> str:
    text = category.full_text
    if '-' in text:
        text = text.split('-', 1)[1].strip()
    else:
        text = text.strip()
    text = text.replace('>', ' ')
    text = ' '.join(text.split())
    return text

client = chromadb.PersistentClient(path="ProductClassifier (Prototype)")
collection = client.create_collection(name="google_taxonomy_en_us")

categories = get_categories_from_file("ProductClassifier (Prototype)\\taxonomy-with-ids.en-US.txt")

ids = [str(category.code) for category in categories]
documents = [get_vectorizable_text(category) for category in categories]
metadatas = [category.model_dump() for category in categories]

collection.add(
    ids= ids,
    documents= documents,
    metadatas= metadatas
)

collection = client.create_collection(name="google_taxonomy_es_es")

categories = get_categories_from_file("ProductClassifier (Prototype)\\taxonomy-with-ids.es-ES.txt")

ids = [str(category.code) for category in categories]
documents = [get_vectorizable_text(category) for category in categories]
metadatas = [category.model_dump() for category in categories]

collection.add(
    ids= ids,
    documents= documents,
    metadatas= metadatas
)