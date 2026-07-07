using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using FactoryCutPlanner.Data;
using FactoryCutPlanner.Models;
using Microsoft.EntityFrameworkCore;

namespace FactoryCutPlanner.ViewModels;

public class ProductOption
{
    public int Id { get; set; }
    public string Display { get; set; } = string.Empty;
}

public class WorkOrderListItem
{
    public int Id { get; set; }
    public string ProjectName { get; set; } = string.Empty;
    public int WasteFactorPct { get; set; }
    public List<string> LineSummaries { get; set; } = new();
}

/// <summary>
/// ViewModel for the Work Orders page.
/// </summary>
public partial class WorkOrdersPageViewModel : ViewModelBase
{
    [ObservableProperty]
    private string _projectName = string.Empty;

    [ObservableProperty]
    private double _wasteFactor = 0;

    public ObservableCollection<WorkOrderLineViewModel> WorkOrderLines { get; } = new();
    
    [ObservableProperty]
    private ObservableCollection<ProductOption> _productOptions = new();

    public ObservableCollection<WorkOrderListItem> WorkOrders { get; } = new();

    [ObservableProperty]
    private bool _isWorkOrdersEmpty = true;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(HasStatus))]
    private string _statusMessage = string.Empty;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(StatusColor))]
    private bool _isError;

    public bool HasStatus => !string.IsNullOrEmpty(StatusMessage);
    public string StatusColor => IsError ? "#F38BA8" : "#A6E3A1";

    public WorkOrdersPageViewModel()
    {
        LoadProducts();
        LoadWorkOrders();
        AddLineRow(); // Add first empty row
    }

    [RelayCommand]
    private void AddLineRow()
    {
        var newLine = new WorkOrderLineViewModel();
        if (ProductOptions.Any())
        {
            newLine.SelectedProduct = ProductOptions.First();
        }
        WorkOrderLines.Add(newLine);
    }

    [RelayCommand]
    private void RemoveLineRow(WorkOrderLineViewModel item)
    {
        WorkOrderLines.Remove(item);
    }

    [RelayCommand]
    private void SaveWorkOrder()
    {
        if (string.IsNullOrWhiteSpace(ProjectName))
        {
            ShowStatus("Proje adı zorunludur.", true);
            return;
        }

        if (!WorkOrderLines.Any())
        {
            ShowStatus("En az bir kalem eklemelisiniz.", true);
            return;
        }

        try
        {
            using var db = new AppDbContext();
            
            var now = DateTime.UtcNow.ToString("yyyy-MM-dd HH:mm:ss");
            var wasteFactorDecimal = (decimal)(WasteFactor / 100.0);

            var wo = new WorkOrder
            {
                ProjectName = ProjectName.Trim(),
                WasteFactor = wasteFactorDecimal,
                CreatedAt = now,
                UpdatedAt = now
            };

            foreach (var line in WorkOrderLines)
            {
                if (line.SelectedProduct == null)
                {
                    ShowStatus("Lütfen her kalem için bir ürün seçin.", true);
                    return;
                }

                if (!int.TryParse(line.Quantity, out var qty) || qty <= 0)
                {
                    ShowStatus($"'{line.SelectedProduct.Display}' için miktar pozitif tam sayı olmalıdır.", true);
                    return;
                }

                wo.Lines.Add(new WorkOrderLine
                {
                    ProductId = line.SelectedProduct.Id,
                    Quantity = qty,
                    CreatedAt = now,
                    UpdatedAt = now
                });
            }

            db.WorkOrders.Add(wo);
            db.SaveChanges();

            ClearForm();
            LoadWorkOrders();
            ShowStatus($"'{wo.ProjectName}' iş emri kaydedildi.", false);
        }
        catch (Exception ex)
        {
            ShowStatus($"Kaydetme hatası: {ex.Message}", true);
        }
    }

    [RelayCommand]
    private void DeleteWorkOrder(WorkOrderListItem item)
    {
        if (item == null) return;

        try
        {
            using var db = new AppDbContext();
            var wo = db.WorkOrders.Include(w => w.Lines).FirstOrDefault(w => w.Id == item.Id);
            if (wo == null) return;

            db.WorkOrderLines.RemoveRange(wo.Lines);
            db.WorkOrders.Remove(wo);
            db.SaveChanges();

            LoadWorkOrders();
            ShowStatus($"'{item.ProjectName}' silindi.", false);
        }
        catch (Exception ex)
        {
            ShowStatus($"Silme hatası: {ex.Message}", true);
        }
    }

    public void ProcessExcelImport(string filePath)
    {
        var service = new FactoryCutPlanner.Services.ExcelImportService();
        var wasteFactorDecimal = (decimal)(WasteFactor / 100.0);
        
        var (success, message) = service.ImportWorkOrder(filePath, ProjectName, wasteFactorDecimal);
        
        ShowStatus(message, !success);
        
        if (success)
        {
            ProjectName = string.Empty;
            WasteFactor = 0;
            RefreshData();
        }
    }

    [RelayCommand]
    public void RefreshData()
    {
        LoadProducts();
        LoadWorkOrders();
        
        // Update product options in existing lines
        foreach (var line in WorkOrderLines)
        {
            if (line.SelectedProduct != null)
            {
                var newSelection = ProductOptions.FirstOrDefault(p => p.Id == line.SelectedProduct.Id);
                line.SelectedProduct = newSelection ?? ProductOptions.FirstOrDefault();
            }
        }
    }

    private void LoadProducts()
    {
        try
        {
            using var db = new AppDbContext();
            var products = db.Products.OrderBy(p => p.Name).ToList();
            ProductOptions.Clear();
            foreach (var p in products)
            {
                ProductOptions.Add(new ProductOption
                {
                    Id = p.Id,
                    Display = $"{p.Name} (ID:{p.Id})"
                });
            }
        }
        catch (Exception ex)
        {
            ShowStatus($"Ürünler yüklenemedi: {ex.Message}", true);
        }
    }

    private void LoadWorkOrders()
    {
        WorkOrders.Clear();
        try
        {
            using var db = new AppDbContext();
            var wos = db.WorkOrders
                .Include(w => w.Lines)
                .ThenInclude(l => l.Product)
                .OrderByDescending(w => w.Id)
                .ToList();

            foreach (var w in wos)
            {
                var summaries = w.Lines.Select((l, i) => $"  {i + 1}. {l.Product.Name}  ×  {l.Quantity} adet").ToList();
                WorkOrders.Add(new WorkOrderListItem
                {
                    Id = w.Id,
                    ProjectName = w.ProjectName,
                    WasteFactorPct = w.WasteFactor.HasValue ? (int)(w.WasteFactor.Value * 100) : 0,
                    LineSummaries = summaries
                });
            }
        }
        catch (Exception ex)
        {
            ShowStatus($"İş emirleri yüklenemedi: {ex.Message}", true);
        }
        
        IsWorkOrdersEmpty = WorkOrders.Count == 0;
    }

    private void ClearForm()
    {
        ProjectName = string.Empty;
        WasteFactor = 0;
        WorkOrderLines.Clear();
        AddLineRow();
    }

    private void ShowStatus(string message, bool isError)
    {
        StatusMessage = message;
        IsError = isError;
    }
}
