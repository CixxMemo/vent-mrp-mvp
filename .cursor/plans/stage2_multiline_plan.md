### Stage 2 Multi-line Work Orders – Plan (no code yet)

1) Data model
   - Add `work_order_lines` table/model with `id, work_order_id (FK), product_id (FK), quantity (>0), created_at/updated_at`.
   - Remove usage of `work_orders.product_id/quantity` in code; keep columns for backward compatibility until migration finishes.
   - Relationship: WorkOrder has many WorkOrderLine; WorkOrderLine belongs to Product.

2) API
   - POST /work-orders: accept `project_name`, `lines:[{product_id, quantity}]`; validate ≥1 line and quantity>0; create lines.
   - GET /work-orders and /work-orders/{id}: return lines with embedded product summary.
   - MRP endpoints use the new lines.
   - Backward compatibility: for a limited period, accept legacy product_id/quantity by transforming into one line (optional, minimize scope if not required).

3) MRP logic
   - For each line: run existing product-type calc (rectangular duct) per-unit → multiply by line.quantity.
   - Aggregate totals across lines; merge BOM items by (name, unit) and sum quantities/costs; bom_cost becomes None if any item lacks cost.
   - Return line-level details + aggregated totals; Excel export uses aggregated data.

4) UI (minimal)
   - Work order form supports multiple lines: add/remove line, each with product selector + quantity.
   - Display selected work order with all lines and run MRP.
   - Keep industrial wording.

5) Steps to implement
   1. Models: add work_order_lines, update relationships; migrate existing records into lines (auto-create single line from legacy fields).
   2. Schemas/services: adjust create/list/get to use lines; optional legacy fallback.
   3. API routers: update payloads/responses.
   4. MRP service: iterate lines, aggregate totals/BOM; update Excel generator.
   5. UI: multi-line work order creation and display; MRP selection uses lines.
   6. Tests: extend MRP tests for multi-line aggregation and BOM merge.

