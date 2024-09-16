from . import schemas
from . import models
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .dependencies import get_db
from typing import List
from datetime import datetime, UTC

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/purchases/", response_model=schemas.Purchase)
def create_purchase(purchase: schemas.PurchaseCreate, db: Session = Depends(get_db)):
    calculated_total = purchase.total
    calculated_date = purchase.date or datetime.now(UTC)

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

    if not calculated_total:
        if purchase.subtotal:
            discount = purchase.discount or 0
            tips = purchase.tips or 0
            calculated_total = purchase.subtotal - discount - tips
        elif purchase.items:
            total_from_items = 0
            empty_flag = True
            for item in purchase.items:
                if item.total is not None:
                    empty_flag = False
                    total_from_items += item.total
                elif item.value is not None:
                    empty_flag = False
                    quantity_mod = item.quantity or 1
                    total_from_items += item.value * quantity_mod
            if not empty_flag:
                calculated_total = total_from_items
    
    if calculated_total is None:
        raise HTTPException(
            status_code=400,
            detail="The purchase total could not be calculated."
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

@app.get("/purchases/", response_model=List[schemas.Purchase])
def get_purchases(db: Session = Depends(get_db)):
    db_entity = db.query(models.Purchase).all()
    return db_entity