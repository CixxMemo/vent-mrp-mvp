import customtkinter as ctk
from core.database import init_db
from ui.frames.work_orders_frame import WorkOrderFrame
from ui.frames.products_frame import ProductsFrame
from ui.frames.mrp_frame import MRPFrame


# ── Renk Paleti (Catppuccin Mocha) ──
COLOR_BG = "#11111B"            # En koyu arkaplan
COLOR_SIDEBAR = "#181825"       # Sidebar arkaplan
COLOR_SURFACE = "#1E1E2E"       # Kart / panel yüzeyleri
COLOR_OVERLAY = "#313244"       # Hover, aktif buton
COLOR_TEXT = "#CDD6F4"          # Ana metin
COLOR_SUBTEXT = "#6C7086"       # İkincil metin
COLOR_ACCENT = "#89B4FA"        # Mavi vurgu
COLOR_DIVIDER = "#313244"       # Ayırıcı


class FactoryCutApp(ctk.CTk):
    """FactoryCut Planner - Ana Masaüstü Uygulaması"""

    def __init__(self):
        super().__init__()

        # Veritabanını başlat
        init_db()

        # ── Pencere ayarları ──
        self.title("FactoryCut Planner")
        self.geometry("1200x800")
        self.minsize(900, 600)
        self.configure(fg_color=COLOR_BG)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Ana grid: sidebar (col 0) + ayırıcı (col 1) + içerik (col 2)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Sol Sidebar ──
        self._build_sidebar()

        # ── Dikey ayırıcı ──
        divider = ctk.CTkFrame(self, width=1, fg_color=COLOR_DIVIDER, corner_radius=0)
        divider.grid(row=0, column=1, sticky="ns")

        # ── Sağ İçerik Alanı ──
        self.content_area = ctk.CTkFrame(self, fg_color=COLOR_BG, corner_radius=0)
        self.content_area.grid(row=0, column=2, sticky="nsew", padx=16, pady=16)
        self.content_area.grid_columnconfigure(0, weight=1)
        self.content_area.grid_rowconfigure(0, weight=1)

        # Sayfa frame'lerini oluştur
        self.frames = {
            "work_orders": WorkOrderFrame(self.content_area),
            "products": ProductsFrame(self.content_area),
            "mrp": MRPFrame(self.content_area),
        }

        # Tüm frame'leri aynı grid hücresine yerleştir (üst üste)
        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

        # İlk sayfayı göster
        self.current_page = None
        self.select_page("work_orders")

    def _build_sidebar(self):
        """Sol navigasyon panelini oluşturur."""
        sidebar = ctk.CTkFrame(self, width=220, fg_color=COLOR_SIDEBAR, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        # ── Logo alanı ──
        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=20, pady=(28, 4))

        ctk.CTkLabel(
            logo_frame,
            text="⚙️  FactoryCut",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLOR_TEXT,
            anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            logo_frame,
            text="Üretim Planlama Sistemi",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_SUBTEXT,
            anchor="w",
        ).pack(fill="x", pady=(2, 0))

        # Ayırıcı
        ctk.CTkFrame(sidebar, height=1, fg_color=COLOR_DIVIDER).pack(
            fill="x", padx=20, pady=(20, 16)
        )

        # ── Menü etiketi ──
        ctk.CTkLabel(
            sidebar,
            text="MENÜ",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COLOR_SUBTEXT,
            anchor="w",
        ).pack(fill="x", padx=24, pady=(0, 8))

        # ── Navigasyon butonları ──
        self.nav_buttons = {}
        nav_items = [
            ("work_orders", "📋  İş Emirleri"),
            ("products",    "📦  Ürünler"),
            ("mrp",         "📊  MRP & Rapor"),
        ]

        for page_key, label in nav_items:
            btn = ctk.CTkButton(
                sidebar,
                text=label,
                font=ctk.CTkFont(size=14),
                fg_color="transparent",
                text_color=COLOR_TEXT,
                hover_color=COLOR_OVERLAY,
                anchor="w",
                height=44,
                corner_radius=10,
                command=lambda key=page_key: self.select_page(key),
            )
            btn.pack(fill="x", padx=14, pady=2)
            self.nav_buttons[page_key] = btn

        # ── Alt bilgi (footer) ──
        footer = ctk.CTkFrame(sidebar, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=20, pady=20)

        ctk.CTkFrame(footer, height=1, fg_color=COLOR_DIVIDER).pack(
            fill="x", pady=(0, 12)
        )
        ctk.CTkLabel(
            footer,
            text="v1.0.0  •  SQLite",
            font=ctk.CTkFont(size=10),
            text_color=COLOR_SUBTEXT,
            anchor="w",
        ).pack(fill="x")

    def select_page(self, page_key: str):
        """Seçilen sayfayı öne getirir ve buton stillerini günceller."""
        if page_key == self.current_page:
            return

        # Seçili frame'i öne getir
        self.frames[page_key].tkraise()
        self.current_page = page_key

        # Buton stillerini güncelle
        for key, btn in self.nav_buttons.items():
            if key == page_key:
                btn.configure(fg_color=COLOR_OVERLAY, text_color=COLOR_ACCENT)
            else:
                btn.configure(fg_color="transparent", text_color=COLOR_TEXT)


if __name__ == "__main__":
    app = FactoryCutApp()
    app.mainloop()
