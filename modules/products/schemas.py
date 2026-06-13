from typing import List, Optional, Union

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


class AHUSpec(BaseModel):
    width_mm: float = Field(..., gt=0, description="Kabin genişliği (mm)")
    height_mm: float = Field(..., gt=0, description="Kabin yüksekliği (mm)")
    length_mm: float = Field(..., gt=0, description="Kabin uzunluğu (mm)")
    panel_thickness_mm: float = Field(..., gt=0, description="Panel kalınlığı (mm)")
    has_profile_framework: bool = Field(True, description="Profil çerçeve mevcut mu?")


class FittingSpec(BaseModel):
    fitting_shape: str = Field(
        ...,
        description="Fitting tipi (ELBOW, TEE, REDUCER vb.)",
    )
    main_dimension_mm: float = Field(..., gt=0, description="Ana ölçü (mm)")
    thickness_mm: float = Field(..., gt=0, description="Sac kalınlığı (mm)")
    angle_degrees: Optional[float] = Field(None, description="Açı (derece)")

    @validator("fitting_shape")
    def validate_fitting_shape(cls, v: str) -> str:
        allowed = {"ELBOW", "TEE", "REDUCER", "OFFSET", "TRANSITION"}
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(
                f"Geçersiz fitting tipi: '{v}'. İzin verilen değerler: {', '.join(sorted(allowed))}"
            )
        return v_upper


# Type-to-spec mapping for validation
_PRODUCT_TYPE_SPEC_MAP = {
    ProductType.RECTANGULAR_DUCT: RectangularDuctSpec,
    ProductType.AHU_CABINET: AHUSpec,
    ProductType.FITTING_DUCT: FittingSpec,
}


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
        from_attributes = True


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    product_type: ProductType
    spec: Union[RectangularDuctSpec, AHUSpec, FittingSpec]
    bom_items: Optional[List[BOMItemCreate]] = Field(default_factory=list)

    @validator("spec")
    def validate_spec_matches_product_type(cls, v, values):
        product_type = values.get("product_type")
        if product_type is None:
            return v
        expected_spec_cls = _PRODUCT_TYPE_SPEC_MAP.get(product_type)
        if expected_spec_cls and not isinstance(v, expected_spec_cls):
            raise ValueError(
                f"'{product_type.value}' ürün tipi için '{expected_spec_cls.__name__}' "
                f"spec bekleniyor, ancak '{type(v).__name__}' verildi."
            )
        return v


class ProductCreate(ProductBase):
    pass


class ProductRead(ProductBase):
    id: int
    bom_items: List[BOMItemRead] = Field(default_factory=list)

    class Config:
        from_attributes = True
