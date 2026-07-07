using System.Collections.Generic;
using System.Text.Json;
using FactoryCutPlanner.Models;
using FactoryCutPlanner.Services;
using Xunit;

namespace FactoryCutPlanner.Tests;

public class MrpServiceTests
{
    [Fact]
    public void ComputeWorkOrder_RectangularDuct_CalculatesAreaAndMassCorrectly()
    {
        // Arrange
        var mrpService = new MrpService();
        
        var product = new Product
        {
            Id = 1,
            Name = "Test Duct",
            ProductType = "RECTANGULAR_DUCT",
            Attributes = new Dictionary<string, JsonElement>
            {
                { "width_mm", JsonSerializer.SerializeToElement(500) },
                { "height_mm", JsonSerializer.SerializeToElement(500) },
                { "length_mm", JsonSerializer.SerializeToElement(1000) },
                { "thickness_mm", JsonSerializer.SerializeToElement(1.0) },
                { "insulation_enabled", JsonSerializer.SerializeToElement(true) }
            },
            BomItems = new List<BomItem>()
        };

        var workOrder = new WorkOrder
        {
            Id = 1,
            Lines = new List<WorkOrderLine>
            {
                new WorkOrderLine { ProductId = 1, Quantity = 2, Product = product }
            }
        };

        // Act
        var result = mrpService.ComputeWorkOrder(workOrder);

        // Assert
        // Area per unit = 2 * (500+500) * 1000 / 1,000,000 = 2.0 m2
        // Total area for qty 2 = 4.0 m2
        // Mass per unit = 2.0 * (1.0/1000) * 7850 = 15.7 kg
        // Total mass for qty 2 = 31.4 kg

        var summary = result.Summary["material"] as dynamic;
        var sheetArea = (decimal)summary.GetType().GetProperty("sheet_area_m2").GetValue(summary, null);
        var sheetMass = (decimal)summary.GetType().GetProperty("sheet_mass_kg").GetValue(summary, null);

        Assert.Equal(4.0m, sheetArea);
        Assert.Equal(31.4m, sheetMass);
    }
}
