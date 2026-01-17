from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from pydantic import ValidationError

from core.errors import ValidationAppException
from core.settings import Settings
from modules.products.schemas import RectangularDuctSpec
from modules.products.types import ProductType
from modules.work_orders.models import WorkOrder, WorkOrderLine


class MRPService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def compute_work_order(self, work_order: WorkOrder) -> Dict[str, Any]:
        lines = work_order.lines or []
        if not lines:
            # Legacy fallback: if a single legacy product exists
            if work_order.product_id and work_order.quantity and work_order.product:
                legacy_line = WorkOrderLine(
                    product_id=work_order.product_id,
                    quantity=work_order.quantity,
                    product=work_order.product,
                )
                lines = [legacy_line]
            else:
                raise ValidationAppException("İş emri satırı bulunamadı")

        per_line_results: List[Dict[str, Any]] = []
        agg_sheet_area = 0.0
        agg_sheet_mass = 0.0
        agg_insulation_area = 0.0
        agg_bom_cost: float = 0.0
        total_quantity = 0

        # Separate aggregation for priced and unpriced items
        # Key: (name, unit), Value: {"total_quantity": float, "cost_per_unit": float, "total_cost": float}
        priced_bom_agg: Dict[Tuple[str, str], Dict[str, Any]] = defaultdict(
            lambda: {"total_quantity": 0.0, "cost_per_unit": None, "total_cost": 0.0}
        )
        unpriced_bom_agg: Dict[Tuple[str, str], Dict[str, float]] = defaultdict(
            lambda: {"total_quantity": 0.0}
        )

        for line_number, line in enumerate(lines, start=1):
            product = line.product
            if product.product_type != ProductType.RECTANGULAR_DUCT.value:
                raise ValidationAppException("Ürün tipi için hesaplama tanımlı değil")
            try:
                spec = RectangularDuctSpec(**product.attributes)
            except ValidationError as exc:
                raise ValidationAppException("Ürün ölçüleri geçersiz") from exc

            qty = line.quantity
            total_quantity += qty
            base_sheet_area = 2 * (spec.width_mm + spec.height_mm) * spec.length_mm / 1_000_000
            sheet_area_per_unit = base_sheet_area * (1 + self.settings.waste_factor)
            sheet_mass_per_unit = sheet_area_per_unit * (spec.thickness_mm / 1000.0) * self.settings.steel_density_kg_m3
            insulation_area_per_unit = sheet_area_per_unit if spec.insulation_enabled else 0.0

            sheet_area_line = sheet_area_per_unit * qty
            sheet_mass_line = sheet_mass_per_unit * qty
            insulation_area_line = insulation_area_per_unit * qty

            agg_sheet_area += sheet_area_line
            agg_sheet_mass += sheet_mass_line
            agg_insulation_area += insulation_area_line

            for item in product.bom_items:
                total_qty = item.quantity_per_unit * qty
                key = (item.name, item.unit or "")

                if item.cost_per_unit is not None:
                    # Priced item
                    item_total_cost = item.cost_per_unit * total_qty
                    agg_bom_cost += item_total_cost
                    entry = priced_bom_agg[key]
                    entry["total_quantity"] += total_qty
                    entry["cost_per_unit"] = item.cost_per_unit
                    entry["total_cost"] += item_total_cost
                else:
                    # Unpriced item
                    unpriced_bom_agg[key]["total_quantity"] += total_qty

            per_line_results.append(
                {
                    "line_number": line_number,
                    "line_id": line.id,
                    "product_id": product.id,
                    "product_name": product.name,
                    "quantity": qty,
                    "per_unit": {
                        "sheet_area_m2": sheet_area_per_unit,
                        "sheet_mass_kg": sheet_mass_per_unit,
                        "insulation_area_m2": insulation_area_per_unit,
                    },
                    "totals": {
                        "sheet_area_m2": sheet_area_line,
                        "sheet_mass_kg": sheet_mass_line,
                        "insulation_area_m2": insulation_area_line,
                    },
                }
            )

        # Build priced items list
        priced_items: List[Dict[str, Any]] = []
        for (name, unit), data in priced_bom_agg.items():
            cost_share_pct = (data["total_cost"] / agg_bom_cost * 100) if agg_bom_cost > 0 else 0.0
            priced_items.append(
                {
                    "name": name,
                    "unit": unit,
                    "total_quantity": data["total_quantity"],
                    "cost_per_unit": data["cost_per_unit"],
                    "total_cost": data["total_cost"],
                    "cost_share_pct": cost_share_pct,
                }
            )

        # Sort priced items by total_cost descending (highest impact first)
        priced_items.sort(key=lambda x: x["total_cost"], reverse=True)

        # Build unpriced items list
        unpriced_items: List[Dict[str, Any]] = []
        for (name, unit), data in unpriced_bom_agg.items():
            unpriced_items.append(
                {
                    "name": name,
                    "unit": unit,
                    "total_quantity": data["total_quantity"],
                }
            )

        total_item_count = len(priced_items) + len(unpriced_items)
        priced_item_count = len(priced_items)
        unpriced_item_count = len(unpriced_items)
        cost_completeness_pct = (priced_item_count / total_item_count * 100) if total_item_count > 0 else 100.0

        result = {
            "header": {
                "project_name": work_order.project_name,
                "work_order_id": work_order.id,
                "generated_at": datetime.now().isoformat(),
                "line_count": len(lines),
                "total_quantity": total_quantity,
            },
            "summary": {
                "material": {
                    "sheet_area_m2": agg_sheet_area,
                    "sheet_mass_kg": agg_sheet_mass,
                    "insulation_area_m2": agg_insulation_area,
                },
                "cost": {
                    "bom_total": agg_bom_cost,
                    "items_with_cost": priced_item_count,
                    "items_missing_cost": unpriced_item_count,
                    "cost_complete": unpriced_item_count == 0,
                },
            },
            "lines": per_line_results,
            "bom_summary": {
                "metrics": {
                    "total_item_count": total_item_count,
                    "priced_item_count": priced_item_count,
                    "unpriced_item_count": unpriced_item_count,
                    "total_cost": agg_bom_cost,
                    "cost_completeness_pct": cost_completeness_pct,
                },
                "priced_items": priced_items,
                "unpriced_items": unpriced_items,
            },
            "notes": "Hesaplama dikdörtgen kanal için yapılmıştır.",
        }
        return result
