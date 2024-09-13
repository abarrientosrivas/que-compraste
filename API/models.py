from sqlalchemy import (
    Column, Integer, String, DateTime, Float, ForeignKey, Text, func
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Entity(Base):
    __tablename__ = 'entities'
    id = Column(Integer, primary_key=True, index=True)
    identification_number = Column(Integer, unique=True, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)

    establishments = relationship('Establishment', back_populates='entity')
    products = relationship('Product', back_populates='entity')

class Establishment(Base):
    __tablename__ = 'establishments'
    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey('entities.id'), nullable=False)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)

    entity = relationship('Entity', back_populates='establishments')
    purchases = relationship('Purchase', back_populates='establishment')

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey('entities.id'), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)

    entity = relationship('Entity', back_populates='products')
    purchase_items = relationship('PurchaseItem', back_populates='product')

class Currency(Base):
    __tablename__ = 'currencies'
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    symbol = Column(String)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)

    purchases = relationship('Purchase', back_populates='currency')
    purchase_items = relationship('PurchaseItem', back_populates='currency')

class Purchase(Base):
    __tablename__ = 'purchases'
    id = Column(Integer, primary_key=True, index=True)
    establishment_id = Column(Integer, ForeignKey('establishments.id'), nullable=True)
    date = Column(DateTime, default=func.now())
    subtotal = Column(Float)
    discount = Column(Float)
    total = Column(Float, nullable=False)
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)

    establishment = relationship('Establishment', back_populates='purchases')
    currency = relationship('Currency', back_populates='purchases')
    items = relationship('PurchaseItem', back_populates='purchase')

class PurchaseItem(Base):
    __tablename__ = 'purchase_items'
    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey('purchases.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'))
    text = Column(String)
    quantity = Column(Float)
    value = Column(Float)
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)

    purchase = relationship('Purchase', back_populates='items')
    product = relationship('Product', back_populates='purchase_items')
    currency = relationship('Currency', back_populates='purchase_items')
