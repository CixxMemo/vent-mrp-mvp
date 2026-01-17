from sqlalchemy import Column, Float, ForeignKey, Integer, String, JSON
from sqlalchemy.orm import relationship

from core.models import Base, TimestampMixin


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1024), nullable=True)
    product_type = Column(String(64), nullable=False)
    attributes = Column(JSON, nullable=False, default=dict)

    bom_items = relationship("BOMItem", cascade="all, delete-orphan", back_populates="product")


class BOMItem(Base, TimestampMixin):
    __tablename__ = "bom_items"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    unit = Column(String(64), nullable=True)
    quantity_per_unit = Column(Float, nullable=False, default=1.0)
    cost_per_unit = Column(Float, nullable=True)

    product = relationship("Product", back_populates="bom_items")


