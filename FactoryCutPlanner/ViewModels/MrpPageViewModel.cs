using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading.Tasks;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using FactoryCutPlanner.Data;
using FactoryCutPlanner.Models;
using FactoryCutPlanner.Services;
using Microsoft.EntityFrameworkCore;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia;
using Avalonia.Controls;

namespace FactoryCutPlanner.ViewModels;

public class WorkOrderOption
{
    public int Id { get; set; }
    public string Display { get; set; } = string.Empty;
}

public class MrpLineDetailViewModel
{
    public string LineNumber { get; set; } = string.Empty;
    public string ProductInfo { get; set; } = string.Empty;
    public string DetailText { get; set; } = string.Empty;
}

public class MrpBomItemViewModel
{
    public string LeftText { get; set; } = string.Empty;
    public string RightText { get; set; } = string.Empty;
    public bool IsPriced { get; set; }
    public string RightTextColor => IsPriced ? "#A6E3A1" : "#F38BA8";
}

public partial class MrpPageViewModel : ViewModelBase
{
    [ObservableProperty]
    private ObservableCollection<WorkOrderOption> _workOrderOptions = new();

    [ObservableProperty]
    private WorkOrderOption? _selectedWorkOrder;

    [ObservableProperty]
    private bool _isEmptyStateVisible = true;

    [ObservableProperty]
    private bool _isResultVisible = false;

    // --- Header Info ---
    [ObservableProperty] private string _projectName = string.Empty;
    [ObservableProperty] private string _workOrderInfo = string.Empty;

    // --- Summary Cards ---
    [ObservableProperty] private string _sheetArea = string.Empty;
    [ObservableProperty] private string _sheetMass = string.Empty;
    [ObservableProperty] private string _insulationArea = string.Empty;
    [ObservableProperty] private string _profileTitle = "Profil İhtiyacı";
    [ObservableProperty] private string _profileValue = string.Empty;
    [ObservableProperty] private string _bomCost = string.Empty;

    // --- Lists ---
    public ObservableCollection<MrpLineDetailViewModel> Lines { get; } = new();
    public ObservableCollection<MrpBomItemViewModel> PricedBomItems { get; } = new();
    public ObservableCollection<MrpBomItemViewModel> UnpricedBomItems { get; } = new();

    [ObservableProperty] private bool _isLinesVisible = false;
    [ObservableProperty] private bool _isPricedVisible = false;
    [ObservableProperty] private string _pricedTitle = string.Empty;
    [ObservableProperty] private bool _isUnpricedVisible = false;
    [ObservableProperty] private string _unpricedTitle = string.Empty;

    // --- Completeness Warning ---
    [ObservableProperty] private bool _isCompletenessWarningVisible = false;
    [ObservableProperty] private string _completenessWarning = string.Empty;

