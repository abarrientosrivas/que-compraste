from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional

class PurchaseItem(BaseModel):
    key: Optional[str]
    text: Optional[str]
    quantity: Optional[float]
    value: Optional[float]

class Purchase(BaseModel):
    entity_id: Optional[int]
    store_name: Optional[str]
    store_address: Optional[str]
    date: Optional[datetime]
    subtotal: Optional[float]
    total: Optional[float]
    items: List[PurchaseItem] = Field(default_factory=list)