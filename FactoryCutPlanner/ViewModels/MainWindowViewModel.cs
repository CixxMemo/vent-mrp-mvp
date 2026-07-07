using CommunityToolkit.Mvvm.ComponentModel;

namespace FactoryCutPlanner.ViewModels;

/// <summary>
/// Root ViewModel for the main window.
///
/// Manages 3 tab pages via a TabControl:
///   - Ürünler (Products)
///   - İş Emirleri (Work Orders)
///   - MRP Hesaplama
///
/// Each tab has its own ViewModel instance. The MainWindow.axaml
/// uses a TabControl that binds each tab's content to these ViewModels,
/// and the ViewLocator automatically resolves the matching View.
/// </summary>
public partial class MainWindowViewModel : ViewModelBase
{
    public ProductsPageViewModel ProductsPage { get; } = new();
    public WorkOrdersPageViewModel WorkOrdersPage { get; } = new();
    public MrpPageViewModel MrpPage { get; } = new();
}
