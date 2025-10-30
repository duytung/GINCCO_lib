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


def draw_plot(varname, var, lon, lat, options, log_box, state=None, is_redraw=False):
    """
    Draw map or line depending on variable dimension and user options.
    options: dict with keys ('vmin', 'vmax', 'cmap', 'lon_min', 'lon_max', 'lat_min', 'lat_max', 'layer')
    """

    #  Chỉ đóng figure cũ nếu là redraw
    if is_redraw and state and state.get("fig") is not None:
        plt.close(state["fig"])
        state["fig"] = None

    #  Ghi log "đang vẽ"
    log_box.insert("end", f"Drawing {varname}... please wait\n")
    log_box.see("end")
    log_box.update_idletasks()  #  cập nhật GUI ngay lập tức

    try:
        data = np.squeeze(var[:])
        nd = data.ndim

        # If 3D → pick selected layer
        if nd == 3:
            layer = options.get("layer", 0)
            data = data[layer, :, :]

        cmap = options.get("cmap", "jet")
        vmin = options.get("vmin", None)
        vmax = options.get("vmax", None)
        lon_min = options.get("lon_min", None)
        lon_max = options.get("lon_max", None)
        lat_min = options.get("lat_min", None)
        lat_max = options.get("lat_max", None)

        if nd == 1:
            plt.figure()
            plt.plot(data)
            plt.title(varname)
            log_box.insert("end", f"Done drawing {varname} \n")
            log_box.see("end")
            log_box.update_idletasks()
            plt.show()

        elif nd >= 2:
            if lon is not None and lat is not None and lon.shape == data.shape:
                fig, ax = plt.subplots(figsize=(7, 6))
                state["fig"] = fig
                lon_min = lon_min or np.nanmin(lon)
                lon_max = lon_max or np.nanmax(lon)
                lat_min = lat_min or np.nanmin(lat)
                lat_max = lat_max or np.nanmax(lat)

                m = Basemap(
                    projection="cyl",
                    llcrnrlon=lon_min,
                    urcrnrlon=lon_max,
                    llcrnrlat=lat_min,
                    urcrnrlat=lat_max,
                    resolution="i",
                    ax=ax
                )

                cs = m.pcolormesh(
                    lon, lat, data,
                    latlon=True, shading="auto",
                    cmap=cmap, vmin=vmin, vmax=vmax
                )
                m.drawcoastlines()
                m.drawparallels(np.arange(-90, 91, 1), labels=[1, 0, 0, 0], fontsize=8)
                m.drawmeridians(np.arange(0, 361, 1), labels=[0, 0, 0, 1], fontsize=8)
                plt.colorbar(cs, label=getattr(var, "units", ""))
                plt.title(varname)
                plt.tight_layout()
                log_box.insert("end", f"Done drawing {varname} \n")
                log_box.see("end")
                log_box.update_idletasks()
                plt.show()
            else:
                plt.figure()
                plt.pcolormesh(data, cmap=cmap, vmin=vmin, vmax=vmax)
                plt.colorbar(label=getattr(var, "units", ""))
                plt.title(varname)
                log_box.insert("end", f"Done drawing {varname} \n")
                log_box.see("end")
                log_box.update_idletasks()
                plt.show()

        log_box.insert("end", f"Plot complete: {varname}\n")
        log_box.see("end")

    except Exception as e:
        log_box.insert("end", f"Error plotting variable {varname}: {e}\n")
        log_box.see("end")
        messagebox.showerror("Plot Error", str(e))


