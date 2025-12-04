# tab_section.py
"""
Tkinter tab for plotting vertical sections from netCDF data.

This module defines a single-column "Section" tab that lets the user:
- choose a variable from a netCDF file,
- set longitude/latitude endpoints for the section,
- configure figure size, color map, and value ranges,
- and plot the section by clicking a "Draw Section" button.
"""

import tkinter as tk
from tkinter import messagebox
import numpy as np
from netCDF4 import Dataset
import matplotlib.cm as cm

from .plot_section import draw_section


def _bind_mousewheel(widget, target):
    """
    Bind the mouse wheel to scroll a target widget when the pointer is over
    a given widget.

    Parameters
    ----------
    widget : tk.Widget
        The widget that listens for mouse enter/leave events.
    target : tk.Widget
        The widget whose y-view should be scrolled (typically a Canvas).
    """
    def _on_mousewheel(event):
        # Windows / macOS use event.delta; X11 often uses Button-4/5.
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

    def _on_enter(_):
        widget.bind_all("<MouseWheel>", _on_mousewheel)
        widget.bind_all("<Button-4>", _on_mousewheel)
        widget.bind_all("<Button-5>", _on_mousewheel)

    def _on_leave(_):
        widget.unbind_all("<MouseWheel>")
        widget.unbind_all("<Button-4>")
        widget.unbind_all("<Button-5>")

    widget.bind("<Enter>", _on_enter)
    widget.bind("<Leave>", _on_leave)


def get_grid_coords(grid_file, suffix):
    """
    Load longitude, latitude, depth, and mask arrays from a grid file.

    This helper looks for variables with names like:
    - longitude_<suffix>, latitude_<suffix>, depth_<suffix>, mask_<suffix>
    and falls back to:
    - longitude_t, latitude_t, depth_t, mask_t

    The mask is returned as a 2D array if possible (first layer is taken
    when the original mask is 3D).

    Parameters
    ----------
    grid_file : str or None
        Path to the grid netCDF file. If None or empty, all outputs are None.
    suffix : str
        Suffix to use when constructing variable names (e.g. "t", "u", "v", "f").

    Returns
    -------
    lon : np.ndarray or None
        Longitudes array, or None on failure.
    lat : np.ndarray or None
        Latitudes array, or None on failure.
    depth : np.ndarray or None
        Depth array, or None on failure.
    mask_t : np.ndarray or None
        2D mask array, or None on failure.
    """
    if not grid_file:
        return None, None, None, None

    try:
        with Dataset(grid_file) as g:
            try:
                lon = g.variables[f"longitude_{suffix}"][:]
                lat = g.variables[f"latitude_{suffix}"][:]
                depth = g.variables[f"depth_{suffix}"][:]
                mask = g.variables[f"mask_{suffix}"][:]
            except KeyError:
                # Fallback to "_t" variables if suffix-specific ones are missing
                lon = g.variables.get("longitude_t")
                lat = g.variables.get("latitude_t")
                depth = g.variables.get("depth_t")
                mask = g.variables.get("mask_t")

                if lon is not None and lat is not None:
                    lon, lat = lon[:], lat[:]
                else:
                    lon, lat = None, None

        # Ensure mask is 2D if available
        if mask is not None:
            mask_t = mask[:] if mask.ndim == 2 else mask[0, :, :]
        else:
            mask_t = None

        return lon, lat, depth, mask_t

    except Exception:
        # On any I/O or netCDF error, return all-None
        return None, None, None, None


