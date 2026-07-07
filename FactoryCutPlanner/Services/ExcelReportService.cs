using System;
using System.Collections.Generic;
using System.IO;
using ClosedXML.Excel;

namespace FactoryCutPlanner.Services;

public class ExcelReportService
{
    public byte[] GenerateMrpReport(MrpCalculationResult mrpData)
    {
        using var wb = new XLWorkbook();
        var ws = wb.Worksheets.Add("MRP Raporu");

        int currentRow = 1;

        // === SECTION 1: REPORT HEADER ===
        ws.Cell(currentRow, 1).Value = "MRP RAPORU";
        ws.Cell(currentRow, 1).Style.Font.SetBold(true);
        ws.Cell(currentRow, 1).Style.Font.FontSize = 14;
        ws.Range(currentRow, 1, currentRow, 6).Merge();
        currentRow += 2;

        var header = mrpData.Header;
        
        string projectStr = "-";
        string workOrderStr = "-";
        string dateStr = "-";
        int lineCount = 0;
        int totalQuantity = 0;
        decimal wasteFactor = 0m;

        if (header != null)
        {
            if (header.TryGetValue("project_name", out var pn) && pn != null) projectStr = pn.ToString()!;
            if (header.TryGetValue("work_order_id", out var wo) && wo != null) workOrderStr = $"#{wo}";
            if (header.TryGetValue("generated_at", out var dt) && dt != null)
            {
                var dtStr = dt.ToString()!;
                dateStr = dtStr.Length > 10 ? dtStr.Substring(0, 10) : dtStr;
            }
            if (header.TryGetValue("line_count", out var lc) && lc != null) lineCount = Convert.ToInt32(lc);
            if (header.TryGetValue("total_quantity", out var tq) && tq != null) totalQuantity = Convert.ToInt32(tq);
            if (header.TryGetValue("waste_factor", out var wf) && wf != null) wasteFactor = Convert.ToDecimal(wf);
        }

        var headerInfo = new List<(string Label, string Value)>
        {
            ("Proje:", projectStr),
            ("İş Emri No:", workOrderStr),
            ("Rapor Tarihi:", dateStr),
            ("Satır Sayısı:", lineCount.ToString()),
            ("Toplam Miktar:", totalQuantity.ToString()),
            ("Fire Oranı:", $"%{wasteFactor * 100:0.0}")
        };

        foreach (var (label, value) in headerInfo)
        {
            ws.Cell(currentRow, 1).Value = label;
            ws.Cell(currentRow, 1).Style.Font.SetBold(true);
            ws.Cell(currentRow, 2).Value = value;
            currentRow++;
        }

        currentRow++;

        // === SECTION 2: EXECUTIVE SUMMARY ===
        ws.Cell(currentRow, 1).Value = "ÖZET BİLGİLER";
        ws.Cell(currentRow, 1).Style.Font.SetBold(true);
        ws.Cell(currentRow, 1).Style.Font.FontSize = 11;
        currentRow++;

        var summary = mrpData.Summary;
        
        decimal sheetArea = 0m;
        decimal sheetMass = 0m;
        decimal insulationArea = 0m;
        decimal profileLength = 0m;
        decimal bomTotal = 0m;

        if (summary != null)
        {
            if (summary.TryGetValue("material", out var matObj) && matObj != null)
            {
                var matDict = matObj as Dictionary<string, object>;
                if (matDict == null)
                {
                    // Fallback if it's an anonymous object or structured class (it's created as an anonymous type in MrpService)
                    var matProps = matObj.GetType().GetProperties();
                    foreach (var prop in matProps)
                    {
                        if (prop.Name == "sheet_area_m2") sheetArea = Convert.ToDecimal(prop.GetValue(matObj) ?? 0m);
                        if (prop.Name == "sheet_mass_kg") sheetMass = Convert.ToDecimal(prop.GetValue(matObj) ?? 0m);
                        if (prop.Name == "insulation_area_m2") insulationArea = Convert.ToDecimal(prop.GetValue(matObj) ?? 0m);
                        if (prop.Name == "profile_length_m") profileLength = Convert.ToDecimal(prop.GetValue(matObj) ?? 0m);
                    }
                }
            }

            if (summary.TryGetValue("cost", out var costObj) && costObj != null)
            {
                var costProps = costObj.GetType().GetProperties();
                foreach (var prop in costProps)
                {
                    if (prop.Name == "bom_total") bomTotal = Convert.ToDecimal(prop.GetValue(costObj) ?? 0m);
                }
            }
        }

        var summaryData = new List<(string Label, string Value)>
        {
            ("Toplam Sac Alanı:", $"{sheetArea:N3} m²"),
            ("Toplam Sac Ağırlığı:", $"{sheetMass:N3} kg"),
            ("Toplam Yalıtım Alanı:", $"{insulationArea:N3} m²"),
            ("Toplam Profil Uzunluğu:", $"{profileLength:N2} m"),
            ("Tahmini BOM Maliyeti:", $"{bomTotal:N2} TL")
        };

        foreach (var (label, value) in summaryData)
        {
            ws.Cell(currentRow, 1).Value = label;
            ws.Cell(currentRow, 1).Style.Font.SetBold(true);
            ws.Cell(currentRow, 2).Value = value;
            currentRow++;
        }

        currentRow += 2;

        // === SECTION 3: LINE DETAILS ===
        ws.Cell(currentRow, 1).Value = "SATIŞ KALEMLERİ DETAYI";
        ws.Cell(currentRow, 1).Style.Font.SetBold(true);
        ws.Cell(currentRow, 1).Style.Font.FontSize = 11;
        currentRow++;

        var lineColumns = new[] { "#", "Ürün", "Miktar", "Sac Alanı (m²)", "Sac Ağırlığı (kg)", "Yalıtım Alanı (m²)", "Profil (m)" };
        for (int i = 0; i < lineColumns.Length; i++)
        {
            var cell = ws.Cell(currentRow, i + 1);
            cell.Value = lineColumns[i];
            cell.Style.Font.SetBold(true);
            cell.Style.Fill.SetBackgroundColor(XLColor.FromHtml("#D9E1F2"));
            cell.Style.Border.SetOutsideBorder(XLBorderStyleValues.Thin);
            cell.Style.Border.SetInsideBorder(XLBorderStyleValues.Thin);
            cell.Style.Alignment.SetHorizontal(XLAlignmentHorizontalValues.Center);
        }
        currentRow++;

        var lines = mrpData.Lines;
        if (lines != null)
        {
            foreach (var line in lines)
            {
                int ln = 0;
                string productName = "-";
                int qty = 0;
                decimal sArea = 0m, sMass = 0m, iArea = 0m, pLen = 0m;

                if (line.TryGetValue("line_number", out var lnObj)) ln = Convert.ToInt32(lnObj ?? 0);
                if (line.TryGetValue("product_name", out var pName)) productName = pName?.ToString() ?? "-";
                if (line.TryGetValue("quantity", out var q)) qty = Convert.ToInt32(q ?? 0);

                if (line.TryGetValue("totals", out var totalsObj) && totalsObj != null)
                {
                    var totalsProps = totalsObj.GetType().GetProperties();
                    foreach (var prop in totalsProps)
                    {
                        if (prop.Name == "sheet_area_m2") sArea = Convert.ToDecimal(prop.GetValue(totalsObj) ?? 0m);
                        if (prop.Name == "sheet_mass_kg") sMass = Convert.ToDecimal(prop.GetValue(totalsObj) ?? 0m);
                        if (prop.Name == "insulation_area_m2") iArea = Convert.ToDecimal(prop.GetValue(totalsObj) ?? 0m);
                        if (prop.Name == "profile_length_m") pLen = Convert.ToDecimal(prop.GetValue(totalsObj) ?? 0m);
                    }
                }

                ws.Cell(currentRow, 1).Value = ln;
                ws.Cell(currentRow, 1).Style.Alignment.SetHorizontal(XLAlignmentHorizontalValues.Center);
                
                ws.Cell(currentRow, 2).Value = productName;
                ws.Cell(currentRow, 2).Style.Alignment.SetHorizontal(XLAlignmentHorizontalValues.Left);
                
                ws.Cell(currentRow, 3).Value = qty;
                ws.Cell(currentRow, 3).Style.Alignment.SetHorizontal(XLAlignmentHorizontalValues.Center);
                
                ws.Cell(currentRow, 4).Value = $"{sArea:N3}";
                ws.Cell(currentRow, 4).Style.Alignment.SetHorizontal(XLAlignmentHorizontalValues.Right);
                
                ws.Cell(currentRow, 5).Value = $"{sMass:N3}";
                ws.Cell(currentRow, 5).Style.Alignment.SetHorizontal(XLAlignmentHorizontalValues.Right);
                
                ws.Cell(currentRow, 6).Value = $"{iArea:N3}";
                ws.Cell(currentRow, 6).Style.Alignment.SetHorizontal(XLAlignmentHorizontalValues.Right);
                
                ws.Cell(currentRow, 7).Value = $"{pLen:N2}";
                ws.Cell(currentRow, 7).Style.Alignment.SetHorizontal(XLAlignmentHorizontalValues.Right);

                for (int i = 1; i <= 7; i++)
                {
                    ws.Cell(currentRow, i).Style.Border.SetOutsideBorder(XLBorderStyleValues.Thin);
                }

                currentRow++;
            }

            // Line subtotals
            ws.Cell(currentRow, 1).Value = "TOPLAM";
            ws.Cell(currentRow, 2).Value = "";
            ws.Cell(currentRow, 3).Value = totalQuantity;
            ws.Cell(currentRow, 4).Value = $"{sheetArea:N3}";
            ws.Cell(currentRow, 5).Value = $"{sheetMass:N3}";
            ws.Cell(currentRow, 6).Value = $"{insulationArea:N3}";
            ws.Cell(currentRow, 7).Value = $"{profileLength:N2}";

            ws.Cell(currentRow, 1).Style.Alignment.SetHorizontal(XLAlignmentHorizontalValues.Center);
            ws.Cell(currentRow, 3).Style.Alignment.SetHorizontal(XLAlignmentHorizontalValues.Center);
            ws.Cell(currentRow, 4).Style.Alignment.SetHorizontal(XLAlignmentHorizontalValues.Right);
            ws.Cell(currentRow, 5).Style.Alignment.SetHorizontal(XLAlignmentHorizontalValues.Right);
            ws.Cell(currentRow, 6).Style.Alignment.SetHorizontal(XLAlignmentHorizontalValues.Right);
            ws.Cell(currentRow, 7).Style.Alignment.SetHorizontal(XLAlignmentHorizontalValues.Right);

            for (int i = 1; i <= 7; i++)
            {
                var cell = ws.Cell(currentRow, i);
                cell.Style.Font.SetBold(true);
                cell.Style.Border.SetOutsideBorder(XLBorderStyleValues.Thin);
            }
            currentRow += 2;
        }

        // Set column widths
        ws.Column(1).Width = 10;
        ws.Column(2).Width = 25;
        ws.Column(3).Width = 15;
        ws.Column(4).Width = 18;
        ws.Column(5).Width = 18;
        ws.Column(6).Width = 18;
        ws.Column(7).Width = 12;

        using var stream = new MemoryStream();
        wb.SaveAs(stream);
        return stream.ToArray();
    }
}
