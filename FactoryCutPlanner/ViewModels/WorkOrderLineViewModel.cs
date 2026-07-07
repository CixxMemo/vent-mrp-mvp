using CommunityToolkit.Mvvm.ComponentModel;

namespace FactoryCutPlanner.ViewModels;

public partial class WorkOrderLineViewModel : ViewModelBase
{
    [ObservableProperty]
    private ProductOption? _selectedProduct;

    [ObservableProperty]
    private string _quantity = string.Empty;
}
