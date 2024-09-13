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
        establishment_id = purchase.establishment_id,
        date = purchase.date,
        subtotal = purchase.subtotal,
        discount = purchase.discount,
        total = purchase.total,
        currency_id = purchase.currency_id,
    )
    db.add(db_entity)
    db.commit()
    db.refresh(db_entity)
    return db_entity

@app.get("/purchases/", response_model=List[schemas.Purchase])
def read_entity(db: Session = Depends(get_db)):
    db_entity = db.query(models.Purchase).all()
    return db_entity