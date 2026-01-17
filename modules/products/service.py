from typing import List, Dict, Any

from sqlalchemy.orm import Session

from core.errors import NotFoundException, ValidationAppException
from modules.products import models, schemas
from modules.products.types import ProductType


def _serialize_product(product: models.Product) -> Dict[str, Any]:
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "product_type": product.product_type,
        "spec": product.attributes,
        "bom_items": [
            {
                "id": bom.id,
                "name": bom.name,
                "unit": bom.unit,
                "quantity_per_unit": bom.quantity_per_unit,
                "cost_per_unit": bom.cost_per_unit,
            }
            for bom in product.bom_items
        ],
    }


def create_product(db: Session, product_in: schemas.ProductCreate) -> models.Product:
    if product_in.product_type != ProductType.RECTANGULAR_DUCT:
        raise ValidationAppException("Şu an yalnızca dikdörtgen kanal ürün tipi destekleniyor")

    product = models.Product(
        name=product_in.name,
        description=product_in.description,
        product_type=product_in.product_type.value,
        attributes=product_in.spec.dict(),
    )

    for bom in product_in.bom_items or []:
        product.bom_items.append(
            models.BOMItem(
                name=bom.name,
                unit=bom.unit,
                quantity_per_unit=bom.quantity_per_unit,
                cost_per_unit=bom.cost_per_unit,
            )
        )

    db.add(product)
    db.commit()
    db.refresh(product)
    return _serialize_product(product)


def list_products(db: Session) -> List[models.Product]:
    products = db.query(models.Product).all()
    return [_serialize_product(p) for p in products]


def get_product(db: Session, product_id: int) -> models.Product:
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise NotFoundException("Ürün bulunamadı")
    return _serialize_product(product)


