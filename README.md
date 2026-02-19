# FactoryCut Planner

FactoryCut Planner is a desktop-ready production planning and material requirements planning (MRP) application for small manufacturing workflows. It replaces spreadsheet-heavy planning with a local-first tool that combines product setup, BOM control, work order management, and automated MRP in a single workflow.

## Key Features

- Product definition with dimensions and material properties
- Bill of Materials (BOM) creation and maintenance
- Work order creation and management
- Automatic MRP calculation for production planning
- Excel report export for operational reporting
- Dark UI optimized for daily operational use
- Fully offline runtime on `localhost`
- One-click launcher that starts backend and UI together

## Technology Stack

### Frontend
- Streamlit

### Backend
- FastAPI
- Uvicorn

### Packaging
- PyInstaller
- Desktop outputs: Windows `.exe` and macOS `.app`

## Running in Development Mode

### Requirements
- Python 3.11+
- pip

### Install

```bash
pip install -r requirements.txt
```

### Run

Use the launcher as the primary entry point:

```bash
python run_app.py
```

Notes:
- `run_app.py` is the correct entry point.
- `streamlit_app.py` should not be run directly.
- The application runs fully offline on `localhost`.
- The launcher starts FastAPI (`127.0.0.1:8000`) and Streamlit (`127.0.0.1:8501`) together.

## Packaged Desktop Version

The project supports one-click desktop packaging for local deployment:

- Windows package: `.exe`
- macOS package: `.app`
- Packaging tool: PyInstaller
- Runtime behavior matches development mode, with backend and UI launched together via the same startup model

## Project Structure

```text
factorycut_planner/
├── run_app.py
├── streamlit_app.py
├── main.py
├── core/
│   ├── database.py
│   ├── models.py
│   ├── settings.py
│   └── errors.py
├── modules/
│   ├── products/
│   ├── work_orders/
│   ├── mrp/
│   └── reports/
├── ui/
├── tests/
├── requirements.txt
├── start_ui.bat
└── hvac_factory_ops.db
```

## Architecture Overview

`Streamlit UI` -> `FastAPI API` -> `Backend Services` -> `Local Database`

- The Streamlit interface sends requests to FastAPI endpoints.
- Backend service modules execute product, BOM, work order, and MRP logic.
- Data is persisted locally, enabling a fully offline localhost deployment.

## Roadmap

- Capacity-aware scheduling and finite planning constraints
- Inventory policy enhancements (safety stock and lead-time strategies)
- Role-based access and audit logging
- Expanded analytics and forecasting support
- Installer hardening and update workflow improvements

## License

This repository is published as a portfolio and demo project focused on real-world manufacturing planning workflows. It is intended for evaluation and demonstration; commercial usage and redistribution require explicit permission from the author.
