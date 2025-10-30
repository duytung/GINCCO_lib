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
    top_frame.pack(side="top", fill="both", expand=True)

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
    bottom_frame.configure(height=150)
    root.update()
    #############################
    # === Left: variable list ===
    #############################
    tk.Label(left_frame, text="Variables").pack(pady=5)
    listbox = Listbox(left_frame)
    listbox.pack(fill="both", expand=True, padx=5, pady=5)







    #############################
    # === Right: controls, scalar tab ===
    #############################
    scalar_tab.grid_columnconfigure(1, weight=1)

    tk.Label(scalar_tab, text="Map Customization",
             font=("DejaVu Sans Mono", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=8)

    # --- Min/Max ---
    tk.Label(scalar_tab, text="Min value:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
    entry_min = tk.Entry(scalar_tab, width=12)
    entry_min.grid(row=1, column=1, sticky="w", padx=5, pady=2)

    tk.Label(scalar_tab, text="Max value:").grid(row=2, column=0, sticky="e", padx=5, pady=2)
    entry_max = tk.Entry(scalar_tab, width=12)
    entry_max.grid(row=2, column=1, sticky="w", padx=5, pady=2)

    # --- Color palette ---
    tk.Label(scalar_tab, text="Color palette:").grid(row=3, column=0, sticky="e", padx=5, pady=2)
    cmap_var = tk.StringVar(value="jet")
    tk.OptionMenu(scalar_tab, cmap_var, "jet", "viridis", "plasma", "coolwarm").grid(row=3, column=1, sticky="w")

    # --- Map resolution ---
    tk.Label(scalar_tab, text="Map resolution:").grid(row=4, column=0, sticky="e", padx=5, pady=2)
    res_map = {
        "Crude": "c",
        "Low": "l",
        "Intermediate": "i",
        "High": "h",
        "Full": "f"
    }
    res_display_var = tk.StringVar(value="Intermediate")
    tk.OptionMenu(scalar_tab, res_display_var, *res_map.keys()).grid(row=4, column=1, sticky="w")

    # --- Layer select ---
    tk.Label(scalar_tab, text="Layer:").grid(row=5, column=0, sticky="e", padx=5, pady=2)
    layer_var = tk.StringVar(value="0")
    layer_menu = tk.OptionMenu(scalar_tab, layer_var, "0")
    layer_menu.grid(row=5, column=1, sticky="w")

    # --- Lon/Lat bounds ---
    tk.Label(scalar_tab, text="Lon min:").grid(row=6, column=0, sticky="e", padx=5, pady=2)
    lon_min_e = tk.Entry(scalar_tab, width=12)
    lon_min_e.grid(row=6, column=1, sticky="w", padx=5, pady=2)

    tk.Label(scalar_tab, text="Lon max:").grid(row=7, column=0, sticky="e", padx=5, pady=2)
    lon_max_e = tk.Entry(scalar_tab, width=12)
    lon_max_e.grid(row=7, column=1, sticky="w", padx=5, pady=2)

    tk.Label(scalar_tab, text="Lat min:").grid(row=8, column=0, sticky="e", padx=5, pady=2)
    lat_min_e = tk.Entry(scalar_tab, width=12)
    lat_min_e.grid(row=8, column=1, sticky="w", padx=5, pady=2)

    tk.Label(scalar_tab, text="Lat max:").grid(row=9, column=0, sticky="e", padx=5, pady=2)
    lat_max_e = tk.Entry(scalar_tab, width=12)
    lat_max_e.grid(row=9, column=1, sticky="w", padx=5, pady=2)

    # --- Redraw button ---
    redraw_btn = tk.Button(scalar_tab, text="Redraw Map", bg="lightblue")
    redraw_btn.grid(row=10, column=0, columnspan=2, pady=10)



    #############################
    # === Right: controls, vector tab ===
    #############################

    vector_tab.grid_columnconfigure(1, weight=1)

    # --- Title ---
    tk.Label(vector_tab, text="Vector Field Settings",
             font=("DejaVu Sans Mono", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=8)

    # --- U / V variable selection ---
    tk.Label(vector_tab, text="U variable:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
    u_var_var = tk.StringVar(value="")
    u_menu = tk.OptionMenu(vector_tab, u_var_var, "")
    u_menu.grid(row=1, column=1, sticky="w", padx=5, pady=2)

    tk.Label(vector_tab, text="V variable:").grid(row=2, column=0, sticky="e", padx=5, pady=2)
    v_var_var = tk.StringVar(value="")
    v_menu = tk.OptionMenu(vector_tab, v_var_var, "")
    v_menu.grid(row=2, column=1, sticky="w", padx=5, pady=2)

    # --- Subsampling step ---
    tk.Label(vector_tab, text="Subsampling step:").grid(row=3, column=0, sticky="e", padx=5, pady=2)
    subsample_entry = tk.Entry(vector_tab, width=10)
    subsample_entry.insert(0, "5")
    subsample_entry.grid(row=3, column=1, sticky="w", padx=5, pady=2)

    # --- Section title for map ---
    tk.Label(vector_tab, text="Map Customization",
             font=("DejaVu Sans Mono", 12, "bold")).grid(row=4, column=0, columnspan=2, pady=8)

    # --- Min / Max ---
    tk.Label(vector_tab, text="Min value:").grid(row=5, column=0, sticky="e", padx=5, pady=2)
    entry_min = tk.Entry(vector_tab, width=12)
    entry_min.grid(row=5, column=1, sticky="w", padx=5, pady=2)

    tk.Label(vector_tab, text="Max value:").grid(row=6, column=0, sticky="e", padx=5, pady=2)
    entry_max = tk.Entry(vector_tab, width=12)
    entry_max.grid(row=6, column=1, sticky="w", padx=5, pady=2)

    # --- Color palette ---
    tk.Label(vector_tab, text="Color palette:").grid(row=7, column=0, sticky="e", padx=5, pady=2)
    cmap_var = tk.StringVar(value="jet")
    tk.OptionMenu(vector_tab, cmap_var, "jet", "viridis", "plasma", "coolwarm").grid(row=7, column=1, sticky="w")

    # --- Map resolution ---
    tk.Label(vector_tab, text="Map resolution:").grid(row=8, column=0, sticky="e", padx=5, pady=2)
    res_map = {
        "Crude": "c",
        "Low": "l",
        "Intermediate": "i",
        "High": "h",
        "Full": "f"
    }
    res_display_var = tk.StringVar(value="Intermediate")
    tk.OptionMenu(vector_tab, res_display_var, *res_map.keys()).grid(row=8, column=1, sticky="w")

    # --- Layer select ---
    tk.Label(vector_tab, text="Layer:").grid(row=9, column=0, sticky="e", padx=5, pady=2)
    layer_var = tk.StringVar(value="0")
    layer_menu = tk.OptionMenu(vector_tab, layer_var, "0")
    layer_menu.grid(row=9, column=1, sticky="w")

    # --- Lon/Lat bounds ---
    tk.Label(vector_tab, text="Lon min:").grid(row=10, column=0, sticky="e", padx=5, pady=2)
    lon_min_e = tk.Entry(vector_tab, width=12)
    lon_min_e.grid(row=10, column=1, sticky="w", padx=5, pady=2)

    tk.Label(vector_tab, text="Lon max:").grid(row=11, column=0, sticky="e", padx=5, pady=2)
    lon_max_e = tk.Entry(vector_tab, width=12)
    lon_max_e.grid(row=11, column=1, sticky="w", padx=5, pady=2)

    tk.Label(vector_tab, text="Lat min:").grid(row=12, column=0, sticky="e", padx=5, pady=2)
    lat_min_e = tk.Entry(vector_tab, width=12)
    lat_min_e.grid(row=12, column=1, sticky="w", padx=5, pady=2)

    tk.Label(vector_tab, text="Lat max:").grid(row=13, column=0, sticky="e", padx=5, pady=2)
    lat_max_e = tk.Entry(vector_tab, width=12)
    lat_max_e.grid(row=13, column=1, sticky="w", padx=5, pady=2)

    # --- Redraw button ---
    redraw_btn = tk.Button(vector_tab, text="Redraw Map", bg="lightblue")
    redraw_btn.grid(row=14, column=0, columnspan=2, pady=10)




    ########################################################################
    # === Bottom: log ===
    ########################################################################

    tk.Label(bottom_frame, text="Log Output").pack()
    log_box = tk.Text(bottom_frame, height=8, bg="black", fg="white",
            font= tkfont.Font(family="DejaVu Sans Mono", size=10)   )  
    log_box.pack(fill="both", expand=True, padx=5, pady=5)






    ########################################################################
    # === netcdf loading ===
    ########################################################################




    # === Load NetCDF ===
    try:
        log_box.insert("end", f"Opening file: {datafile}\n")
        ds = Dataset(datafile)
        for v in ds.variables.keys():
            listbox.insert(END, v)
        log_box.insert("end", "File loaded successfully.\n")
    
        # === Update U/V variable dropdowns in vector tab ===
        u_menu["menu"].delete(0, "end")
        v_menu["menu"].delete(0, "end")

        # Lọc biến có chữ 'u' hoặc 'v' trong tên (không phân biệt hoa/thường)
        u_list = [var for var in ds.variables.keys() if "u" in var.lower()]
        v_list = [var for var in ds.variables.keys() if "v" in var.lower()]

        # Nếu không có biến nào chứa 'u'/'v', fallback về toàn bộ danh sách
        if not u_list:
            u_list = list(ds.variables.keys())
        if not v_list:
            v_list = list(ds.variables.keys())

        # Thêm các lựa chọn vào menu
        for varname in u_list:
            u_menu["menu"].add_command(label=varname, command=tk._setit(u_var_var, varname))
        for varname in v_list:
            v_menu["menu"].add_command(label=varname, command=tk._setit(v_var_var, varname))

        # Gán giá trị mặc định
        if u_list:
            u_var_var.set(u_list[0])
        if v_list:
            v_var_var.set(v_list[0])




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
        current_tab = notebook.tab(notebook.select(), "text")

        if current_tab == "Scalar":
            # Nếu đang ở Scalar tab, phải có state["var"]
            if not state["var"]:
                messagebox.showinfo("Info", "Please select a variable first.")
                return
        else:
            # Nếu đang ở Vector tab, kiểm tra U/V variable
            if not u_var_var.get() or not v_var_var.get():
                messagebox.showinfo("Info", "Please select both U and V variables for vector mode.")
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
