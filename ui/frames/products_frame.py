"""Ürün Tanımları sayfası — Form + Liste."""

import customtkinter as ctk
from tkinter import messagebox

from core.db_helper import get_db_session
from modules.products import service as product_service
from modules.products.schemas import (
    ProductCreate, RectangularDuctSpec, AHUSpec, FittingSpec, BOMItemCreate,
)
from modules.products.types import ProductType

# ── Renkler ──
CLR_SURFACE = "#1E1E2E"
CLR_CARD = "#252536"
CLR_INPUT = "#313244"
CLR_TEXT = "#CDD6F4"
CLR_SUBTEXT = "#6C7086"
CLR_ACCENT = "#A6E3A1"
CLR_DANGER = "#F38BA8"
CLR_BORDER = "#45475A"

# ── Ürün tipi eşlemeleri ──
_TYPE_LABELS = [
    "Dikdörtgen Kanal",
    "Klima Santrali (AHU)",
    "Bağlantı Parçası (Fitting)",
]
_LABEL_TO_ENUM = {
    "Dikdörtgen Kanal": ProductType.RECTANGULAR_DUCT,
    "Klima Santrali (AHU)": ProductType.AHU_CABINET,
    "Bağlantı Parçası (Fitting)": ProductType.FITTING_DUCT,
}
_ENUM_TO_LABEL = {v: k for k, v in _LABEL_TO_ENUM.items()}

# Fitting şekil eşlemeleri
_FITTING_LABELS = ["Dirsek", "Te", "Redüksiyon", "Ofset", "Geçiş"]
_FITTING_LABEL_TO_VALUE = {
    "Dirsek": "ELBOW",
    "Te": "TEE",
    "Redüksiyon": "REDUCER",
    "Ofset": "OFFSET",
    "Geçiş": "TRANSITION",
}
_FITTING_VALUE_TO_LABEL = {v: k for k, v in _FITTING_LABEL_TO_VALUE.items()}


