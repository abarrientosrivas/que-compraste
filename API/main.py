from . import schemas
from . import models
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session, noload
from sqlalchemy.exc import IntegrityError
from .dependencies import get_db
from typing import Dict, List, Optional, Union
from datetime import datetime, timezone
from PyLib import typed_messaging, purchases_tools, receipt_tools
from dotenv import load_dotenv
import logging
import os
import sys

load_dotenv()

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

PRODUCT_CODE_EXCHANGE = os.getenv("PRODUCT_CODE_EXCHANGE",'')
PRODUCT_CODE_NEW_KEY = os.getenv("PRODUCT_CODE_NEW_KEY",'')

if not PRODUCT_CODE_NEW_KEY.strip():
    logging.error("Product code output variables not provided")
    sys.exit(1)
    
ENTITY_EXCHANGE = os.getenv("ENTITY_EXCHANGE",'')
ENTITY_NEW_KEY = os.getenv("ENTITY_NEW_KEY",'')

if not ENTITY_NEW_KEY.strip():
    logging.error("Entity code output variables not provided")
    sys.exit(1)

conn = typed_messaging.PydanticMessageBroker(os.getenv('RABBITMQ_CONNECTION_STRING', 'amqp://guest:guest@localhost:5672/'))
conn.ensure_exchange(PRODUCT_CODE_EXCHANGE)
conn.ensure_exchange(ENTITY_EXCHANGE)
publisher = conn.get_publisher()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse('API/icon.ico')

@app.post("/upload/")
async def receive_ticket_image(file: UploadFile = File(...)):
    #contents = await file.read()
    #with open(f"./{file.filename}", "wb") as f:
    #    f.write(contents)
    return {"filename": file.filename}

@app.get("/reportes/total-by-category", response_model=List[Dict[str, Union[str, int]]])
async def get_total_by_category(start_date: str, end_date: str):
    categories = [
        {"name": "Cat Food", "value": 2000},
        {"name": "Art Ink", "value": 500},
        {"name": "Electronics", "value": 15000},
        {"name": "Clothing", "value": 8000},
        {"name": "Furniture", "value": 12000},
        {"name": "Health & Beauty", "value": 4000},
        {"name": "Sports & Outdoors", "value": 3000},
        {"name": "Toys & Games", "value": 2500},
        {"name": "Automotive Parts & Accessories", "value": 6000},
        {"name": "Books", "value": 1500},
        {"name": "Pet Supplies", "value": 3500},
        {"name": "Home & Garden", "value": 9000},
        {"name": "Video Games", "value": 4500},
        {"name": "Watches", "value": 7000},
        {"name": "Bags & Accessories", "value": 3000},
        {"name": "Computers", "value": 18000},
        {"name": "Kitchen Appliances", "value": 5000},
        {"name": "Musical Instruments", "value": 3500},
        {"name": "Fitness Equipment", "value": 4000},
        {"name": "Baby Products", "value": 6000},
        {"name": "Office Supplies", "value": 2000},
        {"name": "Shoes", "value": 7000},
        {"name": "Jewelry", "value": 3000},
        {"name": "Home Decor", "value": 4000},
        {"name": "Gardening Tools", "value": 2500},
        {"name": "Camping & Hiking", "value": 3500},
        {"name": "Fishing Gear", "value": 3000},
        {"name": "Luggage & Travel Gear", "value": 4500},
        {"name": "Cosmetics", "value": 2500},
        {"name": "Smart Home Devices", "value": 6000},
        {"name": "Cleaning Supplies", "value": 1500},
        {"name": "Safety Equipment", "value": 2000},
        {"name": "Mobile Accessories", "value": 3000},
        {"name": "Personal Care Appliances", "value": 2500},
        {"name": "Dietary Supplements", "value": 2000},
        {"name": "Gifts & Crafts", "value": 4000},
        {"name": "Tickets & Experiences", "value": 7000},
        {"name": "Party Supplies", "value": 1500},
        {"name": "Digital Products", "value": 3000}
    ]
    return categories

@app.get("/purchases/{id}")
async def get_purchase_by_id(id: int):
   return ({
    "store_name": "La Anonima Sucursal 167",
    "store_addr": "Chubut esq. Villarino - Puerto Madryn Provincia de Chubut",
    "entity_id": "30-50673003-8",
    "phone": "",
    "date": "16-04-24",
    "time": "18:43",
    "subtotal": "$20615.00",
    "svc": "",
    "tax": "",
    "total": "$20052.50",
    "tips": "",
    "discount": "-$562.50",
    "line_items": [
        {
            "item_key": "779940044427",
            "item_name": "LECHE LA X1L",
            "item_value": "$2000.00",
            "item_quantity": "3"
        },
        {
            "item_key": "779040048897",
            "item_name": "GREEN HILLS X25U",
            "item_value": "$1615.00",
            "item_quantity": "1"
        },
        {
            "item_key": "779851870961",
            "item_name": "AUN EN LOMITOS L",
            "item_value": "$2600.00",
            "item_quantity": "3"
        },
        {
            "item_key": "77901520190",
            "item_name": "LA VIRGINIAx25",
            "item_value": "$690.00",
            "item_quantity": "2"
        },
        {
            "item_key": "779940044495",
            "item_name": "ARVEJAS BEST x300",
            "item_value": "$785.00",
            "item_quantity": "2"
        },
        {
            "item_key": "779025001618",
            "item_name": "PAPEL HIG X12M2",
            "item_value": "$2250.00",
            "item_quantity": "1"
        }
    ]
}
)


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
    
    try:
        cuit = receipt_tools.normalize_entity_id(purchase.read_entity_identification)
        db_entity = db.query(models.Entity).filter(models.Entity.identification == cuit).first()
        if not db_entity:
            publisher.publish(ENTITY_EXCHANGE, ENTITY_NEW_KEY, schemas.EntityBase(name=purchase.read_entity_name or "", identification=cuit))
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
    )    
    db.add(db_entity)
    db.commit()
    db.refresh(db_entity)
    
    for item in purchase.items:
        product_code = purchases_tools.detect_product_code(item.read_product_key)
        db_product_code = db.query(models.ProductCode).filter(models.ProductCode.code == product_code.code, models.ProductCode.format == product_code.format).first()
        if not db_product_code:
            publisher.publish(PRODUCT_CODE_EXCHANGE, PRODUCT_CODE_NEW_KEY, product_code)

        db_item = models.PurchaseItem(
            purchase_id=db_entity.id,
            read_product_key=item.read_product_key,
            read_product_text=item.read_product_text,
            quantity=item.quantity,
            value=item.value,
            total=item.total
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
    db_entity = db.query(models.Purchase).all()
    return db_entity

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

@app.put("/products/{product_id}")
def update_product(
    product: schemas.ProductUpdate,
    db: Session = Depends(get_db),
    product_id: int = Path(..., description="The ID of the product to update")
):
    logging.info(f"Would update product with id {product_id} with category with id {product.category_id}")
    return True

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

@app.get("/{path:path}")
async def redirect_to_receipt(path: str):
    return RedirectResponse(url="/recibos/")