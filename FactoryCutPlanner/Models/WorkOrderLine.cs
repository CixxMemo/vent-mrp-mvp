namespace FactoryCutPlanner.Models;

/// <summary>
/// Maps to the "work_order_lines" table.
///
/// Each line says: "this work order needs X units of product Y."
/// Example: Work Order "AVM Havalandırma" → 25 units of "Dikdörtgen Kanal 600x400"
///
/// Foreign key behaviors (these MUST match the Python/SQLite schema):
///   - work_order_id → ON DELETE CASCADE (delete work order → delete its lines)
///   - product_id → ON DELETE RESTRICT (can't delete a product used in a work order)
/// </summary>
public partial class WorkOrderLine
{
    public int Id { get; set; }

    public int WorkOrderId { get; set; }

    public int ProductId { get; set; }

    public int Quantity { get; set; }

    public string CreatedAt { get; set; } = null!;

    public string UpdatedAt { get; set; } = null!;

    // Navigation: which product this line refers to
    public virtual Product Product { get; set; } = null!;

    // Navigation: which work order this line belongs to
    public virtual WorkOrder WorkOrder { get; set; } = null!;
}
