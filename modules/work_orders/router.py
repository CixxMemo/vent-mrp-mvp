from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from core.database import get_db
from modules.work_orders import schemas, service

router = APIRouter(prefix="/work-orders", tags=["work_orders"])


@router.post("", response_model=schemas.WorkOrderRead)
def create_work_order_endpoint(work_order_in: schemas.WorkOrderCreate, db: Session = Depends(get_db)):
    return service.create_work_order(db, work_order_in)


@router.post("/import", response_model=schemas.WorkOrderRead)
def import_work_order_endpoint(
    file: UploadFile = File(...),
    project_name: str = Form(...),
    waste_factor: float = Form(0.0),
    db: Session = Depends(get_db)
):
    return service.import_work_order_from_excel(db, file, project_name, waste_factor)


@router.get("", response_model=list[schemas.WorkOrderRead])
def list_work_orders_endpoint(db: Session = Depends(get_db)):
    return service.list_work_orders(db)


@router.get("/{work_order_id}", response_model=schemas.WorkOrderRead)
def get_work_order_endpoint(work_order_id: int, db: Session = Depends(get_db)):
    return service.get_work_order(db, work_order_id)


