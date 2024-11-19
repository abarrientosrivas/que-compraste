from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

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
        from_attributes = True


class PurchaseItemCreate(PurchaseItemBase):
    pass


class PurchaseItemUpdate(PurchaseItemBase):
    id: int
    product_id: Optional[int] = None


class PurchaseItem(PurchaseItemBase):
    id: int
    purchase_id: Optional[int]
    purchase: Optional['Purchase']
    product_id: Optional[int] = None
    product: Optional['Product'] = None


class PurchaseItemOut(PurchaseItemBase):
    id: int
    purchase_id: Optional[int]
    product_id: Optional[int] = None
    product: Optional['Product'] = None


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
        from_attributes = True


class PurchaseCreate(PurchaseBase):
    date: Optional[datetime] = None
    total: Optional[float] = None
    items: List[PurchaseItemCreate] = Field(default_factory=list)


class PurchaseUpdate(PurchaseBase):
    date: Optional[datetime] = None
    total: Optional[float] = None
    entity_id: Optional[int] = None
    items: List[PurchaseItemUpdate] = Field(default_factory=list)


class Purchase(PurchaseBase):
    id: int
    entity_id: Optional[int] = None
    entity: Optional['Entity'] = None
    items: List[PurchaseItem] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

class PurchaseWithReceipt(Purchase):
    receipt: Optional['Receipt'] = None


class PurchaseOut(PurchaseBase):
    id: int
    entity_id: Optional[int] = None
    entity: Optional['Entity'] = None
    items: List[PurchaseItemOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


# --------------------
# Category Schemas
# --------------------
class CategoryBase(BaseModel):
    code: int
    name: str
    name_es_es: Optional[str] = None
    description: Optional[str] = None
    original_text: str

    class Config:
        from_attributes = True


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase):
    id: int
    parent_id: Optional[int] = None
    parent: Optional['Category'] = None
    children: List['Category'] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


# --------------------
# Entity Schemas
# --------------------
class EntityBase(BaseModel):
    name: str
    identification: int
    email: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None

    class Config:
        from_attributes = True


class EntityCreate(EntityBase):
    pass


class Entity(EntityBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


# --------------------
# Establishment Schemas
# --------------------
class EstablishmentBase(BaseModel):
    name: Optional[str] = None
    location: str
    address: str

    class Config:
        from_attributes = True


class EstablishmentCreate(EstablishmentBase):
    entity_id: int


class Establishment(EstablishmentBase):
    id: int
    entity_id: int
    entity: Entity
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


# --------------------
# Product Schemas
# --------------------
class ProductBase(BaseModel):
    title: str
    description: Optional[str] = None
    read_category: Optional[str] = None
    img_url: Optional[str] = None

    class Config:
        from_attributes = True


class ProductCreate(ProductBase):
    img_urls: List[str] = Field(default_factory=list)


class ProductUpdate(ProductBase):
    title: Optional[str] = None
    category_id: Optional[int] = None


class Product(ProductBase):
    id: int
    entity_id: Optional[int] = None
    entity: Optional[Entity] = None
    category_id: Optional[int] = None
    category: Optional[Category] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


# --------------------
# ProductCode Schemas
# --------------------
class ProductCodeBase(BaseModel):
    format: str
    code: str

    class Config:
        from_attributes = True


class ProductCodeCreate(ProductCodeBase):
    product: ProductCreate


class ProductCode(ProductCodeBase):
    id: int
    product_id: int
    product: Product
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


# --------------------
# CrawlCounter Schema
# --------------------
class CrawlCounterBase(BaseModel):
    date: datetime
    uses: int

    class Config:
        from_attributes = True


class CrawlCounter(CrawlCounterBase):
    id: int
    node_token_id: int


# --------------------
# NodeToken Schema
# --------------------
class NodeTokenBase(BaseModel):
    name: str
    key_hash: str
    crawl_daily_limit: int
    can_view_receipt_images: bool

    class Config:
        from_attributes = True


class NodeToken(NodeTokenBase):
    id: int
    crawl_counters: List[CrawlCounter] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


# --------------------
# Receipt Schemas
# --------------------
class ReceiptStatus(str, Enum):
    CREATED = "CREATED"
    WAITING = "WAITING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"
    FAILED = "FAILED"


class ReceiptBase(BaseModel):
    status: ReceiptStatus = ReceiptStatus.WAITING
    image_url: str
    reference_name: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class ReceiptCreate(ReceiptBase):
    pass


class Receipt(ReceiptBase):
    id: int
    purchase_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


# --------------------
# Historic Schemas
# --------------------
class HistoricBase(BaseModel):
    date: datetime
    quantity: float


class Historic(HistoricBase):
    pass

# --------------------
# PredictionItem Schemas
# --------------------
class PredictionItemBase(BaseModel):
    date: datetime
    quantity: float

    class Config:
        from_attributes = True


class PredictionItemCreate(PredictionItemBase):
    pass


class PredictionItem(PredictionItemBase):
    id: int
    prediction_id: int


# --------------------
# Prediction Schemas
# --------------------
class PredictionBase(BaseModel):
    product_key: Optional[str] = None
    category_code: Optional[str] = None

    class Config:
        from_attributes = True


class PredictionCreate(PredictionBase):
    items: List[PredictionItemCreate] = Field(default_factory=list)


class Prediction(PredictionBase):
    id: int
    items: List[PredictionItem] = Field(default_factory=list)
    created_at: datetime
