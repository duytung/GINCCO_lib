"""Section tab for the redesigned GINCCO viewer."""

import random
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

import matplotlib.cm as cm
import numpy as np
from netCDF4 import Dataset

from GINCCO_lib.modules.section_plot import draw_section_figure


def _safe_float(value):
    try:
        return float(value)
    except Exception:
        return None


def _safe_int(value, default):
    try:
        return int(value)
    except Exception:
        return default


def _effective_ndim(shape):
    return sum(1 for size in shape if size is not None and size > 1)


def _variable_suffix(name):
    lname = name.lower()
    for suffix in ("u", "v", "f", "t"):
        if lname.endswith(suffix):
            return suffix
    return "t"


def get_grid_coords(grid_file, suffix):
    if not grid_file:
        return None, None, None, None

    try:
        with Dataset(grid_file) as grid:
            try:
                lon = grid.variables["longitude_{}".format(suffix)][:]
                lat = grid.variables["latitude_{}".format(suffix)][:]
                depth = grid.variables["depth_{}".format(suffix)][:]
                mask = grid.variables["mask_{}".format(suffix)][:]
            except KeyError:
                lon_var = grid.variables.get("longitude_t")
                lat_var = grid.variables.get("latitude_t")
                depth_var = grid.variables.get("depth_t")
                mask_var = grid.variables.get("mask_t")
                lon = lon_var[:] if lon_var is not None else None
                lat = lat_var[:] if lat_var is not None else None
                depth = depth_var[:] if depth_var is not None else None
                mask = mask_var[:] if mask_var is not None else None

        if mask is not None and getattr(mask, "ndim", 0) == 3:
            mask = mask[0, :, :]
        return lon, lat, depth, mask
    except Exception:
        return None, None, None, None


def _combo_width(width):
    return max(1, int(round(width * 1.3)))


