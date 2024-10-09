from sqlalchemy import (
    Column, Integer, String, DateTime, Float, ForeignKey, Text, func, event, UniqueConstraint, BigInteger, Boolean, Date
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Purchase(Base):
    __tablename__ = 'purchases'
    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey('entities.id'), nullable=True)
    read_entity_name=Column(String(255), nullable=True)
    read_entity_branch=Column(String(255), nullable=True)
    read_entity_location=Column(String(255), nullable=True)
    read_entity_address=Column(String(255), nullable=True)
    read_entity_identification=Column(String(255), nullable=True)
    read_entity_phone=Column(String(255), nullable=True)
    date = Column(DateTime, default=func.now())
    subtotal = Column(Float, nullable=True)
    discount = Column(Float, nullable=True)
    tips = Column(Float, nullable=True)
    total = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)

    items = relationship('PurchaseItem', back_populates='purchase', lazy='selectin')
    entity = relationship('Entity')

class PurchaseItem(Base):
    __tablename__ = 'purchase_items'
    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey('purchases.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=True)
    read_product_key = Column(String(255), nullable=True)
    read_product_text = Column(String(255), nullable=True)
    quantity = Column(Float, nullable=True)
    value = Column(Float, nullable=True)
    total = Column(Float, nullable=True)

    purchase = relationship('Purchase', back_populates='items', lazy="noload")
    product = relationship('Product')

def update_purchase_updated_at(_, connection, target):
    connection.execute(
        Purchase.__table__.update()
        .where(Purchase.id == target.purchase_id)
        .values(updated_at=func.now())
    )

event.listen(PurchaseItem, 'after_insert', update_purchase_updated_at)
event.listen(PurchaseItem, 'after_update', update_purchase_updated_at)
event.listen(PurchaseItem, 'after_delete', update_purchase_updated_at)

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    code = Column(Integer, nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    original_text = Column(Text, nullable=False, unique=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)

    parent = relationship('Category', remote_side=[id], back_populates='children', lazy='noload')
    children = relationship('Category', back_populates='parent', lazy='noload') 

class Entity(Base):
    __tablename__ = 'entities'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    identification = Column(BigInteger, nullable=False, unique=True)
    email = Column(String(255), nullable=True)
    address = Column(String(255), nullable=True)
    phone = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)

class Establishment(Base):
    __tablename__ = 'establishments'
    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey('entities.id'), nullable=True)
    name = Column(String(255), nullable=True)
    location = Column(String(255), nullable=False)
    address = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)

    entity = relationship('Entity') 
    
    __table_args__ = (UniqueConstraint('entity_id', 'location', 'address', name='uix_entity_location_address'),)

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey('entities.id'), nullable=True)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    read_category = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)
    
    entity = relationship('Entity') 
    category = relationship('Category') 

class ProductCode(Base):
    __tablename__ = 'product_codes'
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    format = Column(String(255), nullable=False)
    code = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)
    
    product = relationship('Product') 

    __table_args__ = (UniqueConstraint('format', 'code', name='uix_format_code'),)

class NodeToken(Base):
    __tablename__ = "node_tokens"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    key_hash = Column(String, unique=True, index=True, nullable=False)
    crawl_daily_limit = Column(Integer, default=0, nullable=False)
    can_view_receipt_images = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)
    
    crawl_counters = relationship('CrawlCounter', lazy='selectin') 

class CrawlCounter(Base):
    __tablename__ = "crawl_counters"
    id = Column(Integer, primary_key=True, index=True)
    node_token_id = Column(Integer, ForeignKey('node_tokens.id'), nullable=False)
    date = Column(Date, default=func.current_date())
    uses = Column(Integer, default=0)
    
    __table_args__ = (UniqueConstraint('node_token_id', 'date', name='uix_node_token_date'),)