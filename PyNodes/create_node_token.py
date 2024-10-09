from API.models import NodeToken
from API.database import SessionLocal
import secrets
import hashlib
import argparse

def create_node_token():
    node_token = secrets.token_hex(32)
    hashed_key = hashlib.sha256(node_token.encode()).hexdigest()
    return node_token, hashed_key

def add_node_token_to_db(name: str, view_receipts: bool = False, crawl_limit: int = 0):
    node_token_key, hashed_key = create_node_token()
    db = SessionLocal()
    node_token = NodeToken(name=name, key_hash=hashed_key, crawl_daily_limit=crawl_limit, can_view_receipt_images=view_receipts)
    db.add(node_token)
    db.commit()
    db.refresh(node_token)
    db.close()
    print(f"Node token for {name}: {node_token_key}.\nCan view receipt images: {view_receipts}.\nDaily crawl limit: {crawl_limit}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Token generator for nodes.")
    parser.add_argument('name', type=str, help="The name to store with the node token.")
    parser.add_argument('--view_receipts', action='store_true', help='Flag to allow token for receipt image viewing')
    parser.add_argument('--crawl_limit', type=int, default=0, help="Daily crawl limit for the token.")
    
    args = parser.parse_args()
    
    add_node_token_to_db(args.name, args.view_receipts, args.crawl_limit)