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
from GINCCO_lib.commands.map_plot import draw_plot, draw_vector_plot
import matplotlib.cm as cm



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
    root.geometry("550x630")


    def on_close():
        import matplotlib.pyplot as plt
        plt.close('all')  #  đóng toàn bộ cửa sổ plot đang mở
        root.destroy()    #  đóng cửa sổ chính của Tkinter

    root.protocol("WM_DELETE_WINDOW", on_close)


    def redraw():
        current_tab = notebook.tab(notebook.select(), "text")

        def safe_float(v):
            try:
                return float(v)
            except:
                return None

        # ===============================
        # --- SCALAR TAB ---
        # ===============================
        if current_tab == "Scalar":
            opts = {
                "vmin": safe_float(entry_min_scalar.get()),
                "vmax": safe_float(entry_max_scalar.get()),
                "cmap": cmap_var_scalar.get(),
                "layer": int(layer_var_scalar.get()) if layer_var_scalar.get().isdigit() else 0,
                "lon_min": safe_float(lon_min_scalar.get()),
                "lon_max": safe_float(lon_max_scalar.get()),
                "lat_min": safe_float(lat_min_scalar.get()),
                "lat_max": safe_float(lat_max_scalar.get()),
                "resolution": res_map[res_display_var_scalar.get()],
                "dpi": int(dpi_entry_scalar.get()) if dpi_entry_scalar.get() else 100,
            }

            if not state.get("var"):
                messagebox.showinfo("Info", "Please select a variable first.")
                return

            log_box.insert("end", f"Redrawing {state['varname']} (Scalar mode)...\n")
            log_box.see("end")

            draw_plot(
                state["varname"],
                state["var"],
                state["lon"],
                state["lat"],
                opts,
                log_box,
                state,
                is_redraw=True
            )

        # ===============================
        # --- VECTOR TAB ---
        # ===============================
        else:
            opts = {
                "need_rotate_vector": cmap_var_vector.get(),
                "vmin": safe_float(entry_min_vector.get()),
                "vmax": safe_float(entry_max_vector.get()),
                "cmap": cmap_var_vector.get(),
                "cmap_min": safe_float(cmap_min_vector.get()),
                "cmap_max": safe_float(cmap_max_vector.get()),

                "layer": int(layer_var_vector.get()) if layer_var_vector.get().isdigit() else 0,
                "lon_min": safe_float(lon_min_vector.get()),
                "lon_max": safe_float(lon_max_vector.get()),
                "lat_min": safe_float(lat_min_vector.get()),
                "lat_max": safe_float(lat_max_vector.get()),
                "resolution": res_map[res_display_var_vector.get()],
                "dpi": int(dpi_entry_vector.get()) if dpi_entry_vector.get() else 100,
                "scale": int(scale_entry_vector.get()) if scale_entry_vector.get() else 3,
            }

            u_name = u_var_var.get()
            v_name = v_var_var.get()


            if not u_name or not v_name:
                messagebox.showinfo("Info", "Please select both U and V variables for vector mode.")
                return

            var_u = np.squeeze(ds.variables[u_name][:])
            var_v = np.squeeze(ds.variables[v_name][:])

            # --- Nếu dữ liệu là 3D thì chọn layer ---
            layer_idx = int(layer_var_vector.get()) if layer_var_vector.get().isdigit() else 0
            if var_u.ndim == 3:
                var_u = var_u[layer_idx, :, :]
            if var_v.ndim == 3:
                var_v = var_v[layer_idx, :, :]

            quiver_max_n = int(quiver_entry_vector.get())

            # --- Load grid ---
            with Dataset(gridfile) as fgrid:
                lon_u = fgrid.variables.get("longitude_u")
                lat_u = fgrid.variables.get("latitude_u")
                lon_v = fgrid.variables.get("longitude_v")
                lat_v = fgrid.variables.get("latitude_v")
                mask_t_var = fgrid.variables.get("mask_t")

                if mask_t_var is not None:
                    mask_t = mask_t_var[:] if mask_t_var.ndim == 2 else mask_t_var[0, :, :]
                    state["mask_t"] = mask_t

            # --- Lấy lại lon/lat dạng T nếu chưa có ---
            lon_t, lat_t = state.get("lon"), state.get("lat")
            if lon_t is None or lat_t is None:
                lon_t, lat_t = get_grid_coords(gridfile, "t")
                state["lon"], state["lat"] = lon_t, lat_t

            # --- Vẽ ---
            draw_vector_plot(
                var_u,
                var_v,
                state["lon"],
                state["lat"],
                opts,
                log_box,
                state,
                quiver_max_n   )
    # ---- Endof function s



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
    row_s = 0

    tk.Label(
        scalar_tab, text="Map Customization",
        font=("DejaVu Sans Mono", 12, "bold")
    ).grid(row=row_s, column=0, columnspan=2, pady=8)
    row_s += 1

    # --- Value range ---
    tk.Label(scalar_tab, text="Value range:").grid(row=row_s, column=0, sticky="e", padx=5, pady=2)
    frame_minmax_scalar = tk.Frame(scalar_tab)
    frame_minmax_scalar.grid(row=row_s, column=1, sticky="w", padx=5, pady=2)
    tk.Label(frame_minmax_scalar, text="Min").pack(side="left")
    entry_min_scalar = tk.Entry(frame_minmax_scalar, width=6)
    entry_min_scalar.pack(side="left", padx=(2, 5))
    tk.Label(frame_minmax_scalar, text="Max").pack(side="left")
    entry_max_scalar = tk.Entry(frame_minmax_scalar, width=6)
    entry_max_scalar.pack(side="left", padx=(2, 0))
    row_s += 1


    # --- Color palette ---

    # --- Color palette ---
    tk.Label(scalar_tab, text="Color palette:").grid(row=row_s, column=0, sticky="e", padx=5, pady=2)
    cmap_var_scalar = tk.StringVar(value="jet")

    # Dùng Menubutton có chia nhóm
    menu_button = tk.Menubutton(scalar_tab, textvariable=cmap_var_scalar, relief="raised")
    menu = tk.Menu(menu_button, tearoff=False)
    menu_button["menu"] = menu

    # Nhóm thủ công dựa vào tên (vì bản cũ chưa có thuộc tính category)
    def classify_cmap(name):
        name_lower = name.lower()
        if any(x in name_lower for x in ["_r"]):
            name_lower = name_lower.replace("_r", "")
        if name_lower in ["jet", "viridis", "plasma", "inferno", "magma", "cividis", "Greens", "Blues"]:
            return "Sequential"
        elif name_lower in ["coolwarm", "bwr", "RdBu", "PiYG", "PRGn", "BrBG"]:
            return "Diverging"
        elif name_lower in ["Set1", "Set2", "tab10", "tab20", "Pastel1"]:
            return "Qualitative"
        else:
            return "Miscellaneous"

    # Gom nhóm colormap
    categories = {"Sequential": [], "Diverging": [], "Qualitative": [], "Miscellaneous": []}
    for name in sorted(cm.cmap_d.keys()):
        cat = classify_cmap(name)
        categories[cat].append(name)

    # Tạo submenu cho từng nhóm
    for cat_name, cmap_list in categories.items():
        sub = tk.Menu(menu, tearoff=False)
        for cmap_name in sorted(cmap_list):
            sub.add_radiobutton(label=cmap_name, variable=cmap_var_scalar, value=cmap_name)
        menu.add_cascade(label=cat_name, menu=sub)

    menu_button.grid(row=row_s, column=1, sticky="w")
    row_s += 1






    # --- Map resolution ---
    tk.Label(scalar_tab, text="Map resolution:").grid(row=row_s, column=0, sticky="e", padx=5, pady=2)
    res_map = {
        "Crude": "c", "Low": "l", "Intermediate": "i", "High": "h", "Full": "f"
    }
    res_display_var_scalar = tk.StringVar(value="Intermediate")
    tk.OptionMenu(scalar_tab, res_display_var_scalar, *res_map.keys()).grid(row=row_s, column=1, sticky="w")
    row_s += 1

    # --- Layer select ---
    tk.Label(scalar_tab, text="Layer:").grid(row=row_s, column=0, sticky="e", padx=5, pady=2)
    layer_var_scalar = tk.StringVar(value="0")
    layer_menu_scalar = tk.OptionMenu(scalar_tab, layer_var_scalar, "0")
    layer_menu_scalar.grid(row=row_s, column=1, sticky="w")
    row_s += 1

    # --- Lon/Lat bounds ---
    tk.Label(scalar_tab, text="Longitude bounds:").grid(row=row_s, column=0, sticky="e", padx=5, pady=2)
    frame_lon_scalar = tk.Frame(scalar_tab)
    frame_lon_scalar.grid(row=row_s, column=1, sticky="w", padx=5, pady=2)
    tk.Label(frame_lon_scalar, text="Min").pack(side="left")
    lon_min_scalar = tk.Entry(frame_lon_scalar, width=6)
    lon_min_scalar.pack(side="left", padx=(2, 5))
    tk.Label(frame_lon_scalar, text="Max").pack(side="left")
    lon_max_scalar = tk.Entry(frame_lon_scalar, width=6)
    lon_max_scalar.pack(side="left", padx=(2, 0))
    row_s += 1

    tk.Label(scalar_tab, text="Latitude bounds:").grid(row=row_s, column=0, sticky="e", padx=5, pady=2)
    frame_lat_scalar = tk.Frame(scalar_tab)
    frame_lat_scalar.grid(row=row_s, column=1, sticky="w", padx=5, pady=2)
    tk.Label(frame_lat_scalar, text="Min").pack(side="left")
    lat_min_scalar = tk.Entry(frame_lat_scalar, width=6)
    lat_min_scalar.pack(side="left", padx=(2, 5))
    tk.Label(frame_lat_scalar, text="Max").pack(side="left")
    lat_max_scalar = tk.Entry(frame_lat_scalar, width=6)
    lat_max_scalar.pack(side="left", padx=(2, 0))
    row_s += 1

    # --- Figure DPI ---
    tk.Label(scalar_tab, text="Figure DPI:").grid(row=row_s, column=0, sticky="e", padx=5, pady=2)
    dpi_entry_scalar = tk.Entry(scalar_tab, width=10)
    dpi_entry_scalar.insert(0, "100")
    dpi_entry_scalar.grid(row=row_s, column=1, sticky="w", padx=5, pady=2)
    row_s += 1

    # --- Redraw button ---
    redraw_btn_scalar = tk.Button(scalar_tab, text="Redraw Map", bg="lightblue", command=redraw)
    redraw_btn_scalar.grid(row=row_s, column=0, columnspan=2, pady=10)
    row_s += 1



    #############################
    # === Right: controls, vector tab ===
    #############################


    vector_tab.grid_columnconfigure(1, weight=1)
    row_v = 0

    tk.Label(
        vector_tab, text="Vector Field Settings",
        font=("DejaVu Sans Mono", 12, "bold")
    ).grid(row=row_v, column=0, columnspan=2, pady=8)
    row_v += 1

    # --- U/V variable ---
    tk.Label(vector_tab, text="U variable:").grid(row=row_v, column=0, sticky="e", padx=5, pady=2)
    u_var_var = tk.StringVar(value="")
    u_menu = tk.OptionMenu(vector_tab, u_var_var, "")
    u_menu.grid(row=row_v, column=1, sticky="w", padx=5, pady=2)
    row_v += 1

    tk.Label(vector_tab, text="V variable:").grid(row=row_v, column=0, sticky="e", padx=5, pady=2)
    v_var_var = tk.StringVar(value="")
    v_menu = tk.OptionMenu(vector_tab, v_var_var, "")
    v_menu.grid(row=row_v, column=1, sticky="w", padx=5, pady=2)
    row_v += 1

    # --- Rotate option ---
    tk.Label(vector_tab, text="Need rotate:").grid(row=row_v, column=0, sticky="e", padx=5, pady=2)
    need_rotate_vector = tk.StringVar(value="True")  # default = True
    tk.OptionMenu(vector_tab, need_rotate_vector, "True", "False").grid(row=row_v, column=1, sticky="w")
    row_v += 1

    # --- Max number of arrows ---
    tk.Label(vector_tab, text="Max. number of arrows:").grid(row=row_v, column=0, sticky="e", padx=5, pady=2)
    quiver_entry_vector = tk.Entry(vector_tab, width=10)
    quiver_entry_vector.insert(0, "20")
    quiver_entry_vector.grid(row=row_v, column=1, sticky="w", padx=5, pady=2)
    row_v += 1

    # --- Map customization section ---
    tk.Label(vector_tab, text="Map Customization",
             font=("DejaVu Sans Mono", 12, "bold")).grid(row=row_v, column=0, columnspan=2, pady=8)
    row_v += 1

    # --- Value range ---
    tk.Label(vector_tab, text="Value range:").grid(row=row_v, column=0, sticky="e", padx=5, pady=2)
    frame_minmax_vector = tk.Frame(vector_tab)
    frame_minmax_vector.grid(row=row_v, column=1, sticky="w", padx=5, pady=2)
    tk.Label(frame_minmax_vector, text="Min").pack(side="left")
    entry_min_vector = tk.Entry(frame_minmax_vector, width=6)
    entry_min_vector.pack(side="left", padx=(2, 5))
    tk.Label(frame_minmax_vector, text="Max").pack(side="left")
    entry_max_vector = tk.Entry(frame_minmax_vector, width=6)
    entry_max_vector.pack(side="left", padx=(2, 0))
    row_v += 1


    # --- Color palette ---
    tk.Label(vector_tab, text="Color palette:").grid(row=row_v, column=0, sticky="e", padx=5, pady=2)
    cmap_var_vector = tk.StringVar(value="YlOrBr")

    # Dùng Menubutton có chia nhóm
    menu_button = tk.Menubutton(vector_tab, textvariable=cmap_var_vector, relief="raised")
    menu = tk.Menu(menu_button, tearoff=False)
    menu_button["menu"] = menu

    # Nhóm thủ công dựa vào tên (vì bản cũ chưa có thuộc tính category)
    def classify_cmap(name):
        name_lower = name.lower()
        if any(x in name_lower for x in ["_r"]):
            name_lower = name_lower.replace("_r", "")
        if name_lower in ["jet", "viridis", "plasma", "inferno", "magma", "cividis", "Greens", "Blues"]:
            return "Sequential"
        elif name_lower in ["coolwarm", "bwr", "RdBu", "PiYG", "PRGn", "BrBG"]:
            return "Diverging"
        elif name_lower in ["Set1", "Set2", "tab10", "tab20", "Pastel1"]:
            return "Qualitative"
        else:
            return "Miscellaneous"

    # Gom nhóm colormap
    categories = {"Sequential": [], "Diverging": [], "Qualitative": [], "Miscellaneous": []}
    for name in sorted(cm.cmap_d.keys()):
        cat = classify_cmap(name)
        categories[cat].append(name)

    # Tạo submenu cho từng nhóm
    for cat_name, cmap_list in categories.items():
        sub = tk.Menu(menu, tearoff=False)
        for cmap_name in sorted(cmap_list):
            sub.add_radiobutton(label=cmap_name, variable=cmap_var_vector, value=cmap_name)
        menu.add_cascade(label=cat_name, menu=sub)

    menu_button.grid(row=row_v, column=1, sticky="w")
    row_v += 1

    # --- Lon/Lat bounds ---
    tk.Label(vector_tab, text="Cmap range:").grid(row=row_v, column=0, sticky="e", padx=5, pady=2)
    frame_cmap_vector = tk.Frame(vector_tab)
    frame_cmap_vector.grid(row=row_v, column=1, sticky="w", padx=5, pady=2)

    tk.Label(frame_cmap_vector, text="Min").pack(side="left")
    cmap_min_vector = tk.Entry(frame_cmap_vector, width=6)
    cmap_min_vector.pack(side="left", padx=(2, 5))
    cmap_min_vector.insert(0, "0")

    tk.Label(frame_cmap_vector, text="Max").pack(side="left")
    cmap_max_vector = tk.Entry(frame_cmap_vector, width=6)
    cmap_max_vector.pack(side="left", padx=(2, 0))
    cmap_max_vector.insert(0, "0.7")
    row_v += 1







    # --- Map resolution ---
    tk.Label(vector_tab, text="Map resolution:").grid(row=row_v, column=0, sticky="e", padx=5, pady=2)
    res_display_var_vector = tk.StringVar(value="Intermediate")
    tk.OptionMenu(vector_tab, res_display_var_vector, *res_map.keys()).grid(row=row_v, column=1, sticky="w")
    row_v += 1

    # --- Layer select ---
    tk.Label(vector_tab, text="Layer:").grid(row=row_v, column=0, sticky="e", padx=5, pady=2)
    layer_var_vector = tk.StringVar(value="0")
    layer_menu_vector = tk.OptionMenu(vector_tab, layer_var_vector, "0")
    layer_menu_vector.grid(row=row_v, column=1, sticky="w")
    row_v += 1

    # --- Lon/Lat bounds ---
    tk.Label(vector_tab, text="Longitude bounds:").grid(row=row_v, column=0, sticky="e", padx=5, pady=2)
    frame_lon_vector = tk.Frame(vector_tab)
    frame_lon_vector.grid(row=row_v, column=1, sticky="w", padx=5, pady=2)
    tk.Label(frame_lon_vector, text="Min").pack(side="left")
    lon_min_vector = tk.Entry(frame_lon_vector, width=6)
    lon_min_vector.pack(side="left", padx=(2, 5))
    tk.Label(frame_lon_vector, text="Max").pack(side="left")
    lon_max_vector = tk.Entry(frame_lon_vector, width=6)
    lon_max_vector.pack(side="left", padx=(2, 0))
    row_v += 1

    tk.Label(vector_tab, text="Latitude bounds:").grid(row=row_v, column=0, sticky="e", padx=5, pady=2)
    frame_lat_vector = tk.Frame(vector_tab)
    frame_lat_vector.grid(row=row_v, column=1, sticky="w", padx=5, pady=2)
    tk.Label(frame_lat_vector, text="Min").pack(side="left")
    lat_min_vector = tk.Entry(frame_lat_vector, width=6)
    lat_min_vector.pack(side="left", padx=(2, 5))
    tk.Label(frame_lat_vector, text="Max").pack(side="left")
    lat_max_vector = tk.Entry(frame_lat_vector, width=6)
    lat_max_vector.pack(side="left", padx=(2, 0))
    row_v += 1

    # --- Figure DPI ---
    tk.Label(vector_tab, text="Figure DPI:").grid(row=row_v, column=0, sticky="e", padx=5, pady=2)
    dpi_entry_vector = tk.Entry(vector_tab, width=10)
    dpi_entry_vector.insert(0, "100")
    dpi_entry_vector.grid(row=row_v, column=1, sticky="w", padx=5, pady=2)
    row_v += 1

    # --- Scale ---
    tk.Label(vector_tab, text="Scale:").grid(row=row_v, column=0, sticky="e", padx=5, pady=2)
    scale_entry_vector = tk.Entry(vector_tab, width=10)
    scale_entry_vector.insert(0, "3")
    scale_entry_vector.grid(row=row_v, column=1, sticky="w", padx=5, pady=2)
    row_v += 1

    # --- Redraw button ---
    redraw_btn_vector = tk.Button(vector_tab, text="Draw Map", bg="lightblue", command=redraw)
    redraw_btn_vector.grid(row=row_v, column=0, columnspan=2, pady=10)
    row_v += 1


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

        # --- Xác định grid suffix ---
        suffix = "t"
        for s in ["u", "v", "f", "t"]:
            if varname.lower().endswith(s):
                suffix = s
                break
        state["suffix"] = suffix
        lon, lat = get_grid_coords(gridfile, suffix)
        state["lon"], state["lat"] = lon, lat

        # --- Cập nhật menu Layer của tab Scalar ---
        try:
            menu = layer_menu_scalar["menu"]
            menu.delete(0, "end")

            if nd == 3:
                for i in range(data.shape[0]):
                    menu.add_command(label=str(i), command=tk._setit(layer_var_scalar, str(i)))
                layer_var_scalar.set("0")
            else:
                menu.add_command(label="0", command=tk._setit(layer_var_scalar, "0"))
                layer_var_scalar.set("0")
        except Exception as e:
            log_box.insert("end", f"[WARN] Layer menu not found: {e}\n")

        # --- Cập nhật log ---
        log_box.insert("end", f"Selected variable: {varname} ({nd}D)\n")
        log_box.see("end")

        # --- Auto plot ngay khi double-click ---
        opts = {
            "vmin": None,
            "vmax": None,
            "cmap": cmap_var_scalar.get(),
            "layer": int(layer_var_scalar.get()) if layer_var_scalar.get().isdigit() else 0,
            "lon_min": None,
            "lon_max": None,
            "lat_min": None,
            "lat_max": None,
            "dpi": int(dpi_entry_scalar.get()) if dpi_entry_scalar.get() else 100,
        }

        draw_plot(
            state["varname"],
            state["var"],
            state["lon"],
            state["lat"],
            opts,
            log_box,
            state
        )


    def on_vector_select(*args):
        """Cập nhật menu chọn layer khi người dùng thay đổi biến U hoặc V."""
        try:
            # --- Chặn lỗi khi chưa load file hoặc chưa có log_box ---
            if "ds" not in locals() and "ds" not in globals():
                return
            if "log_box" not in locals() and "log_box" not in globals():
                return
            if "layer_menu_vector" not in locals() and "layer_menu_vector" not in globals():
                return

            u_name = u_var_var.get()
            v_name = v_var_var.get()
            if not u_name and not v_name:
                return  # chưa chọn gì cả

            # --- Kiểm tra xem biến có trong file không ---
            if u_name not in ds.variables or v_name not in ds.variables:
                return

            # --- Lấy dữ liệu ---
            var_u = np.squeeze(ds.variables[u_name][:])
            var_v = np.squeeze(ds.variables[v_name][:])

            nd = max(var_u.ndim, var_v.ndim)

            # --- Cập nhật layer menu ---
            menu_v = layer_menu_vector["menu"]
            menu_v.delete(0, "end")

            if nd == 3:
                for i in range(var_u.shape[0]):
                    menu_v.add_command(label=str(i), command=tk._setit(layer_var_vector, str(i)))
                layer_var_vector.set("0")
                if log_box.winfo_exists():
                    log_box.insert("end", f"[Vector] U/V: {u_name}, {v_name} (3D) — layer menu updated.\n")
            else:
                menu_v.add_command(label="0", command=tk._setit(layer_var_vector, "0"))
                layer_var_vector.set("0")
                if log_box.winfo_exists():
                    log_box.insert("end", f"[Vector] U/V: {u_name}, {v_name} (2D)\n")

            if log_box.winfo_exists():
                log_box.see("end")

        except Exception as e:
            try:
                log_box.insert("end", f"[Error] on_vector_select: {e}\n")
                log_box.see("end")
            except:
                print(f"[Error] on_vector_select: {e}")




    u_var_var.trace_add("write", on_vector_select)
    v_var_var.trace_add("write", on_vector_select)









    listbox.bind("<Double-Button-1>", on_var_select)
    redraw_btn_scalar.config(command=redraw)
    redraw_btn_vector.config(command=redraw)
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
