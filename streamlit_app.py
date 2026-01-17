import os
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
import streamlit as st

from ui import components as ui
from ui.api_client import get as api_get, post as api_post
from ui.texts_tr import (
    APP_TITLE,
    BTN_DOWNLOAD_REPORT,
    BTN_RUN_MRP,
    ERR_INSULATION_REQUIRED,
    ERR_NAME_REQUIRED,
    ERR_WO_PRODUCT_REQUIRED,
    ERR_WO_PROJECT_REQUIRED,
    LBL_PRODUCT,
    LBL_PRODUCT_SUMMARY,
    LBL_PROJECT,
    LBL_QUANTITY,
    LBL_SEARCH_PRODUCT,
    LBL_SEARCH_WO,
    LBL_WO_SUMMARY,
    MSG_BOM_EMPTY,
    MSG_MRP_READY,
    MSG_NEED_PRODUCT,
    MSG_NEED_WO,
    MSG_REPORT_FAILED,
    MSG_SUCCESS_PRODUCT,
    MSG_SUCCESS_WO,
    PAGE_MRP,
    PAGE_PRODUCTS,
    PAGE_WORK_ORDERS,
)

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="HVAC Factory Ops", layout="wide")


def load_products() -> List[Dict[str, Any]]:
    try:
        return api_get("/products")
    except Exception as exc:
        ui.error(f"Ürünler alınamadı: {exc}")
        return []


def load_work_orders() -> List[Dict[str, Any]]:
    try:
        return api_get("/work-orders")
    except Exception as exc:
        ui.error(f"İş emirleri alınamadı: {exc}")
        return []


def create_product_form():
    st.subheader("Yeni Ürün (Dikdörtgen Kanal)")
    name = st.text_input("Ürün Adı", placeholder="Örn: Kanal A", key="product_name_input")
    description = st.text_area("Açıklama", "", key="product_desc_input")
    cols = st.columns(4)
    width_mm = cols[0].number_input("Genişlik (mm)", min_value=1.0, key="product_width")
    height_mm = cols[1].number_input("Yükseklik (mm)", min_value=1.0, key="product_height")
    length_mm = cols[2].number_input("Uzunluk (mm)", min_value=1.0, key="product_length")
    thickness_mm = cols[3].number_input("Sac Kalınlığı (mm)", min_value=0.1, key="product_thickness")
    insulation_enabled = st.checkbox("Yalıtım Var", key="product_insulation_enabled")
    ins_min = 0.1 if insulation_enabled else 0.0
    insulation_thickness_mm = st.number_input(
        "Yalıtım Kalınlığı (mm)",
        min_value=ins_min,
        value=0.0 if not insulation_enabled else max(0.1, ins_min),
        step=0.1,
        disabled=not insulation_enabled,
        key="product_insulation_thickness",
    )

    st.markdown("**BOM Kalemleri**")
    bom_count = st.number_input("BOM kalemi sayısı", min_value=0, max_value=10, value=0, step=1, key="bom_count")
    bom_items: List[Dict[str, Any]] = []
    for i in range(int(bom_count)):
        with st.expander(f"Kalem {i + 1}", expanded=True):
            bom_name = st.text_input(f"Ad {i}", key=f"bom_name_{i}")
            bom_unit = st.text_input(f"Birim {i}", key=f"bom_unit_{i}")
            bom_qty = st.number_input(f"Birim Başına Miktar {i}", min_value=0.0, value=1.0, key=f"bom_qty_{i}")
            bom_cost = st.number_input(
                f"Birim Maliyet {i} (opsiyonel)", min_value=0.0, value=0.0, key=f"bom_cost_{i}"
            )
            if bom_name.strip():
                bom_items.append(
                    {
                        "name": bom_name.strip(),
                        "unit": bom_unit.strip() if bom_unit else None,
                        "quantity_per_unit": bom_qty,
                        "cost_per_unit": bom_cost if bom_cost > 0 else None,
                    }
                )

    save_clicked = st.button("Ürünü Kaydet", key="product_save_button")
    if save_clicked:
        if not name.strip():
            ui.error(ERR_NAME_REQUIRED)
            return None
        if insulation_enabled and insulation_thickness_mm <= 0:
            ui.error(ERR_INSULATION_REQUIRED)
            return None
        try:
            payload = {
                "name": name.strip(),
                "description": description,
                "product_type": "RECTANGULAR_DUCT",
                "spec": {
                    "width_mm": width_mm,
                    "height_mm": height_mm,
                    "length_mm": length_mm,
                    "thickness_mm": thickness_mm,
                    "insulation_enabled": insulation_enabled,
                    "insulation_thickness_mm": insulation_thickness_mm if insulation_enabled else None,
                },
                "bom_items": bom_items,
            }
            created = api_post("/products", payload)
            ui.success(MSG_SUCCESS_PRODUCT)
            return created
        except Exception as exc:
            ui.error(f"Ürün kaydedilemedi: {exc}")
    return None


