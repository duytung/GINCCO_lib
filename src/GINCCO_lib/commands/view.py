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


def open_file(datafile, gridfile=None):
    root = tk.Tk()
    root.title(f"GINCCO Viewer - {datafile}")
    root.geometry("1000x700")

    # === Layout setup ===
    # Top frame (3/4)
    top_frame = tk.Frame(root)
    top_frame.pack(fill="both", expand=True)

    # Left: variable list
    left_frame = tk.Frame(top_frame, width=300)
    left_frame.pack(side="left", fill="y")

    tk.Label(left_frame, text="Variables").pack(pady=5)
    listbox = Listbox(left_frame)
    listbox.pack(fill="both", expand=True, padx=5, pady=5)

    # Right: map customization
    right_frame = tk.Frame(top_frame, bg="#f0f0f0", width=700)
    right_frame.pack(side="right", fill="both", expand=True)

    tk.Label(right_frame, text="Map Customization").pack(pady=5)

    # --- Controls ---
    tk.Label(right_frame, text="Min value:").pack()
    entry_min = tk.Entry(right_frame)
    entry_min.pack()

    tk.Label(right_frame, text="Max value:").pack()
    entry_max = tk.Entry(right_frame)
    entry_max.pack()

    tk.Label(right_frame, text="Color palette:").pack()
    cmap_var = tk.StringVar(value="jet")
    tk.OptionMenu(right_frame, cmap_var, "jet", "viridis", "plasma", "coolwarm").pack()

    # --- Bottom frame for log (1/4) ---
    bottom_frame = tk.Frame(root, height=150)
    bottom_frame.pack(fill="x", side="bottom")

    tk.Label(bottom_frame, text="Log Output").pack()
    log_box = tk.Text(bottom_frame, height=8, bg="black", fg="white")
    log_box.pack(fill="both", expand=True, padx=5, pady=5)

    # === Load file ===
    try:
        log_box.insert("end", f"Opening file: {datafile}\n")
        ds = Dataset(datafile)
        for v in ds.variables.keys():
            listbox.insert(END, v)
        log_box.insert("end", "File loaded successfully.\n")
    except Exception as e:
        messagebox.showerror("Error", f"Cannot open file:\n{e}")
        root.destroy()
        return

    # === Plot function ===
    def plot_var(event):
        varname = listbox.get(listbox.curselection())
        log_box.insert("end", f"Plotting variable: {varname}\n")
        log_box.see("end")

        try:
            var = ds.variables[varname]
            data = np.squeeze(var[:])
            nd = data.ndim

            # Detect suffix (_u, _v, _t, _f)
            suffix = "t"
            for s in ["u", "v", "f", "t"]:
                if varname.lower().endswith(s):
                    suffix = s
                    break

            lon, lat = get_grid_coords(gridfile, suffix)

            # Read map options
            vmin = entry_min.get()
            vmax = entry_max.get()
            cmap = cmap_var.get()

            vmin = float(vmin) if vmin else None
            vmax = float(vmax) if vmax else None

            if nd == 1:
                plt.figure()
                plt.plot(data)
                plt.title(varname)
                plt.show()

            elif nd == 2:
                if lon is not None and lat is not None and lon.shape == data.shape:
                    # Geographic plot with Basemap
                    fig, ax = plt.subplots(figsize=(7, 6))
                    lon_min, lon_max = np.nanmin(lon), np.nanmax(lon)
                    lat_min, lat_max = np.nanmin(lat), np.nanmax(lat)
                    m = Basemap(
                        projection="cyl",
                        llcrnrlon=lon_min,
                        urcrnrlon=lon_max,
                        llcrnrlat=lat_min,
                        urcrnrlat=lat_max,
                        resolution="i",
                        ax=ax
                    )
                    cs = m.pcolormesh(lon, lat, data, latlon=True, shading="auto",
                                      cmap=cmap, vmin=vmin, vmax=vmax)
                    m.drawcoastlines()
                    m.drawparallels(np.arange(-90, 91, 1), labels=[1,0,0,0], fontsize=8)
                    m.drawmeridians(np.arange(0, 361, 1), labels=[0,0,0,1], fontsize=8)
                    plt.colorbar(cs, label=getattr(var, "units", ""))
                    plt.title(varname)
                    plt.tight_layout()
                    plt.show()
                else:
                    # Fallback simple plot
                    plt.figure()
                    plt.pcolormesh(data, cmap=cmap, vmin=vmin, vmax=vmax)
                    plt.colorbar(label=getattr(var, "units", ""))
                    plt.title(varname)
                    plt.show()
            else:
                messagebox.showinfo("Unsupported", f"{varname} has {nd} dimensions")

            log_box.insert("end", "Plot complete.\n")
            log_box.see("end")

        except Exception as e:
            messagebox.showerror("Error", f"Cannot plot variable:\n{e}")
            log_box.insert("end", f"Error plotting variable {varname}: {e}\n")
            log_box.see("end")

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
