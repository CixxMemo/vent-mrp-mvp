using System.Collections.Generic;
using System.Text.Json;

namespace FactoryCutPlanner.Models;

/// <summary>
/// Maps to the "products" table.
/// 
/// Each product has a type (RECTANGULAR_DUCT, AHU_CABINET, FITTING_DUCT)
/// and a polymorphic JSON "attributes" column that stores type-specific specs.
/// 
/// Navigation properties:
///   - BomItems: the Bill of Materials (list of raw materials and their costs)
///   - WorkOrderLines: which work order lines reference this product
///   - WorkOrders: legacy direct product-to-work-order relationship (deprecated)
/// </summary>
public partial class Product
{
    public int Id { get; set; }

    public string Name { get; set; } = null!;

    public string? Description { get; set; }

    public string ProductType { get; set; } = null!;

    /// <summary>
    /// Stores product specifications as JSON.
    /// WHY Dictionary&lt;string, JsonElement&gt;:
    /// Each product_type has different keys (width_mm, panel_thickness_mm, etc.).
    /// A generic dictionary handles all shapes. Parsing into strongly-typed specs
    /// happens in the service layer (Phase 3).
    /// </summary>
    public Dictionary<string, JsonElement> Attributes { get; set; } = new();

    public string CreatedAt { get; set; } = null!;

    public string UpdatedAt { get; set; } = null!;

    // Navigation: one product has many BOM items
    public virtual ICollection<BomItem> BomItems { get; set; } = new List<BomItem>();

    // Navigation: one product can appear in many work order lines
    public virtual ICollection<WorkOrderLine> WorkOrderLines { get; set; } = new List<WorkOrderLine>();

    // Navigation: legacy relationship — old work orders pointed directly to a product
    public virtual ICollection<WorkOrder> WorkOrders { get; set; } = new List<WorkOrder>();
}
