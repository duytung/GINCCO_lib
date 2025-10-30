"""
GINCCO_lib.commands.view
------------------------
Tkinter-based NetCDF viewer with Basemap projection support.
Maintains correct latitude/longitude aspect ratio.
"""

import os
import tkinter as tk
from tkinter import messagebox, Listbox, END, ttk
import tkinter.font as tkfont
import numpy as np
from netCDF4 import Dataset
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from GINCCO_lib.commands.view_plot import draw_plot, draw_vector_plot

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
    font_normal = tkfont.Font(family="DejaVu Sans Mono", size=10, weight="bold")
    root.option_add("*Font", font_normal)

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


    #Note book for right frame


    # --- Create tabs for Scalar / Vector ---
    notebook = ttk.Notebook(right_frame)
    notebook.pack(fill="both", expand=True)

    scalar_tab = tk.Frame(notebook, bg="#f5f5f5")
    vector_tab = tk.Frame(notebook, bg="#f5f5f5")

    notebook.add(scalar_tab, text="Scalar")
    notebook.add(vector_tab, text="Vector")




    bottom_frame = tk.Frame(root, height=150)
    bottom_frame.pack(fill="x", side="bottom")

    #############################
    # === Left: variable list ===
    #############################
    tk.Label(left_frame, text="Variables").pack(pady=5)
    listbox = Listbox(left_frame)
    listbox.pack(fill="both", expand=True, padx=5, pady=5)







    #############################
    # === Right: controls, scalar tab ===
    #############################
    tk.Label(scalar_tab, text="Map Customization", font=("DejaVu Sans Mono", 12, "bold")).pack(pady=5)

    entry_min = tk.Entry(scalar_tab); entry_max = tk.Entry(scalar_tab)
    tk.Label(scalar_tab, text="Min value").pack(); entry_min.pack()
    tk.Label(scalar_tab, text="Max value").pack(); entry_max.pack()

    cmap_var = tk.StringVar(value="jet")
    tk.Label(scalar_tab, text="Color palette").pack()
    tk.OptionMenu(scalar_tab, cmap_var, "jet", "viridis", "plasma", "coolwarm").pack()

    # --- Map resolution ---

    tk.Label(scalar_tab, text="Map resolution").pack()

    # mapping hiển thị ⇄ giá trị thực
    res_map = {
        "Crude": "c",
        "Low": "l",
        "Intermediate": "i",
        "High": "h",
        "Full": "f"
    }


    # biến lưu chữ hiển thị
    res_display_var = tk.StringVar(value="Intermediate")

    # menu hiển thị
    res_menu = tk.OptionMenu(scalar_tab, res_display_var, *res_map.keys())
    res_menu.pack()

    # khi cần lấy giá trị thật để vẽ:
    selected_res = res_map[res_display_var.get()]


    # Layer select
    tk.Label(scalar_tab, text="Layer select").pack()
    layer_var = tk.StringVar(value="0")
    layer_menu = tk.OptionMenu(scalar_tab, layer_var, "0")  # default
    layer_menu.pack()

    # lon/lat bounds
    tk.Label(scalar_tab, text="Lon/Lat bounds").pack(pady=5)
    lon_min_e = tk.Entry(scalar_tab); lon_max_e = tk.Entry(scalar_tab)
    lat_min_e = tk.Entry(scalar_tab); lat_max_e = tk.Entry(scalar_tab)
    for w, lbl in [(lon_min_e, "Lon min"), (lon_max_e, "Lon max"),
                   (lat_min_e, "Lat min"), (lat_max_e, "Lat max")]:
        tk.Label(scalar_tab, text=lbl).pack()
        w.pack()

    # Redraw button
    redraw_btn = tk.Button(scalar_tab, text="Redraw Map", bg="lightblue")
    redraw_btn.pack(pady=10)



    #############################
    # === Right: controls, vector tab ===
    #############################


    tk.Label(vector_tab, text="U variable").pack()
    u_var_var = tk.StringVar(value="")
    u_menu = tk.OptionMenu(vector_tab, u_var_var, "")
    u_menu.pack()

    tk.Label(vector_tab, text="V variable").pack()
    v_var_var = tk.StringVar(value="")
    v_menu = tk.OptionMenu(vector_tab, v_var_var, "")
    v_menu.pack()

    tk.Label(vector_tab, text="Subsampling step").pack()
    subsample_entry = tk.Entry(vector_tab)
    subsample_entry.insert(0, "5")  # default step
    subsample_entry.pack()




    tk.Label(vector_tab, text="Map Customization", font=("DejaVu Sans Mono", 12, "bold")).pack(pady=5)

    entry_min = tk.Entry(vector_tab); entry_max = tk.Entry(vector_tab)
    tk.Label(vector_tab, text="Min value").pack(); entry_min.pack()
    tk.Label(vector_tab, text="Max value").pack(); entry_max.pack()

    cmap_var = tk.StringVar(value="jet")
    tk.Label(vector_tab, text="Color palette").pack()
    tk.OptionMenu(vector_tab, cmap_var, "jet", "viridis", "plasma", "coolwarm").pack()

    # --- Map resolution ---

    tk.Label(vector_tab, text="Map resolution").pack()

    # mapping hiển thị ⇄ giá trị thực
    res_map = {
        "Crude": "c",
        "Low": "l",
        "Intermediate": "i",
        "High": "h",
        "Full": "f"
    }


    # biến lưu chữ hiển thị
    res_display_var = tk.StringVar(value="Intermediate")

    # menu hiển thị
    res_menu = tk.OptionMenu(vector_tab, res_display_var, *res_map.keys())
    res_menu.pack()

    # khi cần lấy giá trị thật để vẽ:
    selected_res = res_map[res_display_var.get()]


    # Layer select
    tk.Label(vector_tab, text="Layer select").pack()
    layer_var = tk.StringVar(value="0")
    layer_menu = tk.OptionMenu(vector_tab, layer_var, "0")  # default
    layer_menu.pack()

    # lon/lat bounds
    tk.Label(vector_tab, text="Lon/Lat bounds").pack(pady=5)
    lon_min_e = tk.Entry(vector_tab); lon_max_e = tk.Entry(vector_tab)
    lat_min_e = tk.Entry(vector_tab); lat_max_e = tk.Entry(vector_tab)
    for w, lbl in [(lon_min_e, "Lon min"), (lon_max_e, "Lon max"),
                   (lat_min_e, "Lat min"), (lat_max_e, "Lat max")]:
        tk.Label(vector_tab, text=lbl).pack()
        w.pack()

    # Redraw button
    redraw_btn = tk.Button(vector_tab, text="Redraw Map", bg="lightblue")
    redraw_btn.pack(pady=10)





    # === Bottom: log ===
    tk.Label(bottom_frame, text="Log Output").pack()
    log_box = tk.Text(bottom_frame, height=8, bg="black", fg="white",
            font= tkfont.Font(family="DejaVu Sans Mono", size=10)   )  
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
            "resolution": res_map[res_display_var.get()], 
        }

        log_box.insert("end", f"Redrawing {state['varname']}...\n")
        log_box.see("end")


        # Tab selection 
        current_tab = notebook.tab(notebook.select(), "text")
        if current_tab == "Scalar":
            draw_plot(state["varname"], state["var"], state["lon"], state["lat"], 
                opts, log_box, state, is_redraw=True)
        else: 
            u_name = u_var_var.get()
            v_name = v_var_var.get()
            if not u_name or not v_name:
                messagebox.showinfo("Info", "Please select both U and V variables for vector mode.")
                return

            var_u = ds.variables[u_name][:]
            var_v = ds.variables[v_name][:]
            step = int(subsample_entry.get())
            draw_vector_plot(var_u, var_v, state["lon"], state["lat"], opts, log_box, state, step)






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
