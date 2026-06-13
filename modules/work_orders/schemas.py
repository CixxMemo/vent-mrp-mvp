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
        from_attributes = True


class WorkOrderCreate(BaseModel):
    project_name: str
    lines: List[WorkOrderLineCreate] = Field(default_factory=list)
    waste_factor: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)
    # Legacy fallback
    product_id: Optional[int] = None
    quantity: Optional[int] = Field(default=None, gt=0)


class WorkOrderRead(BaseModel):
    id: int
    project_name: str
    lines: List[WorkOrderLineRead] = Field(default_factory=list)
    waste_factor: float = 0.0
    # Legacy compatibility
    product_id: Optional[int] = None
    quantity: Optional[int] = None

    class Config:
        from_attributes = True