class ProductsFrame(ctk.CTkFrame):
    """Ürün Tanımları modülünün ana frame'i."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=2)   # Sol: form
        self.grid_columnconfigure(1, weight=3)   # Sağ: liste
        self.grid_rowconfigure(1, weight=1)

        # ── Üst başlık ──
        header = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=12, height=60)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text="📦  Ürün Tanımları",
            font=ctk.CTkFont(size=20, weight="bold"), text_color=CLR_TEXT,
        ).grid(row=0, column=0, padx=20, pady=14, sticky="w")

        # ── Sol panel: Form ──
        self.form_panel = self._build_form_panel()
        self.form_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 6))

        # ── Sağ panel: Ürün Listesi ──
        self.list_panel = self._build_list_panel()
        self.list_panel.grid(row=1, column=1, sticky="nsew", padx=(6, 0))

        # İlk yükleme
        self._refresh_product_list()

    # ================================================================
    #  SOL PANEL — ÜRÜN EKLEME FORMU
    # ================================================================
    def _build_form_panel(self) -> ctk.CTkFrame:
        panel = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=12)

        # Başlık
        ctk.CTkLabel(
            panel, text="Yeni Ürün Ekle",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=CLR_TEXT,
        ).pack(anchor="w", padx=16, pady=(16, 12))

        # Kaydırılabilir form alanı
        form_scroll = ctk.CTkScrollableFrame(
            panel, fg_color="transparent", corner_radius=0,
        )
        form_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        form_scroll.grid_columnconfigure(1, weight=1)

        row = 0

        # — Ürün adı —
        row = self._add_field(form_scroll, row, "Ürün Adı *")
        self.entry_name = ctk.CTkEntry(
            form_scroll, fg_color=CLR_INPUT, border_color=CLR_BORDER,
            text_color=CLR_TEXT, placeholder_text="Örn: Dikdörtgen Kanal 300x200",
        )
        self.entry_name.grid(row=row, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 8))
        row += 1

        # — Açıklama —
        row = self._add_field(form_scroll, row, "Açıklama")
        self.entry_desc = ctk.CTkEntry(
            form_scroll, fg_color=CLR_INPUT, border_color=CLR_BORDER,
            text_color=CLR_TEXT, placeholder_text="Opsiyonel açıklama",
        )
        self.entry_desc.grid(row=row, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 12))
        row += 1

        # — Ürün Tipi —
        row = self._add_field(form_scroll, row, "Ürün Tipi *")
        self.product_type_var = ctk.StringVar(value=_TYPE_LABELS[0])
        self.combo_product_type = ctk.CTkComboBox(
            form_scroll, values=_TYPE_LABELS,
            variable=self.product_type_var,
            fg_color=CLR_INPUT, border_color=CLR_BORDER,
            button_color=CLR_BORDER, button_hover_color=CLR_ACCENT,
            text_color=CLR_TEXT, dropdown_fg_color=CLR_CARD,
            dropdown_text_color=CLR_TEXT, dropdown_hover_color=CLR_BORDER,
            font=ctk.CTkFont(size=12),
            command=self._on_product_type_changed,
            state="readonly",
        )
        self.combo_product_type.grid(row=row, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 12))
        row += 1

        # ── Spec Frame'leri (yalnızca biri görünür) ──
        self._spec_row = row  # frame'lerin yerleştirileceği satır
        self.spec_frames = {}

        self.spec_frames["RECTANGULAR_DUCT"] = self._build_rectangular_spec(form_scroll, row)
        self.spec_frames["AHU_CABINET"] = self._build_ahu_spec(form_scroll, row)
        self.spec_frames["FITTING_DUCT"] = self._build_fitting_spec(form_scroll, row)

        # Varsayılan olarak dikdörtgen kanal göster
        self._show_spec_frame("RECTANGULAR_DUCT")
        row += 1

        # — BOM (Malzeme Listesi) —
        ctk.CTkFrame(form_scroll, height=1, fg_color=CLR_BORDER).grid(
            row=row, column=0, columnspan=2, sticky="ew", padx=4, pady=(12, 8)
        )
        row += 1

        bom_header = ctk.CTkFrame(form_scroll, fg_color="transparent")
        bom_header.grid(row=row, column=0, columnspan=2, sticky="ew", padx=4)
        bom_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            bom_header, text="BOM — Malzeme Listesi",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=CLR_TEXT,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            bom_header, text="＋ Satır Ekle", width=90, height=28,
            font=ctk.CTkFont(size=11), fg_color=CLR_INPUT,
            hover_color=CLR_BORDER, text_color=CLR_TEXT, corner_radius=6,
            command=self._add_bom_row,
        ).grid(row=0, column=1, sticky="e")
        row += 1

        # BOM satırlarının konteyneri
        self.bom_container = ctk.CTkFrame(form_scroll, fg_color="transparent")
        self.bom_container.grid(row=row, column=0, columnspan=2, sticky="ew", padx=4, pady=(4, 8))
        self.bom_rows = []  # Her eleman: (frame, name_entry, unit_entry, qty_entry, cost_entry)
        row += 1

        # — Kaydet butonu —
        ctk.CTkButton(
            panel, text="💾  Ürünü Kaydet", height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=CLR_ACCENT, hover_color="#94E2D5",
            text_color="#1E1E2E", corner_radius=10,
            command=self._save_product,
        ).pack(fill="x", padx=16, pady=(4, 16))

        return panel

    # ── Dikdörtgen Kanal spec frame ──
    def _build_rectangular_spec(self, parent, row) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color="transparent")

        # Başlık
        ctk.CTkLabel(
            frame, text="EBATLAR (mm)",
            font=ctk.CTkFont(size=10, weight="bold"), text_color=CLR_SUBTEXT,
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=4, pady=(4, 4))

        # Genişlik / Yükseklik
        dim_frame1 = ctk.CTkFrame(frame, fg_color="transparent")
        dim_frame1.grid(row=1, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 4))
        dim_frame1.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(dim_frame1, text="Genişlik", font=ctk.CTkFont(size=11), text_color=CLR_SUBTEXT).grid(row=0, column=0, sticky="w", padx=(0, 4))
        self.entry_width = ctk.CTkEntry(dim_frame1, fg_color=CLR_INPUT, border_color=CLR_BORDER, text_color=CLR_TEXT, width=80, placeholder_text="mm")
        self.entry_width.grid(row=1, column=0, sticky="ew", padx=(0, 4))

        ctk.CTkLabel(dim_frame1, text="Yükseklik", font=ctk.CTkFont(size=11), text_color=CLR_SUBTEXT).grid(row=0, column=1, sticky="w", padx=(4, 0))
        self.entry_height = ctk.CTkEntry(dim_frame1, fg_color=CLR_INPUT, border_color=CLR_BORDER, text_color=CLR_TEXT, width=80, placeholder_text="mm")
        self.entry_height.grid(row=1, column=1, sticky="ew", padx=(4, 0))

        # Uzunluk / Kalınlık
        dim_frame2 = ctk.CTkFrame(frame, fg_color="transparent")
        dim_frame2.grid(row=2, column=0, columnspan=2, sticky="ew", padx=4, pady=(4, 8))
        dim_frame2.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(dim_frame2, text="Uzunluk", font=ctk.CTkFont(size=11), text_color=CLR_SUBTEXT).grid(row=0, column=0, sticky="w", padx=(0, 4))
        self.entry_length = ctk.CTkEntry(dim_frame2, fg_color=CLR_INPUT, border_color=CLR_BORDER, text_color=CLR_TEXT, width=80, placeholder_text="mm")
        self.entry_length.grid(row=1, column=0, sticky="ew", padx=(0, 4))

        ctk.CTkLabel(dim_frame2, text="Sac Kalınlığı", font=ctk.CTkFont(size=11), text_color=CLR_SUBTEXT).grid(row=0, column=1, sticky="w", padx=(4, 0))
        self.entry_thickness = ctk.CTkEntry(dim_frame2, fg_color=CLR_INPUT, border_color=CLR_BORDER, text_color=CLR_TEXT, width=80, placeholder_text="mm")
        self.entry_thickness.grid(row=1, column=1, sticky="ew", padx=(4, 0))

        # Yalıtım
        insulation_frame = ctk.CTkFrame(frame, fg_color="transparent")
        insulation_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 4))
        insulation_frame.grid_columnconfigure(1, weight=1)

        self.insulation_var = ctk.BooleanVar(value=False)
        self.chk_insulation = ctk.CTkCheckBox(
            insulation_frame, text="Yalıtım Var",
            variable=self.insulation_var,
            font=ctk.CTkFont(size=12), text_color=CLR_TEXT,
            command=self._toggle_insulation,
        )
        self.chk_insulation.grid(row=0, column=0, sticky="w")

        self.entry_insulation = ctk.CTkEntry(
            insulation_frame, fg_color=CLR_INPUT, border_color=CLR_BORDER,
            text_color=CLR_TEXT, width=100, placeholder_text="Kalınlık (mm)",
            state="disabled",
        )
        self.entry_insulation.grid(row=0, column=1, sticky="w", padx=(12, 0))

        return frame

    # ── AHU spec frame ──
    def _build_ahu_spec(self, parent, row) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color="transparent")

        ctk.CTkLabel(
            frame, text="KABİN EBATLARI (mm)",
            font=ctk.CTkFont(size=10, weight="bold"), text_color=CLR_SUBTEXT,
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=4, pady=(4, 4))

        # Genişlik / Yükseklik
        dim_frame1 = ctk.CTkFrame(frame, fg_color="transparent")
        dim_frame1.grid(row=1, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 4))
        dim_frame1.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(dim_frame1, text="Genişlik", font=ctk.CTkFont(size=11), text_color=CLR_SUBTEXT).grid(row=0, column=0, sticky="w", padx=(0, 4))
        self.ahu_entry_width = ctk.CTkEntry(dim_frame1, fg_color=CLR_INPUT, border_color=CLR_BORDER, text_color=CLR_TEXT, width=80, placeholder_text="mm")
        self.ahu_entry_width.grid(row=1, column=0, sticky="ew", padx=(0, 4))

        ctk.CTkLabel(dim_frame1, text="Yükseklik", font=ctk.CTkFont(size=11), text_color=CLR_SUBTEXT).grid(row=0, column=1, sticky="w", padx=(4, 0))
        self.ahu_entry_height = ctk.CTkEntry(dim_frame1, fg_color=CLR_INPUT, border_color=CLR_BORDER, text_color=CLR_TEXT, width=80, placeholder_text="mm")
        self.ahu_entry_height.grid(row=1, column=1, sticky="ew", padx=(4, 0))

        # Uzunluk / Panel Kalınlığı
        dim_frame2 = ctk.CTkFrame(frame, fg_color="transparent")
        dim_frame2.grid(row=2, column=0, columnspan=2, sticky="ew", padx=4, pady=(4, 8))
        dim_frame2.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(dim_frame2, text="Uzunluk", font=ctk.CTkFont(size=11), text_color=CLR_SUBTEXT).grid(row=0, column=0, sticky="w", padx=(0, 4))
        self.ahu_entry_length = ctk.CTkEntry(dim_frame2, fg_color=CLR_INPUT, border_color=CLR_BORDER, text_color=CLR_TEXT, width=80, placeholder_text="mm")
        self.ahu_entry_length.grid(row=1, column=0, sticky="ew", padx=(0, 4))

        ctk.CTkLabel(dim_frame2, text="Panel Kalınlığı", font=ctk.CTkFont(size=11), text_color=CLR_SUBTEXT).grid(row=0, column=1, sticky="w", padx=(4, 0))
        self.ahu_entry_panel_thickness = ctk.CTkEntry(dim_frame2, fg_color=CLR_INPUT, border_color=CLR_BORDER, text_color=CLR_TEXT, width=80, placeholder_text="mm")
        self.ahu_entry_panel_thickness.grid(row=1, column=1, sticky="ew", padx=(4, 0))

        # Profil çerçeve checkbox
        self.ahu_profile_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            frame, text="Profil Çerçeve Mevcut",
            variable=self.ahu_profile_var,
            font=ctk.CTkFont(size=12), text_color=CLR_TEXT,
        ).grid(row=3, column=0, columnspan=2, sticky="w", padx=4, pady=(0, 4))

        return frame

    # ── Fitting spec frame ──
    def _build_fitting_spec(self, parent, row) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color="transparent")

        ctk.CTkLabel(
            frame, text="BAĞLANTI PARÇASI ÖZELLİKLERİ",
            font=ctk.CTkFont(size=10, weight="bold"), text_color=CLR_SUBTEXT,
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=4, pady=(4, 4))

        # Fitting şekli dropdown
        shape_frame = ctk.CTkFrame(frame, fg_color="transparent")
        shape_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 4))
        shape_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(shape_frame, text="Parça Şekli", font=ctk.CTkFont(size=11), text_color=CLR_SUBTEXT).grid(row=0, column=0, columnspan=2, sticky="w")
        self.fitting_shape_var = ctk.StringVar(value=_FITTING_LABELS[0])
        self.combo_fitting_shape = ctk.CTkComboBox(
            shape_frame, values=_FITTING_LABELS,
            variable=self.fitting_shape_var,
            fg_color=CLR_INPUT, border_color=CLR_BORDER,
            button_color=CLR_BORDER, button_hover_color=CLR_ACCENT,
            text_color=CLR_TEXT, dropdown_fg_color=CLR_CARD,
            dropdown_text_color=CLR_TEXT, dropdown_hover_color=CLR_BORDER,
            font=ctk.CTkFont(size=12),
            state="readonly",
        )
        self.combo_fitting_shape.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 4))

        # Ana Ölçü / Kalınlık
        dim_frame = ctk.CTkFrame(frame, fg_color="transparent")
        dim_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 4))
        dim_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(dim_frame, text="Ana Ölçü", font=ctk.CTkFont(size=11), text_color=CLR_SUBTEXT).grid(row=0, column=0, sticky="w", padx=(0, 4))
        self.fitting_entry_main_dim = ctk.CTkEntry(dim_frame, fg_color=CLR_INPUT, border_color=CLR_BORDER, text_color=CLR_TEXT, width=80, placeholder_text="mm")
        self.fitting_entry_main_dim.grid(row=1, column=0, sticky="ew", padx=(0, 4))

        ctk.CTkLabel(dim_frame, text="Sac Kalınlığı", font=ctk.CTkFont(size=11), text_color=CLR_SUBTEXT).grid(row=0, column=1, sticky="w", padx=(4, 0))
        self.fitting_entry_thickness = ctk.CTkEntry(dim_frame, fg_color=CLR_INPUT, border_color=CLR_BORDER, text_color=CLR_TEXT, width=80, placeholder_text="mm")
        self.fitting_entry_thickness.grid(row=1, column=1, sticky="ew", padx=(4, 0))

        # Açı (opsiyonel)
        angle_frame = ctk.CTkFrame(frame, fg_color="transparent")
        angle_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 4))
        angle_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(angle_frame, text="Açı (opsiyonel)", font=ctk.CTkFont(size=11), text_color=CLR_SUBTEXT).grid(row=0, column=0, sticky="w")
        self.fitting_entry_angle = ctk.CTkEntry(angle_frame, fg_color=CLR_INPUT, border_color=CLR_BORDER, text_color=CLR_TEXT, width=80, placeholder_text="derece")
        self.fitting_entry_angle.grid(row=1, column=0, sticky="w")

        return frame

    # ── Spec frame göster/gizle ──
    def _show_spec_frame(self, type_key: str):
        """Yalnızca seçilen ürün tipinin spec frame'ini gösterir."""
        for key, frame in self.spec_frames.items():
            frame.grid_forget()
        target = self.spec_frames.get(type_key)
        if target:
            target.grid(row=self._spec_row, column=0, columnspan=2, sticky="ew")

    def _on_product_type_changed(self, selected_label: str):
        """Ürün tipi combobox değiştiğinde çağrılır."""
        product_type = _LABEL_TO_ENUM.get(selected_label)
        if product_type:
            self._show_spec_frame(product_type.value)

    # ================================================================
    #  SAĞ PANEL — ÜRÜN LİSTESİ
    # ================================================================
    def _build_list_panel(self) -> ctk.CTkFrame:
        panel = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=12)

        ctk.CTkLabel(
            panel, text="Kayıtlı Ürünler",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=CLR_TEXT,
        ).pack(anchor="w", padx=16, pady=(16, 8))

        # Kaydırılabilir liste
        self.product_list = ctk.CTkScrollableFrame(
            panel, fg_color="transparent", corner_radius=0,
        )
        self.product_list.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.product_list.grid_columnconfigure(0, weight=1)

        return panel

    # ================================================================
    #  YARDIMCI METOTLAR
    # ================================================================
    @staticmethod
    def _add_field(parent, row: int, label_text: str) -> int:
        ctk.CTkLabel(
            parent, text=label_text,
            font=ctk.CTkFont(size=12), text_color=CLR_SUBTEXT,
        ).grid(row=row, column=0, columnspan=2, sticky="w", padx=4, pady=(4, 2))
        return row + 1

    def _toggle_insulation(self):
        if self.insulation_var.get():
            self.entry_insulation.configure(state="normal")
        else:
            self.entry_insulation.delete(0, "end")
            self.entry_insulation.configure(state="disabled")

    # ── BOM satır yönetimi ──
    def _add_bom_row(self):
        row_frame = ctk.CTkFrame(self.bom_container, fg_color=CLR_CARD, corner_radius=8)
        row_frame.pack(fill="x", pady=2)
        row_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        e_name = ctk.CTkEntry(row_frame, placeholder_text="Malzeme adı", fg_color=CLR_INPUT, border_color=CLR_BORDER, text_color=CLR_TEXT, height=28, font=ctk.CTkFont(size=11))
        e_name.grid(row=0, column=0, padx=(6, 2), pady=6, sticky="ew")

        e_unit = ctk.CTkEntry(row_frame, placeholder_text="Birim", fg_color=CLR_INPUT, border_color=CLR_BORDER, text_color=CLR_TEXT, height=28, width=60, font=ctk.CTkFont(size=11))
        e_unit.grid(row=0, column=1, padx=2, pady=6, sticky="ew")

        e_qty = ctk.CTkEntry(row_frame, placeholder_text="Miktar", fg_color=CLR_INPUT, border_color=CLR_BORDER, text_color=CLR_TEXT, height=28, width=60, font=ctk.CTkFont(size=11))
        e_qty.grid(row=0, column=2, padx=2, pady=6, sticky="ew")

        e_cost = ctk.CTkEntry(row_frame, placeholder_text="Maliyet", fg_color=CLR_INPUT, border_color=CLR_BORDER, text_color=CLR_TEXT, height=28, width=60, font=ctk.CTkFont(size=11))
        e_cost.grid(row=0, column=3, padx=2, pady=6, sticky="ew")

        btn_del = ctk.CTkButton(
            row_frame, text="✕", width=28, height=28,
            fg_color=CLR_DANGER, hover_color="#EBA0AC",
            text_color="#1E1E2E", corner_radius=6,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self._remove_bom_row(row_frame),
        )
        btn_del.grid(row=0, column=4, padx=(2, 6), pady=6)

        self.bom_rows.append((row_frame, e_name, e_unit, e_qty, e_cost))

    def _remove_bom_row(self, row_frame):
        self.bom_rows = [r for r in self.bom_rows if r[0] != row_frame]
        row_frame.destroy()

    # ── Formu sıfırla ──
    def _clear_form(self):
        self.entry_name.delete(0, "end")
        self.entry_desc.delete(0, "end")

        # Ürün tipini varsayılana dön
        self.product_type_var.set(_TYPE_LABELS[0])
        self._show_spec_frame("RECTANGULAR_DUCT")

        # Dikdörtgen kanal alanları
        self.entry_width.delete(0, "end")
        self.entry_height.delete(0, "end")
        self.entry_length.delete(0, "end")
        self.entry_thickness.delete(0, "end")
        self.insulation_var.set(False)
        self.entry_insulation.configure(state="normal")
        self.entry_insulation.delete(0, "end")
        self.entry_insulation.configure(state="disabled")

        # AHU alanları
        self.ahu_entry_width.delete(0, "end")
        self.ahu_entry_height.delete(0, "end")
        self.ahu_entry_length.delete(0, "end")
        self.ahu_entry_panel_thickness.delete(0, "end")
        self.ahu_profile_var.set(True)

        # Fitting alanları
        self.fitting_shape_var.set(_FITTING_LABELS[0])
        self.fitting_entry_main_dim.delete(0, "end")
        self.fitting_entry_thickness.delete(0, "end")
        self.fitting_entry_angle.delete(0, "end")

        # BOM
        for row_frame, *_ in self.bom_rows:
            row_frame.destroy()
        self.bom_rows.clear()

    # ── Float okuma yardımcısı ──
    @staticmethod
    def _parse_float(value: str, field_name: str) -> float:
        value = value.strip()
        if not value:
            raise ValueError(f"{field_name} boş bırakılamaz")
        try:
            return float(value)
        except ValueError:
            raise ValueError(f"{field_name} geçerli bir sayı olmalıdır")

    @staticmethod
    def _parse_optional_float(value: str) -> float | None:
        value = value.strip()
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            return None

    # ================================================================
    #  VERİTABANI İŞLEMLERİ
    # ================================================================
    def _build_spec(self, product_type: ProductType):
        """Seçili ürün tipine göre doğru Spec nesnesini oluşturur."""
        if product_type == ProductType.RECTANGULAR_DUCT:
            return RectangularDuctSpec(
                width_mm=self._parse_float(self.entry_width.get(), "Genişlik"),
                height_mm=self._parse_float(self.entry_height.get(), "Yükseklik"),
                length_mm=self._parse_float(self.entry_length.get(), "Uzunluk"),
                thickness_mm=self._parse_float(self.entry_thickness.get(), "Sac Kalınlığı"),
                insulation_enabled=self.insulation_var.get(),
                insulation_thickness_mm=(
                    self._parse_float(self.entry_insulation.get(), "Yalıtım Kalınlığı")
                    if self.insulation_var.get() else None
                ),
            )
        elif product_type == ProductType.AHU_CABINET:
            return AHUSpec(
                width_mm=self._parse_float(self.ahu_entry_width.get(), "Genişlik"),
                height_mm=self._parse_float(self.ahu_entry_height.get(), "Yükseklik"),
                length_mm=self._parse_float(self.ahu_entry_length.get(), "Uzunluk"),
                panel_thickness_mm=self._parse_float(self.ahu_entry_panel_thickness.get(), "Panel Kalınlığı"),
                has_profile_framework=self.ahu_profile_var.get(),
            )
        elif product_type == ProductType.FITTING_DUCT:
            shape_label = self.fitting_shape_var.get()
            shape_value = _FITTING_LABEL_TO_VALUE.get(shape_label, shape_label)
            return FittingSpec(
                fitting_shape=shape_value,
                main_dimension_mm=self._parse_float(self.fitting_entry_main_dim.get(), "Ana Ölçü"),
                thickness_mm=self._parse_float(self.fitting_entry_thickness.get(), "Sac Kalınlığı"),
                angle_degrees=self._parse_optional_float(self.fitting_entry_angle.get()),
            )
        else:
            raise ValueError(f"Bilinmeyen ürün tipi: {product_type}")

    def _save_product(self):
        """Formdaki verileri doğrulayıp veritabanına kaydeder."""
        name = self.entry_name.get().strip()
        if not name:
            messagebox.showwarning("Uyarı", "Ürün adı zorunludur.")
            return

        selected_label = self.product_type_var.get()
        product_type = _LABEL_TO_ENUM.get(selected_label)
        if not product_type:
            messagebox.showwarning("Uyarı", "Geçerli bir ürün tipi seçiniz.")
            return

        try:
            spec = self._build_spec(product_type)
        except (ValueError, Exception) as e:
            messagebox.showwarning("Ebat Hatası", str(e))
            return

        # BOM satırlarını topla
        bom_items = []
        for _, e_name, e_unit, e_qty, e_cost in self.bom_rows:
            bom_name = e_name.get().strip()
            if not bom_name:
                continue
            try:
                bom_items.append(BOMItemCreate(
                    name=bom_name,
                    unit=e_unit.get().strip() or None,
                    quantity_per_unit=float(e_qty.get() or 1),
                    cost_per_unit=float(e_cost.get() or 0) if e_cost.get().strip() else None,
                ))
            except (ValueError, Exception):
                messagebox.showwarning("BOM Hatası", f"'{bom_name}' malzemesinde geçersiz değer var.")
                return

        product_in = ProductCreate(
            name=name,
            description=self.entry_desc.get().strip() or None,
            product_type=product_type,
            spec=spec,
            bom_items=bom_items,
        )

        try:
            with get_db_session() as db:
                product_service.create_product(db, product_in)
            self._clear_form()
            self._refresh_product_list()
            messagebox.showinfo("Başarılı", f"'{name}' ürünü kaydedildi.")
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def _delete_product(self, product_id: int, product_name: str):
        """Ürünü veritabanından siler."""
        confirm = messagebox.askyesno("Silme Onayı", f"'{product_name}' ürününü silmek istediğinize emin misiniz?")
        if not confirm:
            return
        try:
            with get_db_session() as db:
                product_service.delete_product(db, product_id)
            self._refresh_product_list()
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def _refresh_product_list(self):
        """Ürün listesini veritabanından yeniden yükler."""
        # Mevcut kartları temizle
        for widget in self.product_list.winfo_children():
            widget.destroy()

        try:
            with get_db_session() as db:
                products = product_service.list_products(db)
        except Exception as e:
            ctk.CTkLabel(
                self.product_list, text=f"Hata: {e}",
                text_color=CLR_DANGER, font=ctk.CTkFont(size=12),
            ).pack(pady=20)
            return

        if not products:
            ctk.CTkLabel(
                self.product_list, text="Henüz ürün eklenmemiş.",
                text_color=CLR_SUBTEXT, font=ctk.CTkFont(size=13),
            ).pack(pady=40)
            return

        for product in products:
            self._create_product_card(product)

    def _create_product_card(self, product: dict):
        """Bir ürün için kart widget'ı oluşturur."""
        card = ctk.CTkFrame(self.product_list, fg_color=CLR_CARD, corner_radius=10)
        card.pack(fill="x", pady=4)
        card.grid_columnconfigure(0, weight=1)

        # Üst satır: ad + tip rozeti + sil butonu
        top_row = ctk.CTkFrame(card, fg_color="transparent")
        top_row.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 2))
        top_row.grid_columnconfigure(0, weight=1)

        # Ürün tipi rozeti
        raw_type = product.get("product_type", "")
        try:
            product_type_enum = ProductType(raw_type)
            type_label = _ENUM_TO_LABEL.get(product_type_enum, raw_type)
        except ValueError:
            type_label = raw_type

        name_label = ctk.CTkLabel(
            top_row, text=product["name"],
            font=ctk.CTkFont(size=14, weight="bold"), text_color=CLR_TEXT, anchor="w",
        )
        name_label.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            top_row, text=type_label,
            font=ctk.CTkFont(size=10), text_color=CLR_ACCENT,
            fg_color=CLR_INPUT, corner_radius=4,
        ).grid(row=0, column=1, sticky="e", padx=(8, 4))

        ctk.CTkButton(
            top_row, text="Sil", width=50, height=26,
            font=ctk.CTkFont(size=11), fg_color=CLR_DANGER,
            hover_color="#EBA0AC", text_color="#1E1E2E", corner_radius=6,
            command=lambda pid=product["id"], pname=product["name"]: self._delete_product(pid, pname),
        ).grid(row=0, column=2, sticky="e")

        # Açıklama
        if product.get("description"):
            ctk.CTkLabel(
                card, text=product["description"],
                font=ctk.CTkFont(size=11), text_color=CLR_SUBTEXT, anchor="w",
            ).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 2))

        # Ebat / özellik bilgisi — ürün tipine göre
        spec = product.get("spec", {})
        dims = self._format_spec_summary(raw_type, spec)
        ctk.CTkLabel(
            card, text=dims,
            font=ctk.CTkFont(size=11), text_color=CLR_SUBTEXT, anchor="w",
        ).grid(row=2, column=0, sticky="w", padx=12, pady=(0, 2))

        # BOM özeti
        bom_count = len(product.get("bom_items", []))
        if bom_count > 0:
            bom_names = ", ".join(b["name"] for b in product["bom_items"][:3])
            suffix = f" +{bom_count - 3}" if bom_count > 3 else ""
            ctk.CTkLabel(
                card, text=f"📎 BOM ({bom_count}): {bom_names}{suffix}",
                font=ctk.CTkFont(size=10), text_color="#89B4FA", anchor="w",
            ).grid(row=3, column=0, sticky="w", padx=12, pady=(0, 10))
        else:
            # Alt boşluk
            ctk.CTkFrame(card, height=6, fg_color="transparent").grid(row=3, column=0)

    @staticmethod
    def _format_spec_summary(product_type: str, spec: dict) -> str:
        """Ürün tipine göre spec özetini biçimlendirir."""
        if product_type == ProductType.RECTANGULAR_DUCT.value:
            dims = (
                f"{spec.get('width_mm', '?')} × {spec.get('height_mm', '?')} "
                f"× {spec.get('length_mm', '?')} mm  •  Sac: {spec.get('thickness_mm', '?')} mm"
            )
            if spec.get("insulation_enabled"):
                dims += f"  •  Yalıtım: {spec.get('insulation_thickness_mm', '?')} mm"
            return dims

        elif product_type == ProductType.AHU_CABINET.value:
            profile = "Evet" if spec.get("has_profile_framework") else "Hayır"
            return (
                f"{spec.get('width_mm', '?')} × {spec.get('height_mm', '?')} "
                f"× {spec.get('length_mm', '?')} mm  •  Panel: {spec.get('panel_thickness_mm', '?')} mm  "
                f"•  Profil Çerçeve: {profile}"
            )

        elif product_type == ProductType.FITTING_DUCT.value:
            shape_raw = spec.get("fitting_shape", "?")
            shape_label = _FITTING_VALUE_TO_LABEL.get(shape_raw, shape_raw)
            dims = f"Şekil: {shape_label}  •  Ölçü: {spec.get('main_dimension_mm', '?')} mm  •  Sac: {spec.get('thickness_mm', '?')} mm"
            if spec.get("angle_degrees") is not None:
                dims += f"  •  Açı: {spec['angle_degrees']}°"
            return dims

        return str(spec)
