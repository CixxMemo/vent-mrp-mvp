# HVAC Factory Ops MVP

FastAPI + SQLAlchemy + SQLite backend with Streamlit frontend for HVAC (dikdörtgen kanal) üretim planlama ve MRP hesaplama.

## Özellikler
- Ürün yönetimi (RECTANGULAR_DUCT) ve ürün bazlı BOM kalemleri
- Proje bazlı iş emirleri
- MRP hesaplama (sac alanı, ağırlık, yalıtım alanı, BOM toplamları)
- Türkçe Streamlit arayüz ve Türkçe Excel raporu
- Hesaplama motoru `modules/mrp/service.py` içinde izole ve test edilebilir

## Çalıştırma
Önce bağımlılıkları kurun (tercihen sanal ortamda):
```
pip install -r requirements.txt
```

### API (FastAPI)
```
uvicorn main:app --reload
```

### Streamlit Arayüz
Varsayılan API URL `http://localhost:8000` (çevresel değişkenle değiştirilebilir).
```
streamlit run streamlit_app.py
```

### Ortam Değişkenleri
- `DATABASE_URL` (varsayılan: sqlite:///./hvac_factory_ops.db)
- `STEEL_DENSITY_KG_M3` (varsayılan: 7850)
- `WASTE_FACTOR` (varsayılan: 0.0)
- `API_URL` (Streamlit için; varsayılan: http://localhost:8000)

`.env` dosyası ile veya `export STEEL_DENSITY_KG_M3=7900` / `export WASTE_FACTOR=0.05` gibi terminalden geçersiz kılınabilir.

### Testler
```
pytest
```

## Mimari
- `core/`: ayarlar, DB oturumu, base modeller, hata yönetimi
- `modules/products`: ürün ve BOM modelleri + CRUD
- `modules/work_orders`: iş emirleri
- `modules/mrp`: hesaplama motoru + API uçları
- `modules/reports`: Excel üretimi (Türkçe)
- `streamlit_app.py`: Türkçe arayüz

## Notlar
- Alembic migration planlanmış; MVP SQLite auto-create ile çalışır.
- Hesaplama ve validasyonlar merkezi; API uçları ince tutulmuştur.

