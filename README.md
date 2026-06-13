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
- **CustomTkinter**: Modern, customizable widgets for desktop GUI design.
- **Catppuccin Mocha**: Elegant color scheme optimized for readability and dark mode environments.

### Core & Database
- **SQLAlchemy**: ORM layers for database transactions.
- **SQLite**: Local embedded database storage.
- **Pandas / OpenPyXL**: Analytical data manipulation and Excel export generation.

### Packaging
- **PyInstaller**: Native desktop deployment packaging (Windows `.exe` and macOS `.app`).

## Running in Development Mode

### Requirements
- Python 3.11+
- pip

### Install

```bash
pip install -r requirements.txt
```

### Run

Launch the application directly:

```bash
python main.py
```

Notes:
- `main.py` is the primary entry point of the desktop application.
- The application executes fully offline with a local database automatically initialized on first run.

## Packaged Desktop Version

The project supports one-click desktop packaging for local deployment:

- **Windows Package**: Standalone `.exe`
- **macOS Package**: Standalone `.app`
- **Packaging Tool**: PyInstaller
- The packaged executable contains all logic and assets, running natively without requiring a Python environment.

## Project Structure

```text
factorycut_planner/
├── main.py
├── core/
│   ├── database.py
│   ├── db_helper.py
│   ├── models.py
│   ├── settings.py
│   └── errors.py
├── modules/
│   ├── products/
│   ├── work_orders/
│   ├── mrp/
│   └── reports/
├── ui/
│   ├── frames/
│   │   ├── mrp_frame.py
│   │   ├── products_frame.py
│   │   └── work_orders_frame.py
│   ├── components.py
│   ├── api_client.py
│   └── texts_tr.py
├── tests/
├── requirements.txt
└── hvac_factory_ops.db
```

## Architecture Overview

`CustomTkinter GUI` -> `Core/Backend Services` -> `Local SQLite Database`

- The UI layer (built with CustomTkinter) interacts directly with core service modules.
- Core backend services execute database actions via SQLAlchemy ORM.
- Operational data is persisted locally in an embedded SQLite database.

## Roadmap

- Capacity-aware scheduling and finite planning constraints
- Inventory policy enhancements (safety stock and lead-time strategies)
- Role-based access and audit logging
- Expanded analytics and forecasting support
- Installer hardening and update workflow improvements

## License

This repository is published as a portfolio and demo project focused on real-world manufacturing planning workflows. It is intended for evaluation and demonstration; commercial usage and redistribution require explicit permission from the author.

