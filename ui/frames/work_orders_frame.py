"""İş Emri Yönetimi sayfası — Form + Liste."""

import customtkinter as ctk
from tkinter import messagebox

from core.db_helper import get_db_session
from modules.products import service as product_service
from modules.work_orders import service as wo_service
from modules.work_orders.schemas import WorkOrderCreate, WorkOrderLineCreate

# ── Renkler ──
CLR_SURFACE = "#1E1E2E"
CLR_CARD = "#252536"
CLR_INPUT = "#313244"
CLR_TEXT = "#CDD6F4"
CLR_SUBTEXT = "#6C7086"
CLR_ACCENT = "#89B4FA"
CLR_DANGER = "#F38BA8"
CLR_BORDER = "#45475A"
CLR_SUCCESS = "#A6E3A1"


class WorkOrderFrame(ctk.CTkFrame):
    """İş Emri Yönetimi modülünün ana frame'i."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=2)   # Sol: form
        self.grid_columnconfigure(1, weight=3)   # Sağ: liste
        self.grid_rowconfigure(1, weight=1)

        # Ürün verisi (dropdown için)
        self._products_cache = []

        # ── Üst başlık ──
        header = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=12, height=60)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text="📋  İş Emri Yönetimi",
            font=ctk.CTkFont(size=20, weight="bold"), text_color=CLR_TEXT,
        ).grid(row=0, column=0, padx=20, pady=14, sticky="w")

        # ── Sol panel: Form ──
        self.form_panel = self._build_form_panel()
        self.form_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 6))

        # ── Sağ panel: İş Emri Listesi ──
        self.list_panel = self._build_list_panel()
        self.list_panel.grid(row=1, column=1, sticky="nsew", padx=(6, 0))

        # İlk yükleme
        self._load_products()
        self._refresh_wo_list()

    # ================================================================
    #  SOL PANEL — İŞ EMRİ FORMU
    # ================================================================
    def _build_form_panel(self) -> ctk.CTkFrame:
        panel = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=12)

        # Başlık
        ctk.CTkLabel(
            panel, text="Yeni İş Emri Oluştur",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=CLR_TEXT,
        ).pack(anchor="w", padx=16, pady=(16, 12))

        # Kaydırılabilir form alanı
        form_scroll = ctk.CTkScrollableFrame(panel, fg_color="transparent", corner_radius=0)
        form_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        form_scroll.grid_columnconfigure(1, weight=1)

        row = 0

        # — Proje Adı —
        ctk.CTkLabel(
            form_scroll, text="Proje Adı *",
            font=ctk.CTkFont(size=12), text_color=CLR_SUBTEXT,
        ).grid(row=row, column=0, columnspan=2, sticky="w", padx=4, pady=(4, 2))
        row += 1

        self.entry_project = ctk.CTkEntry(
            form_scroll, fg_color=CLR_INPUT, border_color=CLR_BORDER,
            text_color=CLR_TEXT, placeholder_text="Örn: AVM Havalandırma Projesi",
        )
        self.entry_project.grid(row=row, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 8))
        row += 1

        # — Fire Oranı —
        fire_frame = ctk.CTkFrame(form_scroll, fg_color="transparent")
        fire_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 12))
        fire_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            fire_frame, text="Fire Oranı (%)",
            font=ctk.CTkFont(size=12), text_color=CLR_SUBTEXT,
        ).grid(row=0, column=0, sticky="w")

        self.slider_waste = ctk.CTkSlider(
            fire_frame, from_=0, to=30, number_of_steps=30,
            fg_color=CLR_INPUT, progress_color=CLR_ACCENT, button_color=CLR_ACCENT,
            button_hover_color="#74C7EC",
            command=self._on_waste_slider_change,
        )
        self.slider_waste.set(0)
        self.slider_waste.grid(row=0, column=1, sticky="ew", padx=(12, 8))

        self.lbl_waste_val = ctk.CTkLabel(
            fire_frame, text="% 0", width=50,
            font=ctk.CTkFont(size=13, weight="bold"), text_color=CLR_ACCENT,
        )
        self.lbl_waste_val.grid(row=0, column=2, sticky="e")
        row += 1

        # — Kalemler başlığı —
        ctk.CTkFrame(form_scroll, height=1, fg_color=CLR_BORDER).grid(
            row=row, column=0, columnspan=2, sticky="ew", padx=4, pady=(4, 8)
        )
        row += 1

        lines_header = ctk.CTkFrame(form_scroll, fg_color="transparent")
        lines_header.grid(row=row, column=0, columnspan=2, sticky="ew", padx=4)
        lines_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            lines_header, text="İş Emri Kalemleri",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=CLR_TEXT,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            lines_header, text="＋ Kalem Ekle", width=100, height=28,
            font=ctk.CTkFont(size=11), fg_color=CLR_INPUT,
            hover_color=CLR_BORDER, text_color=CLR_TEXT, corner_radius=6,
            command=self._add_line_row,
        ).grid(row=0, column=1, sticky="e")
        row += 1

        # Kalem satırları konteyneri
        self.lines_container = ctk.CTkFrame(form_scroll, fg_color="transparent")
        self.lines_container.grid(row=row, column=0, columnspan=2, sticky="ew", padx=4, pady=(4, 8))
        self.line_rows = []  # [(frame, product_combo, qty_entry)]

        # ── İlk satırı otomatik ekle ──
        self._add_line_row()

        # — Kaydet butonu —
        ctk.CTkButton(
            panel, text="💾  İş Emrini Kaydet", height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=CLR_ACCENT, hover_color="#74C7EC",
            text_color="#1E1E2E", corner_radius=10,
            command=self._save_work_order,
        ).pack(fill="x", padx=16, pady=(4, 16))

        return panel

    # ================================================================
    #  SAĞ PANEL — İŞ EMRİ LİSTESİ
    # ================================================================
    def _build_list_panel(self) -> ctk.CTkFrame:
        panel = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=12)

        # Başlık satırı
        list_header = ctk.CTkFrame(panel, fg_color="transparent")
        list_header.pack(fill="x", padx=16, pady=(16, 8))
        list_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            list_header, text="Kayıtlı İş Emirleri",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=CLR_TEXT,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            list_header, text="🔄", width=32, height=32,
            font=ctk.CTkFont(size=14), fg_color=CLR_INPUT,
            hover_color=CLR_BORDER, text_color=CLR_TEXT, corner_radius=8,
            command=self._refresh_wo_list,
        ).grid(row=0, column=1, sticky="e")

        # Kaydırılabilir liste
        self.wo_list = ctk.CTkScrollableFrame(panel, fg_color="transparent", corner_radius=0)
        self.wo_list.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.wo_list.grid_columnconfigure(0, weight=1)

        return panel

    # ================================================================
    #  DİNAMİK SATIR YÖNETİMİ
    # ================================================================
    def _add_line_row(self):
        """Yeni bir ürün-miktar satırı ekler."""
        row_frame = ctk.CTkFrame(self.lines_container, fg_color=CLR_CARD, corner_radius=8)
        row_frame.pack(fill="x", pady=3)
        row_frame.grid_columnconfigure(0, weight=1)

        # Ürün açılır listesi
        product_names = [p["display"] for p in self._products_cache]
        combo = ctk.CTkComboBox(
            row_frame, values=product_names if product_names else ["— Ürün yok —"],
            fg_color=CLR_INPUT, border_color=CLR_BORDER, text_color=CLR_TEXT,
            button_color=CLR_BORDER, button_hover_color=CLR_ACCENT,
            dropdown_fg_color=CLR_CARD, dropdown_hover_color=CLR_BORDER,
            dropdown_text_color=CLR_TEXT,
            font=ctk.CTkFont(size=12),
            state="readonly" if not product_names else "normal",
        )
        combo.grid(row=0, column=0, padx=(8, 4), pady=8, sticky="ew")
        if product_names:
            combo.set(product_names[0])

        # Miktar
        qty_entry = ctk.CTkEntry(
            row_frame, fg_color=CLR_INPUT, border_color=CLR_BORDER,
            text_color=CLR_TEXT, width=70, placeholder_text="Adet",
            font=ctk.CTkFont(size=12),
        )
        qty_entry.grid(row=0, column=1, padx=4, pady=8)

        # Sil butonu
        btn_del = ctk.CTkButton(
            row_frame, text="✕", width=30, height=30,
            fg_color=CLR_DANGER, hover_color="#EBA0AC",
            text_color="#1E1E2E", corner_radius=6,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self._remove_line_row(row_frame),
        )
        btn_del.grid(row=0, column=2, padx=(4, 8), pady=8)

        self.line_rows.append((row_frame, combo, qty_entry))

    def _remove_line_row(self, row_frame):
        """Satırı kaldırır."""
        self.line_rows = [r for r in self.line_rows if r[0] != row_frame]
        row_frame.destroy()

    # ================================================================
    #  VERİ YÜKLEME
    # ================================================================
    def _load_products(self):
        """Veritabanından ürünleri yükleyip dropdown cache'ini günceller."""
        try:
            with get_db_session() as db:
                products = product_service.list_products(db)
            self._products_cache = [
                {"id": p["id"], "name": p["name"], "display": f'{p["name"]} (ID:{p["id"]})'}
                for p in products
            ]
        except Exception:
            self._products_cache = []

    def _get_product_id_from_display(self, display_text: str) -> int | None:
        """Dropdown metninden ürün ID'sini çıkarır."""
        for p in self._products_cache:
            if p["display"] == display_text:
                return p["id"]
        return None

    def _on_waste_slider_change(self, value):
        self.lbl_waste_val.configure(text=f"% {int(value)}")

    # ================================================================
    #  FORM SIFIRLAMA
    # ================================================================
    def _clear_form(self):
        self.entry_project.delete(0, "end")
        self.slider_waste.set(0)
        self.lbl_waste_val.configure(text="% 0")
        for row_frame, *_ in self.line_rows:
            row_frame.destroy()
        self.line_rows.clear()
        self._add_line_row()

    # ================================================================
    #  VERİTABANI İŞLEMLERİ
    # ================================================================
    def _save_work_order(self):
        """Formu doğrulayıp veritabanına kaydeder."""
        project_name = self.entry_project.get().strip()
        if not project_name:
            messagebox.showwarning("Uyarı", "Proje adı zorunludur.")
            return

        if not self.line_rows:
            messagebox.showwarning("Uyarı", "En az bir kalem eklemelisiniz.")
            return

        # Kalemleri oku
        lines = []
        for _, combo, qty_entry in self.line_rows:
            product_display = combo.get()
            product_id = self._get_product_id_from_display(product_display)
            if product_id is None:
                messagebox.showwarning("Uyarı", f"Geçersiz ürün seçimi: '{product_display}'")
                return

            qty_text = qty_entry.get().strip()
            if not qty_text:
                messagebox.showwarning("Uyarı", "Miktar boş bırakılamaz.")
                return
            try:
                qty = int(qty_text)
                if qty <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Uyarı", f"Miktar pozitif bir tam sayı olmalıdır: '{qty_text}'")
                return

            lines.append(WorkOrderLineCreate(product_id=product_id, quantity=qty))

        waste_factor = round(self.slider_waste.get() / 100, 2)

        wo_in = WorkOrderCreate(
            project_name=project_name,
            lines=lines,
            waste_factor=waste_factor,
        )

        try:
            with get_db_session() as db:
                wo_service.create_work_order(db, wo_in)
            self._clear_form()
            self._refresh_wo_list()
            messagebox.showinfo("Başarılı", f"'{project_name}' iş emri kaydedildi.")
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def _delete_work_order(self, wo_id: int, wo_name: str):
        """İş emrini siler."""
        confirm = messagebox.askyesno("Silme Onayı", f"'{wo_name}' iş emrini silmek istediğinize emin misiniz?")
        if not confirm:
            return
        try:
            with get_db_session() as db:
                wo_service.delete_work_order(db, wo_id)
            self._refresh_wo_list()
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def _refresh_wo_list(self):
        """İş emri listesini yeniden yükler."""
        # Ürün cache'ini de tazele (yeni ürün eklenmiş olabilir)
        self._load_products()

        for widget in self.wo_list.winfo_children():
            widget.destroy()

        try:
            with get_db_session() as db:
                work_orders = wo_service.list_work_orders(db)
        except Exception as e:
            ctk.CTkLabel(
                self.wo_list, text=f"Hata: {e}",
                text_color=CLR_DANGER, font=ctk.CTkFont(size=12),
            ).pack(pady=20)
            return

        if not work_orders:
            ctk.CTkLabel(
                self.wo_list, text="Henüz iş emri oluşturulmamış.",
                text_color=CLR_SUBTEXT, font=ctk.CTkFont(size=13),
            ).pack(pady=40)
            return

        for wo in work_orders:
            self._create_wo_card(wo)

    def _create_wo_card(self, wo: dict):
        """Bir iş emri için kart widget'ı oluşturur."""
        card = ctk.CTkFrame(self.wo_list, fg_color=CLR_CARD, corner_radius=10)
        card.pack(fill="x", pady=4)
        card.grid_columnconfigure(0, weight=1)

        # Üst satır: proje adı + fire + sil
        top_row = ctk.CTkFrame(card, fg_color="transparent")
        top_row.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
        top_row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top_row, text=wo["project_name"],
            font=ctk.CTkFont(size=14, weight="bold"), text_color=CLR_TEXT, anchor="w",
        ).grid(row=0, column=0, sticky="w")

        waste_pct = int(wo.get("waste_factor", 0) * 100)
        if waste_pct > 0:
            ctk.CTkLabel(
                top_row, text=f"🔥 %{waste_pct}",
                font=ctk.CTkFont(size=11), text_color="#FAB387",
            ).grid(row=0, column=1, padx=(0, 8))

        ctk.CTkButton(
            top_row, text="Sil", width=50, height=26,
            font=ctk.CTkFont(size=11), fg_color=CLR_DANGER,
            hover_color="#EBA0AC", text_color="#1E1E2E", corner_radius=6,
            command=lambda: self._delete_work_order(wo["id"], wo["project_name"]),
        ).grid(row=0, column=2, sticky="e")

        # Kalem listesi
        lines = wo.get("lines", [])
        if lines:
            for i, line in enumerate(lines):
                product_name = line.get("product", {}).get("name", "?")
                qty = line.get("quantity", 0)
                line_text = f"  {i + 1}. {product_name}  ×  {qty} adet"
                ctk.CTkLabel(
                    card, text=line_text,
                    font=ctk.CTkFont(size=11), text_color=CLR_SUBTEXT, anchor="w",
                ).grid(row=1 + i, column=0, sticky="w", padx=12, pady=(0, 1))

            # Alt boşluk
            ctk.CTkFrame(card, height=8, fg_color="transparent").grid(
                row=1 + len(lines), column=0
            )
        else:
            ctk.CTkLabel(
                card, text="  Kalem yok",
                font=ctk.CTkFont(size=11), text_color=CLR_SUBTEXT, anchor="w",
            ).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 8))

    # ================================================================
    #  SAYFA AKTİF OLDUĞUNDA VERİLERİ TAZELE
    # ================================================================
    def tkraise(self, *args, **kwargs):
        """Sayfa öne geldiğinde ürün listesini ve iş emirlerini tazeler."""
        self._load_products()
        self._refresh_wo_list()
        # Mevcut dropdown'ları güncelle
        product_names = [p["display"] for p in self._products_cache]
        for _, combo, _ in self.line_rows:
            combo.configure(values=product_names if product_names else ["— Ürün yok —"])
        super().tkraise(*args, **kwargs)