    // --- Status ---
    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(HasStatus))]
    private string _statusMessage = string.Empty;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(StatusColor))]
    private bool _isError;

    public bool HasStatus => !string.IsNullOrEmpty(StatusMessage);
    public string StatusColor => IsError ? "#F38BA8" : "#A6E3A1";

    private MrpCalculationResult? _lastResult;

    public MrpPageViewModel()
    {
        LoadWorkOrders();
    }

    [RelayCommand]
    public void RefreshData()
    {
        LoadWorkOrders();
    }

    private void LoadWorkOrders()
    {
        try
        {
            using var db = new AppDbContext();
            var wos = db.WorkOrders.OrderByDescending(w => w.Id).ToList();
            
            WorkOrderOptions.Clear();
            foreach (var wo in wos)
            {
                WorkOrderOptions.Add(new WorkOrderOption
                {
                    Id = wo.Id,
                    Display = $"{wo.ProjectName} (#{wo.Id})"
                });
            }

            if (WorkOrderOptions.Any() && SelectedWorkOrder == null)
            {
                SelectedWorkOrder = WorkOrderOptions.First();
            }
        }
        catch (Exception ex)
        {
            ShowStatus($"İş emirleri yüklenemedi: {ex.Message}", true);
        }
    }

    [RelayCommand]
    private void CalculateMrp()
    {
        if (SelectedWorkOrder == null)
        {
            ShowStatus("Lütfen bir iş emri seçin.", true);
            return;
        }

        try
        {
            using var db = new AppDbContext();
            var woModel = db.WorkOrders
                .Include(w => w.Lines)
                .ThenInclude(l => l.Product)
                .ThenInclude(p => p.BomItems)
                .FirstOrDefault(w => w.Id == SelectedWorkOrder.Id);

            if (woModel == null)
            {
                ShowStatus("İş emri bulunamadı.", true);
                return;
            }

            var mrpService = new MrpService();
            _lastResult = mrpService.ComputeWorkOrder(woModel, woModel.WasteFactor ?? 0m);

            DisplayResults(_lastResult);
            ShowStatus("", false);
        }
        catch (Exception ex)
        {
            ShowStatus($"MRP Hatası: {ex.Message}", true);
            IsEmptyStateVisible = true;
            IsResultVisible = false;
        }
    }

    private void DisplayResults(MrpCalculationResult data)
    {
        IsEmptyStateVisible = false;
        IsResultVisible = true;

        var header = data.Header;
        var summary = data.Summary;
        
        ProjectName = $"📋  {GetValue(header, "project_name", "?")}";
        
        decimal wastePct = Convert.ToDecimal(GetValue(header, "waste_factor", 0m)) * 100m;
        WorkOrderInfo = $"İş Emri #{GetValue(header, "work_order_id", "?")}  •  {GetValue(header, "line_count", 0)} kalem  •  {GetValue(header, "total_quantity", 0)} adet  •  Fire: %{wastePct:0}";

        dynamic? material = summary.TryGetValue("material", out var matObj) ? matObj : null;
        dynamic? cost = summary.TryGetValue("cost", out var costObj) ? costObj : null;

        SheetArea = $"{GetDynProp(material, "sheet_area_m2", 0m):0.000} m²";
        SheetMass = $"{GetDynProp(material, "sheet_mass_kg", 0m):0.000} kg";
        InsulationArea = $"{GetDynProp(material, "insulation_area_m2", 0m):0.000} m²";
        
        ProfileTitle = "Profil İhtiyacı";
        ProfileValue = $"{GetDynProp(material, "profile_length_m", 0m):0.00} m";
        
        BomCost = $"{GetDynProp(cost, "bom_total", 0m):N2} ₺";

        // Lines
        Lines.Clear();
        foreach (var line in data.Lines)
        {
            var productInfo = $"{GetValue(line, "product_name", "?")}  ×  {GetValue(line, "quantity", 0)} adet";
            
            dynamic? totals = line.TryGetValue("totals", out var tObj) ? tObj : null;
            decimal sArea = GetDynProp(totals, "sheet_area_m2", 0m);
            decimal sMass = GetDynProp(totals, "sheet_mass_kg", 0m);
            decimal iArea = GetDynProp(totals, "insulation_area_m2", 0m);
            decimal pLen = GetDynProp(totals, "profile_length_m", 0m);

            string detail = $"Sac: {sArea:0.000} m²  •  {sMass:0.000} kg";
            if (iArea > 0) detail += $"  •  Yalıtım: {iArea:0.000} m²";
            if (pLen > 0) detail += $" | Profil: {pLen:0.00} m";

            Lines.Add(new MrpLineDetailViewModel
            {
                LineNumber = $"  {GetValue(line, "line_number", "?")}.",
                ProductInfo = productInfo,
                DetailText = detail
            });
        }
        IsLinesVisible = Lines.Count > 0;

        // BOM
        PricedBomItems.Clear();
        UnpricedBomItems.Clear();

        if (data.BomSummary.TryGetValue("priced_items", out var pricedObj) && pricedObj is List<Dictionary<string, object>> priced)
        {
            foreach (var p in priced)
            {
                string name = GetValue(p, "name", "?").ToString()!;
                string unit = GetValue(p, "unit", "").ToString()!;
                decimal qty = Convert.ToDecimal(GetValue(p, "total_quantity", 0m));
                decimal tCost = Convert.ToDecimal(GetValue(p, "total_cost", 0m));
                decimal share = Convert.ToDecimal(GetValue(p, "cost_share_pct", 0m));

                PricedBomItems.Add(new MrpBomItemViewModel
                {
                    LeftText = $"  {name}  —  {qty:0.00} {unit}".TrimEnd(),
                    RightText = $"{tCost:N2} ₺  ({share:0.0}%)",
                    IsPriced = true
                });
            }
            PricedTitle = $"Malzeme Listesi — Fiyatlı ({priced.Count} kalem)";
        }
        IsPricedVisible = PricedBomItems.Count > 0;

        if (data.BomSummary.TryGetValue("unpriced_items", out var unpricedObj) && unpricedObj is List<Dictionary<string, object>> unpriced)
        {
            foreach (var u in unpriced)
            {
                string name = GetValue(u, "name", "?").ToString()!;
                string unit = GetValue(u, "unit", "").ToString()!;
                decimal qty = Convert.ToDecimal(GetValue(u, "total_quantity", 0m));

                UnpricedBomItems.Add(new MrpBomItemViewModel
                {
                    LeftText = $"  {name}  —  {qty:0.00} {unit}".TrimEnd(),
                    RightText = "Fiyat eksik",
                    IsPriced = false
                });
            }
            UnpricedTitle = $"Malzeme Listesi — Fiyat Eksik ({unpriced.Count} kalem)";
        }
        IsUnpricedVisible = UnpricedBomItems.Count > 0;

        decimal compPct = 100m;
        if (data.BomSummary.TryGetValue("metrics", out var metObj))
        {
            compPct = GetDynProp(metObj, "cost_completeness_pct", 100m);
        }

        if (compPct < 100m)
        {
            CompletenessWarning = $"⚠️  Maliyet tamlığı: %{compPct:0} — Bazı malzemelerin fiyatı eksik";
            IsCompletenessWarningVisible = true;
        }
        else
        {
            IsCompletenessWarningVisible = false;
        }
    }

    [RelayCommand]
    private async Task ExportExcel()
    {
        if (_lastResult == null)
        {
            ShowStatus("Önce MRP hesaplaması yapın.", true);
            return;
        }

        try
        {
            if (Application.Current?.ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop && desktop.MainWindow != null)
            {
                var topLevel = TopLevel.GetTopLevel(desktop.MainWindow);
                if (topLevel == null) return;

                var file = await topLevel.StorageProvider.SaveFilePickerAsync(new Avalonia.Platform.Storage.FilePickerSaveOptions
                {
                    Title = "Excel Raporunu Kaydet",
                    DefaultExtension = "xlsx",
                    SuggestedFileName = $"MRP_{ProjectName.Replace("📋  ", "").Replace(" ", "_")}.xlsx",
                    FileTypeChoices = new[]
                    {
                        new Avalonia.Platform.Storage.FilePickerFileType("Excel Dosyası") { Patterns = new[] { "*.xlsx" } },
                        new Avalonia.Platform.Storage.FilePickerFileType("Tüm Dosyalar") { Patterns = new[] { "*.*" } }
                    }
                });

                if (file == null) return;

                var excelService = new ExcelReportService();
                var fileBytes = excelService.GenerateMrpReport(_lastResult);

                await System.IO.File.WriteAllBytesAsync(file.Path.LocalPath, fileBytes);
                ShowStatus($"Rapor kaydedildi: {file.Path.LocalPath}", false);
            }
        }
        catch (Exception ex)
        {
            ShowStatus($"Excel oluşturulamadı: {ex.Message}", true);
        }
    }

    private void ShowStatus(string message, bool isError)
    {
        StatusMessage = message;
        IsError = isError;
    }

    private object GetValue(Dictionary<string, object> dict, string key, object fallback)
    {
        if (dict != null && dict.TryGetValue(key, out var val) && val != null) return val;
        return fallback;
    }

    private decimal GetDynProp(object? obj, string propName, decimal fallback)
    {
        if (obj == null) return fallback;
        var prop = obj.GetType().GetProperty(propName);
        if (prop != null)
        {
            var val = prop.GetValue(obj);
            if (val != null) return Convert.ToDecimal(val);
        }
        return fallback;
    }
}
