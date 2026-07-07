using Avalonia.Controls;
using Avalonia.Interactivity;
using Avalonia.Platform.Storage;
using FactoryCutPlanner.ViewModels;
using System.Linq;

namespace FactoryCutPlanner.Views;

public partial class WorkOrdersPageView : UserControl
{
    public WorkOrdersPageView()
    {
        InitializeComponent();
    }

    private async void OnImportFromExcelClicked(object sender, RoutedEventArgs e)
    {
        var vm = DataContext as WorkOrdersPageViewModel;
        if (vm == null) return;

        var topLevel = TopLevel.GetTopLevel(this);
        if (topLevel == null) return;

        var files = await topLevel.StorageProvider.OpenFilePickerAsync(new FilePickerOpenOptions
        {
            Title = "Excel Dosyası Seç",
            AllowMultiple = false,
            FileTypeFilter = new[]
            {
                new FilePickerFileType("Excel Files")
                {
                    Patterns = new[] { "*.xlsx" }
                }
            }
        });

        if (files.Count >= 1)
        {
            var file = files[0];
            // Get the local path
            if (file.TryGetLocalPath() is string filePath)
            {
                vm.ProcessExcelImport(filePath);
            }
        }
    }
}