def build_section_tab(parent, datafile, gridfile=None, draw_callback=None):
    """
    Build the "Section" tab for plotting vertical sections from a netCDF file.

    The tab allows users to:
    - select a variable from the data file,
    - define start/end points in longitude and latitude,
    - configure figure size, value range, colormap, and colormap range,
    - and plot the section via a "Draw Section" button.

    Parameters
    ----------
    parent : tk.Widget
        Parent widget, typically a ttk.Notebook or a Frame.
    datafile : str
        Path to the main netCDF file containing variables to plot.
    gridfile : str or None, optional
        Path to an optional grid netCDF file containing lon/lat/depth/mask
        information. If None, section plotting may be limited.
    draw_callback : callable or None, optional
        Optional custom draw function with signature:
            draw_callback(var_name, lon, lat, opts, state)
        If not provided, the default `draw_section` function is used instead.

    Returns
    -------
    dict
        A dictionary containing at least:
            {"frame": frame}
        where `frame` is the top-level Frame for this tab.
    """
    frame = tk.Frame(parent)
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)  # single column for controls

    # Load dataset early to populate the variable menu
    try:
        ds = Dataset(datafile)
    except Exception as e:
        messagebox.showerror("Error", f"Cannot open file:\n{e}")
        return {"frame": frame}

    # Shared state for this tab; passed into draw functions if needed
    state = {"var_name": None, "lon": None, "lat": None, "mask": None, "depth": None}

    # Main container: canvas + inner controls_frame with vertical scrollbar
    right_container = tk.Frame(frame)
    right_container.grid(row=0, column=0, sticky="nsew", padx=(4, 6), pady=6)
    right_container.grid_rowconfigure(0, weight=1)
    right_container.grid_columnconfigure(0, weight=1)

    canvas = tk.Canvas(right_container, highlightthickness=0)
    canvas.grid(row=0, column=0, sticky="nsew")
    vscroll = tk.Scrollbar(right_container, orient="vertical", command=canvas.yview)
    vscroll.grid(row=0, column=1, sticky="ns")
    canvas.configure(yscrollcommand=vscroll.set)

    controls_frame = tk.Frame(canvas)
    canvas.create_window(0, 0, window=controls_frame, anchor="nw")

    # Inner frame holding all controls
    inner_frame = tk.Frame(controls_frame)
    inner_frame.grid(row=0, column=0, sticky="nw")

    def _on_frame_config(event):
        """Update the scroll region whenever the controls frame is resized."""
        canvas.configure(scrollregion=canvas.bbox("all"))

    controls_frame.bind("<Configure>", _on_frame_config)

    # Enable mouse-wheel scrolling over the controls
    _bind_mousewheel(inner_frame, canvas)

    # ------------ Controls start here ------------ #
    row_v = 0
    tk.Label(
        inner_frame,
        text="Variable settings",
        font=("DejaVu Sans Mono", 12, "bold"),
    ).grid(row=row_v, column=0, columnspan=2, pady=8)
    row_v += 1

    # Variable selection
    tk.Label(inner_frame, text="Variable:").grid(
        row=row_v, column=0, sticky="e", padx=5, pady=2
    )
    v_var_var = tk.StringVar(value="")
    v_menu = tk.OptionMenu(inner_frame, v_var_var, "")
    v_menu.grid(row=row_v, column=1, sticky="w", padx=5, pady=2)
    row_v += 1

    # Lon/Lat bounds for the section endpoints
    tk.Label(inner_frame, text="Longitude of:").grid(
        row=row_v, column=0, sticky="e", padx=5, pady=2
    )
    frame_lon_vector = tk.Frame(inner_frame)
    frame_lon_vector.grid(row=row_v, column=1, sticky="w", padx=5, pady=2)

    tk.Label(frame_lon_vector, text="P1").pack(side="left")
    lon_min_vector = tk.Entry(frame_lon_vector, width=6)
    lon_min_vector.pack(side="left", padx=(2, 5))

    tk.Label(frame_lon_vector, text="P2").pack(side="left")
    lon_max_vector = tk.Entry(frame_lon_vector, width=6)
    lon_max_vector.pack(side="left", padx=(2, 0))
    row_v += 1

    tk.Label(inner_frame, text="Latitude of:").grid(
        row=row_v, column=0, sticky="e", padx=5, pady=2
    )
    frame_lat_vector = tk.Frame(inner_frame)
    frame_lat_vector.grid(row=row_v, column=1, sticky="w", padx=5, pady=2)

    tk.Label(frame_lat_vector, text="P1").pack(side="left")
    lat_min_vector = tk.Entry(frame_lat_vector, width=6)
    lat_min_vector.pack(side="left", padx=(2, 5))

    tk.Label(frame_lat_vector, text="P2").pack(side="left")
    lat_max_vector = tk.Entry(frame_lat_vector, width=6)
    lat_max_vector.pack(side="left", padx=(2, 0))
    row_v += 1


    # ----- Interpolation option ----- #
    tk.Label(
        inner_frame,
        text="Interpolation options",
        font=("DejaVu Sans Mono", 12, "bold"),
    ).grid(row=row_v, column=0, columnspan=2, pady=8)
    row_v += 1


    # Interpolation method
    tk.Label(inner_frame, text="Interpolation method:").grid(
        row=row_v, column=0, sticky="e", padx=5, pady=2
    )

    interp_var = tk.StringVar(value="bilinear")   # Default method
    interp_menu = tk.OptionMenu(inner_frame, interp_var, "bilinear", "idw")
    interp_menu.grid(row=row_v, column=1, sticky="w", padx=5, pady=2)

    row_v += 1

    # No of points
    tk.Label(inner_frame, text="No. of points:").grid(
        row=row_v, column=0, sticky="e", padx=5, pady=2
    )
    number_point = tk.Entry(inner_frame, width=10)
    number_point.insert(0, "100")
    number_point.grid(row=row_v, column=1, sticky="w", padx=5, pady=2)
    row_v += 1


    # Depth interval
    tk.Label(inner_frame, text="Depth interval:").grid(
        row=row_v, column=0, sticky="e", padx=5, pady=2
    )
    depth_interval = tk.Entry(inner_frame, width=10)
    depth_interval.insert(0, "1")
    depth_interval.grid(row=row_v, column=1, sticky="w", padx=5, pady=2)
    row_v += 1


    # ----- Section customization header ----- #
    tk.Label(
        inner_frame,
        text="Section Plot Customization",
        font=("DejaVu Sans Mono", 12, "bold"),
    ).grid(row=row_v, column=0, columnspan=2, pady=8)
    row_v += 1


    # Figure size
    tk.Label(inner_frame, text="Figure size:").grid(
        row=row_v, column=0, sticky="e", padx=5, pady=2
    )
    frame_figsize = tk.Frame(inner_frame)
    frame_figsize.grid(row=row_v, column=1, sticky="w", padx=5, pady=2)

    tk.Label(frame_figsize, text="Width").pack(side="left")
    entry_figsize_width = tk.Entry(frame_figsize, width=6)
    entry_figsize_width.pack(side="left", padx=(2, 5))
    entry_figsize_width.insert(0, "7")

    tk.Label(frame_figsize, text="Height").pack(side="left")
    entry_figsize_height = tk.Entry(frame_figsize, width=6)
    entry_figsize_height.pack(side="left", padx=(2, 0))
    entry_figsize_height.insert(0, "4")
    row_v += 1

    # Value range (data vmin/vmax)
    tk.Label(inner_frame, text="Value range:").grid(
        row=row_v, column=0, sticky="e", padx=5, pady=2
    )
    frame_minmax_vector = tk.Frame(inner_frame)
    frame_minmax_vector.grid(row=row_v, column=1, sticky="w", padx=5, pady=2)

    tk.Label(frame_minmax_vector, text="Min").pack(side="left")
    entry_min_vector = tk.Entry(frame_minmax_vector, width=6)
    entry_min_vector.pack(side="left", padx=(2, 5))

    tk.Label(frame_minmax_vector, text="Max").pack(side="left")
    entry_max_vector = tk.Entry(frame_minmax_vector, width=6)
    entry_max_vector.pack(side="left", padx=(2, 0))

    tk.Label(frame_minmax_vector, text="Interval").pack(side="left")
    entry_range_dv = tk.Entry(frame_minmax_vector, width=6)
    entry_range_dv.pack(side="left", padx=(2, 0))

    row_v += 1

    # Color palette (grouped by type)
    tk.Label(inner_frame, text="Color palette:").grid(
        row=row_v, column=0, sticky="e", padx=5, pady=2
    )
    cmap_var_vector = tk.StringVar(value="jet")
    menu_button = tk.Menubutton(inner_frame, textvariable=cmap_var_vector, relief="raised")
    menu = tk.Menu(menu_button, tearoff=False)
    menu_button["menu"] = menu

    def classify_cmap(name):
        """
        Classify a colormap name into a coarse category for grouping in the menu.
        """
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
        # Minimal fallback if matplotlib's cmap registry is not available
        categories = {
            "Sequential": ["viridis", "jet"],
            "Diverging": ["coolwarm"],
            "Qualitative": ["tab10"],
            "Miscellaneous": [],
        }

    for cat_name, cmap_list in categories.items():
        sub = tk.Menu(menu, tearoff=False)
        for cmap_name in sorted(cmap_list):
            sub.add_radiobutton(
                label=cmap_name,
                variable=cmap_var_vector,
                value=cmap_name,
            )
        menu.add_cascade(label=cat_name, menu=sub)

    menu_button.grid(row=row_v, column=1, sticky="w")
    row_v += 1

    # Colormap value range (normalized or physical, depending on draw function)
    tk.Label(inner_frame, text="Cmap range:").grid(
        row=row_v, column=0, sticky="e", padx=5, pady=2
    )
    frame_cmap_vector = tk.Frame(inner_frame)
    frame_cmap_vector.grid(row=row_v, column=1, sticky="w", padx=5, pady=2)

    tk.Label(frame_cmap_vector, text="Min").pack(side="left")
    cmap_min_vector = tk.Entry(frame_cmap_vector, width=6)
    cmap_min_vector.pack(side="left", padx=(2, 5))
    cmap_min_vector.insert(0, "0")

    tk.Label(frame_cmap_vector, text="Max").pack(side="left")
    cmap_max_vector = tk.Entry(frame_cmap_vector, width=6)
    cmap_max_vector.pack(side="left", padx=(2, 0))
    cmap_max_vector.insert(0, "1")
    row_v += 1

    # Figure DPI
    tk.Label(inner_frame, text="Figure DPI:").grid(
        row=row_v, column=0, sticky="e", padx=5, pady=2
    )
    dpi_entry_vector = tk.Entry(inner_frame, width=10)
    dpi_entry_vector.insert(0, "100")
    dpi_entry_vector.grid(row=row_v, column=1, sticky="w", padx=5, pady=2)
    row_v += 1

    # Redraw function (called when user clicks "Draw Section")
    def redraw():
        """
        Read GUI settings, extract the selected variable, and trigger the plot.
        """
        def safe_float(v):
            try:
                return float(v)
            except Exception:
                return None

        # Set application to "busy" state during plotting
        root = frame.winfo_toplevel()
        root.config(cursor="watch")
        redraw_btn_vector.config(state="disabled")
        root.update_idletasks()

        try:
            opts = {
                "interp_method": interp_var.get(),
                "number_point": int(number_point.get()) if number_point.get().isdigit() else 100,
                "depth_interval": safe_float(depth_interval.get()) or 1,
                "vmin": safe_float(entry_min_vector.get()) if entry_min_vector else None,
                "vmax": safe_float(entry_max_vector.get()) if entry_max_vector else None,
                "dv": safe_float(entry_range_dv.get()) if entry_range_dv else None,
                
                "fig_width": safe_float(entry_figsize_width.get()) if entry_figsize_width else 7,
                "fig_height": safe_float(entry_figsize_height.get()) if entry_figsize_height else 4,
                "cmap": cmap_var_vector.get(),
                "cmap_min": safe_float(cmap_min_vector.get()) if cmap_min_vector else 0,
                "cmap_max": safe_float(cmap_max_vector.get()) if cmap_max_vector else 1,
                "lon_p1": safe_float(lon_min_vector.get()) if lon_min_vector else None,
                "lon_p2": safe_float(lon_max_vector.get()) if lon_max_vector else None,
                "lat_p1": safe_float(lat_min_vector.get()) if lat_min_vector else None,
                "lat_p2": safe_float(lat_max_vector.get()) if lat_max_vector else None,
                "dpi": int(dpi_entry_vector.get()) if dpi_entry_vector.get().isdigit() else 100,
            }

            v_name = v_var_var.get()

            try:
                var_v = np.squeeze(ds.variables[v_name][:])
            except Exception as e:
                messagebox.showerror("Error", f"Cannot read variable data:\n{e}")
                return

            print("Chosen options", opts)

            if callable(draw_callback):
                try:
                    draw_callback(
                        v_name,
                        state.get("lon"),
                        state.get("lat"),
                        opts,
                        state,
                    )
                except Exception as e:
                    messagebox.showerror("Error", f"draw_callback failed:\n{e}")
            elif callable(draw_section):
                try:
                    draw_section(v_name, var_v, opts, state)
                except Exception as e:
                    messagebox.showerror("Error", f"draw_section failed:\n{e}")
            else:
                print("[Section redraw] missing draw function; opts:", opts)

        finally:
            # Restore normal cursor and button state no matter what happened
            root.config(cursor="")
            redraw_btn_vector.config(state="normal")
            root.update_idletasks()

    # "Draw Section" button
    redraw_btn_vector = tk.Button(
        inner_frame,
        text="Draw Section",
        bg="lightblue",
        command=redraw,
    )
    redraw_btn_vector.grid(row=row_v, column=0, columnspan=2, pady=10)
    row_v += 1

    # Populate the variable menu from the dataset
    v_menu["menu"].delete(0, "end")


    v_list = []
    for name, var in ds.variables.items():
        shape = getattr(var, "shape", ())
        # Count dimensions with size > 1
        effective_ndim = sum(1 for s in shape if s is not None and s > 1)
        if effective_ndim == 3:
            v_list.append(name)

    # Add filtered variables to the OptionMenu
    for varname in v_list:
        v_menu["menu"].add_command(
            label=varname,
            command=lambda v=varname: v_var_var.set(v)
        )

    # Set default selection
    v_var_var.set(v_list[0] if v_list else "")


    def on_vector_select(*_):
        """
        Update the stored grid coordinates when the selected variable changes.

        This tries to infer the appropriate grid suffix (u/v/f/t) from the
        variable name and then loads lon/lat/depth/mask from the grid file.
        """
        v_name = v_var_var.get()
        if v_name not in ds.variables:
            return

        # Infer a suffix from the variable name (e.g. *_u, *_v, *_t, *_f)
        suffix = "t"
        for s in ["u", "v", "f", "t"]:
            if v_name.lower().endswith(s):
                suffix = s
                break

        lon, lat, depth, mask = get_grid_coords(gridfile, suffix)
        state["lon"], state["lat"], state["depth"], state["mask"] = lon, lat, depth, mask
        state["var_name"] = v_name

    # Trigger grid update whenever the variable selection changes
    v_var_var.trace_add("write", on_vector_select)

    # Ensure the canvas scroll region is updated when the canvas is resized
    def _on_canvas_config(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    canvas.bind("<Configure>", _on_canvas_config)

    # Initial state based on the default variable
    on_vector_select()

    return {"frame": frame}
