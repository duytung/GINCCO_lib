# scalar_tab.py
"""
Scalar tab: Variables list (left) + Data selection and Map Customization (right).
build_scalar_tab(parent, datafile, gridfile=None, draw_callback=None)
 - draw_callback signature (optional):
     draw_callback(varname, var, lon, lat, opts, state)
"""
import tkinter as tk
from tkinter import messagebox, END
import numpy as np
from netCDF4 import Dataset
import matplotlib.cm as cm

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

def _bind_mousewheel(widget, target):
    """Helper: bind mousewheel on widget to scroll target (works on Windows/mac/Linux)."""
    def _on_mousewheel(event):
        if event.num == 5 or event.delta < 0:
            target.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            target.yview_scroll(-1, "units")
    # Wheel events
    widget.bind("<Enter>", lambda e: widget.bind_all("<MouseWheel>", _on_mousewheel))
    widget.bind("<Leave>", lambda e: widget.unbind_all("<MouseWheel>"))
    # For X11 systems (Button-4/5)
    widget.bind("<Enter>", lambda e: widget.bind_all("<Button-4>", _on_mousewheel))
    widget.bind("<Enter>", lambda e: widget.bind_all("<Button-5>", _on_mousewheel))
    widget.bind("<Leave>", lambda e: widget.unbind_all("<Button-4>"))
    widget.bind("<Leave>", lambda e: widget.unbind_all("<Button-5>"))

