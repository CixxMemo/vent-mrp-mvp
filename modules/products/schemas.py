from typing import List, Optional

from pydantic import BaseModel, Field, validator

from modules.products.types import ProductType


class RectangularDuctSpec(BaseModel):
    width_mm: float = Field(..., gt=0, description="Genişlik (mm)")
    height_mm: float = Field(..., gt=0, description="Yükseklik (mm)")
    length_mm: float = Field(..., gt=0, description="Uzunluk (mm)")
    thickness_mm: float = Field(..., gt=0, description="Sac kalınlığı (mm)")
    insulation_enabled: bool = Field(False, description="Yalıtım var mı?")
    insulation_thickness_mm: Optional[float] = Field(None, description="Yalıtım kalınlığı (mm)")

    @validator("thickness_mm")
    def check_thickness(cls, v: float) -> float:
        if v <= 0 or v > 20:
            raise ValueError("Sac kalınlığı 0'dan büyük ve 20 mm'den küçük olmalıdır")
        return v

    @validator("insulation_thickness_mm")
    def validate_insulation_thickness(cls, v: Optional[float], values):
        if values.get("insulation_enabled") and (v is None or v <= 0):
            raise ValueError("Yalıtım kalınlığı 0'dan büyük olmalıdır")
        return v


class BOMItemBase(BaseModel):
    name: str = Field(..., description="Malzeme/aksesuar adı")
    unit: Optional[str] = Field(None, description="Birim")
    quantity_per_unit: float = Field(..., gt=0, description="Birim başı miktar")
    cost_per_unit: Optional[float] = Field(None, ge=0, description="Birim maliyet")


class BOMItemCreate(BOMItemBase):
    pass


class BOMItemRead(BOMItemBase):
    id: int

    class Config:
        orm_mode = True


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    product_type: ProductType
    spec: RectangularDuctSpec
    bom_items: Optional[List[BOMItemCreate]] = Field(default_factory=list)


class ProductCreate(ProductBase):
    pass


class ProductRead(ProductBase):
    id: int
    bom_items: List[BOMItemRead] = Field(default_factory=list)

    class Config:
        orm_mode = True


