using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.EntityFrameworkCore;
using Xunit;
using Xunit.Abstractions;
using FactoryCutPlanner.Data;
using FactoryCutPlanner.Services;

namespace FactoryCutPlanner.Tests;

public class RealDataMrpTests
{
    private readonly ITestOutputHelper _output;

    public RealDataMrpTests(ITestOutputHelper output)
    {
        _output = output;
    }

    [Fact]
    public void RunMrpOnRealDatabase_ShouldComputeResults()
    {
        string baseDir = AppDomain.CurrentDomain.BaseDirectory;
        string dbPath = Path.GetFullPath(Path.Combine(baseDir, "../../../../hvac_factory_ops.db"));

        _output.WriteLine($"Using database at: {dbPath}");
        Assert.True(File.Exists(dbPath), $"Veritabanı bulunamadı: {dbPath}");

        using var db = new AppDbContext(dbPath);

        // Get the first work order that has lines or is a legacy work order
        var workOrder = db.WorkOrders
            .Include(w => w.Lines)
                .ThenInclude(l => l.Product)
                    .ThenInclude(p => p.BomItems)
            .Include(w => w.Product)
                .ThenInclude(p => p.BomItems)
            .FirstOrDefault();

        Assert.NotNull(workOrder);
        _output.WriteLine($"Found Work Order ID: {workOrder.Id}, Project: {workOrder.ProjectName}");

        var service = new MrpService();
        var result = service.ComputeWorkOrder(workOrder);

        var optionsJson = new JsonSerializerOptions { WriteIndented = true };
        string jsonOutput = JsonSerializer.Serialize(result, optionsJson);
        
        _output.WriteLine("=== MRP CALCULATION RESULT ===");
        _output.WriteLine(jsonOutput);
    }
}
