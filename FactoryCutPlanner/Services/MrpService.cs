using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using FactoryCutPlanner.Models;

namespace FactoryCutPlanner.Services;

public class MrpCalculationResult
{
    public Dictionary<string, object> Header { get; set; } = new();
    public Dictionary<string, object> Summary { get; set; } = new();
    public List<Dictionary<string, object>> Lines { get; set; } = new();
    public Dictionary<string, object> BomSummary { get; set; } = new();
    public string Notes { get; set; } = string.Empty;
}

public class MrpService
{
    private const decimal SteelDensityKgM3 = 7850.0m;

    public MrpCalculationResult ComputeWorkOrder(WorkOrder workOrder, decimal defaultWasteFactor = 0.0m)
    {
        var lines = workOrder.Lines?.ToList() ?? new List<WorkOrderLine>();
        if (!lines.Any())
        {
            if (workOrder.ProductId.HasValue && workOrder.Quantity.HasValue && workOrder.Product != null)
            {
                lines.Add(new WorkOrderLine
                {
                    ProductId = workOrder.ProductId.Value,
                    Quantity = workOrder.Quantity.Value,
                    Product = workOrder.Product
                });
            }
            else
            {
                throw new Exception("İş emri satırı bulunamadı");
            }
        }

        decimal aggSheetArea = 0.0m;
        decimal aggSheetMass = 0.0m;
        decimal aggInsulationArea = 0.0m;
        decimal aggProfileLength = 0.0m;
        decimal aggBomCost = 0.0m;
        int totalQuantity = 0;
        
        decimal wasteFactor = defaultWasteFactor;
        decimal wasteMultiplier = 1.0m + wasteFactor;

        var pricedBomAgg = new Dictionary<(string name, string unit), (decimal totalQuantity, decimal? costPerUnit, decimal totalCost)>();
        var unpricedBomAgg = new Dictionary<(string name, string unit), decimal>();

        var perLineResults = new List<Dictionary<string, object>>();

        int lineNumber = 1;
        foreach (var line in lines)
        {
            var product = line.Product;
            int qty = line.Quantity;
            totalQuantity += qty;

            decimal sheetAreaPerUnit = 0.0m;
            decimal sheetMassPerUnit = 0.0m;
            decimal insulationAreaPerUnit = 0.0m;
            decimal profileLengthPerUnit = 0.0m;

            // Deserialize attributes
            var jsonString = JsonSerializer.Serialize(product.Attributes);

            if (product.ProductType == "RECTANGULAR_DUCT")
            {
                var spec = JsonSerializer.Deserialize<RectangularDuctSpec>(jsonString)!;
                sheetAreaPerUnit = 2m * (spec.WidthMm + spec.HeightMm) * spec.LengthMm / 1_000_000m;
                sheetMassPerUnit = sheetAreaPerUnit * (spec.ThicknessMm / 1000m) * SteelDensityKgM3;
                insulationAreaPerUnit = spec.InsulationEnabled ? sheetAreaPerUnit : 0.0m;
            }
            else if (product.ProductType == "AHU_CABINET")
            {
                var spec = JsonSerializer.Deserialize<AHUSpec>(jsonString)!;
                decimal w = spec.WidthMm;
                decimal h = spec.HeightMm;
                decimal l = spec.LengthMm;
                sheetAreaPerUnit = 2m * (w * h + w * l + h * l) / 1_000_000m;
                sheetMassPerUnit = sheetAreaPerUnit * (spec.PanelThicknessMm / 1000m) * SteelDensityKgM3;
                insulationAreaPerUnit = sheetAreaPerUnit;
                profileLengthPerUnit = spec.HasProfileFramework ? (4m * (w + h + l) / 1000m) : 0.0m;
            }
            else if (product.ProductType == "FITTING_DUCT")
            {
                var spec = JsonSerializer.Deserialize<FittingSpec>(jsonString)!;
                decimal baseArea = (spec.MainDimensionMm / 1000m) * (spec.MainDimensionMm / 1000m) * 3.14m * 1.5m;
                sheetAreaPerUnit = baseArea * 1.30m;
                sheetMassPerUnit = sheetAreaPerUnit * (spec.ThicknessMm / 1000m) * SteelDensityKgM3;
            }
            else
            {
                throw new Exception("Ürün tipi için hesaplama tanımlı değil");
            }

            decimal sheetAreaLine = sheetAreaPerUnit * qty * wasteMultiplier;
            decimal sheetMassLine = sheetMassPerUnit * qty * wasteMultiplier;
            decimal insulationAreaLine = insulationAreaPerUnit * qty * wasteMultiplier;
            decimal profileLengthLine = profileLengthPerUnit * qty * wasteMultiplier;

            aggSheetArea += sheetAreaLine;
            aggSheetMass += sheetMassLine;
            aggInsulationArea += insulationAreaLine;
            aggProfileLength += profileLengthLine;

            foreach (var item in product.BomItems)
            {
                decimal totalQty = (decimal)item.QuantityPerUnit * qty * wasteMultiplier;
                (string name, string unit) key = (item.Name, item.Unit ?? "");

                if (item.CostPerUnit.HasValue)
                {
                    decimal itemTotalCost = (decimal)item.CostPerUnit.Value * totalQty;
                    aggBomCost += itemTotalCost;
                    if (!pricedBomAgg.ContainsKey(key))
                        pricedBomAgg[key] = (0m, null, 0m);
                    
                    var existing = pricedBomAgg[key];
                    pricedBomAgg[key] = (existing.totalQuantity + totalQty, (decimal)item.CostPerUnit.Value, existing.totalCost + itemTotalCost);
                }
                else
                {
                    if (!unpricedBomAgg.ContainsKey(key))
                        unpricedBomAgg[key] = 0m;
                    unpricedBomAgg[key] += totalQty;
                }
            }

            perLineResults.Add(new Dictionary<string, object>
            {
                { "line_number", lineNumber++ },
                { "product_id", product.Id },
                { "product_name", product.Name },
                { "quantity", qty },
                { "totals", new {
                    sheet_area_m2 = sheetAreaLine,
                    sheet_mass_kg = sheetMassLine,
                    insulation_area_m2 = insulationAreaLine,
                    profile_length_m = profileLengthLine
                }}
            });
        }

        var pricedItems = pricedBomAgg.Select(x => new Dictionary<string, object>
        {
            { "name", x.Key.name },
            { "unit", x.Key.unit },
            { "total_quantity", x.Value.totalQuantity },
            { "cost_per_unit", x.Value.costPerUnit! },
            { "total_cost", x.Value.totalCost }
        }).OrderByDescending(x => (decimal)x["total_cost"]).ToList();

        var unpricedItems = unpricedBomAgg.Select(x => new Dictionary<string, object>
        {
            { "name", x.Key.name },
            { "unit", x.Key.unit },
            { "total_quantity", x.Value }
        }).OrderBy(x => (string)x["name"]).ToList();

        foreach (var p in pricedItems)
        {
            decimal itemCost = (decimal)p["total_cost"];
            p["cost_share_pct"] = aggBomCost > 0 ? (itemCost / aggBomCost) * 100m : 0m;
        }

        int totalBomItems = pricedItems.Count + unpricedItems.Count;
        decimal completenessPct = totalBomItems > 0 ? ((decimal)pricedItems.Count / totalBomItems) * 100m : 100m;

        var result = new MrpCalculationResult
        {
            Header = new Dictionary<string, object>
            {
                { "line_count", lines.Count },
                { "total_quantity", totalQuantity },
                { "waste_factor", wasteFactor },
                { "project_name", workOrder.ProjectName },
                { "work_order_id", workOrder.Id }
            },
            Summary = new Dictionary<string, object>
            {
                { "material", new {
                    sheet_area_m2 = aggSheetArea,
                    sheet_mass_kg = aggSheetMass,
                    insulation_area_m2 = aggInsulationArea,
                    profile_length_m = aggProfileLength
                }},
                { "cost", new {
                    bom_total = aggBomCost
                }}
            },
            Lines = perLineResults,
            BomSummary = new Dictionary<string, object>
            {
                { "priced_items", pricedItems },
                { "unpriced_items", unpricedItems },
                { "metrics", new { cost_completeness_pct = completenessPct } }
            }
        };

        return result;
    }
}
