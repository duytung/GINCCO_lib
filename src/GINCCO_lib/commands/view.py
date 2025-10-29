"""
GINCCO_lib.commands.view
------------------------
Tkinter-based NetCDF viewer with curvilinear grid support.

Usage:
    gincco view <datafile.nc> [--grid grid.nc]
"""

import tkinter as tk
from tkinter import messagebox, Listbox, END
import numpy as np
from netCDF4 import Dataset
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt


def get_grid_coords(grid_file, suffix):
    """Return (lon, lat) arrays from grid file, depending on suffix."""
    if grid_file is None:
        return None, None

    with Dataset(grid_file) as g:
        try:
            lon = g.variables[f"longitude_{suffix}"][:]
            lat = g.variables[f"latitude_{suffix}"][:]
            return lon, lat
        except KeyError:
            # fallback to _t
            lon = g.variables.get("longitude_t")
            lat = g.variables.get("latitude_t")
            if lon is not None and lat is not None:
                return lon[:], lat[:]
    return None, None


def open_file(datafile, gridfile=None):
    """Main viewer window."""
    root = tk.Tk()
    root.title(f"GINCCO Viewer - {datafile}")
    root.geometry("400x500")

    try:
        ds = Dataset(datafile)
    except Exception as e:
        messagebox.showerror("Error", f"Cannot open file:\n{e}")
        root.destroy()
        return

    tk.Label(root, text="Select a variable to plot").pack(pady=10)

    listbox = Listbox(root)
    for v in ds.variables.keys():
        listbox.insert(END, v)
    listbox.pack(fill="both", expand=True, padx=10, pady=10)

    def plot_var(event):
        varname = listbox.get(listbox.curselection())
        var = ds.variables[varname]
        data = np.squeeze(var[:])
        nd = data.ndim

        # detect suffix type (t, u, v, f)
        suffix = "t"
        for s in ["u", "v", "f", "t"]:
            if varname.lower().endswith(s):
                suffix = s
                break

        lon, lat = get_grid_coords(gridfile, suffix)

        plt.figure()
        if nd == 1:
            plt.plot(data)
            plt.xlabel(var.dimensions[0])
        elif nd == 2:
            if lon is not None and lat is not None and lon.shape == data.shape:
                plt.pcolormesh(lon, lat, data)
            else:
                plt.pcolormesh(data)
            plt.colorbar(label=getattr(var, "units", ""))
        else:
            messagebox.showinfo("Unsupported", f"{varname} has {nd} dimensions")
            plt.close()
            return

        plt.title(f"{varname} ({', '.join(var.dimensions)})")
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.tight_layout()
        plt.show()

    listbox.bind("<Double-Button-1>", plot_var)
    root.mainloop()


# === CLI interface ===
def register_subparser(subparser):
    subparser.add_argument("filename", help="Path to NetCDF data file")
    subparser.add_argument("--grid", dest="gridfile", help="Path to grid NetCDF file", default=None)
    subparser.set_defaults(func=main)


def main(args):
    datafile = args.filename
    gridfile = args.gridfile
    open_file(datafile, gridfile)
