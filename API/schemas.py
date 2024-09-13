from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# --------------------
# Entity Schemas
# --------------------
class EntityBase(BaseModel):
    identification_number: int
    name: str

    class Config:
        orm_mode = True


class EntityCreate(EntityBase):
    pass


class Entity(EntityBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime] = None


# --------------------
# Establishment Schemas
# --------------------
class EstablishmentBase(BaseModel):
    name: str
    address: str

    class Config:
        orm_mode = True


class EstablishmentCreate(EstablishmentBase):
    pass


class Establishment(EstablishmentBase):
    id: int
    entity_id: int
    entity: Entity
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime] = None


# --------------------
# Product Schemas
# --------------------
class ProductBase(BaseModel):
    name: str
    description: str

    class Config:
        orm_mode = True


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    id: int
    entity_id: int
    entity: Entity
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime] = None


# --------------------
# Currency Schemas
# --------------------
class CurrencyBase(BaseModel):
    code: str
    name: str
    symbol: str

    class Config:
        orm_mode = True


class CurrencyCreate(CurrencyBase):
    pass


class Currency(CurrencyBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime] = None


# --------------------
# PurchaseItem Schemas
# --------------------
class PurchaseItemBase(BaseModel):
    text: str
    quantity: Optional[float]
    value: Optional[float]

    class Config:
        orm_mode = True


class PurchaseItemCreate(PurchaseItemBase):
    product_id: int
    currency_id: int


class PurchaseItem(PurchaseItemBase):
    id: int
    purchase_id: int
    product: Product
    currency: Currency
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime] = None


# --------------------
# Purchase Schemas
# --------------------
class PurchaseBase(BaseModel):
    date: datetime
    subtotal: Optional[float]
    discount: Optional[float]
    total: float

    class Config:
        orm_mode = True


class PurchaseCreate(PurchaseBase):
    establishment_id: Optional[int]
    currency_id: Optional[int]
    items: List[PurchaseItemCreate]


class Purchase(PurchaseBase):
    id: int
    establishment: Optional[Establishment]
    currency: Optional[Currency]
    items: List[PurchaseItem]
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime] = None
