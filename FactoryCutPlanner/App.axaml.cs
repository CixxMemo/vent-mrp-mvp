using Avalonia;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Data.Core;
using Avalonia.Data.Core.Plugins;
using System.Linq;
using Avalonia.Markup.Xaml;
using FactoryCutPlanner.Data;
using FactoryCutPlanner.ViewModels;
using FactoryCutPlanner.Views;

namespace FactoryCutPlanner;

public partial class App : Application
{
    public override void Initialize()
    {
        AvaloniaXamlLoader.Load(this);
    }

    public override void OnFrameworkInitializationCompleted()
    {
        if (ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop)
        {
            // The .db file is not shipped with the app: create it (and its tables)
            // on first run, before any ViewModel queries it. No-op if it already exists.
            using (var db = new AppDbContext())
            {
                db.Database.EnsureCreated();
            }

            desktop.MainWindow = new MainWindow
            {
                DataContext = new MainWindowViewModel(),
            };
        }

        base.OnFrameworkInitializationCompleted();
    }
}