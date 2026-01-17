import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from core.settings import Settings
from modules.mrp.service import MRPService
from modules.products.models import BOMItem, Product
from modules.products.schemas import RectangularDuctSpec
from modules.work_orders.models import WorkOrder, WorkOrderLine


def build_line(width=500, height=400, length=1000, thickness=0.7, qty=1, cost=100):
    spec = RectangularDuctSpec(
        width_mm=width,
        height_mm=height,
        length_mm=length,
        thickness_mm=thickness,
        insulation_enabled=True,
        insulation_thickness_mm=20,
    )
    product = Product(name="Kanal", product_type="RECTANGULAR_DUCT", attributes=spec.model_dump())
    bom = BOMItem(name="Flanş", unit="adet", quantity_per_unit=0.5, cost_per_unit=cost)
    product.bom_items = [bom]
    return WorkOrderLine(product=product, quantity=qty)


def test_multiline_aggregation_and_missing_cost():
    settings = Settings(waste_factor=0.0)
    mrp_service = MRPService(settings=settings)

    line1 = build_line(qty=2, cost=100)
    line2 = build_line(qty=3, cost=None)  # missing cost

    wo = WorkOrder(project_name="Proje Y", lines=[line1, line2])

    result = mrp_service.compute_work_order(wo)

    # Check new hierarchical structure
    assert "header" in result
    assert "summary" in result
    assert "bom_summary" in result

    # Header checks
    assert result["header"]["line_count"] == 2
    assert result["header"]["total_quantity"] == 5

    # Cost summary: bom_total should sum only known costs (line1)
    assert result["summary"]["cost"]["bom_total"] == pytest.approx(100 * 0.5 * 2)
    assert result["summary"]["cost"]["items_missing_cost"] == 1
    assert result["summary"]["cost"]["cost_complete"] is False

    # BOM summary checks
    bom_metrics = result["bom_summary"]["metrics"]
    assert bom_metrics["priced_item_count"] == 1
    assert bom_metrics["unpriced_item_count"] == 1
    assert bom_metrics["total_item_count"] == 2

    # Priced items: only line1's BOM (cost=100)
    priced = result["bom_summary"]["priced_items"]
    assert len(priced) == 1
    assert priced[0]["total_quantity"] == pytest.approx(0.5 * 2)

    # Unpriced items: line2's BOM (cost=None)
    unpriced = result["bom_summary"]["unpriced_items"]
    assert len(unpriced) == 1
    assert unpriced[0]["total_quantity"] == pytest.approx(0.5 * 3)
