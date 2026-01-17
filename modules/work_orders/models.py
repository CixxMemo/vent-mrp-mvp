from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from core.models import Base, TimestampMixin


class WorkOrder(Base, TimestampMixin):
    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String(255), nullable=False)
    # Legacy fields kept for compatibility; not used in new logic
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=True)
    quantity = Column(Integer, nullable=True)

    product = relationship("Product")
    lines = relationship("WorkOrderLine", cascade="all, delete-orphan", back_populates="work_order")


class WorkOrderLine(Base, TimestampMixin):
    __tablename__ = "work_order_lines"

    id = Column(Integer, primary_key=True, index=True)
    work_order_id = Column(Integer, ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Integer, nullable=False)

    work_order = relationship("WorkOrder", back_populates="lines")
    product = relationship("Product")