def open_file(datafile, gridfile=None):
    root = tk.Tk()
    root.title(f"GINCCO Viewer - {datafile}")
    root.geometry("550x600")

    def on_close():
        import matplotlib.pyplot as plt
        plt.close('all')  #  đóng toàn bộ cửa sổ plot đang mở
        root.destroy()    #  đóng cửa sổ chính của Tkinter

    root.protocol("WM_DELETE_WINDOW", on_close)

    # === Layout ===
    top_frame = tk.Frame(root)
    top_frame.pack(fill="both", expand=True)

    left_frame = tk.Frame(top_frame, width=300)
    left_frame.pack(side="left", fill="y")

    right_frame = tk.Frame(top_frame, bg="#f0f0f0", width=750)
    right_frame.pack(side="right", fill="both", expand=True)

    bottom_frame = tk.Frame(root, height=150)
    bottom_frame.pack(fill="x", side="bottom")

    # === Left: variable list ===
    tk.Label(left_frame, text="Variables").pack(pady=5)
    listbox = Listbox(left_frame)
    listbox.pack(fill="both", expand=True, padx=5, pady=5)

    # === Right: controls ===
    tk.Label(right_frame, text="Map Customization", font=("Arial", 12, "bold")).pack(pady=5)

    entry_min = tk.Entry(right_frame); entry_max = tk.Entry(right_frame)
    tk.Label(right_frame, text="Min value").pack(); entry_min.pack()
    tk.Label(right_frame, text="Max value").pack(); entry_max.pack()

    cmap_var = tk.StringVar(value="jet")
    tk.Label(right_frame, text="Color palette").pack()
    tk.OptionMenu(right_frame, cmap_var, "jet", "viridis", "plasma", "coolwarm").pack()

    # Layer select
    tk.Label(right_frame, text="Layer select").pack()
    layer_var = tk.StringVar(value="0")
    layer_menu = tk.OptionMenu(right_frame, layer_var, "0")  # default
    layer_menu.pack()

    # lon/lat bounds
    tk.Label(right_frame, text="Lon/Lat bounds").pack(pady=5)
    lon_min_e = tk.Entry(right_frame); lon_max_e = tk.Entry(right_frame)
    lat_min_e = tk.Entry(right_frame); lat_max_e = tk.Entry(right_frame)
    for w, lbl in [(lon_min_e, "Lon min"), (lon_max_e, "Lon max"),
                   (lat_min_e, "Lat min"), (lat_max_e, "Lat max")]:
        tk.Label(right_frame, text=lbl).pack()
        w.pack()

    # Redraw button
    redraw_btn = tk.Button(right_frame, text="Redraw Map", bg="lightblue")
    redraw_btn.pack(pady=10)

    # === Bottom: log ===
    tk.Label(bottom_frame, text="Log Output").pack()
    log_box = tk.Text(bottom_frame, height=8, bg="black", fg="white")
    log_box.pack(fill="both", expand=True, padx=5, pady=5)

    # === Load NetCDF ===
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

    # === Handlers ===
    state = {"varname": None, "var": None, "lon": None, "lat": None, "suffix": "t", "fig": None}


    def on_var_select(event):
        varname = listbox.get(listbox.curselection())
        state["varname"] = varname
        var = ds.variables[varname]
        state["var"] = var
        data = np.squeeze(var[:])
        nd = data.ndim

        suffix = "t"
        for s in ["u", "v", "f", "t"]:
            if varname.lower().endswith(s):
                suffix = s
                break
        state["suffix"] = suffix
        lon, lat = get_grid_coords(gridfile, suffix)
        state["lon"], state["lat"] = lon, lat

        # Update layer menu if 3D
        menu = layer_menu["menu"]
        menu.delete(0, "end")
        if nd == 3:
            for i in range(data.shape[0]):
                menu.add_command(label=str(i), command=lambda v=i: layer_var.set(str(v)))
            layer_var.set("0")
        else:
            menu.add_command(label="0", command=lambda: layer_var.set("0"))
            layer_var.set("0")

        log_box.insert("end", f"Selected variable: {varname} ({nd}D)\n")
        log_box.see("end")

        # --- Auto-plot immediately on first double-click ---
        opts = {
            "vmin": None, "vmax": None, "cmap": cmap_var.get(),
            "layer": int(layer_var.get()), "lon_min": None, "lon_max": None,
            "lat_min": None, "lat_max": None
        }
        draw_plot(state["varname"], state["var"], state["lon"], state["lat"], opts, log_box, state)

    def redraw():
        if not state["var"]:
            messagebox.showinfo("Info", "Please select a variable first.")
            return

        opts = {
            "vmin": float(entry_min.get()) if entry_min.get() else None,
            "vmax": float(entry_max.get()) if entry_max.get() else None,
            "cmap": cmap_var.get(),
            "layer": int(layer_var.get()),
            "lon_min": float(lon_min_e.get()) if lon_min_e.get() else None,
            "lon_max": float(lon_max_e.get()) if lon_max_e.get() else None,
            "lat_min": float(lat_min_e.get()) if lat_min_e.get() else None,
            "lat_max": float(lat_max_e.get()) if lat_max_e.get() else None,
        }

        log_box.insert("end", f"Redrawing {state['varname']}...\n")
        log_box.see("end")
        draw_plot(state["varname"], state["var"], state["lon"], state["lat"], opts, log_box, state)

    listbox.bind("<Double-Button-1>", on_var_select)
    redraw_btn.config(command=redraw)
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
