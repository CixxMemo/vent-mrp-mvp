# FactoryCut Planner

FactoryCut Planner is a desktop-ready production planning and material requirements planning (MRP) application for small manufacturing workflows. It replaces spreadsheet-heavy planning with a local-first, native desktop application that combines product setup, BOM control, work order management, and automated MRP in a single, streamlined workspace.

## Key Features

- **Product Setup**: Define products with custom dimensions and material properties.
- **BOM Control**: Create and maintain Bills of Materials (BOM) for assembly hierarchies.
- **Work Order Management**: Formulate and track production work orders.
- **Automated MRP**: Run Material Requirements Planning calculations to compute net requirements.
- **Excel Reporting**: Export operational and production reports directly to Excel files.
- **Modern Dark UI**: A sleek, high-contrast dark user interface styled with the Catppuccin Mocha palette, designed for shop-floor and operational usability.
- **Fully Offline**: A local-first architecture powered by an embedded SQLite database.

## Technology Stack

### Desktop UI
- **Avalonia UI**: Cross-platform, modern, customizable XAML framework for desktop GUI design.
- **Catppuccin Mocha**: Elegant color scheme optimized for readability and dark mode environments.
- **CommunityToolkit.Mvvm**: Clean and robust Model-View-ViewModel (MVVM) architecture.

### Core & Database
- **Entity Framework Core**: Robust ORM layer for database transactions.
- **SQLite**: Local embedded database storage.
- **ClosedXML**: Analytical data manipulation and Excel export generation.

### Packaging
- **.NET 10 SDK**: Native desktop deployment packaging for cross-platform support.

## Running in Development Mode

### Requirements
- .NET 10.0 SDK

### Install & Run

Launch the application directly using the .NET CLI:

```bash
cd FactoryCutPlanner
dotnet run
```

Notes:
- The application executes fully offline with a local database automatically initialized on first run.

## Packaged Desktop Version

The project supports one-click desktop packaging for local deployment:

- **Windows Package**: Standalone `.exe`
- **macOS Package**: Standalone `.app`
- **Packaging Tool**: `dotnet publish`
- The packaged executable contains all logic and assets, running natively.

## Project Structure

```text
factorycut_planner/
├── FactoryCutPlanner/
│   ├── Assets/
│   ├── Data/
│   ├── Models/
│   ├── Services/
│   ├── ViewModels/
│   ├── Views/
│   ├── App.axaml
│   ├── Program.cs
│   └── FactoryCutPlanner.csproj
├── FactoryCutPlanner.Tests/
├── FactoryCutPlanner.slnx
└── hvac_factory_ops.db
```

## Architecture Overview

`Avalonia UI (Views/ViewModels)` -> `Core/Backend Services` -> `Local SQLite Database`

- The UI layer (built with Avalonia UI and MVVM) interacts directly with core service modules.
- Core backend services execute database actions via Entity Framework Core ORM.
- Operational data is persisted locally in an embedded SQLite database.

## Roadmap

- Capacity-aware scheduling and finite planning constraints
- Inventory policy enhancements (safety stock and lead-time strategies)
- Role-based access and audit logging
- Expanded analytics and forecasting support
- Installer hardening and update workflow improvements
