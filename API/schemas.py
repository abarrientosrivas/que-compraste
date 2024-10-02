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
        from_attributes = True


class PurchaseItemCreate(PurchaseItemBase):
    pass


class PurchaseItemUpdate(PurchaseItemBase):
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
        from_attributes = True


class PurchaseCreate(PurchaseBase):
    date: Optional[datetime] = None
    total: Optional[float] = None
    items: List[PurchaseItemCreate] = Field(default_factory=list)
    

class PurchaseUpdate(PurchaseBase):
    date: Optional[datetime] = None
    total: Optional[float] = None


class Purchase(PurchaseBase):
    id: int
    items: List[PurchaseItem] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


# --------------------
# Category Schemas
# --------------------
class CategoryBase(BaseModel):
    code: int
    name: str
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
# Product Schemas
# --------------------
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    read_category: Optional[str] = None

    class Config:
        from_attributes = True


class Product(ProductBase):
    id: int
    category_id: Optional[int] = None
    category: Optional[Category] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


# --------------------
# Entity Schemas
# --------------------
class EntityBase(BaseModel):
    name: str = None

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

    class Config:
        from_attributes = True
    

class ProductCreate(ProductBase):
    pass
    

class ProductUpdate(ProductBase):
    title: Optional[str] = None
    category_id: Optional[int] = None


class Product(ProductBase):
    id: int
    entity_id: Optional[int]
    entity: Optional[Entity]
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
    pass


class ProductCode(ProductCodeBase):
    id: int
    product_id: int
    product: Product
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
