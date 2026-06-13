from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from pydantic import ValidationError

from core.errors import ValidationAppException
from core.settings import Settings
from modules.products.schemas import AHUSpec, FittingSpec, RectangularDuctSpec
from modules.products.types import ProductType
from modules.work_orders.models import WorkOrder, WorkOrderLine
from modules.mrp.nesting import optimize_1d_cuts


class MRPService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _resolve_work_order_waste_factor(self, work_order: WorkOrder) -> float:
        """Prefer work-order waste factor; fallback to legacy global setting."""
        value = getattr(work_order, "waste_factor", None)
        if value is None:
            value = self.settings.waste_factor
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            parsed = 0.0
        return max(0.0, parsed)

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
        agg_profile_length = 0.0
        agg_bom_cost: float = 0.0
        total_quantity = 0
        waste_factor = self._resolve_work_order_waste_factor(work_order)
        waste_multiplier = 1.0 + waste_factor

        # Separate aggregation for priced and unpriced items
        # Key: (name, unit), Value: {"total_quantity": float, "cost_per_unit": float, "total_cost": float}
        priced_bom_agg: Dict[Tuple[str, str], Dict[str, Any]] = defaultdict(
            lambda: {"total_quantity": 0.0, "cost_per_unit": None, "total_cost": 0.0}
        )
        unpriced_bom_agg: Dict[Tuple[str, str], Dict[str, float]] = defaultdict(
            lambda: {"total_quantity": 0.0}
        )

        agg_profile_pieces_mm = []

        for line_number, line in enumerate(lines, start=1):
            product = line.product
            qty = line.quantity
            total_quantity += qty

            try:
                if product.product_type == ProductType.RECTANGULAR_DUCT.value:
                    spec = RectangularDuctSpec(**product.attributes)
                    sheet_area_per_unit = 2 * (spec.width_mm + spec.height_mm) * spec.length_mm / 1_000_000
                    sheet_mass_per_unit = sheet_area_per_unit * (spec.thickness_mm / 1000.0) * self.settings.steel_density_kg_m3
                    insulation_area_per_unit = sheet_area_per_unit if spec.insulation_enabled else 0.0
                    profile_length_per_unit = 0.0

                elif product.product_type == ProductType.AHU_CABINET.value:
                    spec = AHUSpec(**product.attributes)
                    W, H, L = spec.width_mm, spec.height_mm, spec.length_mm
                    sheet_area_per_unit = 2 * (W*H + W*L + H*L) / 1_000_000
                    sheet_mass_per_unit = sheet_area_per_unit * (spec.panel_thickness_mm / 1000.0) * self.settings.steel_density_kg_m3
                    insulation_area_per_unit = sheet_area_per_unit
                    profile_length_per_unit = (4 * (W + H + L) / 1000.0) if spec.has_profile_framework else 0.0

                    if spec.has_profile_framework:
                        ahu_pieces = ([spec.width_mm] * 4 + [spec.height_mm] * 4 + [spec.length_mm] * 4) * qty
                        agg_profile_pieces_mm.extend(ahu_pieces)

                elif product.product_type == ProductType.FITTING_DUCT.value:
                    spec = FittingSpec(**product.attributes)
                    base_area = (spec.main_dimension_mm / 1000.0) ** 2 * 3.14 * 1.5
                    sheet_area_per_unit = base_area * 1.30
                    sheet_mass_per_unit = sheet_area_per_unit * (spec.thickness_mm / 1000.0) * self.settings.steel_density_kg_m3
                    insulation_area_per_unit = 0.0
                    profile_length_per_unit = 0.0

                else:
                    raise ValidationAppException("Ürün tipi için hesaplama tanımlı değil")
            except ValidationError as exc:
                raise ValidationAppException("Ürün ölçüleri geçersiz") from exc

            sheet_area_line = sheet_area_per_unit * qty * waste_multiplier
            sheet_mass_line = sheet_mass_per_unit * qty * waste_multiplier
            insulation_area_line = insulation_area_per_unit * qty * waste_multiplier
            profile_length_line = profile_length_per_unit * qty * waste_multiplier

            agg_sheet_area += sheet_area_line
            agg_sheet_mass += sheet_mass_line
            agg_insulation_area += insulation_area_line
            agg_profile_length += profile_length_line

            for item in product.bom_items:
                total_qty = item.quantity_per_unit * qty * waste_multiplier
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
                        "profile_length_m": profile_length_per_unit,
                    },
                    "totals": {
                        "sheet_area_m2": sheet_area_line,
                        "sheet_mass_kg": sheet_mass_line,
                        "insulation_area_m2": insulation_area_line,
                        "profile_length_m": profile_length_line,
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
                "waste_factor": waste_factor,
                "waste_factor_pct": waste_factor * 100.0,
            },
            "summary": {
                "material": {
                    "sheet_area_m2": agg_sheet_area,
                    "sheet_mass_kg": agg_sheet_mass,
                    "insulation_area_m2": agg_insulation_area,
                    "profile_length_m": agg_profile_length,
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
            "notes": "Hesaplama tüm ürün tipleri için yapılmıştır.",
        }

        if agg_profile_pieces_mm:
            nesting_result = optimize_1d_cuts(agg_profile_pieces_mm)
            result["summary"]["material"]["profile_nesting"] = nesting_result

        return result
