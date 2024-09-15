from . import schemas
from . import models
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .dependencies import get_db
from typing import List

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/purchases/", response_model=schemas.Purchase)
def create_entity(purchase: schemas.PurchaseCreate, db: Session = Depends(get_db)):
    db_entity = models.Purchase(
        read_entity_name=purchase.read_entity_name,
        read_entity_branch=purchase.read_entity_branch,
        read_entity_location=purchase.read_entity_location,
        read_entity_address=purchase.read_entity_address,
        read_entity_identification=purchase.read_entity_identification,
        read_entity_phone=purchase.read_entity_phone,
        date = purchase.date,
        subtotal = purchase.subtotal,
        discount = purchase.discount,
        tips = purchase.tips,
        total = purchase.total,
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
def read_entity(db: Session = Depends(get_db)):
    db_entity = db.query(models.Purchase).all()
    return db_entity