import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from core.errors import ValidationAppException
from core.settings import Settings
from modules.mrp.service import MRPService
from modules.products.models import BOMItem, Product
from modules.products.schemas import RectangularDuctSpec
from modules.work_orders.models import WorkOrder, WorkOrderLine


def build_work_order(quantity=10):
    spec = RectangularDuctSpec(
        width_mm=500,
        height_mm=400,
        length_mm=1000,
        thickness_mm=0.7,
        insulation_enabled=True,
        insulation_thickness_mm=20,
    )
    product = Product(name="Kanal", product_type="RECTANGULAR_DUCT", attributes=spec.dict())
    bom = BOMItem(name="Flanş", unit="adet", quantity_per_unit=0.5, cost_per_unit=100)
    product.bom_items = [bom]
    line = WorkOrderLine(product=product, quantity=quantity)
    return WorkOrder(project_name="Proje X", lines=[line])


def test_rectangular_mrp_calculation():
    settings = Settings(waste_factor=0.05)
    mrp_service = MRPService(settings=settings)
    wo = build_work_order(quantity=10)

    result = mrp_service.compute_work_order(wo)

    # Check new hierarchical structure
    assert "header" in result
    assert "summary" in result
    assert "lines" in result
    assert "bom_summary" in result

    # Header checks
    assert result["header"]["project_name"] == "Proje X"
    assert result["header"]["line_count"] == 1
    assert result["header"]["total_quantity"] == 10

    # Line details
    per_unit_area = result["lines"][0]["per_unit"]["sheet_area_m2"]
    assert pytest.approx(per_unit_area, rel=1e-3) == 1.89  # 1.8 m2 with 5% waste
    per_unit_mass = result["lines"][0]["per_unit"]["sheet_mass_kg"]
    assert per_unit_mass > 0

    # Summary totals
    assert result["summary"]["material"]["sheet_area_m2"] == pytest.approx(per_unit_area * 10)
    assert result["summary"]["cost"]["bom_total"] == pytest.approx(500.0)

    # BOM summary
    assert result["bom_summary"]["metrics"]["total_item_count"] == 1
    assert result["bom_summary"]["metrics"]["priced_item_count"] == 1
    assert result["bom_summary"]["priced_items"][0]["total_quantity"] == pytest.approx(5.0)


def test_validation_fails_for_invalid_dimension():
    settings = Settings()
    mrp_service = MRPService(settings=settings)
    spec = {
        "width_mm": 0,
        "height_mm": 400,
        "length_mm": 1000,
        "thickness_mm": 0.7,
        "insulation_enabled": False,
        "insulation_thickness_mm": None,
    }
    product = Product(name="Kanal", product_type="RECTANGULAR_DUCT", attributes=spec)
    wo = WorkOrder(project_name="Proje", product=product, quantity=1)
    with pytest.raises(ValidationAppException):
        mrp_service.compute_work_order(wo)
