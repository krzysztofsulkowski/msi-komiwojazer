import tkinter as tk
from tkinter import filedialog
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


class RouteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Komiwojażer")
        self.root.geometry("1280x720")
        self.root.configure(bg="#f3f4f6")

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
        header = tk.Frame(self.root, bg="#1f2937", height=70)
        header.pack(fill="x")

        title = tk.Label(
            header,
            text="Optymalizacja Trasy Kuriera",
            bg="#1f2937",
            fg="white",
            font=("Arial", 20, "bold")
        )
        title.pack(pady=18)

        content = tk.Frame(self.root, bg="#f3f4f6")
        content.pack(fill="both", expand=True, padx=20, pady=20)

        left_panel = tk.Frame(content, bg="white", width=750, height=560)
        left_panel.pack(side="left", fill="both", expand=True)
        left_panel.pack_propagate(False)

        self.map_widget = tkintermapview.TkinterMapView(
            left_panel,
            corner_radius=0
        )
        self.map_widget.pack(fill="both", expand=True, padx=20, pady=20)

        self.map_widget.set_position(51.2070, 16.1553)
        self.map_widget.set_zoom(13)

        self.create_map_legend(left_panel)
        self.create_route_info_panel(left_panel)

        right_container = tk.Frame(content, bg="white", width=350, height=560)
        right_container.pack(side="right", fill="y", padx=(20, 0))
        right_container.pack_propagate(False)

        right_canvas = tk.Canvas(
            right_container,
            bg="white",
            highlightthickness=0,
            width=330
        )
        right_canvas.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(
            right_container,
            orient="vertical",
            command=right_canvas.yview
        )
        scrollbar.pack(side="right", fill="y")

        right_panel = tk.Frame(right_canvas, bg="white")

        right_canvas_window = right_canvas.create_window(
            (0, 0),
            window=right_panel,
            anchor="nw",
            width=315
        )

        right_canvas.configure(yscrollcommand=scrollbar.set)

        def update_scroll_region(event=None):
            right_canvas.configure(scrollregion=right_canvas.bbox("all"))

        def resize_right_panel(event):
            right_canvas.itemconfig(right_canvas_window, width=event.width)

        def on_mousewheel(event):
            right_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def bind_mousewheel(event):
            right_canvas.bind_all("<MouseWheel>", on_mousewheel)

        def unbind_mousewheel(event):
            right_canvas.unbind_all("<MouseWheel>")

        right_panel.bind("<Configure>", update_scroll_region)
        right_canvas.bind("<Configure>", resize_right_panel)

        right_canvas.bind("<Enter>", bind_mousewheel)
        right_canvas.bind("<Leave>", unbind_mousewheel)
        right_panel.bind("<Enter>", bind_mousewheel)
        right_panel.bind("<Leave>", unbind_mousewheel)

        points_title = tk.Label(
            right_panel,
            text="Punkty trasy",
            bg="white",
            fg="#111827",
            font=("Arial", 16, "bold")
        )
        points_title.pack(anchor="w", padx=20, pady=(20, 10))

        self.create_section_title(right_panel, "Dane testowe")

        sample_button = tk.Button(
            right_panel,
            text="Wczytaj przykładowe punkty",
            bg="#6b7280",
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            padx=12,
            pady=8,
            command=self.load_sample_points
        )
        sample_button.pack(fill="x", padx=20, pady=(0, 8))

        clear_button = tk.Button(
            right_panel,
            text="Wyczyść trasę",
            bg="#dc2626",
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            padx=12,
            pady=8,
            command=self.clear_route
        )
        clear_button.pack(fill="x", padx=20, pady=(0, 20))

        self.create_section_title(right_panel, "Dodawanie punktu")

        form_frame = tk.Frame(right_panel, bg="white")
        form_frame.pack(fill="x", padx=20, pady=(0, 12))

        address_label = tk.Label(
            form_frame,
            text="Adres:",
            bg="white",
            fg="#111827",
            font=("Arial", 11)
        )
        address_label.grid(row=0, column=0, sticky="w", pady=(0, 6))

        self.address_entry = tk.Entry(
            form_frame,
            font=("Arial", 11),
            width=18
        )
        self.address_entry.grid(row=0, column=1, padx=(8, 0), pady=(0, 6))

        comment_label = tk.Label(
            form_frame,
            text="Komentarz:",
            bg="white",
            fg="#111827",
            font=("Arial", 11)
        )
        comment_label.grid(row=1, column=0, sticky="w", pady=(0, 6))

        self.comment_entry = tk.Entry(
            form_frame,
            font=("Arial", 11),
            width=18
        )
        self.comment_entry.grid(row=1, column=1, padx=(8, 0), pady=(0, 6))

        latitude_label = tk.Label(
            form_frame,
            text="Szerokość geograficzna:",
            bg="white",
            fg="#111827",
            font=("Arial", 11)
        )
        latitude_label.grid(row=2, column=0, sticky="w", pady=(0, 6))

        self.latitude_entry = tk.Entry(
            form_frame,
            font=("Arial", 11),
            width=18
        )
        self.latitude_entry.grid(row=2, column=1, padx=(8, 0), pady=(0, 6))

        longitude_label = tk.Label(
            form_frame,
            text="Długość geograficzna:",
            bg="white",
            fg="#111827",
            font=("Arial", 11)
        )
        longitude_label.grid(row=3, column=0, sticky="w")

        self.longitude_entry = tk.Entry(
            form_frame,
            font=("Arial", 11),
            width=18
        )
        self.longitude_entry.grid(row=3, column=1, padx=(8, 0))

        search_address_button = tk.Button(
            right_panel,
            text="Szukaj adresu",
            bg="#0891b2",
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            padx=12,
            pady=8,
            command=self.search_address_from_form
        )
        search_address_button.pack(fill="x", padx=20, pady=(0, 8))

        self.address_results_list = tk.Listbox(
            right_panel,
            font=("Arial", 9),
            bd=0,
            highlightthickness=1,
            highlightbackground="#d1d5db",
            height=4
        )
        self.address_results_list.pack(fill="x", padx=20, pady=(0, 8))
        self.address_results_list.bind("<<ListboxSelect>>", self.select_address_result)

        set_depot_button = tk.Button(
            right_panel,
            text="Ustaw magazyn",
            bg="#16a34a",
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            padx=12,
            pady=8,
            command=self.set_depot
        )
        set_depot_button.pack(fill="x", padx=20, pady=(0, 8))

        add_button = tk.Button(
            right_panel,
            text="Dodaj punkt",
            bg="#2563eb",
            fg="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            padx=12,
            pady=8,
            command=self.add_point
        )
        add_button.pack(fill="x", padx=20, pady=(0, 8))

        delete_button = tk.Button(
            right_panel,
            text="Usuń punkt",
            bg="#dc2626",
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            padx=12,
            pady=8,
            command=self.delete_selected_point
        )
        delete_button.pack(fill="x", padx=20, pady=(0, 8))

        self.create_section_title(right_panel, "Zarządzanie punktem")

        comment_button = tk.Button(
            right_panel,
            text="Zapisz komentarz do punktu",
            bg="#7c3aed",
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            padx=12,
            pady=8,
            command=self.save_comment_to_selected_point
        )
        comment_button.pack(fill="x", padx=20, pady=(0, 20))

        points_list_frame = tk.Frame(right_panel, bg="white")
        points_list_frame.pack(fill="x", padx=20, pady=(0, 20))

        self.points_list = tk.Listbox(
            points_list_frame,
            font=("Arial", 12),
            bd=0,
            highlightthickness=1,
            highlightbackground="#d1d5db",
            height=7,
            yscrollcommand=None
        )
        self.points_list.pack(side="left", fill="both", expand=True)

        points_list_scrollbar = tk.Scrollbar(
            points_list_frame,
            orient="vertical",
            command=self.points_list.yview
        )
        points_list_scrollbar.pack(side="right", fill="y")

        self.points_list.config(yscrollcommand=points_list_scrollbar.set)

        self.points_list.bind("<<ListboxSelect>>", self.show_selected_point_details)

        def on_points_list_mousewheel(event):
            self.points_list.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"

        self.points_list.bind("<MouseWheel>", on_points_list_mousewheel)

        self.details_label = tk.Label(
            right_panel,
            text="Szczegóły punktu: brak wybranego punktu",
            bg="white",
            fg="#374151",
            font=("Arial", 10),
            justify="left",
            anchor="w",
            wraplength=260
        )
        self.details_label.pack(fill="x", padx=20, pady=(0, 12))

        delivered_button = tk.Button(
            right_panel,
            text="Oznacz jako dostarczone/niedostarczone",
            bg="#16a34a",
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            padx=12,
            pady=8,
            command=self.mark_selected_as_delivered
        )
        delivered_button.pack(fill="x", padx=20, pady=(0, 8))

        self.create_section_title(right_panel, "Operacje na trasie")

        optimize_button = tk.Button(
            right_panel,
            text="Optymalizuj trasę",
            bg="#111827",
            fg="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            padx=12,
            pady=10,
            command=self.optimize_route
        )
        optimize_button.pack(fill="x", padx=20, pady=(0, 8))

        export_button = tk.Button(
            right_panel,
            text="Eksportuj trasę do JSON",
            bg="#2563eb",
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            padx=12,
            pady=8,
            command=self.export_route
        )
        export_button.pack(fill="x", padx=20, pady=(0, 8))

        import_button = tk.Button(
            right_panel,
            text="Importuj trasę z JSON",
            bg="#4f46e5",
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            padx=12,
            pady=8,
            command=self.import_route
        )
        import_button.pack(fill="x", padx=20, pady=(0, 8))

        report_button = tk.Button(
            right_panel,
            text="Generuj raport wydajności",
            bg="#7c2d12",
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            padx=12,
            pady=8,
            command=self.generate_performance_report
        )
        report_button.pack(fill="x", padx=20, pady=(0, 20))

    def create_section_title(self, parent, text):
        label = tk.Label(
            parent,
            text=text,
            bg="white",
            fg="#111827",
            font=("Arial", 11, "bold")
        )
        label.pack(anchor="w", padx=20, pady=(16, 8))

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

        self.status_label.config(text="Status: wybrano adres i uzupełniono współrzędne")

    def get_point_data_from_form(self):
        try:
            latitude = float(self.latitude_entry.get())
            longitude = float(self.longitude_entry.get())
        except ValueError:
            self.status_label.config(text="Status: wpisz poprawne współrzędne")
            return None

        if latitude < 51.18 or latitude > 51.23 or longitude < 16.11 or longitude > 16.21:
            self.status_label.config(text="Status: wpisz współrzędne z obszaru Legnicy")
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
            is_start=True
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
        self.improvement_label.config(text="Poprawa: brak")
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
            is_start=False
        )

        self.points.append(point)
        self.point_counter += 1

        self.route_optimized = False
        self.performance_mode = False

        self.clear_point_form()
        self.refresh_points_list()
        self.draw_points()
        self.update_distance_label()
        self.improvement_label.config(text="Poprawa: brak")
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
            is_start=True
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
                is_start=False
            )

            self.points.append(point)
            self.point_counter += 1

        self.route_optimized = False
        self.performance_mode = False
        self.refresh_points_list()
        self.draw_points()
        self.update_distance_label()
        self.improvement_label.config(text="Poprawa: brak")
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
        self.improvement_label.config(text="Poprawa: brak")
        self.status_label.config(text="Status: wyczyszczono trasę")

    def refresh_points_list(self):
        self.points_list.delete(0, tk.END)

        route_index = 1

        for point in self.points:
            comment_status = f" | Komentarz: {point.comment}" if point.comment else ""

            if point.is_start:
                self.points_list.insert(tk.END, f"Start: {point.address}{comment_status}")
            else:
                delivered_status = " - dostarczono" if point.delivered else ""
                self.points_list.insert(
                    tk.END,
                    f"{route_index}. {point.address}{comment_status}{delivered_status}"
                )
                route_index += 1

    def show_selected_point_details(self, event=None):
        selected_index = self.points_list.curselection()

        if not selected_index:
            self.details_label.config(text="Szczegóły punktu: brak wybranego punktu")
            return

        index = selected_index[0]

        if index == 0 and self.points and self.points[0].is_start:
            point = self.points[0]
        else:
            delivery_points = [point for point in self.points if not point.is_start]
            point_index = index - 1

            if point_index < 0 or point_index >= len(delivery_points):
                self.details_label.config(text="Szczegóły punktu: nieprawidłowy wybór")
                return

            point = delivery_points[point_index]

        delivery_status = "dostarczono" if point.delivered else "oczekuje"

        details = (
            f"Szczegóły punktu:\n"
            f"Adres: {point.address}\n"
            f"Komentarz: {point.comment if point.comment else 'brak'}\n"
            f"Latitude: {point.latitude}\n"
            f"Longitude: {point.longitude}\n"
            f"Status: {'baza' if point.is_start else delivery_status}"
        )

        self.details_label.config(text=details)

    def mark_selected_as_delivered(self):
        selected_index = self.points_list.curselection()

        if not selected_index:
            self.status_label.config(text="Status: wybierz punkt z listy")
            return

        selected_text = self.points_list.get(selected_index[0])

        if selected_text.startswith("Start"):
            self.status_label.config(text="Status: magazyn nie jest punktem dostawy")
            return

        delivery_points = [point for point in self.points if not point.is_start]

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
            self.status_label.config(text="Status: oznaczono paczkę jako dostarczoną")
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

        delivery_points = [point for point in self.points if not point.is_start]
        point_index = index - 1

        if point_index < 0 or point_index >= len(delivery_points):
            self.status_label.config(text="Status: nieprawidłowy punkt")
            return

        point_to_delete = delivery_points[point_index]
        self.points.remove(point_to_delete)

        self.point_counter = len([point for point in self.points if not point.is_start])
        self.route_optimized = False
        self.performance_mode = False

        self.refresh_points_list()
        self.draw_points()
        self.update_distance_label()
        self.improvement_label.config(text="Poprawa: brak")
        self.details_label.config(text="Szczegóły punktu: brak wybranego punktu")
        self.status_label.config(text="Status: usunięto punkt")

    def save_comment_to_selected_point(self):
        selected_index = self.points_list.curselection()

        if not selected_index:
            self.status_label.config(text="Status: wybierz punkt z listy")
            return

        selected_text = self.points_list.get(selected_index[0])

        if selected_text.startswith("Start"):
            point = self.points[0]
        else:
            delivery_points = [point for point in self.points if not point.is_start]
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
            font=font
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
                (point.latitude, point.longitude)
                for point in self.points
            ]

            straight_route.append(
                (self.points[0].latitude, self.points[0].longitude)
            )

            path = self.map_widget.set_path(
                straight_route,
                color="#2563eb",
                width=3
            )

            self.map_paths.append(path)


        elif len(self.points) > 1 and self.route_optimized and not self.performance_mode:

            total_road_distance = 0

            full_route = self.points + [self.points[0]]

            segment_colors = [

                "#ff0054",

                "#00b4d8",

                "#ffbe0b",

                "#8338ec",

                "#fb5607",

                "#3a86ff",

                "#ff006e",

                "#7209b7",

                "#06d6a0",

                "#f72585",

                "#4cc9f0",

                "#b5179e",

                "#ff9f1c",

                "#4361ee",

                "#2ec4b6"

            ]

            segments = []

            for i in range(len(full_route) - 1):

                start_point = full_route[i]

                end_point = full_route[i + 1]

                distance_km, route_coordinates = get_road_route_between_points(

                    start_point,

                    end_point

                )

                if route_coordinates:

                    segment_coordinates = route_coordinates

                    total_road_distance += distance_km

                else:

                    segment_coordinates = [

                        (start_point.latitude, start_point.longitude),

                        (end_point.latitude, end_point.longitude)

                    ]

                is_delivered_segment = not end_point.is_start and end_point.delivered

                segments.append(

                    {

                        "coordinates": segment_coordinates,

                        "color": segment_colors[i % len(segment_colors)],

                        "delivered": is_delivered_segment

                    }

                )

            for segment in segments:

                if segment["delivered"]:
                    outline_path = self.map_widget.set_path(

                        segment["coordinates"],

                        color="#111827",

                        width=7

                    )

                    self.map_paths.append(outline_path)

                    path = self.map_widget.set_path(

                        segment["coordinates"],

                        color="#9ca3af",

                        width=5

                    )

                    self.map_paths.append(path)

            for segment in reversed(segments):

                if not segment["delivered"]:
                    outline_path = self.map_widget.set_path(

                        segment["coordinates"],

                        color="#111827",

                        width=7

                    )

                    self.map_paths.append(outline_path)

                    path = self.map_widget.set_path(

                        segment["coordinates"],

                        color=segment["color"],

                        width=5

                    )

                    self.map_paths.append(path)

            self.distance_label.config(text=f"Dystans: {total_road_distance:.2f} km")

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
                point.delivered and not point.is_start
            )

            marker = self.map_widget.set_marker(
                point.latitude,
                point.longitude,
                icon=icon,
                icon_anchor="s"
            )

            self.map_markers.append(marker)

        if self.points and len(self.points) <= 30:
            min_latitude = min(point.latitude for point in self.points)
            max_latitude = max(point.latitude for point in self.points)
            min_longitude = min(point.longitude for point in self.points)
            max_longitude = max(point.longitude for point in self.points)

            if min_latitude != max_latitude and min_longitude != max_longitude:
                self.map_widget.fit_bounding_box(
                    (max_latitude, min_longitude),
                    (min_latitude, max_longitude)
                )
            else:
                self.map_widget.set_position(
                    self.points[0].latitude,
                    self.points[0].longitude
                )
        elif self.points:
            self.map_widget.set_position(
                self.points[0].latitude,
                self.points[0].longitude
            )

    def update_distance_label(self):
        distance = calculate_total_distance(self.points)

        if self.route_optimized:
            self.distance_label.config(text=f"Dystans: {distance:.2f}")
        else:
            self.distance_label.config(text=f"Dystans: {distance:.2f}")

    def optimize_route(self):
        self.performance_mode = False
        self.status_label.config(text="Status: optymalizuję trasę...")
        self.root.update()
        if len(self.points) < 2:
            self.status_label.config(text="Status: za mało punktów do optymalizacji")
            return

        before_distance = calculate_total_distance(self.points)
        best_route, best_distance = genetic_algorithm_route(self.points)

        self.points = best_route
        self.route_optimized = True
        self.refresh_points_list()
        self.draw_points()

        if before_distance > 0:
            improvement_percent = ((before_distance - best_distance) / before_distance) * 100
        else:
            improvement_percent = 0

        self.improvement_label.config(text=f"Poprawa: {improvement_percent:.1f}%")
        self.status_label.config(text="Status: trasa zoptymalizowana")

    def export_route(self):
        if len(self.points) < 2:
            self.status_label.config(text="Status: za mało punktów do eksportu")
            return

        export_route_to_json(self.points, "route_result.json")
        self.status_label.config(text="Status: wyeksportowano trasę do JSON")

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
            self.status_label.config(text="Status: plik JSON nie zawiera trasy")
            return

        self.points = imported_points
        self.point_counter = len([point for point in self.points if not point.is_start])

        self.route_optimized = False
        self.performance_mode = False

        for point in self.points:
            point.x, point.y = self.convert_gps_to_canvas_position(
                point.latitude,
                point.longitude
            )

        self.refresh_points_list()
        self.draw_points()
        self.update_distance_label()
        self.improvement_label.config(text="Poprawa: brak")
        self.status_label.config(text="Status: zaimportowano trasę z JSON")

    def run_performance_test(self):
        self.points = []
        self.point_counter = 0
        self.performance_mode = True

        start_latitude = 51.2070
        start_longitude = 16.1553

        start_x, start_y = self.convert_gps_to_canvas_position(start_latitude, start_longitude)

        start_point = Point(
            name="Baza",
            latitude=start_latitude,
            longitude=start_longitude,
            x=start_x,
            y=start_y,
            address="Magazyn Legnica, ul. Nowodworska 30",
            comment="Punkt startowy testu wydajności",
            is_start=True
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
                is_start=False
            )

            self.points.append(point)
            self.point_counter += 1

        start_time = time.perf_counter()
        best_route, best_distance = genetic_algorithm_route(
            self.points,
            population_size=35,
            generations=40,
            mutation_rate=0.08
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

        test_cases = [
            (10, 60, 80, 60),
            (100, 35, 40, 10)
        ]

        for points_count, population_size, generations, max_time in test_cases:
            test_points = []

            start_latitude = 51.2070
            start_longitude = 16.1553
            start_x, start_y = self.convert_gps_to_canvas_position(start_latitude, start_longitude)

            start_point = Point(
                name="Baza",
                latitude=start_latitude,
                longitude=start_longitude,
                x=start_x,
                y=start_y,
                address="Magazyn Legnica, ul. Nowodworska 30",
                comment="Punkt startowy testu wydajności",
                is_start=True
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
                    is_start=False
                )

                test_points.append(point)

            start_time = time.perf_counter()
            best_route, best_distance = genetic_algorithm_route(
                test_points,
                population_size=population_size,
                generations=generations,
                mutation_rate=0.08
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

        self.status_label.config(text="Status: wygenerowano raport wydajności")

    def create_map_legend(self, parent):
        legend_frame = tk.Frame(
            parent,
            bg="white",
            bd=1,
            relief="solid"
        )
        legend_frame.place(x=35, rely=1.0, y=-35, anchor="sw")

        title = tk.Label(
            legend_frame,
            text="Legenda mapy",
            bg="white",
            fg="#111827",
            font=("Arial", 10, "bold")
        )
        title.pack(anchor="w", padx=10, pady=(8, 4))

        items = [
            ("●", "#16a34a", "magazyn / punkt startowy"),
            ("●", "#f59e0b", "punkt do odwiedzenia"),
            ("●", "#9ca3af", "punkt dostarczony"),
            ("✓", "#16a34a", "dostarczono"),
            ("—", "#2563eb", "trasa przejazdu")
        ]

        for symbol, color, text in items:
            row = tk.Frame(legend_frame, bg="white")
            row.pack(anchor="w", padx=10, pady=1)

            icon = tk.Label(
                row,
                text=symbol,
                bg="white",
                fg=color,
                font=("Arial", 10, "bold"),
                width=2
            )
            icon.pack(side="left")

            label = tk.Label(
                row,
                text=text,
                bg="white",
                fg="#374151",
                font=("Arial", 9)
            )
            label.pack(side="left")

    def create_route_info_panel(self, parent):
        self.route_info_frame = tk.Frame(
            parent,
            bg="white",
            bd=1,
            relief="solid"
        )
        self.route_info_frame.place(relx=1.0, rely=1.0, x=-35, y=-35, anchor="se")

        title = tk.Label(
            self.route_info_frame,
            text="Informacje o trasie",
            bg="white",
            fg="#111827",
            font=("Arial", 10, "bold")
        )
        title.pack(anchor="w", padx=10, pady=(8, 4))

        self.distance_label = tk.Label(
            self.route_info_frame,
            text="Dystans: 0.00 km",
            bg="white",
            fg="#374151",
            font=("Arial", 9)
        )
        self.distance_label.pack(anchor="w", padx=10, pady=1)

        self.improvement_label = tk.Label(
            self.route_info_frame,
            text="Poprawa: brak",
            bg="white",
            fg="#374151",
            font=("Arial", 9)
        )
        self.improvement_label.pack(anchor="w", padx=10, pady=1)

        self.status_label = tk.Label(
            self.route_info_frame,
            text="Status: oczekiwanie",
            bg="white",
            fg="#374151",
            font=("Arial", 9),
            wraplength=250,
            justify="left"
        )
        self.status_label.pack(anchor="w", padx=10, pady=(1, 8))


def run_app():
    root = tk.Tk()
    app = RouteApp(root)
    root.mainloop()