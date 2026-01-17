from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from core.database import get_db
from core.settings import get_settings
from modules.mrp.service import MRPService
from modules.reports.excel import build_mrp_excel
from modules.work_orders import service as work_order_service

router = APIRouter(prefix="/mrp", tags=["mrp"])


@router.get("/work-orders/{work_order_id}")
def calculate_mrp(work_order_id: int, db: Session = Depends(get_db)):
    settings = get_settings()
    work_order = work_order_service._get_work_order_model(db, work_order_id)
    mrp_service = MRPService(settings=settings)
    return mrp_service.compute_work_order(work_order)


@router.get("/work-orders/{work_order_id}/excel")
def download_mrp_excel(work_order_id: int, db: Session = Depends(get_db)):
    settings = get_settings()
    work_order = work_order_service._get_work_order_model(db, work_order_id)
    mrp_service = MRPService(settings=settings)
    mrp_data = mrp_service.compute_work_order(work_order)
    stream = build_mrp_excel(mrp_data)
    filename = f"mrp_{work_order_id}.xlsx"
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


