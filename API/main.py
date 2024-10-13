from . import schemas
from . import models
from pathlib import Path as pt
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Path, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session, noload, joinedload, selectinload
from sqlalchemy.exc import IntegrityError
from .dependencies import get_db, get_node_token, get_client_ip
from typing import Dict, List, Optional, Union
from datetime import datetime, timezone, date
from PyLib import typed_messaging, purchases_tools, receipt_tools
from dotenv import load_dotenv
from PIL import Image
from pdf2image import convert_from_bytes
import logging
import os
import hashlib
import asyncio
import io

load_dotenv()
logging.basicConfig(level=os.getenv("API_LOGGING_LEVEL",'ERROR'))

app = FastAPI()

origins = [
    "http://localhost:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

IMAGE_UPLOADS_BASE_PATH = os.getenv("IMAGE_UPLOADS_BASE_PATH",'')

PRODUCT_CODE_EXCHANGE = os.getenv("PRODUCT_CODE_EXCHANGE",'')
PRODUCT_CODE_NEW_KEY = os.getenv("PRODUCT_CODE_NEW_KEY",'')

ENTITY_EXCHANGE = os.getenv("ENTITY_EXCHANGE",'')
ENTITY_NEW_KEY = os.getenv("ENTITY_NEW_KEY",'')

PRODUCT_EXCHANGE = os.getenv("PRODUCT_EXCHANGE",'')
PRODUCT_CLASSIFY_KEY = os.getenv("PRODUCT_CLASSIFY_KEY",'')

IMAGE_TO_COMPRA_EXCHANGE = os.getenv("IMAGE_TO_COMPRA_EXCHANGE",'')
IMAGE_TO_COMPRA_INPUT_KEY = os.getenv("IMAGE_TO_COMPRA_INPUT_QUEUE",'')

SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000/")

pt(IMAGE_UPLOADS_BASE_PATH).mkdir(parents=True, exist_ok=True)

conn = typed_messaging.PydanticMessageBroker(os.getenv('RABBITMQ_CONNECTION_STRING', 'amqp://guest:guest@localhost:5672/'))
conn.ensure_exchange(PRODUCT_CODE_EXCHANGE)
conn.ensure_exchange(PRODUCT_EXCHANGE)
conn.ensure_exchange(ENTITY_EXCHANGE)
conn.ensure_exchange(IMAGE_TO_COMPRA_EXCHANGE)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/receipts/{file_path:path}")
async def serve_image_file(file_path: str, node_token: schemas.NodeToken = Depends(get_node_token)):
    if not node_token.can_view_receipt_images:
        raise HTTPException(status_code=401, detail="Current node is not authorized to view receipt images")
    full_path = os.path.join(IMAGE_UPLOADS_BASE_PATH, file_path)

    if not os.path.isfile(full_path) or not full_path.lower().endswith('.jpg'):
        raise HTTPException(status_code=404, detail="File not found or invalid")

    return FileResponse(full_path)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse('API/icon.ico')

def get_next_sequence(directory: Path, timestamp: str) -> int:
    sequence = 1
    while (directory / f"{timestamp}-{sequence}.").exists():
        sequence += 1
    return sequence

@app.post("/upload/", response_model=List[schemas.Receipt])
async def receive_receipt_files(files: List[UploadFile] = File(...), db: Session = Depends(get_db), client_ip: str = Depends(get_client_ip)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    current_time = datetime.now()
    timestamp = current_time.strftime('%Y%m%d%H%M%S')
    ip_hash = hashlib.sha256(client_ip.encode('utf-8')).hexdigest()

    year = current_time.strftime('%Y')
    month = current_time.strftime('%m')
    folder_path = pt(f"{IMAGE_UPLOADS_BASE_PATH}/{year}/{month}/{ip_hash}")
    folder_path.mkdir(parents=True, exist_ok=True)

    starting_sequence = get_next_sequence(folder_path, timestamp)
    db_receipts = []
    allowed_extensions = {"jpg", "jpeg", "png", "pdf"}

    for idx, file in enumerate(files):
        sequence = starting_sequence + idx
        filename = f"{timestamp}-{sequence}.jpg"
        file_path = folder_path / filename
        relative_path = file_path.relative_to(pt(IMAGE_UPLOADS_BASE_PATH)).as_posix()
        image_url = f"{SERVER_URL}receipts/{relative_path}"

        db_receipt = models.Receipt(
            reference_name = file.filename,
            image_url = image_url
        )
        try:
            db.add(db_receipt)
            db.commit()
            db.refresh(db_receipt)  
        except IntegrityError:
            db.rollback()
            logging.error(f"Couldn't store file '{file.filename}'. Could not create receipt due to model constraints.")
            continue

        if '.' in file.filename:
            file_extension = file.filename.split(".")[-1]
        else:
            file_extension = "bin"

        if file_extension.lower() not in allowed_extensions:
            db_receipt.error_message = f"Unsupported file type: {file_extension}"
            db_receipt.status = schemas.ReceiptStatus.FAILED
            db.commit()
            db.refresh(db_receipt)
            db_receipts.append(db_receipt)
            continue

        try:
            file_content = await file.read()
        except Exception as e:
            db_receipt.error_message = f"Failed to read {file.filename}: {str(e)}"
            db_receipt.status = schemas.ReceiptStatus.FAILED
            db.commit()
            db.refresh(db_receipt)
            db_receipts.append(db_receipt)
            continue
        finally:
            await file.close()

        try:
            if file_extension.lower() in {'jpg', 'jpeg', 'png'}:
                image = await asyncio.to_thread(Image.open, io.BytesIO(file_content))
                image = image.convert('RGB')
                image.save(file_path, format='JPEG')
            elif file_extension.lower() == 'pdf':
                images = convert_from_bytes(file_content)
                image = images[0]
                image.save(file_path, format='JPEG')
            else:
                db_receipt.error_message = f"Unsupported file type: {file_extension}"
                db_receipt.status = schemas.ReceiptStatus.FAILED
                db.commit()
                db.refresh(db_receipt)
                db_receipts.append(db_receipt)
                continue

        except Exception as e:
            db_receipt.error_message = f"Failed to upload {file.filename}: {str(e)}"
            db_receipt.status = schemas.ReceiptStatus.FAILED
            db.commit()
            db.refresh(db_receipt)
            db_receipts.append(db_receipt)
            continue

        db_receipts.append(db_receipt)
    
    with conn.get_publisher() as publisher:
        for db_receipt in db_receipts:
            if db_receipt.status == schemas.ReceiptStatus.FAILED:
                continue
            db_receipt.status = schemas.ReceiptStatus.WAITING
            db.commit()
            db.refresh(db_receipt)
            try:
                receipt = schemas.Receipt.model_validate(db_receipt)
                publisher.publish(IMAGE_TO_COMPRA_EXCHANGE, IMAGE_TO_COMPRA_INPUT_KEY, receipt)
            except Exception as e:
                db_receipt.error_message = f"Failed to publish '{db_receipt.reference_name}': {str(e)}"
                db_receipt.status = schemas.ReceiptStatus.FAILED
                db.commit()
                db.refresh(db_receipt)
                continue

    return db_receipts

@app.get("/reportes/total-by-category", response_model=List[Dict[str, Union[str, int]]])
async def get_total_by_category(start_date: str, end_date: str):
    categories = [
        {
            "name": "Electrónica",
            "value": 5459
        },
        {
            "name": "Redes",
            "value": 3425
        },
        {
            "name": "Dispositivos portátiles",
            "value": 298
        },
        {
            "name": "Vídeo",
            "value": 4570
        },
        {
            "name": "Sistemas de navegación GPS",
            "value": 339
        },
        {
            "name": "Deportes y aire libre",
            "value": 278
        },
        {
            "name": "Hogar y jardín",
            "value": 3539
        },
        {
            "name": "Ropa y accesorios",
            "value": 5256
        },
        {
            "name": "Suministros de oficina",
            "value": 2027
        },
        {
            "name": "Videoconsolas",
            "value": 1294
        }
    ]
    return categories

@app.get("/purchases/{purchase_id}", response_model=schemas.Purchase)
def get_purchase_by_id(purchase_id: int, db: Session = Depends(get_db)):
    purchase = db.query(models.Purchase).filter(models.Purchase.id == purchase_id).first()

    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")

    return purchase


@app.post("/purchases/", response_model=schemas.Purchase)
def create_purchase(purchase: schemas.PurchaseCreate, db: Session = Depends(get_db)):
    purchase.items = [
        item for item in purchase.items
        if not all(
            getattr(item, field) is None
            for field in [
                'total',
                'value',
                'quantity',
                'read_product_key',
                'read_product_text'
            ]
        )
    ]

    calculated_total = purchases_tools.calculate_purchase_total(purchase, purchase.items)
    calculated_date = purchase.date or datetime.now(timezone.utc)

    if calculated_total is None:
        raise HTTPException(
            status_code=400,
            detail="The purchase's total could not be calculated."
        )

    with conn.get_publisher() as publisher:
        entity_id = None
        try:
            cuit = receipt_tools.normalize_entity_id(purchase.read_entity_identification)
            db_entity = db.query(models.Entity).filter(models.Entity.identification == cuit).first()
            if not db_entity:
                publisher.publish(ENTITY_EXCHANGE, ENTITY_NEW_KEY, schemas.EntityBase(name=purchase.read_entity_name or "", identification=cuit))
            else:
                entity_id = db_entity.id
        except:
            pass

        db_entity = models.Purchase(
            read_entity_name=purchase.read_entity_name,
            read_entity_branch=purchase.read_entity_branch,
            read_entity_location=purchase.read_entity_location,
            read_entity_address=purchase.read_entity_address,
            read_entity_identification=purchase.read_entity_identification,
            read_entity_phone=purchase.read_entity_phone,
            date = calculated_date,
            subtotal = purchase.subtotal,
            discount = purchase.discount,
            tips = purchase.tips,
            total = calculated_total,
            entity_id = entity_id
        )
        db.add(db_entity)
        db.commit()
        db.refresh(db_entity)

        for item in purchase.items:
            product_id = None

            if item.read_product_key:
                product_code = purchases_tools.detect_product_code(item.read_product_key)
                db_product_code = db.query(models.ProductCode).filter(models.ProductCode.code == product_code.code, models.ProductCode.format == product_code.format).first()
                if not db_product_code:
                    publisher.publish(PRODUCT_CODE_EXCHANGE, PRODUCT_CODE_NEW_KEY, product_code)
                else:
                    product_id = db_product_code.product_id

            db_item = models.PurchaseItem(
                purchase_id=db_entity.id,
                read_product_key=item.read_product_key,
                read_product_text=item.read_product_text,
                quantity=item.quantity,
                value=item.value,
                total=item.total,
                product_id = product_id
            )
            db.add(db_item)

        db.commit()
        db.refresh(db_entity)
    return db_entity

@app.put("/purchases/{purchase_id}", response_model=schemas.Purchase)
def update_purchase(
    purchase: schemas.PurchaseUpdate,
    db: Session = Depends(get_db),
    purchase_id: int = Path(..., description="The ID of the purchase to update")
):
    db_purchase = db.query(models.Purchase).filter(models.Purchase.id == purchase_id).first()
    if not db_purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")

    purchase_data = purchase.model_dump(exclude_unset=True)
    if "total" in purchase_data and purchase_data["total"] is None:
        purchase_data["total"] = purchases_tools.calculate_purchase_total(purchase, db_purchase.items)
        if purchase_data["total"] is None:
            raise HTTPException(status_code=400, detail="The purchase's total could not be calculated.")

    for key, value in purchase_data.items():
        setattr(db_purchase, key, value)

    db.commit()
    db.refresh(db_purchase)
    return db_purchase

@app.get("/purchases/", response_model=List[schemas.Purchase])
def get_purchases(db: Session = Depends(get_db)):
    purchases = db.query(models.Purchase).options(
        noload(models.Purchase.entity),
        selectinload(models.Purchase.items).options(
            noload(models.PurchaseItem.product)
        )
    ).all()
    return purchases

@app.put("/purchase_items/{purchase_item_id}", response_model=schemas.PurchaseItem)
def update_purchase_item(
    purchase_item: schemas.PurchaseItemUpdate,
    db: Session = Depends(get_db),
    purchase_item_id: int = Path(..., description="The ID of the purchase item to update")
):
    db_purchase_item = db.query(models.PurchaseItem).filter(models.PurchaseItem.id == purchase_item_id).first()
    if not db_purchase_item:
        raise HTTPException(status_code=404, detail="Purchase item not found")

    purchase_item_data = purchase_item.model_dump(exclude_unset=True)

    for key, value in purchase_item_data.items():
        setattr(db_purchase_item, key, value)

    db.commit()
    db.refresh(db_purchase_item)
    return db_purchase_item

def category_from_string(category_str: str) -> models.Category | None:
    category_str = category_str.strip()
    if not category_str:
        return None
    code_str = category_str.split('-')[0].strip()
    if '>' in category_str:
        name = category_str.split('>').pop().strip()
    else:
        name = category_str.split('-')[1].strip()
    if code_str and name and code_str.isdigit():
        code = int(code_str)
        return models.Category(code=code, name=name, original_text=category_str)
    return None

@app.post("/product_codes/", response_model=schemas.ProductCode)
def create_product_code(product_code: schemas.ProductCodeCreate, db: Session = Depends(get_db)):
    with conn.get_publisher() as publisher:
        db_product = models.Product(
            title=product_code.product.title,
            description=product_code.product.description,
            read_category=product_code.product.read_category,
        )
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        publisher.publish(PRODUCT_EXCHANGE, PRODUCT_CLASSIFY_KEY, schemas.Product.model_validate(db_product))

    db_entity = models.ProductCode(
        product_id=db_product.id,
        format=product_code.format,
        code=product_code.code,
    )
    try:
        db.add(db_entity)
        db.commit()
        db.refresh(db_entity)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Could not create establishment due to model constraints.")

    purchase_items_to_update = db.query(models.PurchaseItem).filter(
            models.PurchaseItem.product_id.is_(None),
            models.PurchaseItem.read_product_key == db_entity.code
        ).all()

    for item in purchase_items_to_update:
        item.product_id = db_entity.product_id
        db.add(item)

    db.commit()

    return db_entity

@app.get("/product_codes/", response_model=List[schemas.ProductCode], response_model_exclude_none=True)
def get_product_codes(lookahead: Optional[str] = None, format: Optional[str] = None, code: Optional[str] = None, db: Session = Depends(get_db)):
    if lookahead is not None and len(lookahead) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lookahead must be at least 3 characters long"
        )
    query = db.query(models.ProductCode).options(
        joinedload(models.ProductCode.product).joinedload(models.Product.category).options(
            noload(models.Category.children),
            noload(models.Category.parent)
        )
    )
    if lookahead is not None:
        query = query.filter(models.ProductCode.code.like(f"{lookahead}%"))
    if format is not None:
        query = query.filter(models.ProductCode.format == format)
    if code is not None:
        query = query.filter(models.ProductCode.code == code)
    entities = query.all()
    return entities

@app.get("/products/{product_id}", response_model=schemas.Product)
def get_product_by_id(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product

@app.put("/products/{product_id}", response_model=schemas.Product)
def update_product(
    product: schemas.ProductUpdate,
    db: Session = Depends(get_db),
    product_id: int = Path(..., description="The ID of the product to update")
):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    product_data = product.model_dump(exclude_unset=True, exclude_none=True)

    for key, value in product_data.items():
        setattr(db_product, key, value)

    try:
        db.commit()
        db.refresh(db_product)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Could not update product due to model constraints.")
    return db_product

@app.post("/categories/")
def set_categories(categories: List[str], db: Session = Depends(get_db)):
    try:
        with db.begin():
            existing_categories = db.query(models.Category).with_for_update().all()
            categories_by_code = {category.code: category for category in existing_categories}
            categories_by_string = {
                category.original_text.split('-', 1)[1].strip(): category for category in existing_categories if '-' in category.original_text
            }

            for category_str in categories:
                category = category_from_string(category_str)
                if not category:
                    continue

                existing = categories_by_code.get(category.code)
                if existing:
                    categories_by_string.pop(existing.original_text.split('-', 1)[1].strip())
                    existing.name = category.name
                    existing.description = category.description
                    existing.original_text = category.original_text
                    category = existing
                    categories_by_string[category.original_text.split('-', 1)[1].strip()] = category
                else:
                    db.add(category)
                    categories_by_code[category.code] = category
                    categories_by_string[category.original_text.split('-', 1)[1].strip()] = category

                if " > " in category_str:
                    parent_str = category_str.split('-', 1)[1].strip()
                    parent_str = parent_str.rsplit(' > ', 1)[0].strip()
                    parent_category = categories_by_string.get(parent_str)
                    if parent_category:
                        category.parent = parent_category

            db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error processing categories: {str(e)}")

@app.get("/categories/", response_model=List[schemas.Category], response_model_exclude_none=True)
def get_categories(code: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Category).options(
        noload(models.Category.children),
        noload(models.Category.parent)
    )
    if code is not None:
        query = query.filter(models.Category.code == code)
    entities = query.all()
    return entities

@app.get("/establishments/", response_model=List[schemas.Establishment])
def get_establishments(db: Session = Depends(get_db)):
    db_entity = db.query(models.Establishment).all()
    return db_entity

@app.post("/establishments/", response_model=schemas.Establishment)
def create_establishment(establishment: schemas.EstablishmentCreate, db: Session = Depends(get_db)):
    db_entity = models.Establishment(
        entity_id = establishment.entity_id,
        name = establishment.name,
        location = establishment.location,
        address = establishment.address
    )
    try:
        db.add(db_entity)
        db.commit()
        db.refresh(db_entity)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Could not create establishment due to model constraints.")
    return db_entity

@app.post("/entities/", response_model=schemas.Entity)
def create_entity(entity: schemas.EntityCreate, db: Session = Depends(get_db)):
    db_entity = models.Entity(
        name = entity.name,
        identification = entity.identification,
        email = entity.email,
        address = entity.address,
        phone = entity.phone,
    )
    try:
        db.add(db_entity)
        db.commit()
        db.refresh(db_entity)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Could not create establishment due to model constraints.")

    purchases_to_update = db.query(models.Purchase).filter(
            models.Purchase.entity_id.is_(None),
            func.regexp_replace(models.Purchase.read_entity_identification, '[^0-9]', '', 'g') == str(db_entity.identification)
        ).all()

    for item in purchases_to_update:
        item.entity_id = db_entity.id
        db.add(item)

    db.commit()

    return db_entity

@app.get("/entities/{entities_id}", response_model=schemas.Entity)
def get_product_by_id(entities_id: int, db: Session = Depends(get_db)):
    entity = db.query(models.Entity).filter(models.Entity.id == entities_id).first()

    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    return entity

@app.get("/entities/", response_model=List[schemas.Entity], response_model_exclude_none=True)
def get_categories(identification: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(models.Entity)
    if identification is not None:
        query = query.filter(models.Entity.identification == identification)
    entities = query.all()
    return entities

@app.post("/node_tokens/authorize_crawl")
def get_crawl_authorization(node_token: schemas.NodeToken = Depends(get_node_token), db: Session = Depends(get_db)):
    today = date.today()

    if node_token.crawl_daily_limit <= 0:
        raise HTTPException(status_code=401, detail="Node Token not valid for crawling")

    crawl_counter = db.query(models.CrawlCounter).filter_by(
        node_token_id=node_token.id,
        date=today
    ).first()

    if crawl_counter is None:
        crawl_counter = models.CrawlCounter(
            node_token_id=node_token.id
        )
        db.add(crawl_counter)
        db.commit()

    if crawl_counter.uses >= node_token.crawl_daily_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Crawl limit reached for today"
        )

    crawl_counter.uses += 1
    db.commit()

    return {"status": "Authorized", "uses_today": crawl_counter.uses}
