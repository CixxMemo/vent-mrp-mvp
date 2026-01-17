from typing import List, Optional

from pydantic import BaseModel, Field

from modules.products.schemas import ProductRead


class WorkOrderLineCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)


class WorkOrderLineRead(WorkOrderLineCreate):
    id: int
    product: ProductRead

    class Config:
        orm_mode = True


class WorkOrderCreate(BaseModel):
    project_name: str
    lines: List[WorkOrderLineCreate] = Field(default_factory=list)
    # Legacy fallback
    product_id: Optional[int] = None
    quantity: Optional[int] = Field(default=None, gt=0)


class WorkOrderRead(BaseModel):
    id: int
    project_name: str
    lines: List[WorkOrderLineRead] = Field(default_factory=list)
    # Legacy compatibility
    product_id: Optional[int] = None
    quantity: Optional[int] = None

    class Config:
        orm_mode = True


