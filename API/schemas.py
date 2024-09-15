from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# --------------------
# PurchaseItem Schemas
# --------------------
class PurchaseItemBase(BaseModel):
    read_product_key: Optional[str] = None
    read_product_text: Optional[str] = None
    quantity: Optional[float] = None
    value: Optional[float] = None
    total: Optional[float] = None

    class Config:
        orm_mode = True


class PurchaseItemCreate(PurchaseItemBase):
    pass


class PurchaseItem(PurchaseItemBase):
    id: int
    purchase_id: int


# --------------------
# Purchase Schemas
# --------------------
class PurchaseBase(BaseModel):
    read_entity_name: Optional[str] = None
    read_entity_branch: Optional[str] = None
    read_entity_location: Optional[str] = None
    read_entity_address: Optional[str] = None
    read_entity_identification: Optional[str] = None
    read_entity_phone: Optional[str] = None
    date: datetime
    subtotal: Optional[float] = None
    discount: Optional[float] = None
    tips: Optional[float] = None
    total: float

    class Config:
        orm_mode = True


class PurchaseCreate(PurchaseBase):
    items: List[PurchaseItemCreate] = Field(default_factory=list)


class Purchase(PurchaseBase):
    id: int
    items: List[PurchaseItem] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
