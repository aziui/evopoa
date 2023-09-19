import tkinter as tk
from tkinter import ttk, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime
import json
import csv

class WeightApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Suivi de poids")

        # Stylisation
        self.root.configure(bg='#f3f4f6')
        style = ttk.Style()
        style.configure("TButton", padding=6, relief="flat", background="#92a8d1")
        style.configure("TLabel", background='#f3f4f6', font=('Arial', 12))
        style.configure("TEntry", relief="flat", font=('Arial', 12))

        self.weights = []
        self.load_data()

        ttk.Label(root, text="Entrez votre poids (à jeun):").pack(pady=10)
        self.weight_entry = ttk.Entry(root)
        self.weight_entry.pack(pady=10, padx=50, ipady=5)

        ttk.Label(root, text="Date (jour/mois/année):").pack(pady=10)
        self.date_entry = ttk.Entry(root)
        self.date_entry.pack(pady=10, padx=50, ipady=5)
        
        ttk.Button(root, text="Enregistrer", command=self.save_weight).pack(pady=5)
        ttk.Button(root, text="Exporter en CSV", command=self.export_csv).pack(pady=5)
        ttk.Button(root, text="Importer de CSV", command=self.import_csv).pack(pady=5)

        self.canvas = FigureCanvasTkAgg(self.get_figure(), master=root)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(pady=20, padx=30)

        self.canvas.mpl_connect('button_press_event', self.on_plot_click)

        self.stats_label = ttk.Label(root, text="")
        self.stats_label.pack(pady=20)

    def load_data(self):
        try:
            with open("weights.json", "r") as f:
                self.weights = json.load(f)
        except FileNotFoundError:
            self.weights = []

    def save_data(self):
        with open("weights.json", "w") as f:
            json.dump(self.weights, f)

    def save_weight(self):
        weight = float(self.weight_entry.get())
        date_str = self.date_entry.get()  
        
        if not date_str:  # Si aucune date n'est entrée, utilisez la date actuelle.
            date_str = datetime.datetime.now().strftime('%d/%m/%Y')
        
        self.weights.append({"date": date_str, "weight": weight})

        self.save_data()
        self.update_stats()
        self.canvas.figure = self.get_figure()
        self.canvas.draw()

    def on_plot_click(self, event):
    # Chercher le point le plus proche
        min_distance = float('inf')
        nearest_point_index = None

        for i, (date, weight) in enumerate(self.weights):
            distance = (event.xdata - date.timestamp())**2 + (event.ydata - weight)**2
            if distance < min_distance:
                min_distance = distance
                nearest_point_index = i

        # Si le clic est suffisamment proche d'un point, ouvrez une boîte de dialogue de modification
        if nearest_point_index is not None and min_distance < 100000:  # Ajustez la valeur si nécessaire
            self.show_edit_dialog(nearest_point_index)

    def show_edit_dialog(self, point_index):
        edit_win = tk.Toplevel(self.root)
        edit_win.title("Modifier le point")

        ttk.Label(edit_win, text="Date (jour/mois/année):").pack(pady=10)
        date_entry = ttk.Entry(edit_win)
        date_entry.insert(0, self.weights[point_index]["date"])
        date_entry.pack(pady=10)

        ttk.Label(edit_win, text="Poids:").pack(pady=10)
        weight_entry = ttk.Entry(edit_win)
        weight_entry.insert(0, self.weights[point_index]["weight"])
        weight_entry.pack(pady=10)

        def save_changes():
            self.weights[point_index]["date"] = date_entry.get()
            self.weights[point_index]["weight"] = float(weight_entry.get())
            self.save_data()
            self.canvas.figure = self.get_figure()
            self.canvas.draw()
            edit_win.destroy()

        ttk.Button(edit_win, text="Sauvegarder les modifications", command=save_changes).pack(pady=20)

    def get_figure(self):
        dates = []
        new_weights = []  # Liste pour stocker les poids des dates valides
        for entry in self.weights:
            try:
                date_obj = datetime.datetime.strptime(entry["date"], '%d/%m/%Y')
                dates.append(date_obj.date())
                new_weights.append(entry["weight"])  # Ajoutez le poids à la nouvelle liste
            except ValueError:
                # Si la date est au mauvais format, imprimez un avertissement
                print(f"Format de date inconnu pour {entry['date']}. Ignoré.")

        self.weights = [{"date": str(d), "weight": w} for d, w in zip(dates, new_weights)]  # Mettez à jour la liste des poids
        self.save_data()  # Sauvegardez la liste mise à jour

        weights = [entry["weight"] for entry in self.weights]

        fig, ax = plt.subplots(figsize=(5, 3))
        
        # Color points based on weight
        colors = ['red' if weight >= 100 else 'blue' for weight in weights]
        
        ax.scatter(dates, weights, c=colors)
        ax.plot(dates, weights, '-o', color="gray")
        ax.set_title('Évolution du poids')
        ax.set_xlabel('Date')
        ax.set_ylabel('Poids (kg)')
        fig.autofmt_xdate()

        return fig

    def update_stats(self):
        if not self.weights:
            return

        avg_weight = sum(entry["weight"] for entry in self.weights) / len(self.weights)
        self.stats_label.config(text=f"Poids moyen: {avg_weight:.2f} kg")
    
    def export_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")])
        if not file_path:
            return
        with open(file_path, "w", newline='') as csvfile:
            fieldnames = ['date', 'weight']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for entry in self.weights:
                writer.writerow(entry)
    
    def import_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")])
        if not file_path:
            return
        with open(file_path, "r", newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            
            self.weights.extend(reader)
            self.update_stats()
            self.canvas.figure = self.get_figure()
            self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = WeightApp(root)
    root.mainloop()