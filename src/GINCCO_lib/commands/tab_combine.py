# combine_tab.py
"""
Combine tab: Scalar setting + Vector setting on one map.

Public API:
    build_combine_tab(parent, datafile, gridfile=None, draw_callback=None)

draw_callback signature (optional):
    draw_callback(scalar_name, scalar_var, var_u, var_v, lon, lat, opts, state)

If draw_callback is None, fallback to local draw_map_combine imported from .draw_combine.
"""

import tkinter as tk
from tkinter import messagebox, END
import numpy as np
from netCDF4 import Dataset
import matplotlib.cm as cm

from .plot_combine_map import draw_map_combine


def get_grid_coords(grid_file, suffix):
    """Read longitude/latitude from grid file for a given suffix (t/u/v/f)."""
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


def _build_cmap_menu(parent, cmap_var):
    """Create grouped colormap menu like in scalar_tab."""
    menu_button = tk.Menubutton(parent, textvariable=cmap_var, relief="raised")
    menu = tk.Menu(menu_button, tearoff=False)
    menu_button["menu"] = menu

    def classify_cmap(name):
        name_lower = name.lower()
        if "_r" in name_lower:
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
        categories = {
            "Sequential": ["viridis", "jet"],
            "Diverging": ["coolwarm"],
            "Qualitative": ["tab10"],
            "Miscellaneous": [],
        }

    for cat_name, cmap_list in categories.items():
        sub = tk.Menu(menu, tearoff=False)
        for cmap_name in sorted(cmap_list):
            sub.add_radiobutton(label=cmap_name, variable=cmap_var, value=cmap_name)
        menu.add_cascade(label=cat_name, menu=sub)

    return menu_button