def create_work_order_form(products: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    st.subheader("Yeni İş Emri")
    if not products:
        ui.warning(MSG_NEED_PRODUCT)
        return None
    product_options = {f"{p['name']} (#{p['id']})": p for p in products}
    if "wo_lines" not in st.session_state:
        st.session_state["wo_lines"] = [{"product_label": None, "quantity": 1}]

    # Header
    project_name = st.text_input(LBL_PROJECT, placeholder="Örn: İstanbul Hastanesi B Blok", key="wo_project_name")

    # Lines table-like UI
    st.markdown("**İş Emri Kalemleri**")
    new_lines = []
    for idx, line in enumerate(st.session_state["wo_lines"]):
        cols = st.columns([3, 1, 0.5])
        product_label = cols[0].selectbox(
            f"{LBL_PRODUCT} {idx+1}",
            ["-"] + list(product_options.keys()),
            index=(list(product_options.keys()).index(line.get("product_label")) + 1) if line.get("product_label") else 0,
            key=f"wo_line_product_{idx}",
        )
        quantity = cols[1].number_input(
            f"{LBL_QUANTITY} {idx+1}",
            min_value=1,
            value=line.get("quantity", 1),
            key=f"wo_line_qty_{idx}",
        )
        remove_clicked = cols[2].button("Sil", key=f"wo_line_remove_{idx}")
        if remove_clicked and len(st.session_state["wo_lines"]) > 1:
            continue
        new_lines.append({"product_label": product_label if product_label != "-" else None, "quantity": quantity})
    st.session_state["wo_lines"] = new_lines

    if st.button("Yeni Kalem Ekle", key="wo_add_line"):
        st.session_state["wo_lines"].append({"product_label": None, "quantity": 1})

    submit = st.button("İş Emrini Kaydet", key="wo_save_button")
    if submit:
        try:
            if not project_name.strip():
                ui.error(ERR_WO_PROJECT_REQUIRED)
                return None
            lines_payload = []
            for line in st.session_state["wo_lines"]:
                if not line["product_label"]:
                    ui.error(ERR_WO_PRODUCT_REQUIRED)
                    return None
                lines_payload.append(
                    {
                        "product_id": product_options[line["product_label"]]["id"],
                        "quantity": int(line["quantity"]),
                    }
                )
            payload = {"project_name": project_name, "lines": lines_payload}
            created = api_post("/work-orders", payload)
            ui.success(MSG_SUCCESS_WO)
            st.session_state["wo_lines"] = [{"product_label": None, "quantity": 1}]
            return created
        except Exception as exc:
            ui.error(f"İş emri kaydedilemedi: {exc}")
    return None


def search_filter(items: List[Dict[str, Any]], text: str, keys: List[str]) -> List[Dict[str, Any]]:
    if not text.strip():
        return items
    t = text.strip().lower()
    return [i for i in items if any(t in str(i.get(k, "")).lower() for k in keys)]


def render_product_table(products: List[Dict[str, Any]]):
    rows = []
    for p in products:
        spec = p.get("spec", {})
        rows.append(
            {
                "ID": p["id"],
                "Ad": p["name"],
                "Açıklama": p.get("description"),
                "Tip": p.get("product_type"),
                "Genişlik": spec.get("width_mm"),
                "Yükseklik": spec.get("height_mm"),
                "Uzunluk": spec.get("length_mm"),
                "Kalınlık": spec.get("thickness_mm"),
                "Yalıtım": "Var" if spec.get("insulation_enabled") else "Yok",
            }
        )
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        ui.info("Henüz ürün yok.")


def render_work_order_table(work_orders: List[Dict[str, Any]]):
    rows = []
    for wo in work_orders:
        rows.append(
            {
                "ID": wo["id"],
                "Proje": wo["project_name"],
                "Satır Sayısı": len(wo.get("lines", [])),
            }
        )
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        ui.info("Henüz iş emri yok.")


def render_mrp_report(mrp: Dict[str, Any], wo_id: int):
    """Render structured MRP report with clear hierarchy."""
    header = mrp.get("header", {})
    summary = mrp.get("summary", {})
    lines = mrp.get("lines", [])
    bom_summary = mrp.get("bom_summary", {})

    # --- Section 1: Report Header ---
    st.markdown("### 📋 Rapor Bilgileri")
    header_cols = st.columns(4)
    header_cols[0].metric("Proje", header.get("project_name", "-"))
    header_cols[1].metric("İş Emri No", f"#{header.get('work_order_id', '-')}")
    header_cols[2].metric("Satır Sayısı", header.get("line_count", 0))
    header_cols[3].metric("Toplam Miktar", header.get("total_quantity", 0))

    st.markdown("---")

    # --- Section 2: Executive Summary ---
    st.markdown("### 📊 Özet Bilgiler")

    material = summary.get("material", {})
    cost = summary.get("cost", {})
    bom_metrics = bom_summary.get("metrics", {})

    # Material metrics
    st.markdown("**Malzeme İhtiyacı**")
    mat_cols = st.columns(3)
    mat_cols[0].metric("Toplam Sac Alanı", f"{material.get('sheet_area_m2', 0):.3f} m²")
    mat_cols[1].metric("Toplam Sac Ağırlığı", f"{material.get('sheet_mass_kg', 0):.3f} kg")
    mat_cols[2].metric("Toplam Yalıtım Alanı", f"{material.get('insulation_area_m2', 0):.3f} m²")

    # Cost metrics
    st.markdown("**Maliyet Özeti**")
    cost_cols = st.columns(3)
    cost_cols[0].metric("Tahmini BOM Maliyeti", f"{cost.get('bom_total', 0):,.2f} TL")
    cost_cols[1].metric("Fiyatlı Kalem", f"{cost.get('items_with_cost', 0)} / {bom_metrics.get('total_item_count', 0)}")
    cost_cols[2].metric("Maliyet Tamlığı", f"{bom_metrics.get('cost_completeness_pct', 0):.1f}%")

    if not cost.get("cost_complete", True):
        ui.warning("⚠ Bazı malzemelerin maliyeti eksik - tahmin tam değildir.")

    st.markdown("---")

    # --- Section 3: Line Details ---
    st.markdown("### 📦 Satır Detayları")
    if lines:
        line_rows = []
        for ln in lines:
            totals = ln.get("totals", {})
            line_rows.append(
                {
                    "#": ln.get("line_number", "-"),
                    "Ürün": ln.get("product_name", "-"),
                    "Miktar": ln.get("quantity", 0),
                    "Sac Alanı (m²)": f"{totals.get('sheet_area_m2', 0):.3f}",
                    "Sac Ağırlığı (kg)": f"{totals.get('sheet_mass_kg', 0):.3f}",
                    "Yalıtım Alanı (m²)": f"{totals.get('insulation_area_m2', 0):.3f}",
                }
            )
        st.dataframe(pd.DataFrame(line_rows), use_container_width=True, hide_index=True)
    else:
        ui.info("Satır bulunamadı.")

    st.markdown("---")

    # --- Section 4: BOM Summary ---
    st.markdown("### 🧾 Malzeme Listesi (BOM)")

    priced_items = bom_summary.get("priced_items", [])
    unpriced_items = bom_summary.get("unpriced_items", [])

    # Priced items table
    if priced_items:
        st.markdown("**Fiyatlı Malzemeler** (maliyet etkisine göre sıralı)")
        priced_rows = []
        for item in priced_items:
            priced_rows.append(
                {
                    "Malzeme": item.get("name", "-"),
                    "Birim": item.get("unit", "-"),
                    "Miktar": f"{item.get('total_quantity', 0):.2f}",
                    "Birim Fiyat": f"{item.get('cost_per_unit', 0):,.2f} TL",
                    "Toplam": f"{item.get('total_cost', 0):,.2f} TL",
                    "Pay": f"{item.get('cost_share_pct', 0):.1f}%",
                }
            )
        st.dataframe(pd.DataFrame(priced_rows), use_container_width=True, hide_index=True)

        # Subtotal
        st.markdown(f"**Toplam Maliyet: {cost.get('bom_total', 0):,.2f} TL**")

    # Unpriced items table
    if unpriced_items:
        st.markdown("**Fiyat Eksik Malzemeler**")
        unpriced_rows = []
        for item in unpriced_items:
            unpriced_rows.append(
                {
                    "Malzeme": item.get("name", "-"),
                    "Birim": item.get("unit", "-"),
                    "Miktar": f"{item.get('total_quantity', 0):.2f}",
                    "Durum": "⚠ Fiyat Gerekli",
                }
            )
        st.dataframe(pd.DataFrame(unpriced_rows), use_container_width=True, hide_index=True)

    if not priced_items and not unpriced_items:
        ui.info(MSG_BOM_EMPTY)

    st.markdown("---")

    # --- Excel Download ---
    excel_resp = requests.get(f"{API_URL}/mrp/work-orders/{wo_id}/excel", timeout=15)
    if excel_resp.ok:
        st.download_button(
            label=BTN_DOWNLOAD_REPORT,
            data=excel_resp.content,
            file_name=f"mrp_{wo_id}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"mrp_excel_download_{wo_id}",
        )
    else:
        ui.warning(MSG_REPORT_FAILED)


def work_order_central(products: List[Dict[str, Any]], work_orders: List[Dict[str, Any]]):
    st.header(PAGE_WORK_ORDERS)
    st.caption("Ürün tanımla, iş emri oluştur, MRP al ve rapor indir.")

    left, right = st.columns([1, 1])
    # Left: selection and filters
    with left:
        st.subheader("Kayıt Seçimi")
        prod_search = st.text_input(LBL_SEARCH_PRODUCT, placeholder="Ürün adı", key="wo_prod_search")
        filtered_products = search_filter(products, prod_search, ["name", "description"])
        product_labels = [f"{p['name']} (#{p['id']})" for p in filtered_products]
        selected_product_label = st.selectbox(
            LBL_PRODUCT, ["-"] + product_labels, key="wo_product_select_box", disabled=not filtered_products
        )

        wo_search = st.text_input(LBL_SEARCH_WO, placeholder="Proje adı", key="wo_search_box")
        filtered_wos = search_filter(work_orders, wo_search, ["project_name"])
        wo_labels = [f"{wo['project_name']} (#{wo['id']})" for wo in filtered_wos]
        selected_wo_label = st.selectbox(
            LBL_WO_SUMMARY, ["-"] + wo_labels, key="wo_select_box", disabled=not filtered_wos
        )

        selected_product = None
        if selected_product_label != "-" and filtered_products:
            selected_product = next(
                (p for p in filtered_products if f"{p['name']} (#{p['id']})" == selected_product_label), None
            )

        selected_wo = None
        if selected_wo_label != "-" and filtered_wos:
            selected_wo = next(
                (wo for wo in filtered_wos if f"{wo['project_name']} (#{wo['id']})" == selected_wo_label), None
            )

        st.markdown("----")
        st.markdown("### Ürün Özeti")
        if selected_product:
            ui.spec_block(selected_product.get("spec", {}))
        else:
            ui.info("Ürün seçilmedi.")

        st.markdown("### Seçili İş Emri Özeti")
        if selected_wo:
            cols = st.columns(2)
            cols[0].write(f"Proje / İş Emri: **{selected_wo['project_name']} (#{selected_wo['id']})**")
            cols[1].write(f"Satır Sayısı: **{len(selected_wo.get('lines', []))}**")
            if selected_wo.get("lines"):
                st.markdown("**Satırlar**")
                line_rows = []
                for ln in selected_wo["lines"]:
                    line_rows.append(
                        {
                            "Ürün": ln["product"]["name"],
                            "Miktar": ln["quantity"],
                        }
                    )
                st.dataframe(pd.DataFrame(line_rows), use_container_width=True, hide_index=True)
        else:
            ui.info("İş emri seçilmedi.")

    # Right: creation forms and MRP
    with right:
        st.subheader("Ürün Oluştur")
        new_product = create_product_form()
        if new_product:
            products.append(new_product)
            st.session_state["flash_message"] = MSG_SUCCESS_PRODUCT
            st.session_state["flash_type"] = "success"
            st.rerun()

        st.markdown("----")
        st.subheader("İş Emri Oluştur")
        if not products:
            ui.warning(MSG_NEED_PRODUCT)
        else:
            new_wo = create_work_order_form(products)
            if new_wo:
                work_orders.append(new_wo)
                st.session_state["flash_message"] = MSG_SUCCESS_WO
                st.session_state["flash_type"] = "success"
                st.rerun()

        st.markdown("----")
        st.subheader("MRP Oluştur ve Rapor")
        if not work_orders:
            ui.warning(MSG_NEED_WO)
        else:
            # KPI preview before MRP
            if selected_wo:
                ui.metric_row(
                    [
                        {"label": "Toplam Satır Sayısı", "value": f"{len(selected_wo.get('lines', []))}"},
                        {"label": "Toplam Miktar", "value": f"{sum([ln['quantity'] for ln in selected_wo.get('lines', [])])}"},
                    ]
                )
            run_disabled = selected_wo is None
            if st.button(BTN_RUN_MRP, disabled=run_disabled, type="primary", key="mrp_run_button"):
                try:
                    mrp = api_get(f"/mrp/work-orders/{selected_wo['id']}")
                    ui.success(MSG_MRP_READY)
                    render_mrp_report(mrp, selected_wo['id'])
                except Exception as exc:
                    ui.error(f"MRP hesaplanamadı: {exc}")


def admin_products_tab(products: List[Dict[str, Any]]):
    st.header(PAGE_PRODUCTS)
    search = st.text_input(LBL_SEARCH_PRODUCT, placeholder="İsim veya açıklama", key="admin_products_search")
    filtered = search_filter(products, search, ["name", "description"])
    render_product_table(filtered)
    st.markdown("---")
    st.subheader("Ürün Detayı")
    if filtered:
        labels = [f"{p['name']} (#{p['id']})" for p in filtered]
        selected = st.selectbox("Ürün seçiniz", labels, key="admin_products_select")
        product = next(p for p in filtered if f"{p['name']} (#{p['id']})" == selected)
        spec = product.get("spec", {})
        ui.spec_block(spec)
        st.markdown("**BOM Kalemleri**")
        bom_rows = []
        for b in product.get("bom_items", []):
            bom_rows.append(
                {
                    "Adı": b.get("name"),
                    "Birim": b.get("unit"),
                    "Birim Başına Miktar": b.get("quantity_per_unit"),
                    "Birim Maliyet": b.get("cost_per_unit") or 0,
                }
            )
        ui.render_table("BOM", bom_rows, ["Adı", "Birim", "Birim Başına Miktar", "Birim Maliyet"])


def admin_work_orders_tab(work_orders: List[Dict[str, Any]]):
    st.header(PAGE_WORK_ORDERS)
    search = st.text_input(LBL_SEARCH_WO, placeholder="Proje adı", key="admin_wos_search")
    filtered = search_filter(work_orders, search, ["project_name"])
    render_work_order_table(filtered)


def admin_mrp_tab(work_orders: List[Dict[str, Any]]):
    st.header(PAGE_MRP)
    if not work_orders:
        ui.info(MSG_NEED_WO)
        return
    labels = [f"{wo['project_name']} (#{wo['id']})" for wo in work_orders]
    selected = st.selectbox("İş emri seçiniz", labels, key="admin_mrp_select")
    selected_wo = next(wo for wo in work_orders if f"{wo['project_name']} (#{wo['id']})" == selected)
    if st.button(BTN_RUN_MRP, key="admin_mrp_run_btn"):
        try:
            mrp = api_get(f"/mrp/work-orders/{selected_wo['id']}")
            ui.success(MSG_MRP_READY)
            render_mrp_report(mrp, selected_wo['id'])
        except Exception as exc:
            ui.error(f"MRP hesaplanamadı: {exc}")


def main():
    if "products" not in st.session_state:
        st.session_state["products"] = load_products()
    if "work_orders" not in st.session_state:
        st.session_state["work_orders"] = load_work_orders()

    # Flash mesaj göster ve temizle
    flash_msg = st.session_state.pop("flash_message", None)
    flash_type = st.session_state.pop("flash_type", None)
    if flash_msg:
        if flash_type == "success":
            ui.success(flash_msg)
        elif flash_type == "warning":
            ui.warning(flash_msg)
        else:
            ui.info(flash_msg)

    products = st.session_state["products"]
    work_orders = st.session_state["work_orders"]

    tabs = st.tabs([PAGE_WORK_ORDERS, PAGE_PRODUCTS, PAGE_MRP])
    with tabs[0]:
        work_order_central(products, work_orders)
    with tabs[1]:
        admin_products_tab(products)
    with tabs[2]:
        admin_mrp_tab(work_orders)


if __name__ == "__main__":
    main()
