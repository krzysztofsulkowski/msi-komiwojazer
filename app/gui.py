import tkinter as tk
import random
import time
from app.models import Point
from app.optimizer import genetic_algorithm_route, calculate_total_distance
from app.exporter import export_route_to_json


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

        self.canvas = tk.Canvas(
            left_panel,
            bg="#eef2f7",
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True, padx=20, pady=20)

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

        legend_title = tk.Label(
            right_panel,
            text="Legenda",
            bg="white",
            fg="#111827",
            font=("Arial", 12, "bold")
        )
        legend_title.pack(anchor="w", padx=20, pady=(10, 6))

        legend_route = tk.Label(
            right_panel,
            text="— pełna linia: przejazd między punktami",
            bg="white",
            fg="#2563eb",
            font=("Arial", 10)
        )
        legend_route.pack(anchor="w", padx=20)

        legend_return = tk.Label(
            right_panel,
            text="— przerywana linia: powrót do bazy",
            bg="white",
            fg="#60a5fa",
            font=("Arial", 10)
        )
        legend_return.pack(anchor="w", padx=20, pady=(0, 10))

    def convert_gps_to_canvas_position(self, latitude, longitude):
        min_latitude = 51.18
        max_latitude = 51.23
        min_longitude = 16.11
        max_longitude = 16.21

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        margin = 60

        usable_width = canvas_width - 2 * margin
        usable_height = canvas_height - 2 * margin

        x = margin + ((longitude - min_longitude) / (max_longitude - min_longitude)) * usable_width
        y = margin + ((max_latitude - latitude) / (max_latitude - min_latitude)) * usable_height

        return x, y

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

        self.refresh_points_list()
        self.draw_points()
        self.update_distance_label()
        self.improvement_label.config(text="Poprawa: 0.00")
        self.status_label.config(text="Status: wczytano przykładowe punkty")

    def clear_route(self):
        self.points = []
        self.point_counter = 0

        self.points_list.delete(0, tk.END)
        self.canvas.delete("all")

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
        self.canvas.delete("all")

        for i in range(len(self.points) - 1):
            p1 = self.points[i]
            p2 = self.points[i + 1]

            self.canvas.create_line(
                p1.x, p1.y,
                p2.x, p2.y,
                fill="#2563eb",
                width=3
            )

        if len(self.points) > 1:
            last_point = self.points[-1]
            start_point = self.points[0]

            self.canvas.create_line(
                last_point.x, last_point.y,
                start_point.x, start_point.y,
                fill="#93c5fd",
                width=2,
                dash=(6, 4)
            )

        delivery_number = 1

        for point in self.points:
            radius = 18

            if point.is_start:
                fill_color = "#16a34a"
                label = "S"
            elif point.delivered:
                fill_color = "#9ca3af"
                label = str(delivery_number)
            else:
                fill_color = "#f59e0b"
                label = str(delivery_number)

            self.canvas.create_oval(
                point.x - radius,
                point.y - radius,
                point.x + radius,
                point.y + radius,
                fill=fill_color,
                outline=""
            )

            self.canvas.create_text(
                point.x,
                point.y,
                text=label,
                fill="white",
                font=("Arial", 11, "bold")
            )

            if point.delivered and not point.is_start:
                self.canvas.create_text(
                    point.x + 14,
                    point.y - 14,
                    text="✓",
                    fill="#16a34a",
                    font=("Arial", 12, "bold")
                )

            if not point.is_start:
                delivery_number += 1

    def update_distance_label(self):
        distance = calculate_total_distance(self.points)
        self.distance_label.config(text=f"Dystans trasy: {distance:.2f}")

    def optimize_route(self):
        if len(self.points) < 2:
            self.status_label.config(text="Status: za mało punktów do optymalizacji")
            return

        before_distance = calculate_total_distance(self.points)
        best_route, best_distance = genetic_algorithm_route(self.points)

        self.points = best_route
        self.refresh_points_list()
        self.draw_points()
        self.update_distance_label()

        improvement = before_distance - best_distance
        self.improvement_label.config(text=f"Poprawa: {improvement:.2f}")
        self.status_label.config(text="Status: trasa zoptymalizowana")

    def export_route(self):
        if len(self.points) < 2:
            self.status_label.config(text="Status: za mało punktów do eksportu")
            return

        export_route_to_json(self.points, "route_result.json")
        self.status_label.config(text="Status: wyeksportowano trasę do JSON")

    def run_performance_test(self):
        self.points = []
        self.point_counter = 0

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
        self.refresh_points_list()
        self.draw_points()
        self.update_distance_label()
        self.improvement_label.config(text="Poprawa: test wydajności")

        self.status_label.config(
            text=f"Status: 100 punktów zoptymalizowano w {elapsed_time:.2f} s"
        )


def run_app():
    root = tk.Tk()
    app = RouteApp(root)
    root.mainloop()