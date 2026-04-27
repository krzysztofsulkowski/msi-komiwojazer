import tkinter as tk
import tkintermapview
import json
import webbrowser
from tkinter import filedialog, messagebox
from app.models import Point
from app.optimizer import genetic_algorithm_route, calculate_total_distance

class RouteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MSI - Problem Komiwojażera")
        self.root.geometry("1250x800")
        self.points = []
        self.path = None
        self.build_layout()

    def build_layout(self):
        # Panel Lewy (Mapa)
        self.map_widget = tkintermapview.TkinterMapView(self.root, width=700, height=700)
        self.map_widget.pack(side="left", fill="both", expand=True)
        self.map_widget.set_position(52.2297, 21.0122) 
        self.map_widget.set_zoom(11)

        # Panel Prawy (Kontrola)
        right_panel = tk.Frame(self.root, width=300, bg="#f3f4f6", padx=20)
        right_panel.pack(side="right", fill="y")

        tk.Label(right_panel, text="Optymalizacja Trasy Kuriera", font=("Arial", 16, "bold"), bg="#f3f4f6").pack(pady=20)

        tk.Button(right_panel, text="📂 Wczytaj json", bg="#2563eb", fg="white", font=("Arial", 10, "bold"), 
                  command=self.load_json).pack(fill="x", pady=10)

        self.opt_button = tk.Button(right_panel, text="Optymalizuj trasę", bg="#111827", fg="white", 
                                    state="disabled", command=self.optimize_route)
        self.opt_button.pack(fill="x", pady=10)

        self.dist_label = tk.Label(right_panel, text="Dystans: 0.00 km", bg="#f3f4f6")
        self.dist_label.pack(pady=10)

        self.status_label = tk.Label(right_panel, text="Status: Czekam na plik", bg="#f3f4f6", fg="gray")
        self.status_label.pack(side="bottom", pady=20)

    def load_json(self):
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not path: return
        try:
            with open(path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            self.points = []
            self.map_widget.delete_all_marker()
            if self.path: self.path.delete()

            d_lat, d_lon = data['depot']
            baza = Point(name="Baza", lat=d_lat, lon=d_lon, is_start=True)
            self.points.append(baza) 
            
            self.map_widget.set_marker(d_lat, d_lon, text="Baza")

            for loc in data['locations']:
                l_lat, l_lon = loc['coords']
                l_id = loc['id']
                nowy_punkt = Point(name=f"P{l_id}", lat=l_lat, lon=l_lon, is_start=False)
                self.points.append(nowy_punkt) 
                self.map_widget.set_marker(l_lat, l_lon, text=f"ID:{l_id}")

            self.opt_button.config(state="normal")
            
            self.map_widget.set_position(d_lat, d_lon)
            dystans = calculate_total_distance(self.points)
            self.dist_label.config(text=f"Dystans: {dystans:.2f} km")
            self.status_label.config(text=f"Wczytano {len(self.points)} punktów", fg="green")

        except Exception as e:
            print(f"Błąd logiki: {e}")
            messagebox.showerror("Błąd", f"Wystąpił błąd podczas wczytywania: {e}")
            
    def optimize_route(self):
        self.status_label.config(text="AI liczy...")
        self.root.update()
        
        best_route, best_dist = genetic_algorithm_route(self.points)
        self.points = best_route
        
        coords = [(p.lat, p.lon) for p in self.points]
        coords.append((self.points[0].lat, self.points[0].lon))
        
        if self.path: self.path.delete()
        self.path = self.map_widget.set_path(coords, color="blue", width=3)
        
        self.dist_label.config(text=f"Dystans: {best_dist:.2f} km")
        self.status_label.config(text="Zoptymalizowano!", fg="blue")

def run_app():
    root = tk.Tk()
    app = RouteApp(root)
    root.mainloop()