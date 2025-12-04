"""
Main viewer entry point.

This module provides a simple Tkinter-based GUI for exploring NetCDF data
using multiple tabs (Scalar, Vector, Combine, Section). It can be called
either directly as a Python module or via the gincco CLI.
"""

import os
import argparse
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from .tab_scalar import build_scalar_tab
from .tab_vector import build_vector_tab
from .tab_combine import build_combine_tab
from .tab_section import build_section_tab

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt


def register_subparser(subparser):
    """
    Register the 'view' subcommand options for the gincco CLI.

    Parameters
    ----------
    subparser : argparse.ArgumentParser
        The subparser corresponding to the 'view' command. This function
        adds the arguments required by the viewer, such as the data file
        and optional grid file.
    """
    subparser.add_argument(
        "filename",
        help="Path to data file (NetCDF).",
    )
    subparser.add_argument(
        "--grid",
        dest="gridfile",
        default=None,
        help="Path to grid file (default: try to find 'grid.nc' near the data file).",
    )


def bring_all_windows_front(root):
    """
    Bring the main Tk root window and all Toplevel windows to the front.

    Parameters
    ----------
    root : tk.Tk
        The main Tkinter root window.
    """
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


def open_file(datafile, gridfile=None):
    """
    Open the main viewer window for a given NetCDF data file.

    This function creates a Tkinter root window, sets up a Notebook with
    multiple tabs (Scalar, Vector, Combine, Section), and starts the Tk
    event loop.

    Parameters
    ----------
    datafile : str
        Path to the NetCDF data file to visualize.
    gridfile : str or None, optional
        Path to the grid file used by some tabs. If None, the viewer may
        still run but certain features (e.g., mapped plots) can be limited.
    """
    if not os.path.exists(datafile):
        messagebox.showerror("Error", f"Data file not found: {datafile}")
        return

    root = tk.Tk()
    root.title(f"GINCCO Viewer (experimental) - {os.path.basename(datafile)}")
    root.geometry("500x600")

    top_frame = tk.Frame(root)
    top_frame.pack(fill="both", expand=True)

    # Main notebook (tabbed interface)
    notebook = ttk.Notebook(top_frame)
    notebook.pack(fill="both", expand=True)

    # Build tabs. Each tab opens the dataset independently (keeps state isolated).
    scalar_tab_widgets = build_scalar_tab(notebook, datafile, gridfile)
    vector_tab_widgets = build_vector_tab(notebook, datafile, gridfile)
    combine_tab_widgets = build_combine_tab(notebook, datafile, gridfile)
    section_tab_widgets = build_section_tab(notebook, datafile, gridfile)

    notebook.add(scalar_tab_widgets["frame"], text="Scalar")
    notebook.add(vector_tab_widgets["frame"], text="Vector")
    notebook.add(combine_tab_widgets["frame"], text="Combine")
    notebook.add(section_tab_widgets["frame"], text="Section")

    root.mainloop()


def main(args=None):
    """
    Entry point for the viewer.

    This function can be called in two ways:

    1. Directly as a Python module:
           python -m GINCCO_lib.commands.view file.nc
       In this case `args` is None and local argparse is used.

    2. Via the gincco CLI:
           gincco view file.nc
       In this case the CLI passes an argparse.Namespace in `args`,
       and this function uses it directly.

    Parameters
    ----------
    args : argparse.Namespace or None, optional
        Parsed arguments. If None, arguments are parsed from the command
        line inside this function.
    """
    if args is None:
        # Called directly as a module: parse arguments here.
        p = argparse.ArgumentParser()
        p.add_argument("filename")
        p.add_argument(
            "--grid",
            dest="gridfile",
            default=None,
            help="Path to grid file (default: search for 'grid.nc' near datafile)",
        )
        ns = p.parse_args()
    else:
        # Called from gincco CLI: use the provided Namespace as-is.
        ns = args

    datafile = ns.filename

    # Ensure data file exists
    if not os.path.exists(datafile):
        print(f"Data file not found: {datafile}")
        return

    # 1) If user provided --grid, use it (if it exists)
    gridfile = None
    grid_arg = getattr(ns, "gridfile", None)
    if grid_arg:
        cand = grid_arg
        if not os.path.isabs(cand):
            # Allow relative paths (relative to current working directory)
            cand = os.path.abspath(cand)
        if os.path.exists(cand):
            gridfile = cand
        else:
            print(f"Warning: provided grid file not found: {grid_arg} (ignored)")

    # 2) If no --grid or it didn't exist, try to find grid.nc next to datafile
    if gridfile is None:
        data_dir = os.path.dirname(os.path.abspath(datafile)) or "."
        candidate = os.path.join(data_dir, "grid.nc")
        if os.path.exists(candidate):
            gridfile = candidate

    # 3) Optionally search parent directories (up to max_levels) for grid.nc
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

    # 4) Last resort: try 'grid.nc' in the current working directory
    if gridfile is None:
        candidate = os.path.abspath("grid.nc")
        if os.path.exists(candidate):
            gridfile = candidate

    if gridfile:
        print(f"Using grid file: {gridfile}")
    else:
        print("No grid file found; running without explicit grid (some features may be unavailable).")

    open_file(datafile, gridfile)


if __name__ == "__main__":
    main()
