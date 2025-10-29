"""
GINCCO_lib.commands.view
------------------------
Tkinter-based NetCDF viewer with Basemap projection support.
Maintains correct latitude/longitude aspect ratio.
"""

import os
import tkinter as tk
from tkinter import messagebox, Listbox, END
import numpy as np
from netCDF4 import Dataset
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap


def get_grid_coords(grid_file, suffix):
    """Return (lon, lat) arrays from grid file, depending on suffix."""
    if not grid_file or not os.path.exists(grid_file):
        return None, None

    with Dataset(grid_file) as g:
        try:
            lon = g.variables[f"longitude_{suffix}"][:]
            lat = g.variables[f"latitude_{suffix}"][:]
        except KeyError:
            lon = g.variables.get("longitude_t")
            lat = g.variables.get("latitude_t")
            if lon is not None and lat is not None:
                lon, lat = lon[:], lat[:]
            else:
                lon, lat = None, None
    return lon, lat


def plot_with_basemap(lon, lat, data, title, units=None):
    """Plot a 2D field on a geographic projection using Basemap."""
    fig, ax = plt.subplots(figsize=(7, 6))

    # Compute map bounds
    lon_min, lon_max = np.nanmin(lon), np.nanmax(lon)
    lat_min, lat_max = np.nanmin(lat), np.nanmax(lat)

    # Set up Basemap
    m = Basemap(
        projection="cyl",
        llcrnrlon=lon_min,
        urcrnrlon=lon_max,
        llcrnrlat=lat_min,
        urcrnrlat=lat_max,
        resolution="i",
        ax=ax
    )

    # Plot data
    cs = m.pcolormesh(lon, lat, data, latlon=True, shading="auto")
    m.drawcoastlines()
    m.drawparallels(np.arange(-90, 91, 1), labels=[1, 0, 0, 0], fontsize=8)
    m.drawmeridians(np.arange(0, 361, 1), labels=[0, 0, 0, 1], fontsize=8)
    plt.colorbar(cs, label=units or "")
    plt.title(title)
    plt.tight_layout()
    plt.show()


def open_file(datafile, gridfile=None):
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

        suffix = "t"
        for s in ["u", "v", "f", "t"]:
            if varname.lower().endswith(s):
                suffix = s
                break

        lon, lat = get_grid_coords(gridfile, suffix)

        if nd == 1:
            plt.figure()
            plt.plot(data)
            plt.title(varname)
            plt.show()
        elif nd == 2:
            if lon is not None and lat is not None and lon.shape == data.shape:
                plot_with_basemap(lon, lat, data, varname, getattr(var, "units", ""))
            else:
                plt.figure()
                plt.pcolormesh(data)
                plt.colorbar(label=getattr(var, "units", ""))
                plt.title(varname)
                plt.show()
        else:
            messagebox.showinfo("Unsupported", f"{varname} has {nd} dimensions")

    listbox.bind("<Double-Button-1>", plot_var)
    root.mainloop()


# === CLI ===
def register_subparser(subparser):
    subparser.add_argument("filename", help="Path to NetCDF data file")
    subparser.add_argument(
        "--grid",
        dest="gridfile",
        help="Path to grid NetCDF file (default: grid.nc if exists)",
        default="grid.nc"
    )
    subparser.set_defaults(func=main)


def main(args):
    datafile = args.filename
    gridfile = args.gridfile
    if not os.path.exists(gridfile):
        gridfile = None
    open_file(datafile, gridfile)
