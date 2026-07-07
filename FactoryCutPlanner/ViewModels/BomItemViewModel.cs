using CommunityToolkit.Mvvm.ComponentModel;

namespace FactoryCutPlanner.ViewModels;

/// <summary>
/// ViewModel for a single BOM (Bill of Materials) row in the product form.
/// Each instance represents one editable material line.
/// Mirrors the Python tuple: (frame, name_entry, unit_entry, qty_entry, cost_entry)
/// </summary>
public partial class BomItemViewModel : ViewModelBase
{
    [ObservableProperty]
    private string _materialName = string.Empty;

    [ObservableProperty]
    private string _unit = string.Empty;

    [ObservableProperty]
    private string _quantityPerUnit = string.Empty;

    [ObservableProperty]
    private string _costPerUnit = string.Empty;
}
