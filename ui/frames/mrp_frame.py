"""MRP ve Raporlar sayfası — Hesaplama + Excel Raporu."""

import customtkinter as ctk
from tkinter import messagebox, filedialog

from core.db_helper import get_db_session
from core.settings import get_settings
from modules.work_orders import service as wo_service
from modules.work_orders.models import WorkOrder
from modules.mrp.service import MRPService
from modules.reports.excel import build_mrp_excel

# ── Renkler ──
CLR_SURFACE = "#1E1E2E"
CLR_CARD = "#252536"
CLR_INPUT = "#313244"
CLR_TEXT = "#CDD6F4"
CLR_SUBTEXT = "#6C7086"
CLR_ACCENT = "#F9E2AF"
CLR_ACCENT_HOVER = "#FAB387"
CLR_BLUE = "#89B4FA"
CLR_GREEN = "#A6E3A1"
CLR_DANGER = "#F38BA8"
CLR_BORDER = "#45475A"


class MRPFrame(ctk.CTkFrame):
    """MRP ve Raporlar modülünün ana frame'i."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._wo_cache = []       # [{"id": ..., "display": ...}, ...]
        self._last_mrp_result = None

        # ── Üst başlık ──
        header = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=12, height=60)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text="📊  MRP ve Raporlar",
            font=ctk.CTkFont(size=20, weight="bold"), text_color=CLR_TEXT,
        ).grid(row=0, column=0, padx=20, pady=14, sticky="w")

        # ── Kontrol paneli ──
        self.control_panel = self._build_control_panel()
        self.control_panel.grid(row=1, column=0, sticky="ew", pady=(0, 12))

        # ── Sonuç alanı ──
        self.result_panel = ctk.CTkScrollableFrame(
            self, fg_color=CLR_SURFACE, corner_radius=12,
        )
        self.result_panel.grid(row=2, column=0, sticky="nsew")
        self.result_panel.grid_columnconfigure(0, weight=1)

        # Başlangıç mesajı
        self._show_empty_state()

        # Veri yükle
        self._load_work_orders()

    # ================================================================
    #  KONTROL PANELİ
    # ================================================================
    def _build_control_panel(self) -> ctk.CTkFrame:
        panel = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=12)
        panel.grid_columnconfigure(1, weight=1)

        # İş emri seçimi
        ctk.CTkLabel(
            panel, text="İş Emri Seçin:",
            font=ctk.CTkFont(size=13), text_color=CLR_TEXT,
        ).grid(row=0, column=0, padx=(16, 8), pady=14, sticky="w")

        self.wo_option = ctk.CTkOptionMenu(
            panel, values=["— Yükleniyor —"],
            fg_color=CLR_INPUT, button_color=CLR_BORDER,
            button_hover_color=CLR_ACCENT, text_color=CLR_TEXT,
            dropdown_fg_color=CLR_CARD, dropdown_hover_color=CLR_BORDER,
            dropdown_text_color=CLR_TEXT,
            font=ctk.CTkFont(size=13), width=300,
        )
        self.wo_option.grid(row=0, column=1, padx=4, pady=14, sticky="ew")

        # Butonlar
        btn_frame = ctk.CTkFrame(panel, fg_color="transparent")
        btn_frame.grid(row=0, column=2, padx=(8, 16), pady=14)

        ctk.CTkButton(
            btn_frame, text="▶  MRP Hesapla", width=140, height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=CLR_ACCENT, hover_color=CLR_ACCENT_HOVER,
            text_color="#1E1E2E", corner_radius=8,
            command=self._run_mrp,
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            btn_frame, text="📥 Excel Kaydet", width=130, height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=CLR_GREEN, hover_color="#94E2D5",
            text_color="#1E1E2E", corner_radius=8,
            command=self._export_excel,
        ).pack(side="left")

        return panel

    # ================================================================
    #  BOŞ DURUM
    # ================================================================
    def _show_empty_state(self):
        for w in self.result_panel.winfo_children():
            w.destroy()

        empty = ctk.CTkFrame(self.result_panel, fg_color="transparent")
        empty.pack(expand=True, pady=80)

        ctk.CTkLabel(empty, text="📊", font=ctk.CTkFont(size=56)).pack(pady=(0, 8))
        ctk.CTkLabel(
            empty, text="Bir iş emri seçip MRP Hesapla'ya basın",
            font=ctk.CTkFont(size=15), text_color=CLR_SUBTEXT,
        ).pack()
        ctk.CTkFrame(empty, height=3, width=50, fg_color=CLR_ACCENT, corner_radius=2).pack(pady=(12, 0))

    # ================================================================
    #  VERİ YÜKLEME
    # ================================================================
    def _load_work_orders(self):
        try:
            with get_db_session() as db:
                wos = wo_service.list_work_orders(db)
            self._wo_cache = [
                {"id": wo["id"], "name": wo["project_name"],
                 "display": f'{wo["project_name"]} (#{wo["id"]})'}
                for wo in wos
            ]
        except Exception:
            self._wo_cache = []

        names = [w["display"] for w in self._wo_cache]
        self.wo_option.configure(values=names if names else ["— İş emri yok —"])
        if names:
            self.wo_option.set(names[0])

    def _get_selected_wo_id(self) -> int | None:
        display = self.wo_option.get()
        for w in self._wo_cache:
            if w["display"] == display:
                return w["id"]
        return None

    # ================================================================
    #  MRP HESAPLAMA
    # ================================================================
    def _run_mrp(self):
        wo_id = self._get_selected_wo_id()
        if wo_id is None:
            messagebox.showwarning("Uyarı", "Lütfen bir iş emri seçin.")
            return

        try:
            with get_db_session() as db:
                # MRPService model nesnesi bekliyor — ORM'den çekelim
                wo_model = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
                if not wo_model:
                    messagebox.showerror("Hata", "İş emri bulunamadı.")
                    return

                settings = get_settings()
                mrp = MRPService(settings)
                result = mrp.compute_work_order(wo_model)

            self._last_mrp_result = result
            self._display_results(result)

        except Exception as e:
            messagebox.showerror("MRP Hatası", str(e))

    # ================================================================
    #  SONUÇLARI GÖSTER
    # ================================================================
    def _display_results(self, data: dict):
        for w in self.result_panel.winfo_children():
            w.destroy()

        header = data.get("header", {})
        summary = data.get("summary", {})
        material = summary.get("material", {})
        cost = summary.get("cost", {})
        lines = data.get("lines", [])
        bom = data.get("bom_summary", {})

        # ── Proje bilgisi ──
        info_frame = ctk.CTkFrame(self.result_panel, fg_color="transparent")
        info_frame.pack(fill="x", padx=12, pady=(12, 8))

        ctk.CTkLabel(
            info_frame, text=f"📋  {header.get('project_name', '?')}",
            font=ctk.CTkFont(size=18, weight="bold"), text_color=CLR_TEXT, anchor="w",
        ).pack(fill="x")

        waste_pct = header.get("waste_factor_pct", 0)
        info_text = f"İş Emri #{header.get('work_order_id', '?')}  •  {header.get('line_count', 0)} kalem  •  {header.get('total_quantity', 0)} adet  •  Fire: %{waste_pct:.0f}"
        ctk.CTkLabel(
            info_frame, text=info_text,
            font=ctk.CTkFont(size=12), text_color=CLR_SUBTEXT, anchor="w",
        ).pack(fill="x", pady=(2, 0))

        # ── Özet kartları ──
        cards_frame = ctk.CTkFrame(self.result_panel, fg_color="transparent")
        cards_frame.pack(fill="x", padx=12, pady=(8, 12))
        cards_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self._summary_card(cards_frame, 0, "📐", "Sac Alanı",
                           f"{material.get('sheet_area_m2', 0):.3f} m²", CLR_BLUE)
        self._summary_card(cards_frame, 1, "⚖️", "Sac Ağırlığı",
                           f"{material.get('sheet_mass_kg', 0):.3f} kg", CLR_GREEN)
        self._summary_card(cards_frame, 2, "🧊", "Yalıtım Alanı",
                           f"{material.get('insulation_area_m2', 0):.3f} m²", "#CBA6F7")
        
        nesting = material.get("profile_nesting")
        if nesting and nesting.get("total_bars", 0) > 0:
            prof_title = f"Profil (Fire: %{nesting.get('waste_percentage', 0):.1f})"
            prof_val = f"{nesting.get('total_bars')} Boy (6m)"
        else:
            prof_title = "Profil İhtiyacı"
            prof_val = f"{material.get('profile_length_m', 0):.2f} m"

        self._summary_card(cards_frame, 3, "📏", prof_title,
                           prof_val, "#F9E2AF")
        self._summary_card(cards_frame, 4, "💰", "BOM Maliyeti",
                           f"{cost.get('bom_total', 0):,.2f} ₺", CLR_ACCENT)

        # ── Kalem detayları ──
        if lines:
            self._section_title("Kalem Detayları")
            for line in lines:
                self._line_detail_card(line)

        # ── BOM Özeti — Fiyatlı kalemler ──
        priced = bom.get("priced_items", [])
        if priced:
            self._section_title(f"Malzeme Listesi — Fiyatlı ({len(priced)} kalem)")
            for item in priced:
                self._bom_item_card(item, priced=True)

        # ── BOM Özeti — Fiyatsız kalemler ──
        unpriced = bom.get("unpriced_items", [])
        if unpriced:
            self._section_title(f"Malzeme Listesi — Fiyat Eksik ({len(unpriced)} kalem)")
            for item in unpriced:
                self._bom_item_card(item, priced=False)

        # ── Maliyet tamlığı uyarısı ──
        metrics = bom.get("metrics", {})
        completeness = metrics.get("cost_completeness_pct", 100)
        if completeness < 100:
            warn = ctk.CTkFrame(self.result_panel, fg_color="#45475A", corner_radius=8)
            warn.pack(fill="x", padx=12, pady=(4, 12))
            ctk.CTkLabel(
                warn, text=f"⚠️  Maliyet tamlığı: %{completeness:.0f} — Bazı malzemelerin fiyatı eksik",
                font=ctk.CTkFont(size=12), text_color=CLR_ACCENT, anchor="w",
            ).pack(padx=12, pady=8)

    # ── Yardımcı: Özet kartı ──
    def _summary_card(self, parent, col, icon, title, value, accent):
        card = ctk.CTkFrame(parent, fg_color=CLR_CARD, corner_radius=12)
        card.grid(row=0, column=col, sticky="nsew", padx=4, pady=0)

        ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=24)).pack(pady=(14, 4))
        ctk.CTkLabel(
            card, text=title,
            font=ctk.CTkFont(size=11), text_color=CLR_SUBTEXT,
        ).pack()
        ctk.CTkLabel(
            card, text=value,
            font=ctk.CTkFont(size=16, weight="bold"), text_color=accent,
        ).pack(pady=(2, 4))
        ctk.CTkFrame(card, height=3, width=40, fg_color=accent, corner_radius=2).pack(pady=(0, 14))

    # ── Yardımcı: Bölüm başlığı ──
    def _section_title(self, text):
        ctk.CTkLabel(
            self.result_panel, text=text,
            font=ctk.CTkFont(size=14, weight="bold"), text_color=CLR_TEXT, anchor="w",
        ).pack(fill="x", padx=16, pady=(12, 6))

    # ── Yardımcı: Kalem detay kartı ──
    def _line_detail_card(self, line: dict):
        card = ctk.CTkFrame(self.result_panel, fg_color=CLR_CARD, corner_radius=8)
        card.pack(fill="x", padx=12, pady=2)
        card.grid_columnconfigure(1, weight=1)

        totals = line.get("totals", {})

        ctk.CTkLabel(
            card, text=f"  {line.get('line_number', '?')}.",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=CLR_BLUE, width=30,
        ).grid(row=0, column=0, padx=(8, 4), pady=8, sticky="w")

        ctk.CTkLabel(
            card, text=f"{line.get('product_name', '?')}  ×  {line.get('quantity', 0)} adet",
            font=ctk.CTkFont(size=12), text_color=CLR_TEXT, anchor="w",
        ).grid(row=0, column=1, padx=4, pady=8, sticky="w")

        detail = f"Sac: {totals.get('sheet_area_m2', 0):.3f} m²  •  {totals.get('sheet_mass_kg', 0):.3f} kg"
        if totals.get("insulation_area_m2", 0) > 0:
            detail += f"  •  Yalıtım: {totals['insulation_area_m2']:.3f} m²"
        if totals.get("profile_length_m", 0) > 0:
            detail += f" | Profil: {totals['profile_length_m']:.2f} m"

        ctk.CTkLabel(
            card, text=detail,
            font=ctk.CTkFont(size=11), text_color=CLR_SUBTEXT,
        ).grid(row=0, column=2, padx=(4, 12), pady=8, sticky="e")

    # ── Yardımcı: BOM kalem kartı ──
    def _bom_item_card(self, item: dict, priced: bool):
        card = ctk.CTkFrame(self.result_panel, fg_color=CLR_CARD, corner_radius=8)
        card.pack(fill="x", padx=12, pady=2)
        card.grid_columnconfigure(0, weight=1)

        name_text = f"  {item.get('name', '?')}"
        unit = item.get("unit", "")
        qty = item.get("total_quantity", 0)

        left = f"{name_text}  —  {qty:.2f} {unit}".strip()

        ctk.CTkLabel(
            card, text=left,
            font=ctk.CTkFont(size=12), text_color=CLR_TEXT, anchor="w",
        ).grid(row=0, column=0, padx=(8, 4), pady=8, sticky="w")

        if priced:
            cost_text = f"{item.get('total_cost', 0):,.2f} ₺  ({item.get('cost_share_pct', 0):.1f}%)"
            ctk.CTkLabel(
                card, text=cost_text,
                font=ctk.CTkFont(size=12, weight="bold"), text_color=CLR_GREEN,
            ).grid(row=0, column=1, padx=(4, 12), pady=8, sticky="e")
        else:
            ctk.CTkLabel(
                card, text="Fiyat eksik",
                font=ctk.CTkFont(size=11), text_color=CLR_DANGER,
            ).grid(row=0, column=1, padx=(4, 12), pady=8, sticky="e")

    # ================================================================
    #  EXCEL RAPORU KAYDET
    # ================================================================
    def _export_excel(self):
        if self._last_mrp_result is None:
            messagebox.showwarning("Uyarı", "Önce MRP hesaplaması yapın.")
            return

        project_name = self._last_mrp_result.get("header", {}).get("project_name", "rapor")
        safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in project_name)

        file_path = filedialog.asksaveasfilename(
            title="Excel Raporunu Kaydet",
            defaultextension=".xlsx",
            initialfile=f"MRP_{safe_name}.xlsx",
            filetypes=[("Excel Dosyası", "*.xlsx"), ("Tüm Dosyalar", "*.*")],
        )

        if not file_path:
            return  # Kullanıcı iptal etti

        try:
            excel_stream = build_mrp_excel(self._last_mrp_result)
            with open(file_path, "wb") as f:
                f.write(excel_stream.read())
            messagebox.showinfo("Başarılı", f"Rapor kaydedildi:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Hata", f"Excel oluşturulamadı:\n{e}")

    # ================================================================
    #  SAYFA AKTİF OLDUĞUNDA VERİLERİ TAZELE
    # ================================================================
    def tkraise(self, *args, **kwargs):
        self._load_work_orders()
        super().tkraise(*args, **kwargs)