class SectionTab:
    def __init__(self, parent, datafile, gridfile, status_var):
        self.parent = parent
        self.datafile = datafile
        self.gridfile = gridfile
        self.status_var = status_var
        self.frame = ttk.Frame(parent, padding=10)
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        self.ds = None
        self.variables = []
        self.state = {"lon": None, "lat": None, "depth": None, "mask": None, "var_name": None}
        self.vars = {}

        self._open_dataset()
        self._build()
        self._populate_variables()

    def _open_dataset(self):
        try:
            self.ds = Dataset(self.datafile)
        except Exception as exc:
            messagebox.showerror("Error", "Cannot open file:\n{}".format(exc))
            self.ds = None

    def _build(self):
        bg = ttk.Style(self.frame).lookup("TFrame", "background") or self.frame.cget("background")
        canvas = tk.Canvas(self.frame, highlightthickness=0, background=bg)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)

        content = ttk.Frame(canvas, padding=(0, 0, 12, 0))
        canvas_window = canvas.create_window((0, 0), window=content, anchor="nw")
        content.grid_columnconfigure(0, weight=1)

        def on_content_config(_):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_config(event):
            canvas.itemconfigure(canvas_window, width=event.width)

        content.bind("<Configure>", on_content_config)
        canvas.bind("<Configure>", on_canvas_config)

        row = 0
        self._build_variable_group(content, row)
        row += 1
        self._build_endpoint_group(content, row)
        row += 1
        self._build_processing_group(content, row)
        row += 1
        self._build_style_group(content, row)
        row += 1
        self._build_action_group(content, row)

    def _group(self, parent, title, row):
        group = ttk.LabelFrame(parent, text=title, style="Panel.TLabelframe")
        group.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        for col in (1, 2, 3):
            group.grid_columnconfigure(col, weight=1, uniform="value_slots")
        return group

    def _entry(self, parent, row, column, default="", width=10):
        entry = ttk.Entry(parent, width=width)
        if default != "":
            entry.insert(0, str(default))
        entry.grid(row=row, column=column, sticky="w", padx=(4, 12), pady=3)
        return entry

    def _combo(self, parent, row, column, values, default, width=18):
        values = list(values or [])
        if values and (default == "" or default not in values):
            default = values[0]
        combo = ttk.Combobox(parent, values=values, state="readonly", width=_combo_width(width))
        combo.set(default)
        combo.grid(row=row, column=column, sticky="w", padx=(4, 12), pady=3)
        return combo

    def _value_slot(self, parent, row, slot, label, default="", width=8):
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=slot, sticky="ew", padx=(4, 12), pady=3)
        frame.grid_columnconfigure(1, weight=1)
        ttk.Label(frame, text=label).grid(row=0, column=0, sticky="w", padx=(0, 4))
        entry = ttk.Entry(frame, width=width)
        if default != "":
            entry.insert(0, str(default))
        entry.grid(row=0, column=1, sticky="w")
        return entry

    def _pair_entries(self, parent, row, label, left_label, right_label, left_default="", right_default="", width=8):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="e", padx=(0, 6), pady=3)
        left = self._value_slot(parent, row, 1, left_label, left_default, width)
        right = self._value_slot(parent, row, 2, right_label, right_default, width)
        return left, right

    def _triple_entries(self, parent, row, label, labels, width=7):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="e", padx=(0, 6), pady=3)
        entries = []
        for slot, item_label in enumerate(labels, start=1):
            entries.append(self._value_slot(parent, row, slot, item_label, width=width))
        return entries

    def _build_variable_group(self, parent, row):
        group = self._group(parent, "Variable", row)
        ttk.Label(group, text="Variable").grid(row=0, column=0, sticky="e", padx=(0, 6), pady=3)
        self.variable_combo = self._combo(group, 0, 1, [], "", width=32)
        self.variable_combo.bind("<<ComboboxSelected>>", lambda _event: self._on_variable_change())

    def _build_endpoint_group(self, parent, row):
        group = self._group(parent, "Section Endpoints", row)
        self.lon_p1, self.lon_p2 = self._pair_entries(group, 0, "Longitude", "P1", "P2")
        self.lat_p1, self.lat_p2 = self._pair_entries(group, 1, "Latitude", "P1", "P2")
        random_btn = ttk.Button(group, text="Random", command=self._fill_random_section)
        random_btn.grid(row=2, column=1, sticky="w", padx=(4, 12), pady=(6, 3))

    def _set_entry(self, entry, value):
        entry.configure(state="normal")
        entry.delete(0, "end")
        entry.insert(0, "{:.1f}".format(float(value)))

    def _fill_random_section(self):
        lon = self.state.get("lon")
        lat = self.state.get("lat")
        if lon is None or lat is None:
            messagebox.showerror("Error", "Grid longitude/latitude are not available.")
            return

        lon = np.asarray(lon, dtype=float)
        lat = np.asarray(lat, dtype=float)
        valid = np.isfinite(lon) & np.isfinite(lat)
        if not np.any(valid):
            messagebox.showerror("Error", "Grid longitude/latitude do not contain finite values.")
            return

        lon_valid = lon[valid].ravel()
        lat_valid = lat[valid].ravel()
        if lon_valid.size < 2:
            messagebox.showerror("Error", "At least two valid grid points are required.")
            return

        i1, i2 = random.sample(range(lon_valid.size), 2)
        self._set_entry(self.lon_p1, lon_valid[i1])
        self._set_entry(self.lat_p1, lat_valid[i1])
        self._set_entry(self.lon_p2, lon_valid[i2])
        self._set_entry(self.lat_p2, lat_valid[i2])
        self.status_var.set("Random section endpoints selected")

    def _build_processing_group(self, parent, row):
        group = self._group(parent, "Processing", row)
        ttk.Label(group, text="Interpolation").grid(row=0, column=0, sticky="e", padx=(0, 6), pady=3)
        self.interp_combo = self._combo(group, 0, 1, ("bilinear", "idw"), "bilinear")

        ttk.Label(group, text="Points").grid(row=1, column=0, sticky="e", padx=(0, 6), pady=3)
        self.number_point = self._entry(group, 1, 1, "400")

        ttk.Label(group, text="Depth interval").grid(row=2, column=0, sticky="e", padx=(0, 6), pady=3)
        self.depth_interval = self._entry(group, 2, 1, "1")

        ttk.Label(group, text="Bottom smoothing").grid(row=3, column=0, sticky="e", padx=(0, 6), pady=3)
        self.bottom_smoothing = self._combo(group, 3, 1, ("none", "median", "moving_average", "gaussian"), "none")
        self.bottom_smoothing.bind("<<ComboboxSelected>>", lambda _event: self._update_smoothing_state())

        self.bottom_window, self.bottom_sigma = self._pair_entries(
            group, 4, "Smoothing params", "Window", "Sigma", "6", "3", width=6
        )
        self._update_smoothing_state()

    def _build_style_group(self, parent, row):
        group = self._group(parent, "Figure", row)
        ttk.Label(group, text="Plot type").grid(row=0, column=0, sticky="e", padx=(0, 6), pady=3)
        self.plot_type = self._combo(group, 0, 1, ("contourf", "pcolormesh"), "contourf")

        self.fig_width, self.fig_height = self._pair_entries(group, 1, "Figure size", "W", "H", "7", "4", width=6)
        self.vmin, self.vmax, self.dv = self._triple_entries(group, 2, "Value range", ("Min", "Max", "Interval"), width=7)

        ttk.Label(group, text="Color map").grid(row=3, column=0, sticky="e", padx=(0, 6), pady=3)
        cmap_values = sorted(cm.cmap_d.keys()) if hasattr(cm, "cmap_d") else ["jet", "viridis", "coolwarm"]
        self.cmap = self._combo(group, 3, 1, cmap_values, "jet", width=24)

        self.cmap_min, self.cmap_max = self._pair_entries(group, 4, "Cmap range", "Min", "Max", "0", "1", width=7)

        ttk.Label(group, text="DPI").grid(row=5, column=0, sticky="e", padx=(0, 6), pady=3)
        self.dpi = self._entry(group, 5, 1, "100")

    def _build_action_group(self, parent, row):
        group = ttk.Frame(parent)
        group.grid(row=row, column=0, sticky="ew", pady=(2, 0))
        group.grid_columnconfigure(0, weight=1)
        self.draw_button = ttk.Button(group, text="Draw Section", style="Primary.TButton", command=self.draw)
        self.draw_button.grid(row=0, column=0, sticky="e")

    def _populate_variables(self):
        if self.ds is None:
            return
        self.variables = []
        for name, var in self.ds.variables.items():
            if _effective_ndim(getattr(var, "shape", ())) == 3:
                self.variables.append(name)
        self.variable_combo.configure(values=self.variables)
        if self.variables:
            current = self.variable_combo.get()
            if current not in self.variables:
                self.variable_combo.set(self.variables[0])
            self._on_variable_change()

    def _on_variable_change(self):
        var_name = self.variable_combo.get()
        if not var_name or self.ds is None or var_name not in self.ds.variables:
            return
        suffix = _variable_suffix(var_name)
        lon, lat, depth, mask = get_grid_coords(self.gridfile, suffix)
        self.state.update({"lon": lon, "lat": lat, "depth": depth, "mask": mask, "var_name": var_name})
        if lon is None or lat is None or depth is None:
            self.status_var.set("Selected {}; grid coordinates unavailable".format(var_name))
        else:
            self.status_var.set("Selected {}; grid suffix '{}'".format(var_name, suffix))

    def _update_smoothing_state(self):
        state = "disabled" if self.bottom_smoothing.get() == "none" else "normal"
        self.bottom_window.configure(state=state)
        self.bottom_sigma.configure(state=state)

    def _options(self):
        return {
            "lon_min": _safe_float(self.lon_p1.get()),
            "lon_max": _safe_float(self.lon_p2.get()),
            "lat_min": _safe_float(self.lat_p1.get()),
            "lat_max": _safe_float(self.lat_p2.get()),
            "number_point": _safe_int(self.number_point.get(), 400),
            "depth_interval": _safe_float(self.depth_interval.get()) or 1.0,
            "method": self.interp_combo.get(),
            "plot_type": self.plot_type.get(),
            "bottom_smoothing": self.bottom_smoothing.get(),
            "bottom_smoothing_window": _safe_int(self.bottom_window.get(), 6),
            "bottom_smoothing_sigma": _safe_float(self.bottom_sigma.get()) or 3.0,
            "fig_width": _safe_float(self.fig_width.get()) or 7.0,
            "fig_height": _safe_float(self.fig_height.get()) or 4.0,
            "dpi": _safe_int(self.dpi.get(), 100),
            "cmap_name": self.cmap.get() or "jet",
            "cmap_min": _safe_float(self.cmap_min.get()),
            "cmap_max": _safe_float(self.cmap_max.get()),
            "vmin": _safe_float(self.vmin.get()),
            "vmax": _safe_float(self.vmax.get()),
            "dv": _safe_float(self.dv.get()),
        }

    def draw(self):
        var_name = self.variable_combo.get()
        if not var_name:
            messagebox.showerror("Error", "No 3D variable available in this file.")
            return
        if self.state.get("lon") is None or self.state.get("lat") is None or self.state.get("depth") is None:
            messagebox.showerror("Error", "Grid lon/lat/depth are required to draw a section.")
            return

        root = self.frame.winfo_toplevel()
        root.config(cursor="watch")
        self.draw_button.configure(state="disabled")
        self.status_var.set("Drawing section...")
        root.update_idletasks()

        try:
            data = np.squeeze(self.ds.variables[var_name][:])
            opts = self._options()
            draw_section_figure(
                title="Section of {}".format(var_name),
                data=data,
                lon=self.state["lon"],
                lat=self.state["lat"],
                depth=self.state["depth"],
                lon_min=opts["lon_min"],
                lon_max=opts["lon_max"],
                lat_min=opts["lat_min"],
                lat_max=opts["lat_max"],
                number_point=opts["number_point"],
                depth_interval=opts["depth_interval"],
                method=opts["method"],
                fig_width=opts["fig_width"],
                fig_height=opts["fig_height"],
                dpi=opts["dpi"],
                cmap_name=opts["cmap_name"],
                cmap_min=opts["cmap_min"],
                cmap_max=opts["cmap_max"],
                vmin=opts["vmin"],
                vmax=opts["vmax"],
                dv=opts["dv"],
                plot_type=opts["plot_type"],
                bottom_smoothing=opts["bottom_smoothing"],
                bottom_smoothing_window=opts["bottom_smoothing_window"],
                bottom_smoothing_sigma=opts["bottom_smoothing_sigma"],
                show=True,
            )
            self.status_var.set("Done")
        except Exception as exc:
            self.status_var.set("Draw failed")
            messagebox.showerror("Error", "draw_section failed:\n{}".format(exc))
        finally:
            root.config(cursor="")
            self.draw_button.configure(state="normal")
            root.update_idletasks()
