using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using ClosedXML.Excel;
using FactoryCutPlanner.Data;
using FactoryCutPlanner.Models;

namespace FactoryCutPlanner.Services;

public class ExcelImportService
{
    public (bool Success, string Message) ImportWorkOrder(string filePath, string projectName, decimal wasteFactor)
    {
        if (string.IsNullOrWhiteSpace(projectName))
        {
            return (false, "Excel içe aktarımı için Proje Adı zorunludur.");
        }

        try
        {
            using var workbook = new XLWorkbook(filePath);
            var worksheet = workbook.Worksheets.FirstOrDefault();
            if (worksheet == null)
            {
                return (false, "Excel dosyasında sayfa bulunamadı.");
            }

            // Find columns by header name (row 1 is assumed to be header)
            var headers = worksheet.Row(1).CellsUsed().ToDictionary(c => c.GetString().Trim(), c => c.Address.ColumnNumber);
            
            var expectedCols = new[] { "Ürün Adı", "Miktar", "Genişlik", "Yükseklik", "Uzunluk", "Kalınlık" };
            foreach (var col in expectedCols)
            {
                if (!headers.ContainsKey(col))
                {
                    return (false, $"Eksik kolon: {col}");
                }
            }

            using var db = new AppDbContext();
            
            var now = DateTime.UtcNow.ToString("yyyy-MM-dd HH:mm:ss");
            var workOrder = new WorkOrder
            {
                ProjectName = projectName,
                WasteFactor = wasteFactor,
                CreatedAt = now,
                UpdatedAt = now
            };

            var lastRowUsed = worksheet.LastRowUsed().RowNumber();
            int importedLines = 0;

            for (int i = 2; i <= lastRowUsed; i++)
            {
                var row = worksheet.Row(i);
                if (row.IsEmpty()) continue;

                var qtyString = row.Cell(headers["Miktar"]).GetString();
                if (string.IsNullOrWhiteSpace(qtyString) || !int.TryParse(qtyString, out var qty) || qty <= 0)
                {
                    continue; // Skip invalid quantities
                }

                var name = row.Cell(headers["Ürün Adı"]).GetString();
                if (string.IsNullOrWhiteSpace(name))
                {
                    return (false, $"Satır {i} işlenirken hata: Ürün Adı boş olamaz.");
                }

                decimal width = GetDecimalValue(row.Cell(headers["Genişlik"]));
                decimal height = GetDecimalValue(row.Cell(headers["Yükseklik"]));
                decimal length = GetDecimalValue(row.Cell(headers["Uzunluk"]));
                decimal thickness = GetDecimalValue(row.Cell(headers["Kalınlık"]));

                // Create spec
                var spec = new RectangularDuctSpec
                {
                    WidthMm = width,
                    HeightMm = height,
                    LengthMm = length,
                    ThicknessMm = thickness,
                    InsulationEnabled = false
                };

                // Convert spec to dictionary for Attributes
                var json = JsonSerializer.Serialize(spec);
                var attributes = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(json) ?? new Dictionary<string, JsonElement>();

                // Create new Product for each row
                var product = new Product
                {
                    Name = name,
                    Description = "Excel'den içe aktarıldı",
                    ProductType = "RECTANGULAR_DUCT",
                    Attributes = attributes,
                    CreatedAt = now,
                    UpdatedAt = now
                };

                db.Products.Add(product);
                
                // Add to WorkOrder
                workOrder.Lines.Add(new WorkOrderLine
                {
                    Product = product,
                    Quantity = qty,
                    CreatedAt = now,
                    UpdatedAt = now
                });
                
                importedLines++;
            }

            if (importedLines == 0)
            {
                return (false, "İçe aktarılacak geçerli satır bulunamadı.");
            }

            db.WorkOrders.Add(workOrder);
            db.SaveChanges();

            return (true, $"'{projectName}' iş emri Excel'den içe aktarıldı.");
        }
        catch (Exception ex)
        {
            return (false, $"Excel dosyası okunurken hata: {ex.Message}");
        }
    }

    private decimal GetDecimalValue(IXLCell cell)
    {
        if (cell.TryGetValue<double>(out var val))
        {
            return (decimal)val;
        }
        if (cell.TryGetValue<string>(out var strVal) && decimal.TryParse(strVal, out var decVal))
        {
            return decVal;
        }
        return 0m;
    }
}
