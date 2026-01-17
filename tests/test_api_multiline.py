"""API-level tests for multi-line work orders and BOM merge."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    """Reset database before each test by re-initializing."""
    from core.database import Base, engine
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def create_test_product(name: str = "Test Kanal", with_bom: bool = True, bom_cost: float = 100):
    """Create a product for testing."""
    payload = {
        "name": name,
        "description": "Test ürün",
        "product_type": "RECTANGULAR_DUCT",
        "spec": {
            "width_mm": 500,
            "height_mm": 400,
            "length_mm": 1000,
            "thickness_mm": 0.7,
            "insulation_enabled": True,
            "insulation_thickness_mm": 20,
        },
        "bom_items": [
            {
                "name": "Flanş",
                "unit": "adet",
                "quantity_per_unit": 0.5,
                "cost_per_unit": bom_cost if with_bom else None,
            }
        ] if with_bom else [],
    }
    resp = client.post("/products", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_create_multiline_work_order():
    """Test creating a work order with multiple lines."""
    prod1 = create_test_product("Kanal A")
    prod2 = create_test_product("Kanal B")

    payload = {
        "project_name": "Çoklu Hat Projesi",
        "lines": [
            {"product_id": prod1["id"], "quantity": 5},
            {"product_id": prod2["id"], "quantity": 10},
        ],
    }
    resp = client.post("/work-orders", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["project_name"] == "Çoklu Hat Projesi"
    assert len(data["lines"]) == 2
    assert data["lines"][0]["product_id"] == prod1["id"]
    assert data["lines"][0]["quantity"] == 5
    assert data["lines"][1]["product_id"] == prod2["id"]
    assert data["lines"][1]["quantity"] == 10


def test_get_multiline_work_order():
    """Test retrieving a multi-line work order."""
    prod1 = create_test_product("Kanal A")
    prod2 = create_test_product("Kanal B")

    create_resp = client.post("/work-orders", json={
        "project_name": "Get Test",
        "lines": [
            {"product_id": prod1["id"], "quantity": 3},
            {"product_id": prod2["id"], "quantity": 7},
        ],
    })
    assert create_resp.status_code == 200
    wo_id = create_resp.json()["id"]

    get_resp = client.get(f"/work-orders/{wo_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()

    assert len(data["lines"]) == 2
    assert data["lines"][0]["product"]["name"] == "Kanal A"
    assert data["lines"][1]["product"]["name"] == "Kanal B"


def test_legacy_single_product_fallback():
    """Test that legacy single product/quantity payload creates a work order line."""
    prod = create_test_product("Legacy Kanal")

    payload = {
        "project_name": "Legacy Proje",
        "product_id": prod["id"],
        "quantity": 5,
    }
    resp = client.post("/work-orders", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["project_name"] == "Legacy Proje"
    assert len(data["lines"]) == 1
    assert data["lines"][0]["product_id"] == prod["id"]
    assert data["lines"][0]["quantity"] == 5


def test_mrp_multiline_aggregation():
    """Test MRP calculation aggregates across multiple lines."""
    prod1 = create_test_product("Kanal A", with_bom=True, bom_cost=100)
    prod2 = create_test_product("Kanal B", with_bom=True, bom_cost=200)

    wo_resp = client.post("/work-orders", json={
        "project_name": "MRP Test",
        "lines": [
            {"product_id": prod1["id"], "quantity": 2},
            {"product_id": prod2["id"], "quantity": 3},
        ],
    })
    assert wo_resp.status_code == 200
    wo_id = wo_resp.json()["id"]

    mrp_resp = client.get(f"/mrp/work-orders/{wo_id}")
    assert mrp_resp.status_code == 200
    data = mrp_resp.json()

    # Check new hierarchical structure
    assert "header" in data
    assert "summary" in data
    assert "lines" in data
    assert "bom_summary" in data

    # Summary totals should be aggregated
    assert data["summary"]["material"]["sheet_area_m2"] > 0
    assert data["summary"]["material"]["sheet_mass_kg"] > 0
    assert data["summary"]["cost"]["bom_total"] > 0

    # Lines should have per-line results
    assert len(data["lines"]) == 2
    assert data["lines"][0]["quantity"] == 2
    assert data["lines"][1]["quantity"] == 3


def test_bom_merge_by_name_unit():
    """Test BOM items with same (name, unit) are merged in MRP result."""
    # Create two products with same BOM item (name, unit) and same cost
    prod1 = create_test_product("Kanal A", with_bom=True, bom_cost=100)
    prod2 = create_test_product("Kanal B", with_bom=True, bom_cost=100)

    wo_resp = client.post("/work-orders", json={
        "project_name": "BOM Merge Test",
        "lines": [
            {"product_id": prod1["id"], "quantity": 2},
            {"product_id": prod2["id"], "quantity": 3},
        ],
    })
    assert wo_resp.status_code == 200
    wo_id = wo_resp.json()["id"]

    mrp_resp = client.get(f"/mrp/work-orders/{wo_id}")
    assert mrp_resp.status_code == 200
    data = mrp_resp.json()

    # Both products have BOM item "Flanş" with unit "adet" and quantity_per_unit=0.5
    # Line 1: 0.5 * 2 = 1.0
    # Line 2: 0.5 * 3 = 1.5
    # Merged total: 2.5
    priced_items = data["bom_summary"]["priced_items"]
    assert len(priced_items) == 1  # Should be merged into one
    assert priced_items[0]["name"] == "Flanş"
    assert priced_items[0]["unit"] == "adet"
    assert pytest.approx(priced_items[0]["total_quantity"], rel=1e-3) == 2.5


def test_missing_cost_items_in_mrp():
    """Test that missing cost items are reported in MRP result."""
    prod1 = create_test_product("Kanal A", with_bom=True, bom_cost=100)
    prod2 = create_test_product("Kanal B", with_bom=True, bom_cost=None)  # No cost

    wo_resp = client.post("/work-orders", json={
        "project_name": "Missing Cost Test",
        "lines": [
            {"product_id": prod1["id"], "quantity": 1},
            {"product_id": prod2["id"], "quantity": 1},
        ],
    })
    assert wo_resp.status_code == 200
    wo_id = wo_resp.json()["id"]

    mrp_resp = client.get(f"/mrp/work-orders/{wo_id}")
    assert mrp_resp.status_code == 200
    data = mrp_resp.json()

    # Should have unpriced items in bom_summary
    unpriced = data["bom_summary"]["unpriced_items"]
    assert len(unpriced) == 1
    assert unpriced[0]["name"] == "Flanş"

    # Cost summary should indicate incomplete
    assert data["summary"]["cost"]["items_missing_cost"] == 1
    assert data["summary"]["cost"]["cost_complete"] is False

    # BOM cost should only include known costs (from prod1)
    assert data["summary"]["cost"]["bom_total"] == pytest.approx(100 * 0.5 * 1)


def test_work_order_validation_empty_lines():
    """Test that creating a work order without lines fails."""
    resp = client.post("/work-orders", json={
        "project_name": "Empty Lines",
        "lines": [],
    })
    assert resp.status_code == 422  # Validation error


def test_work_order_validation_invalid_product():
    """Test that creating a work order with invalid product_id fails."""
    resp = client.post("/work-orders", json={
        "project_name": "Invalid Product",
        "lines": [
            {"product_id": 99999, "quantity": 1},
        ],
    })
    assert resp.status_code == 404  # Not found
