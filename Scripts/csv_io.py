import csv
import os
import time


def project_root(script_file):
    """
    Return the repo/project root directory.

    Historically the entry script lived in `Scripts/`, but in the modular version
    some callers live in `Scripts/scenes/`. We handle both cases.
    """
    here = os.path.abspath(os.path.dirname(script_file))
    base = os.path.basename(here).lower()
    if base == "scenes":
        return os.path.abspath(os.path.join(here, "..", ".."))
    return os.path.abspath(os.path.join(here, ".."))


def ask_open_csv_path(initialdir):
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        try:
            root.attributes("-topmost", True)
        except Exception:
            pass
        path = filedialog.askopenfilename(
            title="Open CSV (x,y)",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=initialdir,
        )
        root.destroy()
        return path if path else None
    except Exception:
        return None


def ask_save_csv_path(initialdir, default_name="points_export.csv"):
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        try:
            root.attributes("-topmost", True)
        except Exception:
            pass
        path = filedialog.asksaveasfilename(
            title="Save CSV",
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=initialdir,
        )
        root.destroy()
        return path if path else None
    except Exception:
        return None


def read_xy_from_csv(path):
    """Read (x,y) pairs from CSV. Header optional."""
    xy = []
    with open(path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or len(row) < 2:
                continue
            try:
                x = float(row[0])
                y = float(row[1])
            except ValueError:
                continue
            xy.append((x, y))
    return xy


def default_export_name(prefix="clustering_export"):
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.csv"


def write_points_csv(path, rows, header):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

