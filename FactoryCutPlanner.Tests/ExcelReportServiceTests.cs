using System;
using System.IO;
using FactoryCutPlanner.Services;
using FactoryCutPlanner.Models;
using Xunit;
using System.Collections.Generic;

namespace FactoryCutPlanner.Tests;

public class ExcelReportServiceTests
{
    [Fact]
    public void GenerateMrpReport_ShouldCreateValidExcelFile()
    {
        // Arrange
        var mrpData = new MrpCalculationResult
        {
            Header = new Dictionary<string, object>
            {
                { "project_name", "Test Project" },
                { "work_order_id", "1001" },
                { "generated_at", DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") },
                { "line_count", 2 },
                { "total_quantity", 10 },
                { "waste_factor", 0.05m }
            },
            Summary = new Dictionary<string, object>
            {
                { "material", new {
                    sheet_area_m2 = 150.23m,
                    sheet_mass_kg = 850.5m,
                    insulation_area_m2 = 120.0m,
                    profile_length_m = 45.0m
                }},
                { "cost", new {
                    bom_total = 15500.50m
                }}
            },
            Lines = new List<Dictionary<string, object>>
            {
                new Dictionary<string, object>
                {
                    { "line_number", 1 },
                    { "product_name", "Hava Kanalı 500x500" },
                    { "quantity", 5 },
                    { "totals", new {
                        sheet_area_m2 = 75.1m,
                        sheet_mass_kg = 425.2m,
                        insulation_area_m2 = 60.0m,
                        profile_length_m = 0.0m
                    }}
                },
                new Dictionary<string, object>
                {
                    { "line_number", 2 },
                    { "product_name", "Hücreli Aspiratör" },
                    { "quantity", 5 },
                    { "totals", new {
                        sheet_area_m2 = 75.13m,
                        sheet_mass_kg = 425.3m,
                        insulation_area_m2 = 60.0m,
                        profile_length_m = 45.0m
                    }}
                }
            }
        };

        var service = new ExcelReportService();

        // Act
        var resultBytes = service.GenerateMrpReport(mrpData);

        // Assert
        Assert.NotNull(resultBytes);
        Assert.True(resultBytes.Length > 0);

        // Write to a temporary file for visual inspection if needed
        var filePath = "test_mrp_report.xlsx";
        File.WriteAllBytes(filePath, resultBytes);
        Assert.True(File.Exists(filePath));
        
        // Clean up
        if (File.Exists(filePath))
        {
            File.Delete(filePath);
        }
    }
}
