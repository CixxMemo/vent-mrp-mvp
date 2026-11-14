using System.Text.Json;
using FactoryCutPlanner.Data;
using FactoryCutPlanner.Models;
using FactoryCutPlanner.Services;
using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;

namespace FactoryCutPlanner.Tests;

/// <summary>
/// End-to-end check against a real SQLite file: the app must be able to create
/// its own schema from scratch, persist a work order, read it back, and compute
/// the same MRP numbers as the in-memory tests.
/// </summary>
public class DatabaseMrpTests : IDisposable
{
    private readonly string _dbPath =
        Path.Combine(Path.GetTempPath(), $"factorycut-test-{Guid.NewGuid():N}.db");

    public void Dispose()
    {
        // Pooled connections keep the file locked on Windows.
        SqliteConnection.ClearAllPools();
        if (File.Exists(_dbPath))
        {
            File.Delete(_dbPath);
        }
    }

    [Fact]
    public void FreshDatabase_IsCreated_AndWorkOrderRoundTripsThroughMrp()
    {
        // Arrange: no database file exists yet — the app has to create it.
        Assert.False(File.Exists(_dbPath));

        using (var db = new AppDbContext(_dbPath))
        {
            Assert.True(db.Database.EnsureCreated());

            var product = new Product
            {
                Name = "Test Kanal 500x500",
                ProductType = "RECTANGULAR_DUCT",
                Attributes = new Dictionary<string, JsonElement>
                {
                    { "width_mm", JsonSerializer.SerializeToElement(500) },
                    { "height_mm", JsonSerializer.SerializeToElement(500) },
                    { "length_mm", JsonSerializer.SerializeToElement(1000) },
                    { "thickness_mm", JsonSerializer.SerializeToElement(1.0) },
                    { "insulation_enabled", JsonSerializer.SerializeToElement(true) }
                },
                BomItems = new List<BomItem>
                {
                    new BomItem { Name = "Galvaniz Sac", Unit = "kg", QuantityPerUnit = 10m, CostPerUnit = 45m }
                }
            };

            var workOrder = new WorkOrder { ProjectName = "Test Projesi", WasteFactor = 0m };
            workOrder.Lines.Add(new WorkOrderLine { Product = product, Quantity = 2 });

            db.WorkOrders.Add(workOrder);
            db.SaveChanges();
        }

        // Act: load through a fresh context, the same way the MRP page does.
        MrpCalculationResult result;
        using (var db = new AppDbContext(_dbPath))
        {
            var workOrder = db.WorkOrders
                .Include(w => w.Lines)
                    .ThenInclude(l => l.Product)
                        .ThenInclude(p => p.BomItems)
                .Single();

            result = new MrpService().ComputeWorkOrder(workOrder);
        }

        // Assert
        // Area: 2 * (500 + 500) * 1000 / 1,000,000 = 2.0 m2 per unit, x2 = 4.0 m2
        // Mass: 2.0 * (1.0 / 1000) * 7850 = 15.7 kg per unit, x2 = 31.4 kg
        // Cost: 10 kg * 2 units * 45 TL = 900 TL
        Assert.Equal(4.0m, ReadDecimal(result.Summary["material"], "sheet_area_m2"));
        Assert.Equal(31.4m, ReadDecimal(result.Summary["material"], "sheet_mass_kg"));
        Assert.Equal(4.0m, ReadDecimal(result.Summary["material"], "insulation_area_m2"));
        Assert.Equal(900m, ReadDecimal(result.Summary["cost"], "bom_total"));
    }

    // MrpService returns anonymous objects inside its dictionaries, so the values
    // can only be read by reflection.
    private static decimal ReadDecimal(object source, string propertyName)
    {
        var property = source.GetType().GetProperty(propertyName);
        Assert.NotNull(property);
        return (decimal)property.GetValue(source)!;
    }
}
