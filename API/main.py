from . import schemas
from . import models
from fastapi import FastAPI, Depends, HTTPException, Path
from sqlalchemy.orm import Session, noload
from .dependencies import get_db
from typing import List, Optional
from datetime import datetime, timezone
import logging

def calculate_purchase_total(purchase: schemas.PurchaseBase, items: List[schemas.PurchaseItemBase]) -> float | None:    
    if purchase.total is not None:
        return purchase.total
    if purchase.subtotal is not None:
        discount = purchase.discount or 0
        tips = purchase.tips or 0
        return purchase.subtotal - discount - tips
    if items:
        total_from_items = 0
        empty_flag = True
        for item in items:
            if item.total is not None:
                empty_flag = False
                total_from_items += item.total
            elif item.value is not None:
                empty_flag = False
                quantity_mod = item.quantity or 1
                total_from_items += item.value * quantity_mod
        if not empty_flag:
            return total_from_items
    return None

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

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
    
    calculated_total = calculate_purchase_total(purchase, purchase.items)
    calculated_date = purchase.date or datetime.now(timezone.utc)

    if calculated_total is None:
        raise HTTPException(
            status_code=400,
            detail="The purchase's total could not be calculated."
        )

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
        purchase_data["total"] = calculate_purchase_total(purchase, db_purchase.items)
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
def update_purchase_item(
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