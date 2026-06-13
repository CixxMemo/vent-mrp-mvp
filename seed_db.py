#!/usr/bin/env python3
import sqlite3
import json
from datetime import datetime

DB_NAME = "hvac_factory_ops.db"


def seed_database():
    print(f"🚀 '{DB_NAME}' veritabanı gerçekçi test verileri ile dolduruluyor...")
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # ── 1. Mevcut verileri temizle ──
    print("🧹 Eski veriler temizleniyor...")
    cur.execute("DELETE FROM work_order_lines")
    cur.execute("DELETE FROM work_orders")
    cur.execute("DELETE FROM bom_items")
    cur.execute("DELETE FROM products")
    conn.commit()

    now_str = datetime.now().isoformat()

    # ── 2. Gerçekçi Ürünleri Tanımla ──
    # [A] RECTANGULAR_DUCT - İzolasyonlu Geniş Kanal
    spec_duct_large = {
        "width_mm": 600.0,
        "height_mm": 400.0,
        "length_mm": 1500.0,
        "thickness_mm": 0.8,
        "insulation_enabled": True,
        "insulation_thickness_mm": 20.0,
    }
    # [B] RECTANGULAR_DUCT - İzolasyonsuz İnce Kanal
    spec_duct_small = {
        "width_mm": 300.0,
        "height_mm": 200.0,
        "length_mm": 1200.0,
        "thickness_mm": 0.6,
        "insulation_enabled": False,
        "insulation_thickness_mm": None,
    }
    # [C] RECTANGULAR_DUCT - İzolasyonlu Büyük Yüksek Basınç Kanalı
    spec_duct_hp = {
        "width_mm": 800.0,
        "height_mm": 600.0,
        "length_mm": 1000.0,
        "thickness_mm": 1.0,
        "insulation_enabled": True,
        "insulation_thickness_mm": 30.0,
    }
    # [D] AHU_CABINET - Klima Santrali Hücresi
    spec_ahu = {
        "width_mm": 1500.0,
        "height_mm": 1500.0,
        "length_mm": 2200.0,
        "panel_thickness_mm": 50.0,
        "has_profile_framework": True,
    }
    # [E] FITTING_DUCT - 90 Derece Dirsek
    spec_fitting_elbow = {
        "fitting_shape": "ELBOW",
        "main_dimension_mm": 500.0,
        "thickness_mm": 0.8,
        "angle_degrees": 90.0,
    }
    # [F] FITTING_DUCT - Simetrik T Parçası
    spec_fitting_tee = {
        "fitting_shape": "TEE",
        "main_dimension_mm": 300.0,
        "thickness_mm": 0.6,
        "angle_degrees": 90.0,
    }

    products_data = [
        (
            "Dikdörtgen Kanal 600x400 (İzolasyonlu)",
            "Hastaneler ve ofisler için standart yalıtımlı galvaniz hava kanalı",
            "RECTANGULAR_DUCT",
            json.dumps(spec_duct_large),
        ),
        (
            "Dikdörtgen Kanal 300x200 (Yalıtımsız)",
            "Küçük debili hatlar için yalıtımsız ekonomik hava kanalı",
            "RECTANGULAR_DUCT",
            json.dumps(spec_duct_small),
        ),
        (
            "Dikdörtgen Kanal 800x600 (İzolasyonlu - HP)",
            "Ana besleme hatları için yüksek mukavemetli yalıtımlı hava kanalı",
            "RECTANGULAR_DUCT",
            json.dumps(spec_duct_hp),
        ),
        (
            "Klima Santrali Hücresi (KS-100)",
            "Çift cidarlı, 50 mm taşyünü dolgulu karkaslı klima santrali hücresi",
            "AHU_CABINET",
            json.dumps(spec_ahu),
        ),
        (
            "90 Derece Dirsek (Dirsek 500)",
            "Kanal dönüşleri için 90 derece flanşlı dirsek fitting elemanı",
            "FITTING_DUCT",
            json.dumps(spec_fitting_elbow),
        ),
        (
            "Simetrik T Parçası (T-300)",
            "Hava dağıtımı için simetrik T bağlantı fitting elemanı",
            "FITTING_DUCT",
            json.dumps(spec_fitting_tee),
        ),
    ]

    product_ids = {}
    for name, desc, p_type, attrs in products_data:
        cur.execute(
            """
            INSERT INTO products (name, description, product_type, attributes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (name, desc, p_type, attrs, now_str, now_str),
        )
        product_ids[name] = cur.lastrowid

    print(f"✅ {len(products_data)} adet ürün sisteme eklendi.")

    # ── 3. Ürünlere BOM (Reçete) Kalemlerini Ekle ──
    # BOM Kalemleri Yapısı: (product_name, material_name, unit, qty_per_unit, cost_per_unit)
    # Fiyatı boş (None) bırakılan kalemler MRP'de "fiyat eksik" uyarısını tetikleyecektir.
    bom_data = [
        # Dikdörtgen Kanal 600x400 (İzolasyonlu) BOM
        (
            "Dikdörtgen Kanal 600x400 (İzolasyonlu)",
            "Galvaniz Sac (0.80 mm)",
            "kg",
            18.5,
            45.0,
        ),
        (
            "Dikdörtgen Kanal 600x400 (İzolasyonlu)",
            "Flanş Profili (25 mm)",
            "metre",
            4.0,
            120.0,
        ),
        (
            "Dikdörtgen Kanal 600x400 (İzolasyonlu)",
            "Köşe Elemanı (25 mm)",
            "adet",
            4.0,
            8.0,
        ),
        (
            "Dikdörtgen Kanal 600x400 (İzolasyonlu)",
            "Neopren Conta (Flanş İçin)",
            "metre",
            4.0,
            12.5,
        ),
        (
            "Dikdörtgen Kanal 600x400 (İzolasyonlu)",
            "Kauçuk Yalıtım Levhası (20 mm)",
            "m²",
            3.2,
            180.0,
        ),
        (
            "Dikdörtgen Kanal 600x400 (İzolasyonlu)",
            "Silikon / Mastik (Kartuş)",
            "adet",
            0.2,
            75.0,
        ),
        (
            "Dikdörtgen Kanal 600x400 (İzolasyonlu)",
            "Flanş Civatası (M8x25)",
            "adet",
            16.0,
            2.5,
        ),
        # Dikdörtgen Kanal 300x200 (Yalıtımsız) BOM
        (
            "Dikdörtgen Kanal 300x200 (Yalıtımsız)",
            "Galvaniz Sac (0.60 mm)",
            "kg",
            8.5,
            48.0,
        ),
        (
            "Dikdörtgen Kanal 300x200 (Yalıtımsız)",
            "Flanş Profili (20 mm)",
            "metre",
            2.4,
            95.0,
        ),
        (
            "Dikdörtgen Kanal 300x200 (Yalıtımsız)",
            "Köşe Elemanı (20 mm)",
            "adet",
            4.0,
            6.5,
        ),
        # Fiyatı eksik öğe testi için ucuza mal olan conta fiyatını None bırakıyoruz
        (
            "Dikdörtgen Kanal 300x200 (Yalıtımsız)",
            "Neopren Conta (Flanş İçin)",
            "metre",
            2.4,
            None,
        ),
        (
            "Dikdörtgen Kanal 300x200 (Yalıtımsız)",
            "Silikon / Mastik (Kartuş)",
            "adet",
            0.1,
            75.0,
        ),
        (
            "Dikdörtgen Kanal 300x200 (Yalıtımsız)",
            "Flanş Civatası (M8x25)",
            "adet",
            8.0,
            2.5,
        ),
        # Dikdörtgen Kanal 800x600 (İzolasyonlu - HP) BOM
        (
            "Dikdörtgen Kanal 800x600 (İzolasyonlu - HP)",
            "Galvaniz Sac (1.00 mm)",
            "kg",
            25.0,
            42.0,
        ),
        (
            "Dikdörtgen Kanal 800x600 (İzolasyonlu - HP)",
            "Flanş Profili (30 mm)",
            "metre",
            2.8,
            150.0,
        ),
        (
            "Dikdörtgen Kanal 800x600 (İzolasyonlu - HP)",
            "Köşe Elemanı (30 mm)",
            "adet",
            4.0,
            12.0,
        ),
        (
            "Dikdörtgen Kanal 800x600 (İzolasyonlu - HP)",
            "Neopren Conta (Flanş İçin)",
            "metre",
            2.8,
            12.5,
        ),
        (
            "Dikdörtgen Kanal 800x600 (İzolasyonlu - HP)",
            "Taşyünü Levha (30 mm)",
            "m²",
            3.0,
            220.0,
        ),
        (
            "Dikdörtgen Kanal 800x600 (İzolasyonlu - HP)",
            "Flanş Civatası (M10x30)",
            "adet",
            12.0,
            4.5,
        ),
        # Klima Santrali Hücresi (KS-100) BOM
        (
            "Klima Santrali Hücresi (KS-100)",
            "Alüminyum Karkas Profili",
            "metre",
            20.0,
            250.0,
        ),
        ("Klima Santrali Hücresi (KS-100)", "Kabin Köşe Birleştirici", "adet", 8.0, 110.0),
        ("Klima Santrali Hücresi (KS-100)", "Sandviç Panel (50 mm)", "m²", 18.0, 450.0),
        (
            "Klima Santrali Hücresi (KS-100)",
            "Kabin Kapı Kolu ve Menteşesi",
            "adet",
            2.0,
            350.0,
        ),
        (
            "Klima Santrali Hücresi (KS-100)",
            "Filtre Sızdırmazlık Contası",
            "metre",
            6.0,
            35.0,
        ),
        # 90 Derece Dirsek (Dirsek 500) BOM
        ("90 Derece Dirsek (Dirsek 500)", "Galvaniz Sac (0.80 mm)", "kg", 12.0, 45.0),
        ("90 Derece Dirsek (Dirsek 500)", "Flanş Profili (25 mm)", "metre", 2.0, 120.0),
        ("90 Derece Dirsek (Dirsek 500)", "Köşe Elemanı (25 mm)", "adet", 4.0, 8.0),
        ("90 Derece Dirsek (Dirsek 500)", "Neopren Conta (Flanş İçin)", "metre", 2.0, 12.5),
        ("90 Derece Dirsek (Dirsek 500)", "Silikon / Mastik (Kartuş)", "adet", 0.15, 75.0),
    ]

    for p_name, item_name, unit, qty, cost in bom_data:
        p_id = product_ids[p_name]
        cur.execute(
            """
            INSERT INTO bom_items (product_id, name, unit, quantity_per_unit, cost_per_unit, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (p_id, item_name, unit, qty, cost, now_str, now_str),
        )

    print(f"✅ Ürünlere toplam {len(bom_data)} adet reçete (BOM) kalemi bağlandı.")

    # ── 4. Gerçekçi İş Emirlerini Ekle ──
    # [İş Emri 1] - Çoklu hat barındıran, 5% fire payı olan ana havalandırma projesi
    cur.execute(
        """
        INSERT INTO work_orders (project_name, waste_factor, created_at, updated_at)
        VALUES (?, ?, ?, ?)
    """,
        ("Merkez AVM Havalandırma Tesisatı İşi", 0.05, now_str, now_str),
    )
    wo1_id = cur.lastrowid

    # İş Emri 1 Satırları (Line Items)
    # 25 adet 600x400 İzolasyonlu Kanal ve 40 adet 300x200 Yalıtımsız Kanal
    lines_wo1 = [
        (wo1_id, product_ids["Dikdörtgen Kanal 600x400 (İzolasyonlu)"], 25),
        (wo1_id, product_ids["Dikdörtgen Kanal 300x200 (Yalıtımsız)"], 40),
    ]

    # [İş Emri 2] - Kritik yoğun bakım ünitesi projesi, 2% fire payı olan kanal hattı
    cur.execute(
        """
        INSERT INTO work_orders (project_name, waste_factor, created_at, updated_at)
        VALUES (?, ?, ?, ?)
    """,
        ("Acıbadem Hastanesi Yoğun Bakım Ünitesi", 0.02, now_str, now_str),
    )
    wo2_id = cur.lastrowid

    lines_wo2 = [
        (wo2_id, product_ids["Dikdörtgen Kanal 800x600 (İzolasyonlu - HP)"], 12),
        (wo2_id, product_ids["Dikdörtgen Kanal 600x400 (İzolasyonlu)"], 18),
    ]

    # [İş Emri 3] - Klima santrali hücresi ve dirsek içeren sipariş.
    # Bu iş emri MRP'ye gönderildiğinde hata fırlatma mekanizmasını (Ahize/Hücre kanalı dışı tipi doğrulaması) test ettirir.
    cur.execute(
        """
        INSERT INTO work_orders (project_name, waste_factor, created_at, updated_at)
        VALUES (?, ?, ?, ?)
    """,
        ("Klima Santrali & Bağlantı İmalatı (Santral Projesi)", 0.0, now_str, now_str),
    )
    wo3_id = cur.lastrowid

    lines_wo3 = [
        (wo3_id, product_ids["Klima Santrali Hücresi (KS-100)"], 2),
        (wo3_id, product_ids["90 Derece Dirsek (Dirsek 500)"], 10),
    ]

    all_lines = lines_wo1 + lines_wo2 + lines_wo3
    for wo_id, p_id, qty in all_lines:
        cur.execute(
            """
            INSERT INTO work_order_lines (work_order_id, product_id, quantity, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """,
            (wo_id, p_id, qty, now_str, now_str),
        )

    conn.commit()
    conn.close()

    print(f"✅ {len(all_lines)} adet iş emri satırı başarıyla eklendi.")
    print("🎉 Test verileri başarıyla yüklendi! Uygulamayı açarak tüm özellikleri test edebilirsiniz.")


if __name__ == "__main__":
    seed_database()
