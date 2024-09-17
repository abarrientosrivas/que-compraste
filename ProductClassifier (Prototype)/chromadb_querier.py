import chromadb
import argparse

def main():
    parser = argparse.ArgumentParser(description="Query ChromaDB with a product description.")
    parser.add_argument('query', type=str, help='The product description to query.')
    parser.add_argument('--lang', type=str, choices=['en', 'es'], default='en', help='Language of the taxonomy to query (en or es).')

    args = parser.parse_args()
    query_text = args.query
    language = args.lang

    client = chromadb.PersistentClient(path="ProductClassifier (Prototype)")
    if language == 'en':
        collection = client.get_collection(name="google_taxonomy_en_us")
    elif language == 'es':
        collection = client.get_collection(name="google_taxonomy_es_es")
    else:
        print("Unsupported language.")
        return
    results = collection.query(
        query_texts=[query_text],
        n_results=1
    )

    print("Query Result:")
    for id_list, metadata_list, distance_list in zip(results['ids'], results['metadatas'], results['distances']):
        for id, metadata, distance in zip(id_list, metadata_list, distance_list):
            print(f"ID: {id}")
            print(f"Metadata: {metadata}")
            print(f"Distance: {distance}")
            print("---")

if __name__ == '__main__':
    main()