def build_combine_tab(parent, datafile, gridfile=None, draw_callback=None):
    """
    Build the Combine tab.

    Returns a dict with:
        - frame
        - state
        - redraw_btn
        - scalar_var_var
        - scalar_layer_var
        - u_var_var
        - v_var_var
        - layer_var_vector
    """
    frame = tk.Frame(parent)
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    # ---- Open dataset ----
    try:
        ds = Dataset(datafile)
    except Exception as e:
        messagebox.showerror("Error", f"Cannot open file in combine tab:\n{e}")
        return {"frame": frame}

    # Shared state
    state = {
        "scalar_name": None,
        "u_name": None,
        "v_name": None,
        "lon": None,
        "lat": None,
        "sin_t": None,
        "cos_t": None,
        "mask_t": None,
    }

    # ---- Scrollable right panel ----
    container = tk.Frame(frame)
    container.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
    container.grid_rowconfigure(0, weight=1)
    container.grid_columnconfigure(0, weight=1)

    canvas = tk.Canvas(container, highlightthickness=0)
    canvas.grid(row=0, column=0, sticky="nsew")

    vscroll = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
    vscroll.grid(row=0, column=1, sticky="ns")
    canvas.configure(yscrollcommand=vscroll.set)

    controls_frame = tk.Frame(canvas)
    canvas_window = canvas.create_window((0, 0), window=controls_frame, anchor="nw")

    def _on_frame_config(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig(canvas_window, width=canvas.winfo_width())

    controls_frame.bind("<Configure>", _on_frame_config)
    _bind_mousewheel(controls_frame, canvas)

    def _on_canvas_config(event):
        canvas.itemconfig(canvas_window, width=event.width)
    canvas.bind("<Configure>", _on_canvas_config)

    # ------------------------------------------------------------------
    # Scalar setting
    # ------------------------------------------------------------------
    row = 0
    tk.Label(
        controls_frame,
        text="Scalar setting",
        font=("DejaVu Sans Mono", 12, "bold"),
    ).grid(row=row, column=0, columnspan=2, pady=8, sticky="")
    row += 1

    # Scalar variable choice
    tk.Label(controls_frame, text="Scalar variable:").grid(
        row=row, column=0, sticky="e", padx=5, pady=2
    )
    scalar_var_var = tk.StringVar(value="")
    scalar_menu = tk.OptionMenu(controls_frame, scalar_var_var, "")
    scalar_menu.grid(row=row, column=1, sticky="w", padx=5, pady=2)
    row += 1

    # Scalar layer choice
    tk.Label(controls_frame, text="Scalar layer:").grid(
        row=row, column=0, sticky="e", padx=5, pady=2
    )
    scalar_layer_var = tk.StringVar(value="0")
    scalar_layer_menu = tk.OptionMenu(controls_frame, scalar_layer_var, "0")
    scalar_layer_menu.config(width=4)
    scalar_layer_menu.grid(row=row, column=1, sticky="w", padx=5, pady=2)
    row += 1

    # Value range
    tk.Label(controls_frame, text="Value range:").grid(
        row=row, column=0, sticky="e", padx=5, pady=2
    )
    frame_minmax_scalar = tk.Frame(controls_frame)
    frame_minmax_scalar.grid(row=row, column=1, sticky="w", padx=5, pady=2)
    tk.Label(frame_minmax_scalar, text="Min").pack(side="left")
    entry_min_scalar = tk.Entry(frame_minmax_scalar, width=6)
    entry_min_scalar.pack(side="left", padx=(2, 5))
    tk.Label(frame_minmax_scalar, text="Max").pack(side="left")
    entry_max_scalar = tk.Entry(frame_minmax_scalar, width=6)
    entry_max_scalar.pack(side="left", padx=(2, 0))
    row += 1

    # Color palette
    tk.Label(controls_frame, text="Color palette:").grid(
        row=row, column=0, sticky="e", padx=5, pady=2
    )
    cmap_var_scalar = tk.StringVar(value="jet")
    cmap_menu_btn = _build_cmap_menu(controls_frame, cmap_var_scalar)
    cmap_menu_btn.grid(row=row, column=1, sticky="w", padx=5, pady=2)
    row += 1

    # Map resolution
    tk.Label(controls_frame, text="Map resolution:").grid(
        row=row, column=0, sticky="e", padx=5, pady=2
    )
    res_map = {"Crude": "c", "Low": "l", "Intermediate": "i", "High": "h", "Full": "f"}
    res_display_var_scalar = tk.StringVar(value="Intermediate")
    tk.OptionMenu(controls_frame, res_display_var_scalar, *res_map.keys()).grid(
        row=row, column=1, sticky="w", padx=5, pady=2
    )
    row += 1

    # Lon/Lat bounds
    tk.Label(controls_frame, text="Longitude bounds:").grid(
        row=row, column=0, sticky="e", padx=5, pady=2
    )
    frame_lon_scalar = tk.Frame(controls_frame)
    frame_lon_scalar.grid(row=row, column=1, sticky="w", padx=5, pady=2)
    tk.Label(frame_lon_scalar, text="Min").pack(side="left")
    lon_min_scalar = tk.Entry(frame_lon_scalar, width=6)
    lon_min_scalar.pack(side="left", padx=(2, 5))
    tk.Label(frame_lon_scalar, text="Max").pack(side="left")
    lon_max_scalar = tk.Entry(frame_lon_scalar, width=6)
    lon_max_scalar.pack(side="left", padx=(2, 0))
    row += 1

    tk.Label(controls_frame, text="Latitude bounds:").grid(
        row=row, column=0, sticky="e", padx=5, pady=2
    )
    frame_lat_scalar = tk.Frame(controls_frame)
    frame_lat_scalar.grid(row=row, column=1, sticky="w", padx=5, pady=2)
    tk.Label(frame_lat_scalar, text="Min").pack(side="left")
    lat_min_scalar = tk.Entry(frame_lat_scalar, width=6)
    lat_min_scalar.pack(side="left", padx=(2, 5))
    tk.Label(frame_lat_scalar, text="Max").pack(side="left")
    lat_max_scalar = tk.Entry(frame_lat_scalar, width=6)
    lat_max_scalar.pack(side="left", padx=(2, 0))
    row += 1

    # Figure DPI
    tk.Label(controls_frame, text="Figure DPI:").grid(
        row=row, column=0, sticky="e", padx=5, pady=2
    )
    dpi_entry_scalar = tk.Entry(controls_frame, width=10)
    dpi_entry_scalar.insert(0, "100")
    dpi_entry_scalar.grid(row=row, column=1, sticky="w", padx=5, pady=2)
    row += 1

    # ------------------------------------------------------------------
    # Vector setting
    # ------------------------------------------------------------------
    tk.Label(
        controls_frame,
        text="Vector setting",
        font=("DejaVu Sans Mono", 12, "bold"),
    ).grid(row=row, column=0, columnspan=2, pady=8, sticky="")
    row += 1

    # U variable
    tk.Label(controls_frame, text="U variable:").grid(
        row=row, column=0, sticky="e", padx=5, pady=2
    )
    u_var_var = tk.StringVar(value="")
    u_menu = tk.OptionMenu(controls_frame, u_var_var, "")
    u_menu.grid(row=row, column=1, sticky="w", padx=5, pady=2)
    row += 1

    # V variable
    tk.Label(controls_frame, text="V variable:").grid(
        row=row, column=0, sticky="e", padx=5, pady=2
    )
    v_var_var = tk.StringVar(value="")
    v_menu = tk.OptionMenu(controls_frame, v_var_var, "")
    v_menu.grid(row=row, column=1, sticky="w", padx=5, pady=2)
    row += 1

    # Need rotate
    tk.Label(controls_frame, text="Need rotate:").grid(
        row=row, column=0, sticky="e", padx=5, pady=2
    )
    need_rotate_vector = tk.StringVar(value="True")
    tk.OptionMenu(controls_frame, need_rotate_vector, "True", "False").grid(
        row=row, column=1, sticky="w", padx=5, pady=2
    )
    row += 1

    # Layer select (for vector)
    tk.Label(controls_frame, text="Layer (vector):").grid(
        row=row, column=0, sticky="e", padx=5, pady=2
    )
    layer_var_vector = tk.StringVar(value="0")
    layer_menu_vector = tk.OptionMenu(controls_frame, layer_var_vector, "0")
    layer_menu_vector.config(width=5)
    layer_menu_vector.grid(row=row, column=1, sticky="w", padx=5, pady=2)
    row += 1

    # Max number of arrows
    tk.Label(controls_frame, text="Max. number of arrows:").grid(
        row=row, column=0, sticky="e", padx=5, pady=2
    )
    quiver_entry_vector = tk.Entry(controls_frame, width=10)
    quiver_entry_vector.insert(0, "20")
    quiver_entry_vector.grid(row=row, column=1, sticky="w", padx=5, pady=2)
    row += 1

    # Scale
    tk.Label(controls_frame, text="Scale:").grid(
        row=row, column=0, sticky="e", padx=5, pady=2
    )
    scale_entry_vector = tk.Entry(controls_frame, width=10)
    scale_entry_vector.insert(0, "400")
    scale_entry_vector.grid(row=row, column=1, sticky="w", padx=5, pady=2)
    row += 1

    # ------------------------------------------------------------------
    # Fill menus
    # ------------------------------------------------------------------
    all_vars = list(ds.variables.keys())
    # scalar: dùng tất cả biến
    scalar_menu["menu"].delete(0, "end")
    for varname in all_vars:
        scalar_menu["menu"].add_command(
            label=varname, command=lambda v=varname: scalar_var_var.set(v)
        )
    if all_vars:
        scalar_var_var.set(all_vars[0])

    # U / V prefer names containing 'u' / 'v'
    u_list = [v for v in all_vars if "u" in v.lower()]
    v_list = [v for v in all_vars if "v" in v.lower()]
    if not u_list:
        u_list = all_vars[:]
    if not v_list:
        v_list = all_vars[:]

    u_menu["menu"].delete(0, "end")
    v_menu["menu"].delete(0, "end")
    for varname in u_list:
        u_menu["menu"].add_command(
            label=varname, command=lambda v=varname: u_var_var.set(v)
        )
    for varname in v_list:
        v_menu["menu"].add_command(
            label=varname, command=lambda v=varname: v_var_var.set(v)
        )
    if u_list:
        u_var_var.set(u_list[0])
    if v_list:
        v_var_var.set(v_list[0])

    # ---------------- Scalar selection: update layer menu + state -------------
    def on_scalar_change(*_):
        name = scalar_var_var.get()
        if not name or name not in ds.variables:
            return

        var = ds.variables[name]
        data = np.squeeze(var[:])
        nd = data.ndim

        menu = scalar_layer_menu["menu"]
        menu.delete(0, "end")

        if nd == 3:
            for i in range(data.shape[0]):
                menu.add_command(
                    label=str(i), command=lambda v=str(i): scalar_layer_var.set(v)
                )
            scalar_layer_var.set("0")
        else:
            menu.add_command(label="0", command=lambda: scalar_layer_var.set("0"))
            scalar_layer_var.set("0")

        state["scalar_name"] = name

    scalar_var_var.trace_add("write", on_scalar_change)
    on_scalar_change()

    # ---------------- Vector selection: update layer menu + lon/lat ----------
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
                menu_v.add_command(
                    label=str(i), command=lambda v=str(i): layer_var_vector.set(v)
                )
            layer_var_vector.set("0")
        else:
            menu_v.add_command(label="0", command=lambda: layer_var_vector.set("0"))
            layer_var_vector.set("0")

        # lon/lat: dùng T-grid
        lon_t, lat_t = get_grid_coords(gridfile, "t") if gridfile else (None, None)
        state["lon"], state["lat"] = lon_t, lat_t
        state["u_name"], state["v_name"] = u_name, v_name

    u_var_var.trace_add("write", on_vector_select)
    v_var_var.trace_add("write", on_vector_select)
    on_vector_select()

    # ------------------------------------------------------------------
    # Redraw logic
    # ------------------------------------------------------------------
    def redraw():
        def safe_float(v):
            try:
                return float(v)
            except Exception:
                return None

        scalar_name = scalar_var_var.get()
        u_name = u_var_var.get()
        v_name = v_var_var.get()

        if not scalar_name:
            messagebox.showinfo("Info", "Please select a scalar variable.")
            return
        if not u_name or not v_name:
            messagebox.showinfo("Info", "Please select U and V variables.")
            return

        if scalar_name not in ds.variables:
            messagebox.showerror("Error", f"Scalar variable not found: {scalar_name}")
            return
        if u_name not in ds.variables or v_name not in ds.variables:
            messagebox.showerror("Error", "U/V variable not found in dataset.")
            return

        scalar_var = ds.variables[scalar_name]
        var_u = np.squeeze(ds.variables[u_name][:])
        var_v = np.squeeze(ds.variables[v_name][:])

        # scalar options (map customization + layer)
        scalar_opts = {
            "vmin": safe_float(entry_min_scalar.get()) if entry_min_scalar else None,
            "vmax": safe_float(entry_max_scalar.get()) if entry_max_scalar else None,
            "cmap": cmap_var_scalar.get() if cmap_var_scalar else "jet",
            "lon_min": safe_float(lon_min_scalar.get()) if lon_min_scalar else None,
            "lon_max": safe_float(lon_max_scalar.get()) if lon_max_scalar else None,
            "lat_min": safe_float(lat_min_scalar.get()) if lat_min_scalar else None,
            "lat_max": safe_float(lat_max_scalar.get()) if lat_max_scalar else None,
            "resolution": res_map.get(res_display_var_scalar.get(), "i")
            if res_display_var_scalar
            else "i",
            "dpi": int(dpi_entry_scalar.get())
            if dpi_entry_scalar and dpi_entry_scalar.get().isdigit()
            else 100,
            "layer": int(scalar_layer_var.get())
            if scalar_layer_var.get().isdigit()
            else 0,
        }

        # vector options
        try:
            quiver_max_n = int(quiver_entry_vector.get())
        except Exception:
            quiver_max_n = 20

        try:
            scale_val = int(scale_entry_vector.get())
        except Exception:
            scale_val = 400

        vector_opts = {
            "need_rotate": (need_rotate_vector.get() == "True"),
            "layer": int(layer_var_vector.get())
            if layer_var_vector.get().isdigit()
            else 0,
            "quiver_max_n": quiver_max_n,
            "scale": scale_val,
        }

        opts = {"scalar": scalar_opts, "vector": vector_opts}

        # Load grid info (sin, cos, mask_t) if available
        if gridfile:
            try:
                with Dataset(gridfile) as g:
                    state["sin_t"] = g.variables.get("gridrotsin_t")[:]
                    state["cos_t"] = g.variables.get("gridrotcos_t")[:]

                    mask_t_var = g.variables.get("mask_t")
                    if mask_t_var is not None:
                        mask_t = (
                            mask_t_var[:]
                            if mask_t_var.ndim == 2
                            else mask_t_var[0, :, :]
                        )
                        state["mask_t"] = mask_t
            except Exception as e:
                print("Could not load sin/cos/mask_t from grid:", e)

        # lon/lat: ensure we have them
        if state.get("lon") is None or state.get("lat") is None:
            lon_t, lat_t = get_grid_coords(gridfile, "t") if gridfile else (None, None)
            state["lon"], state["lat"] = lon_t, lat_t

        lon = state.get("lon")
        lat = state.get("lat")

        if lon is None or lat is None:
            messagebox.showerror(
                "Error",
                "No longitude/latitude information found (grid file missing or invalid).",
            )
            return

        print("Combine tab options:", opts)

        draw_fn = draw_callback if callable(draw_callback) else draw_map_combine
        if not callable(draw_fn):
            print("No valid draw_map_combine / draw_callback function.")
            return

        try:
            draw_fn(
                scalar_name,
                scalar_var,
                var_u,
                var_v,
                lon,
                lat,
                opts,
                state,
            )
        except Exception as e:
            messagebox.showerror("Error", f"draw_map_combine failed:\n{e}")

    redraw_btn = tk.Button(
        controls_frame, text="Draw Map", bg="lightblue", command=redraw
    )
    redraw_btn.grid(row=row, column=0, columnspan=2, pady=10)
    row += 1

    return {
        "frame": frame,
        "state": state,
        "redraw_btn": redraw_btn,
        "scalar_var_var": scalar_var_var,
        "scalar_layer_var": scalar_layer_var,
        "u_var_var": u_var_var,
        "v_var_var": v_var_var,
        "layer_var_vector": layer_var_vector,
    }
