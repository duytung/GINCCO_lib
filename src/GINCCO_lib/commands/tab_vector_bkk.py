# vector_tab.py
"""
Vector tab (single-column controls). No left Variables box.
build_vector_tab(parent, datafile, gridfile=None, draw_callback=None)

draw_callback (optional) signature:
    draw_callback(u_name, v_name, var_u, var_v, lon, lat, opts, state)
If not provided, this module will try to call draw_vector_plot from map_plot.
"""
import tkinter as tk
from tkinter import messagebox, END
import numpy as np
from netCDF4 import Dataset
import matplotlib.cm as cm
from .plot_vector_map import draw_vector_plot


def _bind_mousewheel(widget, target):
    """Bind mouse wheel to scroll 'target' when pointer over 'widget'."""
    def _on_mousewheel(event):
        if hasattr(event, "delta"):
            if event.delta < 0:
                target.yview_scroll(1, "units")
            else:
                target.yview_scroll(-1, "units")
        else:
            if event.num == 5:
                target.yview_scroll(1, "units")
            elif event.num == 4:
                target.yview_scroll(-1, "units")

    widget.bind("<Enter>", lambda e: widget.bind_all("<MouseWheel>", _on_mousewheel))
    widget.bind("<Leave>", lambda e: widget.unbind_all("<MouseWheel>"))
    widget.bind("<Enter>", lambda e: widget.bind_all("<Button-4>", _on_mousewheel))
    widget.bind("<Enter>", lambda e: widget.bind_all("<Button-5>", _on_mousewheel))
    widget.bind("<Leave>", lambda e: widget.unbind_all("<Button-4>"))
    widget.bind("<Leave>", lambda e: widget.unbind_all("<Button-5>"))


def get_grid_coords(grid_file, suffix):
    if not grid_file:
        return None, None
    try:
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
    except Exception:
        return None, None


