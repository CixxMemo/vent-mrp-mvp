using System.Collections.Generic;

namespace FactoryCutPlanner.Models;

/// <summary>
/// Maps to the "work_orders" table.
///
/// A work order represents a manufacturing project (e.g., "Merkez AVM Havalandırma").
/// It contains multiple lines (WorkOrderLine), each specifying a product and quantity.
///
/// Legacy fields (ProductId, Quantity): The old Python version stored a single product
/// per work order. The new version uses WorkOrderLines for multi-product orders.
/// These legacy columns are kept for backward compatibility with existing data.
/// </summary>
public partial class WorkOrder
{
    public int Id { get; set; }

    public string ProjectName { get; set; } = null!;

    /// <summary>Legacy: old schema had one product per order. Nullable, not used in new logic.</summary>
    public int? ProductId { get; set; }

    /// <summary>Legacy: old schema had quantity here. Nullable, not used in new logic.</summary>
    public int? Quantity { get; set; }

    /// <summary>
    /// Waste/scrap factor as a percentage (0.05 = 5%).
    /// Added to material requirements to account for cutting waste.
    /// WHY decimal: same reason as BomItem — exact financial arithmetic.
    /// </summary>
    public decimal? WasteFactor { get; set; }

    public string CreatedAt { get; set; } = null!;

    public string UpdatedAt { get; set; } = null!;

    /// <summary>Legacy navigation — old work orders pointed directly to a product.</summary>
    public virtual Product? Product { get; set; }

    /// <summary>
    /// The line items of this work order.
    /// Named "Lines" to match the Python model's "lines" relationship,
    /// making cross-reference between Python and C# code easier during migration.
    /// </summary>
    public virtual ICollection<WorkOrderLine> Lines { get; set; } = new List<WorkOrderLine>();
}
