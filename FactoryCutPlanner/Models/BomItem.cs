namespace FactoryCutPlanner.Models;

/// <summary>
/// Maps to the "bom_items" table (Bill of Materials).
///
/// Each BOM item represents one raw material or component needed to build a product.
/// Example: "Galvaniz Sac (0.80 mm)", 18.5 kg per unit, 45.0 TL/kg.
///
/// WHY decimal for QuantityPerUnit and CostPerUnit:
/// Python uses float64 which introduces rounding errors in multiplication
/// (e.g., 45.0 * 18.5 = 832.9999...). C#'s decimal type uses base-10 arithmetic,
/// giving exact results (832.50). For cost calculations, exactness is critical.
/// </summary>
public partial class BomItem
{
    public int Id { get; set; }

    public int ProductId { get; set; }

    public string Name { get; set; } = null!;

    public string? Unit { get; set; }

    /// <summary>
    /// How much of this material is needed per one product unit.
    /// Example: 18.5 kg of galvanized sheet per duct.
    /// WHY decimal: exact arithmetic for cost calculations.
    /// </summary>
    public decimal QuantityPerUnit { get; set; }

    /// <summary>
    /// Cost per unit of this material (e.g., 45.0 TL/kg).
    /// Nullable because some BOM items may not have a price yet —
    /// MRP will flag these as "fiyat eksik" (missing price) warnings.
    /// WHY decimal: exact arithmetic for cost calculations.
    /// </summary>
    public decimal? CostPerUnit { get; set; }

    public string CreatedAt { get; set; } = null!;

    public string UpdatedAt { get; set; } = null!;

    // Navigation: each BOM item belongs to exactly one product
    public virtual Product Product { get; set; } = null!;
}