def build_scalar_tab(parent, datafile, gridfile=None, draw_callback=None):
    # outer frame for the tab
    frame = tk.Frame(parent, bg="#f5f5f5")
    # make frame's grid expand
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=0)  # left (list) keep fixed width
    frame.grid_columnconfigure(1, weight=1)  # right (controls) expand

    # state
    state = {"varname": None, "var": None, "lon": None, "lat": None, "suffix": "t"}

    # LEFT: container with Listbox + vertical scrollbar
    left_container = tk.Frame(frame)
    left_container.grid(row=0, column=0, sticky="nsew", padx=(6,4), pady=6)
    # Label row (0) fixed, listbox row (1) expands
    left_container.grid_rowconfigure(0, weight=0)
    left_container.grid_rowconfigure(1, weight=1)
    left_container.grid_columnconfigure(0, weight=1)

    tk.Label(left_container, text="Variables", font=("DejaVu Sans Mono", 11, "bold")).grid(row=0, column=0, sticky="w", pady=(0,6))

    listbox_frame = tk.Frame(left_container)
    listbox_frame.grid(row=1, column=0, sticky="nsew")
    listbox_frame.grid_rowconfigure(0, weight=1)
    listbox_frame.grid_columnconfigure(0, weight=1)

    listbox = tk.Listbox(listbox_frame, activestyle="dotbox")
    listbox.grid(row=0, column=0, sticky="nsew")
    vscroll_left = tk.Scrollbar(listbox_frame, orient="vertical", command=listbox.yview)
    vscroll_left.grid(row=0, column=1, sticky="ns")
    listbox.configure(yscrollcommand=vscroll_left.set)

    # Try open dataset and populate listbox
    try:
        ds = Dataset(datafile)
    except Exception as e:
        messagebox.showerror("Error", f"Cannot open file in scalar tab:\n{e}")
        return {"frame": frame}
    for v in ds.variables.keys():
        listbox.insert(END," " + v)

    # bind mousewheel to left listbox
    _bind_mousewheel(listbox, listbox)

    # RIGHT: use a Canvas + inner frame so we can have a vertical scrollbar for many controls
    right_container = tk.Frame(frame)
    right_container.grid(row=0, column=1, sticky="nsew", padx=(4,6), pady=6)
    right_container.grid_rowconfigure(0, weight=1)
    right_container.grid_columnconfigure(0, weight=1)

    canvas = tk.Canvas(right_container, highlightthickness=0)
    canvas.grid(row=0, column=0, sticky="nsew")

    vscroll_right = tk.Scrollbar(right_container, orient="vertical", command=canvas.yview)
    vscroll_right.grid(row=0, column=1, sticky="ns")
    canvas.configure(yscrollcommand=vscroll_right.set)

    # inner frame inside canvas where we place all controls
    controls_frame = tk.Frame(canvas)
    # create window in canvas
    canvas_window = canvas.create_window((0,0), window=controls_frame, anchor="nw")

    # ensure canvas scrollregion updates when controls_frame size changes
    def _on_frame_config(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
        # make inner frame width match canvas width
        canvas.itemconfig(canvas_window, width=canvas.winfo_width())
    controls_frame.bind("<Configure>", _on_frame_config)

    # allow mousewheel scrolling when pointer over controls_frame
    _bind_mousewheel(controls_frame, canvas)

    # now populate controls_frame with the original right-side widgets
    row_s = 0
    tk.Label(controls_frame,text="Data selection",
        font=("DejaVu Sans Mono", 12, "bold")).grid(row=row_s, column=0, columnspan=2, pady=8, sticky="")
    row_s += 1

    # Layer/Depth controls (single row)
    mode_var = tk.StringVar(value="layer")   # 'layer' or 'depth'
    layer_var = tk.StringVar(value="0")
    depth_var = tk.StringVar(value="")

    top_row = tk.Frame(controls_frame)
    top_row.grid(row=row_s, column=0, columnspan=2, sticky="we", pady=(4,6))
    rb_layer = tk.Radiobutton(top_row, text="Layer", variable=mode_var, value="layer")
    rb_layer.pack(side="left")
    top_layer_menu = tk.OptionMenu(top_row, layer_var, "0")
    top_layer_menu.config(width=2)
    top_layer_menu.pack(side="left", padx=(6,10))
    rb_depth = tk.Radiobutton(top_row, text="Depth", variable=mode_var, value="depth")
    rb_depth.pack(side="left")
    depth_entry = tk.Entry(top_row, textvariable=depth_var, width=12)
    depth_entry.pack(side="left", padx=(6,0))
    row_s += 1

    # Map Customization header
    tk.Label(controls_frame,text="Map customization",
        font=("DejaVu Sans Mono", 12, "bold")).grid(row=row_s, column=0, columnspan=2, pady=8, sticky="")
    row_s += 1

    # Value range
    tk.Label(controls_frame, text="Value range:").grid(row=row_s, column=0, sticky="e", padx=5, pady=2)
    frame_minmax_scalar = tk.Frame(controls_frame)
    frame_minmax_scalar.grid(row=row_s, column=1, sticky="w", padx=5, pady=2)
    tk.Label(frame_minmax_scalar, text="Min").pack(side="left")
    entry_min_scalar = tk.Entry(frame_minmax_scalar, width=6)
    entry_min_scalar.pack(side="left", padx=(2, 5))
    tk.Label(frame_minmax_scalar, text="Max").pack(side="left")
    entry_max_scalar = tk.Entry(frame_minmax_scalar, width=6)
    entry_max_scalar.pack(side="left", padx=(2, 0))
    row_s += 1

    # Color palette (grouped)
    tk.Label(controls_frame, text="Color palette:").grid(row=row_s, column=0, sticky="e", padx=5, pady=2)
    cmap_var_scalar = tk.StringVar(value="jet")

    menu_button = tk.Menubutton(controls_frame, textvariable=cmap_var_scalar, relief="raised")
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
            sub.add_radiobutton(label=cmap_name, variable=cmap_var_scalar, value=cmap_name)
        menu.add_cascade(label=cat_name, menu=sub)

    menu_button.grid(row=row_s, column=1, sticky="w")
    row_s += 1

    # Map resolution
    tk.Label(controls_frame, text="Map resolution:").grid(row=row_s, column=0, sticky="e", padx=5, pady=2)
    res_map = {"Crude": "c", "Low": "l", "Intermediate": "i", "High": "h", "Full": "f"}
    res_display_var_scalar = tk.StringVar(value="Intermediate")
    tk.OptionMenu(controls_frame, res_display_var_scalar, *res_map.keys()).grid(row=row_s, column=1, sticky="w")
    row_s += 1

    # Lon/Lat bounds
    tk.Label(controls_frame, text="Longitude bounds:").grid(row=row_s, column=0, sticky="e", padx=5, pady=2)
    frame_lon_scalar = tk.Frame(controls_frame)
    frame_lon_scalar.grid(row=row_s, column=1, sticky="w", padx=5, pady=2)
    tk.Label(frame_lon_scalar, text="Min").pack(side="left")
    lon_min_scalar = tk.Entry(frame_lon_scalar, width=6)
    lon_min_scalar.pack(side="left", padx=(2, 5))
    tk.Label(frame_lon_scalar, text="Max").pack(side="left")
    lon_max_scalar = tk.Entry(frame_lon_scalar, width=6)
    lon_max_scalar.pack(side="left", padx=(2, 0))
    row_s += 1

    tk.Label(controls_frame, text="Latitude bounds:").grid(row=row_s, column=0, sticky="e", padx=5, pady=2)
    frame_lat_scalar = tk.Frame(controls_frame)
    frame_lat_scalar.grid(row=row_s, column=1, sticky="w", padx=5, pady=2)
    tk.Label(frame_lat_scalar, text="Min").pack(side="left")
    lat_min_scalar = tk.Entry(frame_lat_scalar, width=6)
    lat_min_scalar.pack(side="left", padx=(2, 5))
    tk.Label(frame_lat_scalar, text="Max").pack(side="left")
    lat_max_scalar = tk.Entry(frame_lat_scalar, width=6)
    lat_max_scalar.pack(side="left", padx=(2, 0))
    row_s += 1

    # Figure DPI
    tk.Label(controls_frame, text="Figure DPI:").grid(row=row_s, column=0, sticky="e", padx=5, pady=2)
    dpi_entry_scalar = tk.Entry(controls_frame, width=10)
    dpi_entry_scalar.insert(0, "100")
    dpi_entry_scalar.grid(row=row_s, column=1, sticky="w", padx=5, pady=2)
    row_s += 1

    # Redraw button and function
    def redraw():
        def safe_float(v):
            try:
                return float(v)
            except Exception:
                return None

        opts = {
            "vmin": safe_float(entry_min_scalar.get()) if entry_min_scalar else None,
            "vmax": safe_float(entry_max_scalar.get()) if entry_max_scalar else None,
            "cmap": cmap_var_scalar.get() if cmap_var_scalar else None,
            "lon_min": safe_float(lon_min_scalar.get()) if lon_min_scalar else None,
            "lon_max": safe_float(lon_max_scalar.get()) if lon_max_scalar else None,
            "lat_min": safe_float(lat_min_scalar.get()) if lat_min_scalar else None,
            "lat_max": safe_float(lat_max_scalar.get()) if lat_max_scalar else None,
            "resolution": res_map[res_display_var_scalar.get()] if res_display_var_scalar else "i",
            "dpi": int(dpi_entry_scalar.get()) if dpi_entry_scalar and dpi_entry_scalar.get().isdigit() else 100,
        }

        if mode_var.get() == "depth":
            dtxt = depth_var.get().strip()
            if dtxt == "":
                messagebox.showinfo("Info", "Please enter a depth value.")
                return
            try:
                opts["depth"] = float(dtxt)
            except Exception:
                messagebox.showinfo("Info", "Invalid depth value.")
                return
        else:
            opts["layer"] = int(layer_var.get()) if layer_var.get().isdigit() else 0

        if not state.get("var"):
            messagebox.showinfo("Info", "Please select a variable first.")
            return

        if callable(draw_callback):
            try:
                draw_callback(state["varname"], state["var"], state["lon"], state["lat"], opts, state)
            except Exception as e:
                messagebox.showerror("Error", f"draw_callback failed:\n{e}")
        else:
            print("[Scalar redraw] var:", state["varname"], "opts:", opts)

    redraw_btn_scalar = tk.Button(controls_frame, text="Draw Map", bg="lightblue", command=redraw)
    redraw_btn_scalar.grid(row=row_s, column=0, columnspan=2, pady=10)
    row_s += 1

    # Update layer menu when variable selected
    def update_layer_menu_and_state(varname):
        try:
            var = ds.variables[varname]
        except Exception:
            return
        data = np.squeeze(var[:])
        nd = data.ndim
        menu = top_layer_menu["menu"]
        menu.delete(0, "end")
        if nd == 3:
            for i in range(data.shape[0]):
                menu.add_command(label=str(i), command=lambda v=str(i): layer_var.set(v))
            layer_var.set("0")
        else:
            menu.add_command(label="0", command=lambda: layer_var.set("0"))
            layer_var.set("0")

        # update grid coords and state
        suffix = "t"
        for s in ["u", "v", "f", "t"]:
            if varname.lower().endswith(s):
                suffix = s
                break
        state["suffix"] = suffix
        lon, lat = get_grid_coords(gridfile, suffix)
        state["lon"], state["lat"] = lon, lat
        state["varname"] = varname
        state["var"] = var

    def on_var_change(evt):
        sel = listbox.curselection()
        if not sel:
            return
        raw = listbox.get(sel)
        varname = raw.strip()  # REMOVE leading/trailing spaces if any
        update_layer_menu_and_state(varname)

    listbox.bind("<<ListboxSelect>>", on_var_change)
    listbox.bind("<Double-Button-1>", on_var_change)

    # Mode switching: enable/disable widgets accordingly
    def set_mode(*_):
        if mode_var.get() == "layer":
            try:
                top_layer_menu.config(state="normal")
            except Exception:
                pass
            try:
                depth_entry.config(state="disabled")
            except Exception:
                pass
        else:
            try:
                top_layer_menu.config(state="disabled")
            except Exception:
                pass
            try:
                depth_entry.config(state="normal")
            except Exception:
                pass

    mode_var.trace_add("write", lambda *a: set_mode())
    depth_var.trace_add("write", lambda *a: mode_var.set("depth") if depth_var.get().strip() else None)
    set_mode()

    # ensure canvas resizes properly: if the right_container changes width, update inner window width
    def _on_canvas_config(event):
        canvas.itemconfig(canvas_window, width=event.width)
    canvas.bind("<Configure>", _on_canvas_config)

    # return handles
    return {
        "frame": frame,
        "listbox": listbox,
        "top_layer_menu": top_layer_menu,
        "layer_var": layer_var,
        "depth_var": depth_var,
        "redraw_btn": redraw_btn_scalar,
        "set_mode_func": set_mode,
        "state": state,
    }