def build_vector_tab(parent, datafile, gridfile=None, draw_callback=None):
    frame = tk.Frame(parent)
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)  # single column for controls

    # load dataset early to populate U/V menus
    try:
        ds = Dataset(datafile)
    except Exception as e:
        messagebox.showerror("Error", f"Cannot open file in vector tab:\n{e}")
        return {"frame": frame}

    state = {"u_name": None, "v_name": None, "lon": None, "lat": None, "sin_t": None, "cos_t": None, "mask_t": None}

    # RIGHT (full width): canvas + inner controls_frame with vertical scrollbar
    right_container = tk.Frame(frame)
    right_container.grid(row=0, column=0, sticky="nsew", padx=(4,6), pady=6)
    right_container.grid_rowconfigure(0, weight=1)
    right_container.grid_columnconfigure(0, weight=1)

    canvas = tk.Canvas(right_container, highlightthickness=0)
    canvas.grid(row=0, column=0, sticky="nsew")
    vscroll = tk.Scrollbar(right_container, orient="vertical", command=canvas.yview)
    vscroll.grid(row=0, column=1, sticky="ns")
    canvas.configure(yscrollcommand=vscroll.set)

    controls_frame = tk.Frame(canvas)
    canvas_window = canvas.create_window((0,0), window=controls_frame, anchor="nw")

    def _on_frame_config(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig(canvas_window, width=canvas.winfo_width())
    controls_frame.bind("<Configure>", _on_frame_config)
    _bind_mousewheel(controls_frame, canvas)

    # populate controls_frame
    row_v = 0
    tk.Label(controls_frame, text="Vector Field Settings", font=("DejaVu Sans Mono", 12, "bold")).grid(row=row_v, column=0, columnspan=2, pady=8)
    row_v += 1

    # U variable
    tk.Label(controls_frame, text="U variable:").grid(row=row_v, column=0, sticky="e", padx=5, pady=2)
    u_var_var = tk.StringVar(value="")
    u_menu = tk.OptionMenu(controls_frame, u_var_var, "")
    u_menu.grid(row=row_v, column=1, sticky="w", padx=5, pady=2)
    row_v += 1

    # V variable
    tk.Label(controls_frame, text="V variable:").grid(row=row_v, column=0, sticky="e", padx=5, pady=2)
    v_var_var = tk.StringVar(value="")
    v_menu = tk.OptionMenu(controls_frame, v_var_var, "")
    v_menu.grid(row=row_v, column=1, sticky="w", padx=5, pady=2)
    row_v += 1

    # Need rotate
    tk.Label(controls_frame, text="Need rotate:").grid(row=row_v, column=0, sticky="e", padx=5, pady=2)
    need_rotate_vector = tk.StringVar(value="True")
    tk.OptionMenu(controls_frame, need_rotate_vector, "True", "False").grid(row=row_v, column=1, sticky="w")
    row_v += 1

    # Layer select
    tk.Label(controls_frame, text="Layer:").grid(row=row_v, column=0, sticky="e", padx=5, pady=2)
    layer_var_vector = tk.StringVar(value="0")
    layer_menu_vector = tk.OptionMenu(controls_frame, layer_var_vector, "0")
    layer_menu_vector.config(width=5)
    layer_menu_vector.grid(row=row_v, column=1, sticky="w")
    row_v += 1


    # Map customization header
    tk.Label(controls_frame, text="Map Customization", font=("DejaVu Sans Mono", 12, "bold")).grid(row=row_v, column=0, columnspan=2, pady=8)
    row_v += 1

    # Max number of arrows
    tk.Label(controls_frame, text="Max. number of arrows:").grid(row=row_v, column=0, sticky="e", padx=5, pady=2)
    quiver_entry_vector = tk.Entry(controls_frame, width=10)
    quiver_entry_vector.insert(0, "20")
    quiver_entry_vector.grid(row=row_v, column=1, sticky="w", padx=5, pady=2)
    row_v += 1


    # Value range
    tk.Label(controls_frame, text="Value range:").grid(row=row_v, column=0, sticky="e", padx=5, pady=2)
    frame_minmax_vector = tk.Frame(controls_frame)
    frame_minmax_vector.grid(row=row_v, column=1, sticky="w", padx=5, pady=2)
    tk.Label(frame_minmax_vector, text="Min").pack(side="left")
    entry_min_vector = tk.Entry(frame_minmax_vector, width=6)
    entry_min_vector.pack(side="left", padx=(2, 5))
    tk.Label(frame_minmax_vector, text="Max").pack(side="left")
    entry_max_vector = tk.Entry(frame_minmax_vector, width=6)
    entry_max_vector.pack(side="left", padx=(2, 0))
    row_v += 1

    # Color palette (grouped)
    tk.Label(controls_frame, text="Color palette:").grid(row=row_v, column=0, sticky="e", padx=5, pady=2)
    cmap_var_vector = tk.StringVar(value="YlOrBr")
    menu_button = tk.Menubutton(controls_frame, textvariable=cmap_var_vector, relief="raised")
    menu = tk.Menu(menu_button, tearoff=False)
    menu_button["menu"] = menu

    def classify_cmap(name):
        name_lower = name.lower()
        if any(x in name_lower for x in ["_r"]):
            name_lower = name_lower.replace("_r", "")
        if name_lower in ["jet", "viridis", "plasma", "inferno", "magma", "cividis", "greens", "blues"]:
            return "Sequential"
        elif name_lower in ["coolwarm", "bwr", "rdbu", "piyg", "prgn", "brbg"]:
            return "Diverging"
        elif name_lower in ["set1", "set2", "tab10", "tab20", "pastel1"]:
            return "Qualitative"
        else:
            return "Miscellaneous"

    categories = {"Sequential": [], "Diverging": [], "Qualitative": [], "Miscellaneous": []}
    try:
        for name in sorted(cm.cmap_d.keys()):
            cat = classify_cmap(name)
            categories[cat].append(name)
    except Exception:
        categories = {"Sequential": ["viridis", "jet"], "Diverging": ["coolwarm"], "Qualitative": ["tab10"], "Miscellaneous": []}

    for cat_name, cmap_list in categories.items():
        sub = tk.Menu(menu, tearoff=False)
        for cmap_name in sorted(cmap_list):
            sub.add_radiobutton(label=cmap_name, variable=cmap_var_vector, value=cmap_name)
        menu.add_cascade(label=cat_name, menu=sub)

    menu_button.grid(row=row_v, column=1, sticky="w")
    row_v += 1

    # Cmap range
    tk.Label(controls_frame, text="Cmap range:").grid(row=row_v, column=0, sticky="e", padx=5, pady=2)
    frame_cmap_vector = tk.Frame(controls_frame)
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

    # Map resolution
    tk.Label(controls_frame, text="Map resolution:").grid(row=row_v, column=0, sticky="e", padx=5, pady=2)
    res_map = {"Crude": "c", "Low": "l", "Intermediate": "i", "High": "h", "Full": "f"}
    res_display_var_vector = tk.StringVar(value="Intermediate")
    tk.OptionMenu(controls_frame, res_display_var_vector, *res_map.keys()).grid(row=row_v, column=1, sticky="w")
    row_v += 1


    # Lon/Lat bounds
    tk.Label(controls_frame, text="Longitude bounds:").grid(row=row_v, column=0, sticky="e", padx=5, pady=2)
    frame_lon_vector = tk.Frame(controls_frame)
    frame_lon_vector.grid(row=row_v, column=1, sticky="w", padx=5, pady=2)
    tk.Label(frame_lon_vector, text="Min").pack(side="left")
    lon_min_vector = tk.Entry(frame_lon_vector, width=6)
    lon_min_vector.pack(side="left", padx=(2, 5))
    tk.Label(frame_lon_vector, text="Max").pack(side="left")
    lon_max_vector = tk.Entry(frame_lon_vector, width=6)
    lon_max_vector.pack(side="left", padx=(2, 0))
    row_v += 1

    tk.Label(controls_frame, text="Latitude bounds:").grid(row=row_v, column=0, sticky="e", padx=5, pady=2)
    frame_lat_vector = tk.Frame(controls_frame)
    frame_lat_vector.grid(row=row_v, column=1, sticky="w", padx=5, pady=2)
    tk.Label(frame_lat_vector, text="Min").pack(side="left")
    lat_min_vector = tk.Entry(frame_lat_vector, width=6)
    lat_min_vector.pack(side="left", padx=(2, 5))
    tk.Label(frame_lat_vector, text="Max").pack(side="left")
    lat_max_vector = tk.Entry(frame_lat_vector, width=6)
    lat_max_vector.pack(side="left", padx=(2, 0))
    row_v += 1

    # Figure DPI
    tk.Label(controls_frame, text="Figure DPI:").grid(row=row_v, column=0, sticky="e", padx=5, pady=2)
    dpi_entry_vector = tk.Entry(controls_frame, width=10)
    dpi_entry_vector.insert(0, "100")
    dpi_entry_vector.grid(row=row_v, column=1, sticky="w", padx=5, pady=2)
    row_v += 1

    # Scale
    tk.Label(controls_frame, text="Scale:").grid(row=row_v, column=0, sticky="e", padx=5, pady=2)
    scale_entry_vector = tk.Entry(controls_frame, width=10)
    scale_entry_vector.insert(0, "3")
    scale_entry_vector.grid(row=row_v, column=1, sticky="w", padx=5, pady=2)
    row_v += 1

    # Redraw function (calls draw_vector_plot or draw_callback)
    def redraw():
        def safe_float(v):
            try:
                return float(v)
            except Exception:
                return None

        opts = {
            "need_rotate": (need_rotate_vector.get() == "True"),
            "vmin": safe_float(entry_min_vector.get()) if entry_min_vector else None,
            "vmax": safe_float(entry_max_vector.get()) if entry_max_vector else None,
            "cmap": cmap_var_vector.get(),
            "cmap_min": safe_float(cmap_min_vector.get()) if cmap_min_vector else 0,
            "cmap_max": safe_float(cmap_max_vector.get()) if cmap_max_vector else 0.7,
            "layer": int(layer_var_vector.get()) if layer_var_vector.get().isdigit() else 0,
            "lon_min": safe_float(lon_min_vector.get()) if lon_min_vector else None,
            "lon_max": safe_float(lon_max_vector.get()) if lon_max_vector else None,
            "lat_min": safe_float(lat_min_vector.get()) if lat_min_vector else None,
            "lat_max": safe_float(lat_max_vector.get()) if lat_max_vector else None,
            "resolution": res_map.get(res_display_var_vector.get(), "i"),
            "dpi": int(dpi_entry_vector.get()) if dpi_entry_vector.get().isdigit() else 100,
            "scale": int(scale_entry_vector.get()) if scale_entry_vector.get().isdigit() else 3,
        }

        u_name = u_var_var.get()
        v_name = v_var_var.get()
        if not u_name or not v_name:
            messagebox.showinfo("Info", "Please select both U and V variables for vector mode.")
            return

        try:
            var_u = np.squeeze(ds.variables[u_name][:])
            var_v = np.squeeze(ds.variables[v_name][:])
        except Exception as e:
            messagebox.showerror("Error", f"Cannot read U/V variables:\n{e}")
            return


        try:
            quiver_max_n = int(quiver_entry_vector.get())
        except Exception:
            quiver_max_n = 10


        # --- Load grid ---
        with Dataset(gridfile) as fgrid:
            state["sin_t"] = fgrid.variables.get("gridrotsin_t")[:]
            state["cos_t"] = fgrid.variables.get("gridrotcos_t")[:]

            mask_t_var = fgrid.variables.get("mask_t")

            if mask_t_var is not None:
                mask_t = mask_t_var[:] if mask_t_var.ndim == 2 else mask_t_var[0, :, :]
                state["mask_t"] = mask_t

        # --- Lấy lại lon/lat dạng T nếu chưa có ---
        lon_t, lat_t = get_grid_coords(gridfile, "t")
        state["lon"], state["lat"] = lon_t, lat_t


        print (state.get("lon").shape, state.get("lat").shape)

        print ('Chosen options', opts)

        if callable(draw_callback):
            try:
                draw_callback(u_name, v_name, var_u, var_v, state.get("lon"), state.get("lat"), opts, state)
            except Exception as e:
                messagebox.showerror("Error", f"draw_callback failed:\n{e}")
        elif callable(draw_vector_plot):
            try:
                draw_vector_plot(var_u, var_v, state.get("lon"), state.get("lat"), opts, state, quiver_max_n=quiver_max_n)

            except Exception as e:
                messagebox.showerror("Error", f"draw_vector_plot failed:\n{e}")
        else:
            print("[Vector redraw] missing draw function; opts:", opts)


    # ---- Endof function redraw-------#
    ####################################



    redraw_btn_vector = tk.Button(controls_frame, text="Draw Map", bg="lightblue", command=redraw)
    redraw_btn_vector.grid(row=row_v, column=0, columnspan=2, pady=10)
    row_v += 1

    # Fill u_menu / v_menu choices (prefer variables containing 'u' / 'v')
    u_menu["menu"].delete(0, "end")
    v_menu["menu"].delete(0, "end")
    u_list = [var for var in ds.variables.keys() if "u" in var.lower()]
    v_list = [var for var in ds.variables.keys() if "v" in var.lower()]
    if not u_list:
        u_list = list(ds.variables.keys())
    if not v_list:
        v_list = list(ds.variables.keys())
    for varname in u_list:
        u_menu["menu"].add_command(label=varname, command=lambda v=varname: u_var_var.set(v))
    for varname in v_list:
        v_menu["menu"].add_command(label=varname, command=lambda v=varname: v_var_var.set(v))
    if u_list:
        u_var_var.set(u_list[0])
    if v_list:
        v_var_var.set(v_list[0])
    
        
    # on_vector_select: update layer menu depending on u/v variables
    def on_vector_select(*_):
        u_name = u_var_var.get()
        v_name = v_var_var.get()
        if not u_name or not v_name:
            return
        if u_name not in ds.variables or v_name not in ds.variables:
            return
        var_u = np.squeeze(ds.variables[u_name][:])
        var_v = np.squeeze(ds.variables[v_name][:])
        nd = max(getattr(var_u, "ndim", 0), getattr(var_v, "ndim", 0))
        menu_v = layer_menu_vector["menu"]
        menu_v.delete(0, "end")
        if nd == 3:
            nlayer = var_u.shape[0]
            for i in range(nlayer):
                menu_v.add_command(label=str(i), command=lambda v=str(i): layer_var_vector.set(v))
            layer_var_vector.set("0")
        else:
            menu_v.add_command(label="0", command=lambda: layer_var_vector.set("0"))
            layer_var_vector.set("0")

        # update grid lon/lat if possible
        suffix = "t"
        for s in ["u", "v", "f", "t"]:
            if u_name.lower().endswith(s) or v_name.lower().endswith(s):
                suffix = s
                break
        lon, lat = get_grid_coords(gridfile, suffix)
        state["lon"], state["lat"] = lon, lat
        state["u_name"], state["v_name"] = u_name, v_name

    u_var_var.trace_add("write", on_vector_select)
    v_var_var.trace_add("write", on_vector_select)

    # ensure canvas resizes properly
    def _on_canvas_config(event):
        canvas.itemconfig(canvas_window, width=event.width)
    canvas.bind("<Configure>", _on_canvas_config)

    # initial update for layer menu based on default u/v
    on_vector_select()

    return {
        "frame": frame,
        "u_var_var": u_var_var,
        "v_var_var": v_var_var,
        "layer_var_vector": layer_var_vector,
        "layer_menu_vector": layer_menu_vector,
        "redraw_btn_vector": redraw_btn_vector,
        "state": state,
    }
