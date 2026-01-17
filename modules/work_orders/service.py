from typing import List, Dict, Any

from sqlalchemy.orm import Session

from core.errors import NotFoundException, ValidationAppException
from modules.products import models as product_models
from modules.work_orders import models, schemas


def create_work_order(db: Session, work_order_in: schemas.WorkOrderCreate) -> Dict[str, Any]:
    lines = list(work_order_in.lines or [])
    # Legacy fallback: if legacy fields provided, convert to single line
    if not lines and work_order_in.product_id and work_order_in.quantity:
        lines.append(
            schemas.WorkOrderLineCreate(product_id=work_order_in.product_id, quantity=work_order_in.quantity)
        )
    if not lines:
        raise ValidationAppException("En az bir satır eklemelisiniz")

    # Validate products and quantities, build model lines
    model_lines = []
    for line in lines:
        if line.quantity <= 0:
            raise ValidationAppException("Miktar 0'dan büyük olmalıdır")
        product = db.query(product_models.Product).filter(product_models.Product.id == line.product_id).first()
        if not product:
            raise NotFoundException("Ürün bulunamadı")
        model_lines.append(models.WorkOrderLine(product_id=line.product_id, quantity=line.quantity, product=product))

    work_order = models.WorkOrder(project_name=work_order_in.project_name, lines=model_lines)
    db.add(work_order)
    db.commit()
    db.refresh(work_order)
    return _serialize_work_order(work_order)


def list_work_orders(db: Session) -> List[Dict[str, Any]]:
    work_orders = db.query(models.WorkOrder).all()
    return [_serialize_work_order(wo) for wo in work_orders]


def get_work_order(db: Session, work_order_id: int) -> Dict[str, Any]:
    work_order = _get_work_order_model(db, work_order_id)
    return _serialize_work_order(work_order)


def _get_work_order_model(db: Session, work_order_id: int) -> models.WorkOrder:
    work_order = (
        db.query(models.WorkOrder)
        .filter(models.WorkOrder.id == work_order_id)
        .first()
    )
    if not work_order:
        raise NotFoundException("İş emri bulunamadı")
    return work_order


def _serialize_work_order(work_order: models.WorkOrder) -> Dict[str, Any]:
    lines_payload = []
    for line in work_order.lines or []:
        product = line.product
        lines_payload.append(
            {
                "id": line.id,
                "product_id": line.product_id,
                "quantity": line.quantity,
                "product": {
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
                },
            }
        )

    return {
        "id": work_order.id,
        "project_name": work_order.project_name,
        "lines": lines_payload,
        # Legacy compatibility: echo old fields if present
        "product_id": work_order.product_id,
        "quantity": work_order.quantity,
    }


def migrate_legacy_work_orders(db: Session) -> None:
    """Create line records for legacy work_orders that have product_id/quantity but no lines."""
    legacy_wos = (
        db.query(models.WorkOrder)
        .filter(models.WorkOrder.product_id.isnot(None))
        .filter(models.WorkOrder.quantity.isnot(None))
        .all()
    )
    created_lines = 0
    for wo in legacy_wos:
        if wo.lines:
            continue
        if wo.product_id is None or wo.quantity is None:
            continue
        line = models.WorkOrderLine(product_id=wo.product_id, quantity=wo.quantity, work_order=wo)
        db.add(line)
        created_lines += 1
    if created_lines:
        db.commit()


