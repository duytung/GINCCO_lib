
"""
Main viewer (simplified)
"""
import os
import argparse
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from .tab_scalar import build_scalar_tab
from .tab_vector import build_vector_tab
from .tab_combine import build_combine_tab   

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt




def bring_all_windows_front(root):
    """Bring root + all Toplevel windows to the front."""
    try:
        root.deiconify()
        root.lift()
        root.focus_force()
    except Exception:
        pass

    for w in root.winfo_children():
        if isinstance(w, tk.Toplevel):
            try:
                w.deiconify()
                w.lift()
            except Exception:
                pass


def on_any_focus_in(event):
    """Whenever ANY widget in the app gains focus, bring all windows front."""
    root = event.widget.winfo_toplevel()
    bring_all_windows_front(root)






def open_file(datafile, gridfile=None):
    if not os.path.exists(datafile):
        messagebox.showerror("Error", f"Data file not found: {datafile}")
        return

    root = tk.Tk()
    root.title(f"GINCCO Viewer (experimental) - {os.path.basename(datafile)}")
    root.geometry("500x500")

    root.bind_all("<FocusIn>", on_any_focus_in)


    top_frame = tk.Frame(root)
    top_frame.pack(fill="both", expand=True)

    # notebook on the right (single area)
    notebook = ttk.Notebook(top_frame)
    notebook.pack(fill="both", expand=True)

    # Build tabs. Each tab loads the dataset independently (keeps them isolated).
    scalar_tab_widgets = build_scalar_tab(notebook, datafile, gridfile)
    vector_tab_widgets = build_vector_tab(notebook, datafile, gridfile)
    combine_tab_widgets = build_combine_tab(notebook, datafile, gridfile)


    notebook.add(scalar_tab_widgets['frame'], text="Scalar")
    notebook.add(vector_tab_widgets['frame'], text="Vector")
    notebook.add(combine_tab_widgets['frame'], text="Combine")  # <--- tab mới


    root.mainloop()

def main():
    p = argparse.ArgumentParser()
    p.add_argument('filename')
    p.add_argument('--grid', dest='gridfile', default=None,
                   help="Path to grid file (default: search for 'grid.nc' near datafile)")
    ns = p.parse_args()

    datafile = ns.filename

    # ensure datafile exists
    if not os.path.exists(datafile):
        print(f"Data file not found: {datafile}")
        return

    # 1) if user provided --grid, use it (if exists)
    gridfile = None
    if ns.gridfile:
        cand = ns.gridfile
        if not os.path.isabs(cand):
            # allow relative to current cwd
            cand = os.path.abspath(cand)
        if os.path.exists(cand):
            gridfile = cand
        else:
            print(f"Warning: provided grid file not found: {ns.gridfile} (ignored)")

    # 2) If no --grid or it didn't exist, try to find grid.nc next to datafile
    if gridfile is None:
        data_dir = os.path.dirname(os.path.abspath(datafile)) or "."
        candidate = os.path.join(data_dir, "grid.nc")
        if os.path.exists(candidate):
            gridfile = candidate

    # 3) Optionally search up parent directories (up to max_levels)
    if gridfile is None:
        max_levels = 2
        cur = os.path.abspath(os.path.dirname(datafile))
        for _ in range(max_levels):
            candidate = os.path.join(cur, "grid.nc")
            if os.path.exists(candidate):
                gridfile = candidate
                break
            parent = os.path.dirname(cur)
            if parent == cur:
                break
            cur = parent

    if gridfile is None:
        # last resort: try 'grid.nc' in cwd (keeps some compatibility)
        candidate = os.path.abspath("grid.nc")
        if os.path.exists(candidate):
            gridfile = candidate

    if gridfile:
        print(f"Using grid file: {gridfile}")
    else:
        print("No grid file found; running without explicit grid (some features may be unavailable).")

    open_file(datafile, gridfile)


if __name__ == '__main__':
    main()
