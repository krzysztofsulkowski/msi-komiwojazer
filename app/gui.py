import tkinter as tk
from tkinter import filedialog, ttk
import customtkinter as ctk
import tkintermapview
import random
import time
from datetime import datetime
from app.models import Point
from app.optimizer import genetic_algorithm_route, calculate_total_distance
from app.exporter import export_route_to_json, import_route_from_json
from app.geocoder import search_address
from app.route_service import get_road_route_between_points
from PIL import Image, ImageDraw, ImageFont, ImageTk

C = {
    "bg_app":       "#0f172a",   
    "bg_sidebar":   "#1e293b",   
    "bg_card":      "#263548",   
    "bg_input":     "#1a2d42",   
    "bg_map":       "#f1f5f9",   
    "accent":       "#38bdf8",   
    "accent_hover": "#0ea5e9",   
    "success":      "#4ade80",   
    "success_dk":   "#16a34a",   
    "warning":      "#fbbf24",   
    "danger":       "#f87171",   
    "danger_dk":    "#dc2626",   
    "purple":       "#a78bfa",   
    "purple_dk":    "#7c3aed",   
    "indigo":       "#818cf8",  
    "indigo_dk":    "#4f46e5",  
    "slate":        "#475569",   
    "slate_dk":     "#334155",   
    "text_h":       "#f1f5f9",   
    "text_b":       "#cbd5e1",   
    "text_muted":   "#64748b",   
    "border":       "#334155",   
    "map_bg":       "#ffffff",   
}

FONT_H1  = ("Segoe UI", 18, "bold")
FONT_H2  = ("Segoe UI", 12, "bold")
FONT_H3  = ("Segoe UI", 10, "bold")
FONT_B   = ("Segoe UI", 10)
FONT_SM  = ("Segoe UI", 9)
FONT_BTN = ("Segoe UI", 10, "bold")

def add_hover(widget, normal_bg, hover_bg):
    widget.bind("<Enter>", lambda e: widget.config(bg=hover_bg))
    widget.bind("<Leave>", lambda e: widget.config(bg=normal_bg))

def make_button(parent, text, command, bg, hover, fg="white",
                pady=9, font=FONT_BTN, padx=14,
                border_color=None):
    """Jeśli border_color podany – zwraca Frame-wrapper jako obramówka."""
    container = tk.Frame(parent, bg=border_color, padx=1, pady=1) \
        if border_color else parent

    btn = tk.Button(
        container,
        text=text,
        command=command,
        bg=bg,
        fg=fg,
        activebackground=hover,
        activeforeground=fg,
        font=font,
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=padx,
        pady=pady,
    )
    add_hover(btn, bg, hover)

    if border_color:
        btn.pack(fill="x")
        return container   
    else:
        return btn         

def make_section_label(parent, text):
    wrapper = tk.Frame(parent, bg=C["bg_sidebar"])
    wrapper.pack(fill="x", padx=16, pady=(18, 6))

    tk.Label(
        wrapper,
        text=text.upper(),
        bg=C["bg_sidebar"],
        fg=C["text_muted"],
        font=("Segoe UI", 8, "bold"),
        anchor="w",
    ).pack(side="left")

    tk.Frame(wrapper, bg=C["border"], height=1).pack(
        side="left", fill="x", expand=True, padx=(8, 0), pady=6
    )


class RouteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Komiwojażer — Optymalizacja Trasy")
        self.root.geometry("1340x760")
        self.root.configure(bg=C["bg_app"])
        self.root.minsize(1100, 640)

        self.points = []
        self.point_counter = 0

        self.canvas = None
        self.points_list = None
        self.distance_label = None
        self.improvement_label = None
        self.status_label = None
        self.details_label = None
        self.route_info_frame = None

        self.map_widget = None
        self.map_markers = []
        self.marker_icons = []
        self.map_path = None
        self.map_paths = []
        self.route_optimized = False
        self.performance_mode = False

        self.address_results_list = None
        self.address_search_results = []

        self.latitude_entry = None
        self.longitude_entry = None
        self.address_entry = None
        self.comment_entry = None

        self.build_layout()


    def build_layout(self):
        header = tk.Frame(self.root, bg=C["bg_app"], height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        inner_h = tk.Frame(header, bg=C["bg_app"])
        inner_h.pack(fill="both", expand=True, padx=28)

        dot = tk.Label(inner_h, text="⬡", bg=C["bg_app"], fg=C["accent"],
                       font=("Segoe UI", 24))
        dot.pack(side="left", pady=14)

        tk.Label(
            inner_h,
            text="  Komiwojażer",
            bg=C["bg_app"],
            fg=C["text_h"],
            font=("Segoe UI", 17, "bold"),
        ).pack(side="left", pady=14)

        tk.Label(
            inner_h,
            text="Optymalizacja trasy kuriera",
            bg=C["bg_app"],
            fg=C["text_muted"],
            font=("Segoe UI", 10),
        ).pack(side="left", padx=(10, 0), pady=17)

        tk.Frame(self.root, bg=C["border"], height=1).pack(fill="x")

        content = tk.Frame(self.root, bg=C["bg_app"])
        content.pack(fill="both", expand=True, padx=16, pady=14)

        map_outer = tk.Frame(
            content, bg=C["map_bg"], bd=0,
            highlightthickness=1, highlightbackground=C["border"]
        )
        map_outer.pack(side="left", fill="both", expand=True)

        self.map_widget = tkintermapview.TkinterMapView(
            map_outer, corner_radius=0
        )
        self.map_widget.pack(fill="both", expand=True, padx=0, pady=0)
        self.map_widget.set_position(51.2070, 16.1553)
        self.map_widget.set_zoom(13)

        self.create_map_legend(map_outer)
        self.create_route_info_panel(map_outer)

        tk.Frame(content, bg=C["border"], width=1).pack(
            side="left", fill="y", padx=(10, 0)
        )

        sidebar_outer = tk.Frame(
            content, bg=C["bg_sidebar"], width=358
        )
        sidebar_outer.pack(side="right", fill="y", padx=(8, 0))
        sidebar_outer.pack_propagate(False)

        sb_style = ttk.Style()
        sb_style.theme_use("clam")
        sb_style.configure(
            "Sidebar.Vertical.TScrollbar",
            gripcount=0,
            background="#475569",
            darkcolor="#334155",
            lightcolor="#475569",
            troughcolor="#131f2e",
            bordercolor="#1e293b",
            arrowcolor="#94a3b8",
            arrowsize=14,
        )
        sb_style.map(
            "Sidebar.Vertical.TScrollbar",
            background=[("active", "#64748b"), ("pressed", "#94a3b8")],
        )

        right_canvas = tk.Canvas(
            sidebar_outer, bg=C["bg_sidebar"],
            highlightthickness=0, width=340
        )
        right_canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            sidebar_outer, orient="vertical",
            command=right_canvas.yview,
            style="Sidebar.Vertical.TScrollbar",
        )
        scrollbar.pack(side="right", fill="y")

        right_panel = tk.Frame(right_canvas, bg=C["bg_sidebar"])
        win_id = right_canvas.create_window(
            (0, 0), window=right_panel, anchor="nw", width=340
        )
        right_canvas.configure(yscrollcommand=scrollbar.set)

        def update_scroll_region(e=None):
            right_canvas.configure(scrollregion=right_canvas.bbox("all"))

        def resize_right_panel(e):
            right_canvas.itemconfig(win_id, width=e.width)

        def on_mousewheel(e):
            right_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        def bind_mw(e):   right_canvas.bind_all("<MouseWheel>", on_mousewheel)
        def unbind_mw(e): right_canvas.unbind_all("<MouseWheel>")

        right_panel.bind("<Configure>", update_scroll_region)
        right_canvas.bind("<Configure>", resize_right_panel)
        right_canvas.bind("<Enter>", bind_mw)
        right_canvas.bind("<Leave>", unbind_mw)
        right_panel.bind("<Enter>", bind_mw)
        right_panel.bind("<Leave>", unbind_mw)

        self._build_sidebar(right_panel)

    def _build_sidebar(self, panel):
        tk.Label(
            panel, text="Punkty trasy",
            bg=C["bg_sidebar"], fg=C["text_h"],
            font=("Segoe UI", 14, "bold")
        ).pack(anchor="w", padx=18, pady=(18, 0))

        tk.Label(
            panel, text="Zarządzaj trasą i punktami dostawy",
            bg=C["bg_sidebar"], fg=C["text_muted"],
            font=FONT_SM
        ).pack(anchor="w", padx=18, pady=(2, 0))

        make_section_label(panel, "Dane testowe")

        make_button(panel, "⟳  Wczytaj przykładowe punkty",
                    self.load_sample_points,
                    "#1e293b", "#334155",
                    border_color="#94a3b8"
                    ).pack(fill="x", padx=16, pady=(0, 6))

        make_button(panel, "✕  Wyczyść trasę",
                    self.clear_route,
                    "#7f1d1d", "#991b1b"
                    ).pack(fill="x", padx=16, pady=(0, 4))

        make_section_label(panel, "Dodaj punkt")

        card = tk.Frame(panel, bg=C["bg_card"],
                        highlightthickness=1,
                        highlightbackground=C["border"])
        card.pack(fill="x", padx=16, pady=(0, 6))

        fields = [
            ("Adres", "address_entry"),
            ("Komentarz", "comment_entry"),
            ("Szerokość geogr.", "latitude_entry"),
            ("Długość geogr.", "longitude_entry"),
        ]

        for label_text, attr in fields:
            row = tk.Frame(card, bg=C["bg_card"])
            row.pack(fill="x", padx=12, pady=4)

            tk.Label(row, text=label_text,
                     bg=C["bg_card"], fg=C["text_muted"],
                     font=("Segoe UI", 8, "bold"), anchor="w",
                     width=16
                     ).pack(side="left")

            entry = tk.Entry(
                row,
                font=FONT_B,
                bg=C["bg_input"],
                fg=C["text_b"],
                insertbackground=C["accent"],
                relief="flat",
                bd=0,
                highlightthickness=1,
                highlightbackground=C["border"],
                highlightcolor=C["accent"],
            )
            entry.pack(side="left", fill="x", expand=True)
            setattr(self, attr, entry)

        tk.Frame(card, bg=C["bg_card"], height=6).pack()

        make_button(panel, "🔍  Szukaj adresu",
                    self.search_address_from_form,
                    "#172554", "#1e3a8a",
                    border_color="#94a3b8"
                    ).pack(fill="x", padx=16, pady=(0, 4))

        addr_frame = tk.Frame(panel, bg=C["bg_sidebar"])
        addr_frame.pack(fill="x", padx=16, pady=(0, 6))

        tk.Label(
            addr_frame,
            text="Wyniki wyszukiwania adresu",
            bg=C["bg_sidebar"],
            fg=C["text_muted"],
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(0, 3))

        self.address_results_list = tk.Listbox(
            addr_frame,
            font=FONT_SM,
            bg=C["bg_card"],
            fg=C["text_b"],
            selectbackground=C["accent_hover"],
            selectforeground="#0f172a",
            bd=0,
            highlightthickness=1,
            highlightbackground=C["border"],
            highlightcolor=C["accent"],
            height=4,
            activestyle="none",
        )
        self.address_results_list.pack(fill="x")
        self.address_results_list.bind("<<ListboxSelect>>",
                                       self.select_address_result)

        make_button(panel, "🏠  Ustaw magazyn",
                    self.set_depot,
                    "#1e3a8a", "#2563eb"
                    ).pack(fill="x", padx=16, pady=(0, 4))

        make_button(panel, "+  Dodaj punkt",
                    self.add_point,
                    "#1e3a8a", "#2563eb"
                    ).pack(fill="x", padx=16, pady=(0, 4))

        make_button(panel, "−  Usuń punkt",
                    self.delete_selected_point,
                    "#7f1d1d", "#991b1b"
                    ).pack(fill="x", padx=16, pady=(0, 4))

        make_section_label(panel, "Zarządzanie punktem")

        make_button(panel, "💬  Zapisz komentarz do punktu",
                    self.save_comment_to_selected_point,
                    "#1e293b", "#334155",
                    border_color="#94a3b8"
                    ).pack(fill="x", padx=16, pady=(0, 4))

        make_section_label(panel, "Lista punktów")

        pts_frame = tk.Frame(panel, bg=C["bg_sidebar"])
        pts_frame.pack(fill="x", padx=16, pady=(0, 6))

        self.points_list = tk.Listbox(
            pts_frame,
            font=FONT_B,
            bg=C["bg_card"],
            fg=C["text_b"],
            selectbackground=C["accent_hover"],
            selectforeground="#0f172a",
            bd=0,
            highlightthickness=1,
            highlightbackground=C["border"],
            highlightcolor=C["accent"],
            height=7,
            activestyle="none",
        )
        self.points_list.pack(side="left", fill="both", expand=True)

        pts_scroll = tk.Scrollbar(pts_frame, orient="vertical",
                                  command=self.points_list.yview)
        pts_scroll.pack(side="right", fill="y")
        self.points_list.config(yscrollcommand=pts_scroll.set)
        self.points_list.bind("<<ListboxSelect>>",
                              self.show_selected_point_details)

        def _pts_wheel(e):
            self.points_list.yview_scroll(int(-1 * (e.delta / 120)), "units")
            return "break"
        self.points_list.bind("<MouseWheel>", _pts_wheel)

        self.details_label = tk.Label(
            panel,
            text="Szczegóły punktu: brak wybranego punktu",
            bg=C["bg_card"],
            fg=C["text_b"],
            font=FONT_SM,
            justify="left",
            anchor="w",
            wraplength=290,
            padx=12,
            pady=8,
        )
        self.details_label.pack(fill="x", padx=16, pady=(0, 6))

        make_button(panel, "✔  Oznacz jako dostarczone / niedostarczone",
                    self.mark_selected_as_delivered,
                    "#1e293b", "#334155", pady=8,
                    border_color="#94a3b8"
                    ).pack(fill="x", padx=16, pady=(0, 4))

        make_section_label(panel, "Operacje na trasie")

        ops = [
            ("⚡  Optymalizuj trasę",        self.optimize_route,
             "#172554", "#1e3a8a", "#94a3b8"),
            ("↑  Eksportuj trasę do JSON",    self.export_route,
             "#1e293b", "#334155", "#94a3b8"),
            ("↓  Importuj trasę z JSON",      self.import_route,
             "#1e293b", "#334155", "#94a3b8"),
            ("📊  Generuj raport wydajności", self.generate_performance_report,
             "#1e293b", "#334155", "#94a3b8"),
        ]

        for label, cmd, bg, hov, brd in ops:
            make_button(panel, label, cmd, bg, hov,
                        border_color=brd
                        ).pack(fill="x", padx=16, pady=(0, 4))

        tk.Frame(panel, bg=C["bg_sidebar"], height=20).pack()


    def create_section_title(self, parent, text):
        """Kompatybilność – nie używana bezpośrednio, ale zostawiona."""
        make_section_label(parent, text)

    def convert_gps_to_canvas_position(self, latitude, longitude):
        min_latitude = 51.18
        max_latitude = 51.23
        min_longitude = 16.11
        max_longitude = 16.21
        virtual_width = 1000
        virtual_height = 600
        x = ((longitude - min_longitude) / (max_longitude - min_longitude)) * virtual_width
        y = ((max_latitude - latitude) / (max_latitude - min_latitude)) * virtual_height
        return x, y

    def create_map_legend(self, parent):
        legend_frame = tk.Frame(
            parent,
            bg=C["bg_sidebar"],
            bd=0,
            highlightthickness=1,
            highlightbackground=C["border"],
        )
        legend_frame.place(x=16, rely=1.0, y=-16, anchor="sw")

        tk.Label(
            legend_frame,
            text="LEGENDA",
            bg=C["bg_sidebar"],
            fg=C["text_muted"],
            font=("Segoe UI", 7, "bold"),
            padx=10,
            pady=4,
        ).pack(anchor="w", pady=(6, 2), padx=10)

        items = [
            ("●", C["success"],  "magazyn / start"),
            ("●", C["warning"],  "punkt dostawy"),
            ("●", C["slate"],    "dostarczono"),
            ("—", "#2563eb",     "trasa przejazdu"),
        ]

        for sym, color, text in items:
            row = tk.Frame(legend_frame, bg=C["bg_sidebar"])
            row.pack(anchor="w", padx=10, pady=1)
            tk.Label(row, text=sym, bg=C["bg_sidebar"], fg=color,
                     font=("Segoe UI", 11, "bold"), width=2
                     ).pack(side="left")
            tk.Label(row, text=text, bg=C["bg_sidebar"], fg=C["text_b"],
                     font=FONT_SM).pack(side="left")

        tk.Frame(legend_frame, bg=C["bg_sidebar"], height=6).pack()

    def create_route_info_panel(self, parent):
        self.route_info_frame = tk.Frame(
            parent,
            bg=C["bg_sidebar"],
            bd=0,
            highlightthickness=1,
            highlightbackground=C["border"],
        )
        self.route_info_frame.place(relx=1.0, rely=1.0, x=-16, y=-16,
                                    anchor="se")

        tk.Label(
            self.route_info_frame,
            text="INFORMACJE O TRASIE",
            bg=C["bg_sidebar"],
            fg=C["text_muted"],
            font=("Segoe UI", 7, "bold"),
        ).pack(anchor="w", padx=12, pady=(8, 2))

        self.distance_label = tk.Label(
            self.route_info_frame,
            text="Dystans: 0.00 km",
            bg=C["bg_sidebar"],
            fg=C["accent"],
            font=("Segoe UI", 10, "bold"),
        )
        self.distance_label.pack(anchor="w", padx=12, pady=1)

        self.improvement_label = tk.Label(
            self.route_info_frame,
            text="Poprawa: —",
            bg=C["bg_sidebar"],
            fg=C["success"],
            font=FONT_SM,
        )
        self.improvement_label.pack(anchor="w", padx=12, pady=1)

        self.status_label = tk.Label(
            self.route_info_frame,
            text="Status: oczekiwanie",
            bg=C["bg_sidebar"],
            fg=C["text_b"],
            font=FONT_SM,
            wraplength=260,
            justify="left",
        )
        self.status_label.pack(anchor="w", padx=12, pady=(1, 10))


    def search_address_from_form(self):
        address = self.address_entry.get().strip()
        result = search_address(address)
        self.address_results_list.delete(0, tk.END)
        self.address_search_results = []
        if not result["success"]:
            self.status_label.config(text=f"Status: {result['message']}")
            return
        self.address_search_results = result["results"]
        for item in self.address_search_results:
            display_address = item["address"]
            if len(display_address) > 70:
                display_address = display_address[:67] + "..."
            self.address_results_list.insert(tk.END, display_address)
        self.status_label.config(text=f"Status: {result['message']}")

    def select_address_result(self, event=None):
        selected_index = self.address_results_list.curselection()
        if not selected_index:
            return
        index = selected_index[0]
        if index < 0 or index >= len(self.address_search_results):
            self.status_label.config(text="Status: nieprawidłowy wynik adresu")
            return
        selected_result = self.address_search_results[index]
        self.address_entry.delete(0, tk.END)
        self.address_entry.insert(0, selected_result["address"])
        self.latitude_entry.delete(0, tk.END)
        self.latitude_entry.insert(0, str(selected_result["latitude"]))
        self.longitude_entry.delete(0, tk.END)
        self.longitude_entry.insert(0, str(selected_result["longitude"]))
        self.status_label.config(
            text="Status: wybrano adres i uzupełniono współrzędne"
        )

    def get_point_data_from_form(self):
        try:
            latitude = float(self.latitude_entry.get())
            longitude = float(self.longitude_entry.get())
        except ValueError:
            self.status_label.config(text="Status: wpisz poprawne współrzędne")
            return None
        if latitude < 51.18 or latitude > 51.23 or longitude < 16.11 or longitude > 16.21:
            self.status_label.config(
                text="Status: wpisz współrzędne z obszaru Legnicy"
            )
            return None
        address = self.address_entry.get().strip()
        comment = self.comment_entry.get().strip()
        return address, comment, latitude, longitude

    def clear_point_form(self):
        self.address_entry.delete(0, tk.END)
        self.comment_entry.delete(0, tk.END)
        self.latitude_entry.delete(0, tk.END)
        self.longitude_entry.delete(0, tk.END)

    def set_depot(self):
        data = self.get_point_data_from_form()
        if data is None:
            return
        address, comment, latitude, longitude = data
        if not address:
            address = "Magazyn"
        x, y = self.convert_gps_to_canvas_position(latitude, longitude)
        depot = Point(
            name="Baza",
            latitude=latitude,
            longitude=longitude,
            x=x,
            y=y,
            address=address,
            comment=comment,
            is_start=True,
        )
        if self.points and self.points[0].is_start:
            self.points[0] = depot
        else:
            self.points.insert(0, depot)
        self.route_optimized = False
        self.performance_mode = False
        self.clear_point_form()
        self.refresh_points_list()
        self.draw_points()
        self.update_distance_label()
        self.improvement_label.config(text="Poprawa: —")
        self.status_label.config(text="Status: ustawiono magazyn")

    def add_point(self):
        if not self.points or not self.points[0].is_start:
            self.status_label.config(text="Status: najpierw ustaw magazyn")
            return
        data = self.get_point_data_from_form()
        if data is None:
            return
        address, comment, latitude, longitude = data
        if not address:
            address = f"Punkt {self.point_counter + 1}"
        x, y = self.convert_gps_to_canvas_position(latitude, longitude)
        point = Point(
            name=f"Punkt {self.point_counter + 1}",
            latitude=latitude,
            longitude=longitude,
            x=x,
            y=y,
            address=address,
            comment=comment,
            is_start=False,
        )
        self.points.append(point)
        self.point_counter += 1
        self.route_optimized = False
        self.performance_mode = False
        self.clear_point_form()
        self.refresh_points_list()
        self.draw_points()
        self.update_distance_label()
        self.improvement_label.config(text="Poprawa: —")
        self.status_label.config(text="Status: dodano punkt trasy")

    def load_sample_points(self):
        self.points = []
        self.point_counter = 0
        start_latitude = 51.2070
        start_longitude = 16.1553
        x, y = self.convert_gps_to_canvas_position(start_latitude, start_longitude)
        start_point = Point(
            name="Baza",
            latitude=start_latitude,
            longitude=start_longitude,
            x=x,
            y=y,
            address="Magazyn Legnica",
            comment="",
            is_start=True,
        )
        self.points.append(start_point)
        self.point_counter += 1
        for i in range(1, 11):
            latitude = random.uniform(51.18, 51.23)
            longitude = random.uniform(16.11, 16.21)
            x, y = self.convert_gps_to_canvas_position(latitude, longitude)
            point = Point(
                name=f"Punkt {i}",
                latitude=latitude,
                longitude=longitude,
                x=x,
                y=y,
                address=f"Testowy punkt {i}",
                comment="",
                is_start=False,
            )
            self.points.append(point)
            self.point_counter += 1
        self.route_optimized = False
        self.performance_mode = False
        self.refresh_points_list()
        self.draw_points()
        self.update_distance_label()
        self.improvement_label.config(text="Poprawa: —")
        self.status_label.config(text="Status: wczytano 10 punktów + magazyn")

    def clear_route(self):
        self.points = []
        self.point_counter = 0
        self.route_optimized = False
        self.performance_mode = False
        self.points_list.delete(0, tk.END)
        for marker in self.map_markers:
            marker.delete()
        self.map_markers = []
        self.clear_map_paths()
        self.clear_point_form()
        self.distance_label.config(text="Dystans trasy: 0.00")
        self.improvement_label.config(text="Poprawa: —")
        self.status_label.config(text="Status: wyczyszczono trasę")

    def refresh_points_list(self):
        self.points_list.delete(0, tk.END)
        route_index = 1
        for point in self.points:
            comment_status = (
                f" · {point.comment}" if point.comment else ""
            )
            if point.is_start:
                self.points_list.insert(
                    tk.END, f"🏠 Start: {point.address}{comment_status}"
                )
            else:
                delivered_status = " ✓" if point.delivered else ""
                self.points_list.insert(
                    tk.END,
                    f"{route_index:>2}. {point.address}"
                    f"{comment_status}{delivered_status}",
                )
                route_index += 1

    def show_selected_point_details(self, event=None):
        selected_index = self.points_list.curselection()
        if not selected_index:
            self.details_label.config(
                text="Szczegóły punktu: brak wybranego punktu"
            )
            return
        index = selected_index[0]
        if index == 0 and self.points and self.points[0].is_start:
            point = self.points[0]
        else:
            delivery_points = [p for p in self.points if not p.is_start]
            point_index = index - 1
            if point_index < 0 or point_index >= len(delivery_points):
                self.details_label.config(
                    text="Szczegóły punktu: nieprawidłowy wybór"
                )
                return
            point = delivery_points[point_index]
        delivery_status = "dostarczono ✓" if point.delivered else "oczekuje"
        details = (
            f"Adres: {point.address}\n"
            f"Komentarz: {point.comment if point.comment else '—'}\n"
            f"Lat: {point.latitude:.5f}  ·  Lon: {point.longitude:.5f}\n"
            f"Status: {'baza' if point.is_start else delivery_status}"
        )
        self.details_label.config(text=details)

    def mark_selected_as_delivered(self):
        selected_index = self.points_list.curselection()
        if not selected_index:
            self.status_label.config(text="Status: wybierz punkt z listy")
            return
        selected_text = self.points_list.get(selected_index[0])
        if selected_text.startswith("🏠"):
            self.status_label.config(
                text="Status: magazyn nie jest punktem dostawy"
            )
            return
        delivery_points = [p for p in self.points if not p.is_start]
        point_index = selected_index[0] - 1
        if point_index < 0 or point_index >= len(delivery_points):
            self.status_label.config(text="Status: nieprawidłowy punkt")
            return
        selected_point = delivery_points[point_index]
        selected_point.delivered = not selected_point.delivered
        self.refresh_points_list()
        self.draw_points()
        self.show_selected_point_details()
        if selected_point.delivered:
            self.status_label.config(text="Status: oznaczono jako dostarczone ✓")
        else:
            self.status_label.config(text="Status: cofnięto status dostarczenia")

    def delete_selected_point(self):
        selected_index = self.points_list.curselection()
        if not selected_index:
            self.status_label.config(text="Status: wybierz punkt z listy")
            return
        index = selected_index[0]
        if index == 0:
            self.status_label.config(text="Status: nie można usunąć magazynu")
            return
        delivery_points = [p for p in self.points if not p.is_start]
        point_index = index - 1
        if point_index < 0 or point_index >= len(delivery_points):
            self.status_label.config(text="Status: nieprawidłowy punkt")
            return
        point_to_delete = delivery_points[point_index]
        self.points.remove(point_to_delete)
        self.point_counter = len([p for p in self.points if not p.is_start])
        self.route_optimized = False
        self.performance_mode = False
        self.refresh_points_list()
        self.draw_points()
        self.update_distance_label()
        self.improvement_label.config(text="Poprawa: —")
        self.details_label.config(
            text="Szczegóły punktu: brak wybranego punktu"
        )
        self.status_label.config(text="Status: usunięto punkt")

    def save_comment_to_selected_point(self):
        selected_index = self.points_list.curselection()
        if not selected_index:
            self.status_label.config(text="Status: wybierz punkt z listy")
            return
        selected_text = self.points_list.get(selected_index[0])
        if selected_text.startswith("🏠"):
            point = self.points[0]
        else:
            delivery_points = [p for p in self.points if not p.is_start]
            point_index = selected_index[0] - 1
            if point_index < 0 or point_index >= len(delivery_points):
                self.status_label.config(text="Status: nieprawidłowy punkt")
                return
            point = delivery_points[point_index]
        comment = self.comment_entry.get().strip()
        if not comment:
            self.status_label.config(text="Status: wpisz komentarz")
            return
        point.comment = comment
        self.comment_entry.delete(0, tk.END)
        self.refresh_points_list()
        self.show_selected_point_details()
        self.status_label.config(text="Status: zapisano komentarz do punktu")

    def clear_map_paths(self):
        if self.map_path:
            self.map_path.delete()
            self.map_path = None
        for path in self.map_paths:
            path.delete()
        self.map_paths = []

    def create_marker_icon(self, label, color, delivered=False):
        image = Image.new("RGBA", (44, 62), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse((7, 3, 37, 33), fill=color, outline="#111827", width=2)
        draw.polygon([(17, 30), (27, 30), (22, 55)], fill=color)
        draw.line([(17, 30), (22, 55), (27, 30)], fill="#111827", width=2)
        try:
            font = ImageFont.truetype("arial.ttf", 14)
        except OSError:
            font = ImageFont.load_default()
        text_box = draw.textbbox((0, 0), label, font=font)
        text_width = text_box[2] - text_box[0]
        text_height = text_box[3] - text_box[1]
        draw.text(
            (22 - text_width / 2, 18 - text_height / 2),
            label,
            fill="white",
            font=font,
        )
        if delivered:
            draw.ellipse((28, 0, 43, 15), fill="#16a34a", outline="white", width=1)
            draw.line([(31, 8), (35, 12), (41, 3)], fill="white", width=2)
        icon = ImageTk.PhotoImage(image)
        self.marker_icons.append(icon)
        return icon

    def draw_points(self):
        for marker in self.map_markers:
            marker.delete()
        self.map_markers = []
        self.marker_icons = []
        self.clear_map_paths()

        if not self.points:
            return

        if len(self.points) > 1 and not self.route_optimized:
            straight_route = [
                (point.latitude, point.longitude) for point in self.points
            ]
            straight_route.append(
                (self.points[0].latitude, self.points[0].longitude)
            )
            path = self.map_widget.set_path(
                straight_route, color="#2563eb", width=3
            )
            self.map_paths.append(path)

        elif len(self.points) > 1 and self.route_optimized and not self.performance_mode:
            total_road_distance = 0
            full_route = self.points + [self.points[0]]
            segment_colors = [
                "#ff0054", "#00b4d8", "#ffbe0b", "#8338ec", "#fb5607",
                "#3a86ff", "#ff006e", "#7209b7", "#06d6a0", "#f72585",
                "#4cc9f0", "#b5179e", "#ff9f1c", "#4361ee", "#2ec4b6",
            ]
            segments = []
            for i in range(len(full_route) - 1):
                start_point = full_route[i]
                end_point = full_route[i + 1]
                distance_km, route_coordinates = get_road_route_between_points(
                    start_point, end_point
                )
                if route_coordinates:
                    segment_coordinates = route_coordinates
                    total_road_distance += distance_km
                else:
                    segment_coordinates = [
                        (start_point.latitude, start_point.longitude),
                        (end_point.latitude, end_point.longitude),
                    ]
                is_delivered_segment = (
                    not end_point.is_start and end_point.delivered
                )
                segments.append(
                    {
                        "coordinates": segment_coordinates,
                        "color": segment_colors[i % len(segment_colors)],
                        "delivered": is_delivered_segment,
                    }
                )
            for segment in segments:
                if segment["delivered"]:
                    outline_path = self.map_widget.set_path(
                        segment["coordinates"], color="#111827", width=7
                    )
                    self.map_paths.append(outline_path)
                    path = self.map_widget.set_path(
                        segment["coordinates"], color="#9ca3af", width=5
                    )
                    self.map_paths.append(path)
            for segment in reversed(segments):
                if not segment["delivered"]:
                    outline_path = self.map_widget.set_path(
                        segment["coordinates"], color="#111827", width=7
                    )
                    self.map_paths.append(outline_path)
                    path = self.map_widget.set_path(
                        segment["coordinates"],
                        color=segment["color"],
                        width=5,
                    )
                    self.map_paths.append(path)
            self.distance_label.config(
                text=f"Dystans: {total_road_distance:.2f} km"
            )

        delivery_number = 1
        for point in self.points:
            if point.is_start:
                marker_text = "S"
                marker_color = "#16a34a"
            else:
                marker_text = f"{delivery_number}"
                marker_color = "#9ca3af" if point.delivered else "#f59e0b"
                if point.delivered:
                    marker_text = f"{delivery_number} ✓"
                delivery_number += 1

            icon = self.create_marker_icon(
                marker_text.replace(" ✓", ""),
                marker_color,
                point.delivered and not point.is_start,
            )
            marker = self.map_widget.set_marker(
                point.latitude,
                point.longitude,
                icon=icon,
                icon_anchor="s",
            )
            self.map_markers.append(marker)

        if self.points and len(self.points) <= 30:
            min_lat = min(p.latitude for p in self.points)
            max_lat = max(p.latitude for p in self.points)
            min_lon = min(p.longitude for p in self.points)
            max_lon = max(p.longitude for p in self.points)
            if min_lat != max_lat and min_lon != max_lon:
                self.map_widget.fit_bounding_box(
                    (max_lat, min_lon), (min_lat, max_lon)
                )
            else:
                self.map_widget.set_position(
                    self.points[0].latitude, self.points[0].longitude
                )
        elif self.points:
            self.map_widget.set_position(
                self.points[0].latitude, self.points[0].longitude
            )

    def update_distance_label(self):
        distance = calculate_total_distance(self.points)
        self.distance_label.config(text=f"Dystans: {distance:.2f} km")

    def optimize_route(self):
        self.performance_mode = False
        self.status_label.config(text="Status: optymalizuję trasę…")
        self.root.update()
        if len(self.points) < 2:
            self.status_label.config(
                text="Status: za mało punktów do optymalizacji"
            )
            return
        before_distance = calculate_total_distance(self.points)
        best_route, best_distance = genetic_algorithm_route(self.points)
        self.points = best_route
        self.route_optimized = True
        self.refresh_points_list()
        self.draw_points()
        improvement_percent = (
            ((before_distance - best_distance) / before_distance) * 100
            if before_distance > 0
            else 0
        )
        self.improvement_label.config(
            text=f"Poprawa: {improvement_percent:.1f}%"
        )
        self.status_label.config(text="Status: trasa zoptymalizowana ✓")

    def export_route(self):
        if len(self.points) < 2:
            self.status_label.config(
                text="Status: za mało punktów do eksportu"
            )
            return
        export_route_to_json(self.points, "route_result.json")
        self.status_label.config(text="Status: wyeksportowano trasę do JSON ✓")

    def import_route(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")]
        )
        if not file_path:
            return
        try:
            imported_points = import_route_from_json(file_path)
        except Exception:
            self.status_label.config(text="Status: błąd importu JSON")
            return
        if not imported_points:
            self.status_label.config(
                text="Status: plik JSON nie zawiera trasy"
            )
            return
        self.points = imported_points
        self.point_counter = len([p for p in self.points if not p.is_start])
        self.route_optimized = False
        self.performance_mode = False
        for point in self.points:
            point.x, point.y = self.convert_gps_to_canvas_position(
                point.latitude, point.longitude
            )
        self.refresh_points_list()
        self.draw_points()
        self.update_distance_label()
        self.improvement_label.config(text="Poprawa: —")
        self.status_label.config(text="Status: zaimportowano trasę z JSON ✓")

    def run_performance_test(self):
        self.points = []
        self.point_counter = 0
        self.performance_mode = True
        start_latitude = 51.2070
        start_longitude = 16.1553
        start_x, start_y = self.convert_gps_to_canvas_position(
            start_latitude, start_longitude
        )
        start_point = Point(
            name="Baza",
            latitude=start_latitude,
            longitude=start_longitude,
            x=start_x,
            y=start_y,
            address="Magazyn Legnica, ul. Nowodworska 30",
            comment="Punkt startowy testu wydajności",
            is_start=True,
        )
        self.points.append(start_point)
        self.point_counter += 1
        for i in range(1, 101):
            latitude = random.uniform(51.18, 51.23)
            longitude = random.uniform(16.11, 16.21)
            x, y = self.convert_gps_to_canvas_position(latitude, longitude)
            point = Point(
                name=f"Punkt {i}",
                latitude=latitude,
                longitude=longitude,
                x=x,
                y=y,
                address=f"Testowy punkt {i}",
                comment="",
                is_start=False,
            )
            self.points.append(point)
            self.point_counter += 1
        start_time = time.perf_counter()
        best_route, best_distance = genetic_algorithm_route(
            self.points,
            population_size=35,
            generations=40,
            mutation_rate=0.08,
        )
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.points = best_route
        self.route_optimized = False
        self.performance_mode = True
        self.refresh_points_list()
        self.draw_points()
        self.update_distance_label()
        self.improvement_label.config(text="Poprawa: test wydajności")
        self.status_label.config(
            text=f"Status: test 100 pkt: {elapsed_time:.2f} s"
        )

    def generate_performance_report(self):
        results = []
        test_cases = [(10, 60, 80, 60), (100, 35, 40, 10)]
        for points_count, population_size, generations, max_time in test_cases:
            test_points = []
            start_latitude = 51.2070
            start_longitude = 16.1553
            start_x, start_y = self.convert_gps_to_canvas_position(
                start_latitude, start_longitude
            )
            start_point = Point(
                name="Baza",
                latitude=start_latitude,
                longitude=start_longitude,
                x=start_x,
                y=start_y,
                address="Magazyn Legnica, ul. Nowodworska 30",
                comment="Punkt startowy testu wydajności",
                is_start=True,
            )
            test_points.append(start_point)
            for i in range(1, points_count + 1):
                latitude = random.uniform(51.18, 51.23)
                longitude = random.uniform(16.11, 16.21)
                x, y = self.convert_gps_to_canvas_position(latitude, longitude)
                point = Point(
                    name=f"Punkt {i}",
                    latitude=latitude,
                    longitude=longitude,
                    x=x,
                    y=y,
                    address=f"Testowy punkt {i}",
                    comment="",
                    is_start=False,
                )
                test_points.append(point)
            start_time = time.perf_counter()
            best_route, best_distance = genetic_algorithm_route(
                test_points,
                population_size=population_size,
                generations=generations,
                mutation_rate=0.08,
            )
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time
            status = "SPEŁNIONO" if elapsed_time <= max_time else "NIE SPEŁNIONO"
            results.append(
                f"{points_count} punktów:\n"
                f"czas: {elapsed_time:.2f} s\n"
                f"dystans: {best_distance:.2f}\n"
                f"limit: {max_time} s\n"
                f"status: {status}\n"
            )
        report_content = (
            "RAPORT WYDAJNOŚCI\n"
            f"Data wygenerowania: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            "Zakres testu:\n"
            "Raport mierzy czas działania algorytmu optymalizacji trasy.\n"
            "Test nie uwzględnia czasu geokodowania adresów, pobierania trasy z OSRM ani rysowania mapy.\n\n"
            + "\n".join(results)
        )
        with open("performance_report.txt", "w", encoding="utf-8") as file:
            file.write(report_content)
        self.status_label.config(
            text="Status: wygenerowano raport wydajności ✓"
        )


def run_app():
    root = tk.Tk()
    app = RouteApp(root)
    root.mainloop()
