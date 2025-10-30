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


APP_BG = "#f3f4f6"       # nền chính
FRAME_BG = "#ffffff"      # nền khung
LABEL_BG = "#f3f4f6"
TEXT_BG = "#ffffff"
TEXT_FG = "#333333"
ACCENT = "#0078d7"        # xanh dịu





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



    def redraw():
        current_tab = notebook.tab(notebook.select(), "text")

        # --- Tạo trước opts cho cả Scalar và Vector ---
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
            "dpi": int(dpi_entry.get()) if dpi_entry.get() else 100,
            "scale": int(scale_entry.get()) if scale_entry.get() else 400,

        }



        ################
        # In scalar tab
        ################
        if current_tab == "Scalar":
            # Kiểm tra variable
            if not state["var"]:
                messagebox.showinfo("Info", "Please select a variable first.")
                return

            log_box.insert("end", f"Redrawing {state['varname']} (Scalar mode)...\n")
            log_box.see("end")

            draw_plot(
                state["varname"], state["var"], state["lon"], state["lat"],
                opts, log_box, state, is_redraw=True
            )


        ################
        # In vector tab
        ################
 
        else:  # Vector tab
            u_name = u_var_var.get()
            v_name = v_var_var.get()
            if not u_name or not v_name:
                messagebox.showinfo("Info", "Please select both U and V variables for vector mode.")
                return

            var_u = np.squeeze(ds.variables[u_name][:])
            var_v = np.squeeze(ds.variables[v_name][:])

            # --- Nếu 3D, lấy layer được chọn hoặc layer 0 ---
            if var_u.ndim == 3:
                layer = int(layer_var.get()) if layer_var.get().isdigit() else 0
                var_u = var_u[layer, :, :]
            if var_v.ndim == 3:
                layer = int(layer_var.get()) if layer_var.get().isdigit() else 0
                var_v = var_v[layer, :, :]

            quiver_max_n = int(quiver_entry.get())

            # --- Load grid for U/V ---
            fgrid = Dataset(gridfile)
            lon_u = fgrid.variables.get("longitude_u")[:]
            lat_u = fgrid.variables.get("latitude_u")[:]
            lon_v = fgrid.variables.get("longitude_v")[:]
            lat_v = fgrid.variables.get("latitude_v")[:]
            mask_t_var = fgrid.variables.get("mask_t")
            if mask_t_var is not None:
                mask_t = mask_t_var[:] if mask_t_var.ndim == 2 else mask_t_var[0,:,:]
                state["mask_t"] = mask_t

            lon_t, lat_t = state.get("lon"), state.get("lat")
            if lon_t is None or lat_t is None:
                lon_t, lat_t = get_grid_coords(gridfile, "t")
                state["lon"], state["lat"] = lon_t, lat_t
            
            draw_vector_plot(var_u, var_v, state["lon"], state["lat"], opts, log_box, state, quiver_max_n)











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
    listbox = tk.Listbox(
        left_frame,
        borderwidth=2,
        relief="groove",
        highlightthickness=4,   # viền trắng giữa chữ và khung
        highlightbackground="#d0d0d0",  # màu khung nhẹ
        selectbackground="#cce6ff",     # màu khi chọn
        selectforeground="black",       # màu chữ khi chọn
        font=("DejaVu Sans Mono", 10),
    )
    listbox.pack(fill="both", expand=True, padx=10, pady=8)


    #############################
    # === Right: controls, scalar tab ===
    #############################
    scalar_tab.grid_columnconfigure(1, weight=1)
    row_i = 0  # khởi tạo biến đếm hàng

    # --- Tiêu đề ---
    tk.Label(scalar_tab, text="Map Customization",
             font=("DejaVu Sans Mono", 12, "bold")).grid(row=row_i, column=0, columnspan=2, pady=8)
    row_i += 1

    # --- Value range (Min/Max chung dòng) ---
    tk.Label(scalar_tab, text="Value range:").grid(row=row_i, column=0, sticky="e", padx=5, pady=2)
    frame_minmax = tk.Frame(scalar_tab)
    frame_minmax.grid(row=row_i, column=1, sticky="w", padx=5, pady=2)
    tk.Label(frame_minmax, text="Min").pack(side="left")
    entry_min = tk.Entry(frame_minmax, width=6)
    entry_min.pack(side="left", padx=(2,5))
    tk.Label(frame_minmax, text="Max").pack(side="left")
    entry_max = tk.Entry(frame_minmax, width=6)
    entry_max.pack(side="left", padx=(2,0))
    row_i += 1

    # --- Color palette ---
    tk.Label(scalar_tab, text="Color palette:").grid(row=row_i, column=0, sticky="e", padx=5, pady=2)
    cmap_var = tk.StringVar(value="jet")
    tk.OptionMenu(scalar_tab, cmap_var, "jet", "viridis", "plasma", "coolwarm").grid(row=row_i, column=1, sticky="w")
    row_i += 1

    # --- Map resolution ---
    tk.Label(scalar_tab, text="Map resolution:").grid(row=row_i, column=0, sticky="e", padx=5, pady=2)
    res_map = {
        "Crude": "c",
        "Low": "l",
        "Intermediate": "i",
        "High": "h",
        "Full": "f"
    }
    res_display_var = tk.StringVar(value="Intermediate")
    tk.OptionMenu(scalar_tab, res_display_var, *res_map.keys()).grid(row=row_i, column=1, sticky="w")
    row_i += 1

    # --- Layer select ---
    tk.Label(scalar_tab, text="Layer:").grid(row=row_i, column=0, sticky="e", padx=5, pady=2)
    layer_var = tk.StringVar(value="0")
    layer_menu = tk.OptionMenu(scalar_tab, layer_var, "0")
    layer_menu.grid(row=row_i, column=1, sticky="w")
    row_i += 1

    # --- Lon/Lat bounds ---
    tk.Label(scalar_tab, text="Longitude bounds:").grid(row=row_i, column=0, sticky="e", padx=5, pady=2)
    frame_lon = tk.Frame(scalar_tab)
    frame_lon.grid(row=row_i, column=1, sticky="w", padx=5, pady=2)
    tk.Label(frame_lon, text="Min").pack(side="left")
    lon_min_e = tk.Entry(frame_lon, width=6)
    lon_min_e.pack(side="left", padx=(2,5))
    tk.Label(frame_lon, text="Max").pack(side="left")
    lon_max_e = tk.Entry(frame_lon, width=6)
    lon_max_e.pack(side="left", padx=(2,0))
    row_i += 1

    tk.Label(scalar_tab, text="Latitude bounds:").grid(row=row_i, column=0, sticky="e", padx=5, pady=2)
    frame_lat = tk.Frame(scalar_tab)
    frame_lat.grid(row=row_i, column=1, sticky="w", padx=5, pady=2)
    tk.Label(frame_lat, text="Min").pack(side="left")
    lat_min_e = tk.Entry(frame_lat, width=6)
    lat_min_e.pack(side="left", padx=(2,5))
    tk.Label(frame_lat, text="Max").pack(side="left")
    lat_max_e = tk.Entry(frame_lat, width=6)
    lat_max_e.pack(side="left", padx=(2,0))
    row_i += 1

    # --- Figure DPI ---
    tk.Label(scalar_tab, text="Figure DPI:").grid(row=row_i, column=0, sticky="e", padx=5, pady=2)
    dpi_entry = tk.Entry(scalar_tab, width=10)
    dpi_entry.insert(0, "100")
    dpi_entry.grid(row=row_i, column=1, sticky="w", padx=5, pady=2)
    row_i += 1

    # --- Redraw button ---
    redraw_btn = tk.Button(scalar_tab, text="Redraw Map", bg="lightblue", command=redraw)
    redraw_btn.grid(row=row_i, column=0, columnspan=2, pady=10)
    row_i += 1



    #############################
    # === Right: controls, vector tab ===
    #############################
    vector_tab.grid_columnconfigure(1, weight=1)
    row_i = 0  # khởi tạo biến đếm hàng

    # --- Title ---
    tk.Label(vector_tab, text="Vector Field Settings",
             font=("DejaVu Sans Mono", 12, "bold")).grid(row=row_i, column=0, columnspan=2, pady=8)
    row_i += 1

    # --- U variable ---
    tk.Label(vector_tab, text="U variable:").grid(row=row_i, column=0, sticky="e", padx=5, pady=2)
    u_var_var = tk.StringVar(value="")
    u_menu = tk.OptionMenu(vector_tab, u_var_var, "")
    u_menu.grid(row=row_i, column=1, sticky="w", padx=5, pady=2)
    row_i += 1

    # --- V variable ---
    tk.Label(vector_tab, text="V variable:").grid(row=row_i, column=0, sticky="e", padx=5, pady=2)
    v_var_var = tk.StringVar(value="")
    v_menu = tk.OptionMenu(vector_tab, v_var_var, "")
    v_menu.grid(row=row_i, column=1, sticky="w", padx=5, pady=2)
    row_i += 1

    # --- Max number of arrows ---
    tk.Label(vector_tab, text="Max. number of arrows:").grid(row=row_i, column=0, sticky="e", padx=5, pady=2)
    quiver_entry = tk.Entry(vector_tab, width=10)
    quiver_entry.insert(0, "10")
    quiver_entry.grid(row=row_i, column=1, sticky="w", padx=5, pady=2)
    row_i += 1

    # --- Map customization section ---
    tk.Label(vector_tab, text="Map Customization",
             font=("DejaVu Sans Mono", 12, "bold")).grid(row=row_i, column=0, columnspan=2, pady=8)
    row_i += 1

    # --- Value range ---
    tk.Label(vector_tab, text="Value range:").grid(row=row_i, column=0, sticky="e", padx=5, pady=2)
    frame_minmax_v = tk.Frame(vector_tab)
    frame_minmax_v.grid(row=row_i, column=1, sticky="w", padx=5, pady=2)
    tk.Label(frame_minmax_v, text="Min").pack(side="left")
    entry_min = tk.Entry(frame_minmax_v, width=6)
    entry_min.pack(side="left", padx=(2,5))
    tk.Label(frame_minmax_v, text="Max").pack(side="left")
    entry_max = tk.Entry(frame_minmax_v, width=6)
    entry_max.pack(side="left", padx=(2,0))
    row_i += 1

    # --- Color palette ---
    tk.Label(vector_tab, text="Color palette:").grid(row=row_i, column=0, sticky="e", padx=5, pady=2)
    cmap_var = tk.StringVar(value="jet")
    tk.OptionMenu(vector_tab, cmap_var, "jet", "viridis", "plasma", "coolwarm").grid(row=row_i, column=1, sticky="w")
    row_i += 1

    # --- Map resolution ---
    tk.Label(vector_tab, text="Map resolution:").grid(row=row_i, column=0, sticky="e", padx=5, pady=2)
    res_map = {
        "Crude": "c",
        "Low": "l",
        "Intermediate": "i",
        "High": "h",
        "Full": "f"
    }
    res_display_var = tk.StringVar(value="Intermediate")
    tk.OptionMenu(vector_tab, res_display_var, *res_map.keys()).grid(row=row_i, column=1, sticky="w")
    row_i += 1

    # --- Layer select ---
    tk.Label(vector_tab, text="Layer:").grid(row=row_i, column=0, sticky="e", padx=5, pady=2)
    layer_var = tk.StringVar(value="0")
    layer_menu = tk.OptionMenu(vector_tab, layer_var, "0")
    layer_menu.grid(row=row_i, column=1, sticky="w")
    row_i += 1


    # --- Lon/Lat bounds ---
    tk.Label(vector_tab, text="Longitude bounds:").grid(row=row_i, column=0, sticky="e", padx=5, pady=2)
    frame_lon = tk.Frame(vector_tab)
    frame_lon.grid(row=row_i, column=1, sticky="w", padx=5, pady=2)
    tk.Label(frame_lon, text="Min").pack(side="left")
    lon_min_e = tk.Entry(frame_lon, width=6)
    lon_min_e.pack(side="left", padx=(2,5))
    tk.Label(frame_lon, text="Max").pack(side="left")
    lon_max_e = tk.Entry(frame_lon, width=6)
    lon_max_e.pack(side="left", padx=(2,0))
    row_i += 1

    tk.Label(vector_tab, text="Latitude bounds:").grid(row=row_i, column=0, sticky="e", padx=5, pady=2)
    frame_lat = tk.Frame(vector_tab)
    frame_lat.grid(row=row_i, column=1, sticky="w", padx=5, pady=2)
    tk.Label(frame_lat, text="Min").pack(side="left")
    lat_min_e = tk.Entry(frame_lat, width=6)
    lat_min_e.pack(side="left", padx=(2,5))
    tk.Label(frame_lat, text="Max").pack(side="left")
    lat_max_e = tk.Entry(frame_lat, width=6)
    lat_max_e.pack(side="left", padx=(2,0))
    row_i += 1


    # --- Figure DPI ---
    tk.Label(vector_tab, text="Figure DPI:").grid(row=row_i, column=0, sticky="e", padx=5, pady=2)
    dpi_entry = tk.Entry(vector_tab, width=10)
    dpi_entry.insert(0, "100")
    dpi_entry.grid(row=row_i, column=1, sticky="w", padx=5, pady=2)
    row_i += 1

    # --- Scale ---
    tk.Label(vector_tab, text="Scale:").grid(row=row_i, column=0, sticky="e", padx=5, pady=2)
    scale_entry = tk.Entry(vector_tab, width=10)
    scale_entry.insert(0, "400")
    scale_entry.grid(row=row_i, column=1, sticky="w", padx=5, pady=2)
    row_i += 1

    # --- Redraw button ---
    redraw_btn = tk.Button(vector_tab, text="Draw Map", bg="lightblue", command=redraw)
    redraw_btn.grid(row=row_i, column=0, columnspan=2, pady=10)
    row_i += 1




    ########################################################################
    # === Bottom: log ===
    ########################################################################

    tk.Label(bottom_frame, text="Log Output").pack()
    log_box = tk.Text(bottom_frame, height=8, bg="black", fg="white",
            font= tkfont.Font(family="DejaVu Sans Mono", size=10)   )  
    log_box.pack(fill="both", expand=True, padx=5, pady=5)

    ########################################################################
    # === Theme ===
    ########################################################################


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
                menu.add_command(label=str(i), command=tk._setit(layer_var, str(i)))
            layer_var.set("0")
        else:
            menu.add_command(label="0", command=tk._setit(layer_var, "0"))
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
