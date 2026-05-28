"""Redesigned Tk viewer prototype for GINCCO NetCDF files."""

import argparse
import os
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

import matplotlib
matplotlib.use("TkAgg")

from .map_tabs import CombineTab, ScalarTab, VectorTab
from .section_tab import SectionTab


def _find_grid_file(datafile, grid_arg=None):
    if grid_arg:
        candidate = grid_arg if os.path.isabs(grid_arg) else os.path.abspath(grid_arg)
        if os.path.exists(candidate):
            return candidate
        print("Warning: provided grid file not found: {} (ignored)".format(grid_arg))

    data_dir = os.path.dirname(os.path.abspath(datafile)) or "."
    candidates = [os.path.join(data_dir, "grid.nc"), os.path.abspath("grid.nc")]

    cur = data_dir
    for _ in range(2):
        candidates.append(os.path.join(cur, "grid.nc"))
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return None


def _configure_style(root):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("TFrame", padding=0)
    style.configure("TNotebook.Tab", font=("TkDefaultFont", 10, "bold"), padding=(12, 6))
    style.configure("Panel.TLabelframe", padding=10)
    style.configure("Panel.TLabelframe.Label", font=("TkDefaultFont", 10, "bold"))
    style.configure("Primary.TButton", padding=(12, 6))
    style.configure("Status.TLabel", padding=(8, 4))


def open_file(datafile, gridfile=None):
    if not os.path.exists(datafile):
        messagebox.showerror("Error", "Data file not found: {}".format(datafile))
        return

    root = tk.Tk()
    _configure_style(root)
    root.title("GINCCO Viewer 2 - {}".format(os.path.basename(datafile)))
    root.geometry("560x760")
    root.minsize(520, 620)

    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    notebook = ttk.Notebook(root)
    notebook.grid(row=0, column=0, sticky="nsew")

    status_var = tk.StringVar(value="Ready")

    scalar_tab = ScalarTab(notebook, datafile, gridfile, status_var)
    vector_tab = VectorTab(notebook, datafile, gridfile, status_var)
    combine_tab = CombineTab(notebook, datafile, gridfile, status_var)
    section_tab = SectionTab(notebook, datafile, gridfile, status_var)

    notebook.add(scalar_tab.frame, text="Scalar")
    notebook.add(vector_tab.frame, text="Vector")
    notebook.add(combine_tab.frame, text="Combine")
    notebook.add(section_tab.frame, text="Section")

    status = ttk.Label(root, textvariable=status_var, style="Status.TLabel", anchor="w")
    status.grid(row=1, column=0, sticky="ew")

    root.mainloop()


def main(args=None):
    if args is None:
        parser = argparse.ArgumentParser()
        parser.add_argument("filename")
        parser.add_argument("--grid", dest="gridfile", default=None)
        ns = parser.parse_args()
    else:
        ns = args

    datafile = ns.filename
    if not os.path.exists(datafile):
        print("Data file not found: {}".format(datafile))
        return

    gridfile = _find_grid_file(datafile, getattr(ns, "gridfile", None))
    if gridfile:
        print("Using grid file: {}".format(gridfile))
    else:
        print("No grid file found; section plotting will be limited.")

    open_file(datafile, gridfile)


if __name__ == "__main__":
    main()
