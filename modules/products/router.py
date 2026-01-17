from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from modules.products import schemas, service

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=schemas.ProductRead)
def create_product_endpoint(product_in: schemas.ProductCreate, db: Session = Depends(get_db)):
    return service.create_product(db, product_in)


@router.get("", response_model=list[schemas.ProductRead])
def list_products_endpoint(db: Session = Depends(get_db)):
    return service.list_products(db)


@router.get("/{product_id}", response_model=schemas.ProductRead)
def get_product_endpoint(product_id: int, db: Session = Depends(get_db)):
    return service.get_product(db, product_id)


