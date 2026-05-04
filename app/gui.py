import tkinter as tk
import tkintermapview
import random
import time
from datetime import datetime
from app.models import Point
from app.optimizer import genetic_algorithm_route, calculate_total_distance
from app.exporter import export_route_to_json
from app.geocoder import search_address
from app.route_service import get_road_route_between_points


class RouteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MSI - Problem Komiwojażera")
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

        self.map_widget = None
        self.map_markers = []
        self.map_path = None
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

        right_panel.bind("<Configure>", update_scroll_region)
        right_canvas.bind("<Configure>", resize_right_panel)
        right_canvas.bind_all("<MouseWheel>", on_mousewheel)

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
        sample_button.pack(anchor="w", padx=20, pady=(0, 8))

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
        clear_button.pack(anchor="w", padx=20, pady=(0, 20))

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
            text="Latitude:",
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
            text="Longitude:",
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
        search_address_button.pack(anchor="w", padx=20, pady=(0, 8))

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
        add_button.pack(anchor="w", padx=20, pady=(0, 8))

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
        comment_button.pack(anchor="w", padx=20, pady=(0, 20))

        self.points_list = tk.Listbox(
            right_panel,
            font=("Arial", 12),
            bd=0,
            highlightthickness=0,
            height=7
        )
        self.points_list.pack(fill="x", expand=False, padx=20, pady=(0, 20))

        self.points_list.bind("<<ListboxSelect>>", self.show_selected_point_details)

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
            text="Oznacz jako dostarczone",
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

        performance_button = tk.Button(
            right_panel,
            text="Test wydajności 100 punktów",
            bg="#0f766e",
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            padx=12,
            pady=8,
            command=self.run_performance_test
        )
        performance_button.pack(fill="x", padx=20, pady=(0, 20))

        report_button = tk.Button(
            right_panel,
            text="Raport wydajności",
            bg="#7c2d12",
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            padx=12,
            pady=8,
            command=self.generate_performance_report
        )
        report_button.pack(fill="x", padx=20, pady=(0, 20))

        self.distance_label = tk.Label(
            right_panel,
            text="Dystans trasy: 0.00",
            bg="white",
            fg="#111827",
            font=("Arial", 12)
        )
        self.distance_label.pack(anchor="w", padx=20, pady=(0, 10))

        self.improvement_label = tk.Label(
            right_panel,
            text="Poprawa: 0.00",
            bg="white",
            fg="#15803d",
            font=("Arial", 12)
        )
        self.improvement_label.pack(anchor="w", padx=20, pady=(0, 10))

        self.status_label = tk.Label(
            right_panel,
            text="Status: oczekiwanie",
            bg="white",
            fg="#6b7280",
            font=("Arial", 11)
        )
        self.status_label.pack(anchor="w", padx=20, pady=(0, 20))

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

    def add_point(self):
        try:
            latitude = float(self.latitude_entry.get())
            longitude = float(self.longitude_entry.get())
        except ValueError:
            self.status_label.config(text="Status: wpisz poprawne latitude i longitude")
            return

        if latitude < 51.18 or latitude > 51.23 or longitude < 16.11 or longitude > 16.21:
            self.status_label.config(text="Status: wpisz współrzędne z obszaru Legnicy")
            return

        address = self.address_entry.get().strip()
        comment = self.comment_entry.get().strip()

        if not address:
            address = "Baza" if self.point_counter == 0 else f"Punkt {self.point_counter}"

        x, y = self.convert_gps_to_canvas_position(latitude, longitude)

        if self.point_counter == 0:
            point = Point(
                name="Baza",
                latitude=latitude,
                longitude=longitude,
                x=x,
                y=y,
                address=address,
                comment=comment,
                is_start=True
            )
        else:
            point = Point(
                name=f"Punkt {self.point_counter}",
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

        self.address_entry.delete(0, tk.END)
        self.comment_entry.delete(0, tk.END)
        self.latitude_entry.delete(0, tk.END)
        self.longitude_entry.delete(0, tk.END)

        self.route_optimized = False
        self.performance_mode = False
        self.refresh_points_list()
        self.draw_points()
        self.update_distance_label()
        self.improvement_label.config(text="Poprawa: 0.00")
        self.status_label.config(text="Status: dodano punkt")

    def load_sample_points(self):
        self.points = []
        self.point_counter = 0

        sample_positions = [
            ("Magazyn Legnica, ul. Nowodworska 30", "", 51.1876, 16.1752),
            ("Legnica, Rynek 24", "", 51.2074, 16.1619),
            ("Legnica, ul. Złotoryjska 65", "", 51.2054, 16.1489),
            ("Legnica, ul. Wrocławska 88", "", 51.2087, 16.1815),
            ("Legnica, ul. Gwiezdna 4", "", 51.2172, 16.1847),
            ("Legnica, ul. Jaworzyńska 43", "", 51.1989, 16.1554),
            ("Legnica, ul. Chojnowska 76", "", 51.2131, 16.1342)
        ]

        for address, comment, latitude, longitude in sample_positions:
            x, y = self.convert_gps_to_canvas_position(latitude, longitude)

            if self.point_counter == 0:
                point = Point(
                    name="Baza",
                    latitude=latitude,
                    longitude=longitude,
                    x=x,
                    y=y,
                    address=address,
                    comment=comment,
                    is_start=True
                )
            else:
                point = Point(
                    name=f"Punkt {self.point_counter}",
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
        self.refresh_points_list()
        self.draw_points()
        self.update_distance_label()
        self.improvement_label.config(text="Poprawa: 0.00")
        self.status_label.config(text="Status: wczytano przykładowe punkty")

    def clear_route(self):
        self.points = []
        self.point_counter = 0
        self.route_optimized = False
        self.performance_mode = False

        self.points_list.delete(0, tk.END)
        for marker in self.map_markers:
            marker.delete()

        self.map_markers = []

        if self.map_path:
            self.map_path.delete()
            self.map_path = None

        self.address_entry.delete(0, tk.END)
        self.comment_entry.delete(0, tk.END)
        self.latitude_entry.delete(0, tk.END)
        self.longitude_entry.delete(0, tk.END)

        self.distance_label.config(text="Dystans trasy: 0.00")
        self.improvement_label.config(text="Poprawa: 0.00")
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
            self.status_label.config(text="Status: baza nie jest punktem dostawy")
            return

        delivery_points = [point for point in self.points if not point.is_start]

        point_index = selected_index[0] - 1

        if point_index < 0 or point_index >= len(delivery_points):
            self.status_label.config(text="Status: nieprawidłowy punkt")
            return

        delivery_points[point_index].delivered = True

        self.refresh_points_list()
        self.draw_points()
        self.show_selected_point_details()
        self.status_label.config(text="Status: oznaczono paczkę jako dostarczoną")

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

    def draw_points(self):
        for marker in self.map_markers:
            marker.delete()

        self.map_markers = []

        if self.map_path:
            self.map_path.delete()
            self.map_path = None

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

            self.map_path = self.map_widget.set_path(
                straight_route,
                color="#2563eb",
                width=3
            )

        elif len(self.points) > 1 and self.route_optimized and not self.performance_mode:
            road_route_coordinates = []
            total_road_distance = 0

            full_route = self.points + [self.points[0]]

            for i in range(len(full_route) - 1):
                distance_km, route_coordinates = get_road_route_between_points(
                    full_route[i],
                    full_route[i + 1]
                )

                if route_coordinates:
                    if road_route_coordinates:
                        road_route_coordinates.extend(route_coordinates[1:])
                    else:
                        road_route_coordinates.extend(route_coordinates)

                    total_road_distance += distance_km
                else:
                    fallback_coordinates = [
                        (full_route[i].latitude, full_route[i].longitude),
                        (full_route[i + 1].latitude, full_route[i + 1].longitude)
                    ]

                    if road_route_coordinates:
                        road_route_coordinates.extend(fallback_coordinates[1:])
                    else:
                        road_route_coordinates.extend(fallback_coordinates)

            self.map_path = self.map_widget.set_path(
                road_route_coordinates,
                color="#dc2626",
                width=4
            )

            self.distance_label.config(text=f"Dystans trasy: {total_road_distance:.2f} km")

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

            marker = self.map_widget.set_marker(
                point.latitude,
                point.longitude,
                text=marker_text,
                marker_color_circle=marker_color,
                marker_color_outside=marker_color
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
        self.distance_label.config(text=f"Dystans trasy: {distance:.2f}")

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
        self.update_distance_label()

        improvement = before_distance - best_distance
        self.improvement_label.config(text=f"Poprawa: {improvement:.2f}")
        self.status_label.config(
            text=f"Status: zoptymalizowano trasę (poprawa {improvement:.2f})"
        )

    def export_route(self):
        if len(self.points) < 2:
            self.status_label.config(text="Status: za mało punktów do eksportu")
            return

        export_route_to_json(self.points, "route_result.json")
        self.status_label.config(text="Status: wyeksportowano trasę do JSON")

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

        info = tk.Label(
            legend_frame,
            text="Trasa jest rysowana na mapie OSM.",
            bg="white",
            fg="#6b7280",
            font=("Arial", 8)
        )
        info.pack(anchor="w", padx=10, pady=(4, 8))


def run_app():
    root = tk.Tk()
    app = RouteApp(root)
    root.mainloop()