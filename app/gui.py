import tkinter as tk
from app.models import Point
from app.optimizer import genetic_algorithm_route, calculate_total_distance


class RouteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MSI - Problem Komiwojażera")
        self.root.geometry("1200x700")
        self.root.configure(bg="#f3f4f6")

        self.points = []
        self.point_counter = 0

        self.canvas = None
        self.points_list = None
        self.distance_label = None
        self.improvement_label = None
        self.status_label = None

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

        right_panel = tk.Frame(content, bg="white", width=350, height=560)
        right_panel.pack(side="right", fill="y", padx=(20, 0))
        right_panel.pack_propagate(False)

        points_title = tk.Label(
            right_panel,
            text="Punkty trasy",
            bg="white",
            fg="#111827",
            font=("Arial", 16, "bold")
        )
        points_title.pack(anchor="w", padx=20, pady=(20, 10))

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
        add_button.pack(anchor="w", padx=20, pady=(0, 20))

        self.points_list = tk.Listbox(
            right_panel,
            font=("Arial", 12),
            bd=0,
            highlightthickness=0,
            height=12
        )
        self.points_list.pack(fill="x", expand=False, padx=20, pady=(0, 20))

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
        optimize_button.pack(fill="x", padx=20, pady=(0, 20))

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

    def add_point(self):
        predefined_positions = [
            (120, 100),
            (250, 180),
            (160, 320),
            (420, 360),
            (560, 220),
            (620, 120),
            (300, 420),
            (500, 100)
        ]

        if self.point_counter < len(predefined_positions):
            x, y = predefined_positions[self.point_counter]
        else:
            x = 100 + (self.point_counter * 30) % 600
            y = 100 + (self.point_counter * 40) % 400

        if self.point_counter == 0:
            point = Point(
                name="Baza",
                x=x,
                y=y,
                is_start=True
            )
        else:
            point = Point(
                name=f"Punkt {self.point_counter}",
                x=x,
                y=y,
                is_start=False
            )

        self.points.append(point)
        self.point_counter += 1

        self.refresh_points_list()
        self.draw_points()
        self.update_distance_label()
        self.improvement_label.config(text="Poprawa: 0.00")
        self.status_label.config(text="Status: dodano punkt")

    def refresh_points_list(self):
        self.points_list.delete(0, tk.END)

        route_index = 1

        for point in self.points:
            if point.is_start:
                self.points_list.insert(tk.END, "Start: Baza")
            else:
                self.points_list.insert(tk.END, f"{route_index}. {point.name}")
                route_index += 1

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
            fill_color = "#16a34a" if point.is_start else "#f59e0b"
            label = "S" if point.is_start else str(delivery_number)

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


def run_app():
    root = tk.Tk()
    app = RouteApp(root)
    root.mainloop()