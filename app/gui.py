import tkinter as tk


def run_app():
    root = tk.Tk()
    root.title("MSI - Problem Komiwojażera")
    root.geometry("1200x700")
    root.configure(bg="#f3f4f6")

    header = tk.Frame(root, bg="#1f2937", height=70)
    header.pack(fill="x")

    title = tk.Label(
        header,
        text="Optymalizacja Trasy Kuriera",
        bg="#1f2937",
        fg="white",
        font=("Arial", 20, "bold")
    )
    title.pack(pady=18)

    content = tk.Frame(root, bg="#f3f4f6")
    content.pack(fill="both", expand=True, padx=20, pady=20)

    left_panel = tk.Frame(content, bg="white", width=750, height=560)
    left_panel.pack(side="left", fill="both", expand=True)
    left_panel.pack_propagate(False)

    map_placeholder = tk.Label(
        left_panel,
        text="Tutaj będzie mapa / plansza trasy",
        bg="white",
        fg="#6b7280",
        font=("Arial", 16)
    )
    map_placeholder.place(relx=0.5, rely=0.5, anchor="center")

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
        pady=8
    )
    add_button.pack(anchor="w", padx=20, pady=(0, 20))

    points_list = tk.Listbox(
        right_panel,
        font=("Arial", 12),
        bd=0,
        highlightthickness=0
    )
    points_list.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    optimize_button = tk.Button(
        right_panel,
        text="Optymalizuj trasę",
        bg="#111827",
        fg="white",
        font=("Arial", 12, "bold"),
        relief="flat",
        padx=12,
        pady=10
    )
    optimize_button.pack(fill="x", padx=20, pady=(0, 20))

    root.mainloop()