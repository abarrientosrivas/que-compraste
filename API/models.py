from sqlalchemy import (
    Column, Integer, String, DateTime, Float, ForeignKey, Text, func, event
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Purchase(Base):
    __tablename__ = 'purchases'
    id = Column(Integer, primary_key=True, index=True)
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

    items = relationship('PurchaseItem', back_populates='purchase')

class PurchaseItem(Base):
    __tablename__ = 'purchase_items'
    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey('purchases.id'), nullable=False)
    read_product_key = Column(String(255), nullable=True)
    read_product_text = Column(String(255), nullable=True)
    quantity = Column(Float, nullable=True)
    value = Column(Float, nullable=True)
    total = Column(Float, nullable=True)

    purchase = relationship('Purchase', back_populates='items')

def update_purchase_updated_at(mapper, connection, target):
    connection.execute(
        Purchase.__table__.update()
        .where(Purchase.id == target.purchase_id)
        .values(updated_at=func.now())
    )

event.listen(PurchaseItem, 'after_insert', update_purchase_updated_at)
event.listen(PurchaseItem, 'after_update', update_purchase_updated_at)
event.listen(PurchaseItem, 'after_delete', update_purchase_updated_at)