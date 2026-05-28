"""Redesigned Scalar, Vector, and Combine tabs for view2."""

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

import matplotlib.cm as cm
import numpy as np
from netCDF4 import Dataset

from GINCCO_lib.commands.view.plot_scalar_map import draw_map_plot
from GINCCO_lib.commands.view.plot_vector_map import draw_vector_plot
from GINCCO_lib.commands.view.plot_combine_map import draw_map_combine


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


def _suffix(name):
    lname = str(name).lower()
    for s in ("u", "v", "f", "t"):
        if lname.endswith(s):
            return s
    return "t"


def _cmap_values():
    try:
        return sorted(cm.cmap_d.keys())
    except Exception:
        return ["jet", "viridis", "YlOrBr", "coolwarm"]


BASEMAP_RESOLUTIONS = ("crude", "low", "intermediate", "high", "full")
_BASEMAP_RESOLUTION_CODES = {
    "crude": "c",
    "low": "l",
    "intermediate": "i",
    "high": "h",
    "full": "f",
    "c": "c",
    "l": "l",
    "i": "i",
    "h": "h",
    "f": "f",
}


def _basemap_resolution_code(value):
    return _BASEMAP_RESOLUTION_CODES.get(str(value or "").lower(), "i")


def _load_grid(gridfile, suffix="t"):
    state = {"lon": None, "lat": None, "depth_levels": None, "mask_t": None, "sin_t": None, "cos_t": None}
    if not gridfile:
        return state
    try:
        with Dataset(gridfile) as grid:
            lon = grid.variables.get("longitude_{}".format(suffix))
            if lon is None:
                lon = grid.variables.get("longitude_t")
            lat = grid.variables.get("latitude_{}".format(suffix))
            if lat is None:
                lat = grid.variables.get("latitude_t")
            depth = grid.variables.get("depth_{}".format(suffix))
            if depth is None:
                depth = grid.variables.get("depth_t")
            mask = grid.variables.get("mask_{}".format(suffix))
            if mask is None:
                mask = grid.variables.get("mask_t")
            sin_t = grid.variables.get("gridrotsin_t")
            cos_t = grid.variables.get("gridrotcos_t")

            state["lon"] = lon[:] if lon is not None else None
            state["lat"] = lat[:] if lat is not None else None
            state["depth_levels"] = depth[:] if depth is not None else None
            if mask is not None:
                mask_arr = mask[:]
                state["mask_t"] = mask_arr if mask_arr.ndim == 2 else mask_arr[0, :, :]
            state["sin_t"] = sin_t[:] if sin_t is not None else None
            state["cos_t"] = cos_t[:] if cos_t is not None else None
    except Exception:
        pass
    return state


class _BaseMapTab:
    def __init__(self, parent, datafile, gridfile, status_var):
        self.parent = parent
        self.datafile = datafile
        self.gridfile = gridfile
        self.status_var = status_var
        self.frame = ttk.Frame(parent, padding=10)
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        self.ds = None
        self.widgets = {}
        self.state = {}
        self._open_dataset()
        self.content = self._scroll_content()

    def _open_dataset(self):
        try:
            self.ds = Dataset(self.datafile)
        except Exception as exc:
            messagebox.showerror("Error", "Cannot open file:\n{}".format(exc))

    def _scroll_content(self):
        bg = ttk.Style(self.frame).lookup("TFrame", "background") or self.frame.cget("background")
        canvas = tk.Canvas(self.frame, highlightthickness=0, background=bg)
        canvas.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(self.frame, orient="vertical", command=canvas.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scroll.set)
        content = ttk.Frame(canvas, padding=(0, 0, 12, 0))
        win = canvas.create_window((0, 0), window=content, anchor="nw")
        content.grid_columnconfigure(0, weight=1)
        content.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(win, width=e.width))
        return content

    def group(self, title, row):
        group = ttk.LabelFrame(self.content, text=title, style="Panel.TLabelframe")
        group.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        for col in (1, 2, 3):
            group.grid_columnconfigure(col, weight=1, uniform="value_slots")
        return group

    def label(self, parent, text, row):
        ttk.Label(parent, text=text).grid(row=row, column=0, sticky="e", padx=(0, 6), pady=3)

    def combo(self, parent, row, values, default="", width=24):
        values = list(values or [])
        if values and (default == "" or default not in values):
            default = values[0]
        combo = ttk.Combobox(parent, values=values, state="readonly", width=width)
        combo.set(default)
        combo.grid(row=row, column=1, sticky="w", padx=(4, 12), pady=3)
        return combo

    def entry(self, parent, row, default="", width=10):
        ent = ttk.Entry(parent, width=width)
        if default != "":
            ent.insert(0, str(default))
        ent.grid(row=row, column=1, sticky="w", padx=(4, 12), pady=3)
        return ent

    def set_combo_values(self, combo, values, default=None):
        values = [str(v) for v in values] or ["0"]
        combo.configure(values=values)
        combo.set(str(default) if default is not None else values[0])

    def load_t_grid(self):
        return _load_grid(self.gridfile, "t")

    def value_slot(self, parent, row, slot, label, default="", width=8):
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=slot, sticky="ew", padx=(4, 12), pady=3)
        frame.grid_columnconfigure(1, weight=1)
        ttk.Label(frame, text=label).grid(row=0, column=0, sticky="w", padx=(0, 4))
        entry = ttk.Entry(frame, width=width)
        if default != "":
            entry.insert(0, str(default))
        entry.grid(row=0, column=1, sticky="w")
        return entry

    def pair_entries(self, parent, row, label, left_label, right_label, left_default="", right_default="", width=8):
        self.label(parent, label, row)
        left = self.value_slot(parent, row, 1, left_label, left_default, width)
        right = self.value_slot(parent, row, 2, right_label, right_default, width)
        return left, right

    def triplet_entries(
        self,
        parent,
        row,
        label,
        left_label,
        middle_label,
        right_label,
        left_default="",
        middle_default="",
        right_default="",
        width=7,
    ):
        self.label(parent, label, row)
        left = self.value_slot(parent, row, 1, left_label, left_default, width)
        middle = self.value_slot(parent, row, 2, middle_label, middle_default, width)
        right = self.value_slot(parent, row, 3, right_label, right_default, width)
        return left, middle, right

    def bounds_group(self, parent, start_row=0):
        lon_min, lon_max, lon_interval = self.triplet_entries(parent, start_row, "Longitude", "Min", "Max", "Interval")
        lat_min, lat_max, lat_interval = self.triplet_entries(parent, start_row + 1, "Latitude", "Min", "Max", "Interval")
        return lon_min, lon_max, lon_interval, lat_min, lat_max, lat_interval

    def value_range(self, parent, row):
        return self.triplet_entries(parent, row, "Value range", "Min", "Max", "Interval")

    def cmap_group(self, parent, row, default="jet"):
        self.label(parent, "Color map", row)
        cmap = self.combo(parent, row, _cmap_values(), default, width=22)
        cmap_min, cmap_max = self.pair_entries(parent, row + 1, "Cmap range", "Min", "Max", "0", "1", width=7)
        return cmap, cmap_min, cmap_max

    def action(self, row, text, command):
        frame = ttk.Frame(self.content)
        frame.grid(row=row, column=0, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)
        button = ttk.Button(frame, text=text, style="Primary.TButton", command=command)
        button.grid(row=0, column=0, sticky="e")
        return button

    def variables(self, allowed_ndim=(2, 3)):
        if self.ds is None:
            return []
        out = []
        for name, var in self.ds.variables.items():
            if _effective_ndim(getattr(var, "shape", ())) in allowed_ndim:
                out.append(name)
        return out

    def busy(self, message):
        root = self.frame.winfo_toplevel()
        root.config(cursor="watch")
        self.status_var.set(message)
        root.update_idletasks()
        return root

    def done(self, root, message="Done"):
        root.config(cursor="")
        self.status_var.set(message)
        root.update_idletasks()


class ScalarTab(_BaseMapTab):
    def __init__(self, parent, datafile, gridfile, status_var):
        super().__init__(parent, datafile, gridfile, status_var)
        self.allow_depth = True
        self._build()

    def _build(self):
        row = 0
        group = self.group("Variable", row); row += 1
        self.label(group, "Variable", 0)
        vals = list(self.ds.variables.keys()) if self.ds is not None else []
        self.var_combo = self.combo(group, 0, vals, vals[0] if vals else "", width=30)
        self.var_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_variable_change())

        self.mode_var = tk.StringVar(value="layer")
        ttk.Label(group, text="Selection").grid(row=1, column=0, sticky="e", padx=(0, 6), pady=3)
        layer_slot = ttk.Frame(group)
        layer_slot.grid(row=1, column=1, sticky="ew", padx=(4, 12), pady=3)
        self.layer_radio = ttk.Radiobutton(layer_slot, text="Layer", variable=self.mode_var, value="layer", command=self._update_mode_state)
        self.layer_radio.grid(row=0, column=0, sticky="w", padx=(0, 4))
        self.layer_combo = ttk.Combobox(layer_slot, values=("0",), state="readonly", width=6)
        self.layer_combo.set("0")
        self.layer_combo.grid(row=0, column=1, sticky="w")
        depth_slot = ttk.Frame(group)
        depth_slot.grid(row=1, column=2, sticky="ew", padx=(4, 12), pady=3)
        self.depth_radio = ttk.Radiobutton(depth_slot, text="Depth", variable=self.mode_var, value="depth", command=self._update_mode_state)
        self.depth_radio.grid(row=0, column=0, sticky="w", padx=(0, 4))
        self.depth_entry = ttk.Entry(depth_slot, width=10)
        self.depth_entry.grid(row=0, column=1, sticky="w")
        self.depth_entry.bind("<FocusIn>", lambda _e: self._select_depth_mode())

        group = self.group("Map Bounds", row); row += 1
        self.lon_min, self.lon_max, self.lon_interval, self.lat_min, self.lat_max, self.lat_interval = self.bounds_group(group)

        group = self.group("Map-drawing options", row); row += 1
        self.vmin, self.vmax, self.value_interval = self.value_range(group, 0)
        self.cmap, self.cmap_min, self.cmap_max = self.cmap_group(group, 1)
        self.fig_width, self.fig_height = self.pair_entries(group, 3, "Figure size", "W", "H", "7", "6", width=6)
        self.label(group, "Basemap Resolution", 4)
        self.resolution = self.combo(group, 4, BASEMAP_RESOLUTIONS, "intermediate", width=14)
        self.label(group, "DPI", 6)
        self.dpi = self.entry(group, 6, "100")
        self.label(group, "Missing color", 7)
        self.bad_color = self.combo(group, 7, ("white", "lightgray", "none", "black"), "white", width=12)
        self.show_coastline = tk.BooleanVar(value=True)
        self.show_gridlines = tk.BooleanVar(value=True)
        self.fill_continents = tk.BooleanVar(value=False)
        ttk.Checkbutton(group, text="Draw coastlines", variable=self.show_coastline).grid(row=8, column=1, sticky="w", padx=(4, 12), pady=3)
        ttk.Checkbutton(group, text="Draw gridlines", variable=self.show_gridlines).grid(row=8, column=2, sticky="w", padx=(4, 12), pady=3)
        ttk.Checkbutton(group, text="Fill continents", variable=self.fill_continents).grid(row=8, column=3, sticky="w", padx=(4, 12), pady=3)
        self.label(group, "Continent color", 9)
        self.continent_color = self.combo(group, 9, ("0.8", "lightgray", "white", "tan", "darkgray"), "0.8", width=12)
        self.label(group, "Lake color", 10)
        self.lake_color = self.combo(group, 10, ("white", "lightblue", "0.9"), "white", width=12)
        self.label(group, "Title", 11)
        self.title_entry = self.entry(group, 11, "", width=26)
        self.label(group, "Colorbar label", 12)
        self.cbar_label = self.entry(group, 12, "", width=26)

        self.draw_button = self.action(row, "Draw Scalar Map", self.draw)
        self._on_variable_change()

    def _on_variable_change(self):
        name = self.var_combo.get()
        if not name or self.ds is None or name not in self.ds.variables:
            return
        var = self.ds.variables[name]
        data = np.squeeze(var[:])
        if data.ndim >= 3:
            nlayer = data.shape[-3]
            self.set_combo_values(self.layer_combo, range(nlayer), 0)
            self.allow_depth = True
        else:
            self.set_combo_values(self.layer_combo, [0], 0)
            self.allow_depth = False
            self.mode_var.set("layer")
            self.depth_entry.delete(0, "end")
        self.state = _load_grid(self.gridfile, _suffix(name))
        self._update_mode_state()
        self.status_var.set("Scalar ready: {}".format(name))

    def _select_depth_mode(self):
        if self.allow_depth:
            self.mode_var.set("depth")
            self._update_mode_state()

    def _update_mode_state(self):
        if not self.allow_depth:
            self.mode_var.set("layer")
            self.layer_radio.configure(state="disabled")
            self.layer_combo.configure(state="disabled")
            self.depth_radio.configure(state="disabled")
            self.depth_entry.configure(state="disabled")
            return
        self.layer_radio.configure(state="normal")
        self.depth_radio.configure(state="normal")
        if self.mode_var.get() == "depth":
            self.layer_combo.configure(state="disabled")
            self.depth_entry.configure(state="normal")
        else:
            self.layer_combo.configure(state="readonly")
            self.depth_entry.configure(state="disabled")

    def draw(self):
        name = self.var_combo.get()
        if not name:
            return
        root = self.busy("Drawing scalar map...")
        self.draw_button.configure(state="disabled")
        try:
            opts = {
                "lon_min": _safe_float(self.lon_min.get()),
                "lon_max": _safe_float(self.lon_max.get()),
                "lon_interval": _safe_float(self.lon_interval.get()),
                "lat_min": _safe_float(self.lat_min.get()),
                "lat_max": _safe_float(self.lat_max.get()),
                "lat_interval": _safe_float(self.lat_interval.get()),
                "vmin": _safe_float(self.vmin.get()),
                "vmax": _safe_float(self.vmax.get()),
                "value_interval": _safe_float(self.value_interval.get()),
                "cmap": self.cmap.get() or "jet",
                "cmap_min": _safe_float(self.cmap_min.get()),
                "cmap_max": _safe_float(self.cmap_max.get()),
                "resolution": _basemap_resolution_code(self.resolution.get()),
                "dpi": _safe_int(self.dpi.get(), 100),
                "fig_width": _safe_float(self.fig_width.get()) or 7,
                "fig_height": _safe_float(self.fig_height.get()) or 6,
                "show_coastline": self.show_coastline.get(),
                "fill_continents": self.fill_continents.get(),
                "continent_color": self.continent_color.get() or "0.8",
                "lake_color": self.lake_color.get() or "white",
                "show_gridlines": self.show_gridlines.get(),
                "n_ticks": 4,
                "bad_color": self.bad_color.get() or "white",
                "title": self.title_entry.get().strip() or None,
                "colorbar_label": self.cbar_label.get().strip() or None,
            }
            if self.mode_var.get() == "depth" and self.allow_depth:
                depth = _safe_float(self.depth_entry.get())
                if depth is None:
                    messagebox.showinfo("Info", "Please enter a valid depth value.")
                    return
                opts["depth"] = depth
            else:
                opts["layer"] = _safe_int(self.layer_combo.get(), 0)

            draw_map_plot(name, self.ds.variables[name], self.state.get("lon"), self.state.get("lat"), opts, self.state)
            self.status_var.set("Done")
        except Exception as exc:
            self.status_var.set("Draw failed")
            messagebox.showerror("Error", "draw scalar failed:\n{}".format(exc))
        finally:
            self.draw_button.configure(state="normal")
            self.done(root, self.status_var.get())


class VectorTab(_BaseMapTab):
    def __init__(self, parent, datafile, gridfile, status_var):
        super().__init__(parent, datafile, gridfile, status_var)
        self._build()

    def _vector_lists(self):
        names = list(self.ds.variables.keys()) if self.ds is not None else []
        u_list = [name for name in names if "u" in name.lower()]
        v_list = [name for name in names if "v" in name.lower()]
        return u_list or names, v_list or names

    def _build(self):
        u_vals, v_vals = self._vector_lists()
        row = 0
        group = self.group("Variables", row); row += 1
        self.label(group, "U variable", 0)
        self.u_combo = self.combo(group, 0, u_vals, u_vals[0] if u_vals else "", width=30)
        self.label(group, "V variable", 1)
        self.v_combo = self.combo(group, 1, v_vals, v_vals[0] if v_vals else "", width=30)
        self.u_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_vector_change())
        self.v_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_vector_change())

        self.label(group, "Layer", 2)
        self.layer_combo = ttk.Combobox(group, values=("0",), state="readonly", width=6)
        self.layer_combo.set("0")
        self.layer_combo.grid(row=2, column=1, sticky="w", padx=(4, 12), pady=3)
        self.rotate_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(group, text="Rotate using grid angle", variable=self.rotate_var).grid(
            row=3, column=1, columnspan=3, sticky="w", padx=(4, 12), pady=3
        )

        group = self.group("Map Bounds", row); row += 1
        self.lon_min, self.lon_max, self.lon_interval, self.lat_min, self.lat_max, self.lat_interval = self.bounds_group(group)

        group = self.group("Map-drawing options", row); row += 1
        self.label(group, "Max arrows", 0)
        self.quiver_n = self.entry(group, 0, "20")
        self.vmin, self.vmax, self.value_interval = self.value_range(group, 1)
        self.cmap, self.cmap_min, self.cmap_max = self.cmap_group(group, 2, default="YlOrBr")
        self.cmap_max.delete(0, "end"); self.cmap_max.insert(0, "0.7")
        self.fig_width, self.fig_height = self.pair_entries(group, 4, "Figure size", "W", "H", "7", "6", width=6)
        self.label(group, "Basemap Resolution", 5)
        self.resolution = self.combo(group, 5, BASEMAP_RESOLUTIONS, "intermediate", width=14)
        self.label(group, "DPI", 7)
        self.dpi = self.entry(group, 7, "100")
        self.label(group, "Scale", 8)
        self.scale = self.entry(group, 8, "3")
        self.label(group, "Missing color", 9)
        self.bad_color = self.combo(group, 9, ("white", "lightgray", "none", "black"), "white", width=12)
        self.show_coastline = tk.BooleanVar(value=True)
        self.show_gridlines = tk.BooleanVar(value=True)
        self.fill_continents = tk.BooleanVar(value=False)
        ttk.Checkbutton(group, text="Draw coastlines", variable=self.show_coastline).grid(row=10, column=1, sticky="w", padx=(4, 12), pady=3)
        ttk.Checkbutton(group, text="Draw gridlines", variable=self.show_gridlines).grid(row=10, column=2, sticky="w", padx=(4, 12), pady=3)
        ttk.Checkbutton(group, text="Fill continents", variable=self.fill_continents).grid(row=10, column=3, sticky="w", padx=(4, 12), pady=3)
        self.label(group, "Continent color", 11)
        self.continent_color = self.combo(group, 11, ("0.8", "lightgray", "white", "tan", "darkgray"), "0.8", width=12)
        self.label(group, "Lake color", 12)
        self.lake_color = self.combo(group, 12, ("white", "lightblue", "0.9"), "white", width=12)
        self.label(group, "Title", 13)
        self.title_entry = self.entry(group, 13, "", width=26)
        self.label(group, "Colorbar label", 14)
        self.cbar_label = self.entry(group, 14, "", width=26)

        self.draw_button = self.action(row, "Draw Vector Map", self.draw)
        self._on_vector_change()

    def _on_vector_change(self):
        u_name, v_name = self.u_combo.get(), self.v_combo.get()
        if not u_name or not v_name or self.ds is None:
            return
        if u_name not in self.ds.variables or v_name not in self.ds.variables:
            return
        u = np.squeeze(self.ds.variables[u_name][:])
        v = np.squeeze(self.ds.variables[v_name][:])
        nd = max(getattr(u, "ndim", 0), getattr(v, "ndim", 0))
        if nd == 3:
            self.set_combo_values(self.layer_combo, range(u.shape[0]), 0)
        else:
            self.set_combo_values(self.layer_combo, [0], 0)

        # The vector drawing backend expects T-grid lon/lat plus mask_t for staggered interpolation.
        self.state = self.load_t_grid()
        self.status_var.set("Vector ready: {}, {}".format(u_name, v_name))

    def draw(self):
        u_name, v_name = self.u_combo.get(), self.v_combo.get()
        if not u_name or not v_name:
            return
        root = self.busy("Drawing vector map...")
        self.draw_button.configure(state="disabled")
        try:
            # Refresh grid at draw time so grid edits/reloads are picked up like the original tab.
            self.state = self.load_t_grid()
            opts = self._vector_opts()
            draw_vector_plot(
                np.squeeze(self.ds.variables[u_name][:]),
                np.squeeze(self.ds.variables[v_name][:]),
                self.state.get("lon"),
                self.state.get("lat"),
                opts,
                self.state,
                quiver_max_n=_safe_int(self.quiver_n.get(), 20),
            )
            self.status_var.set("Done")
        except Exception as exc:
            self.status_var.set("Draw failed")
            messagebox.showerror("Error", "draw vector failed:\n{}".format(exc))
        finally:
            self.draw_button.configure(state="normal")
            self.done(root, self.status_var.get())

    def _vector_opts(self):
        return {
            "layer": _safe_int(self.layer_combo.get(), 0),
            "need_rotate": self.rotate_var.get(),
            "lon_min": _safe_float(self.lon_min.get()),
            "lon_max": _safe_float(self.lon_max.get()),
            "lon_interval": _safe_float(self.lon_interval.get()),
            "lat_min": _safe_float(self.lat_min.get()),
            "lat_max": _safe_float(self.lat_max.get()),
            "lat_interval": _safe_float(self.lat_interval.get()),
            "vmin": _safe_float(self.vmin.get()),
            "vmax": _safe_float(self.vmax.get()),
            "value_interval": _safe_float(self.value_interval.get()),
            "cmap": self.cmap.get() or "YlOrBr",
            "cmap_min": _safe_float(self.cmap_min.get()) or 0,
            "cmap_max": _safe_float(self.cmap_max.get()) or 0.7,
            "scale": _safe_float(self.scale.get()) or 3,
            "resolution": _basemap_resolution_code(self.resolution.get()),
            "dpi": _safe_int(self.dpi.get(), 100),
            "fig_width": _safe_float(self.fig_width.get()) or 7,
            "fig_height": _safe_float(self.fig_height.get()) or 6,
            "show_coastline": self.show_coastline.get(),
            "fill_continents": self.fill_continents.get(),
            "continent_color": self.continent_color.get() or "0.8",
            "lake_color": self.lake_color.get() or "white",
            "show_gridlines": self.show_gridlines.get(),
            "n_ticks": 4,
            "bad_color": self.bad_color.get() or "white",
            "title": self.title_entry.get().strip() or None,
            "colorbar_label": self.cbar_label.get().strip() or None,
        }


class CombineTab(VectorTab):
    def _build(self):
        names = list(self.ds.variables.keys()) if self.ds is not None else []
        scalar_vals = names
        u_vals, v_vals = self._vector_lists()
        row = 0
        group = self.group("Variables", row); row += 1
        self.label(group, "Scalar", 0)
        self.scalar_combo = self.combo(group, 0, scalar_vals, scalar_vals[0] if scalar_vals else "", width=30)
        self.scalar_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_scalar_change())
        self.label(group, "Scalar layer", 1)
        self.scalar_layer_combo = ttk.Combobox(group, values=("0",), state="readonly", width=6)
        self.scalar_layer_combo.set("0")
        self.scalar_layer_combo.grid(row=1, column=1, sticky="w", padx=(4, 12), pady=3)

        self.label(group, "U variable", 2)
        self.u_combo = self.combo(group, 2, u_vals, u_vals[0] if u_vals else "", width=30)
        self.label(group, "V variable", 3)
        self.v_combo = self.combo(group, 3, v_vals, v_vals[0] if v_vals else "", width=30)
        self.u_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_vector_change())
        self.v_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_vector_change())
        self.label(group, "Vector layer", 4)
        self.layer_combo = ttk.Combobox(group, values=("0",), state="readonly", width=6)
        self.layer_combo.set("0")
        self.layer_combo.grid(row=4, column=1, sticky="w", padx=(4, 12), pady=3)
        self.rotate_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(group, text="Rotate using grid angle", variable=self.rotate_var).grid(
            row=5, column=1, columnspan=3, sticky="w", padx=(4, 12), pady=3
        )

        group = self.group("Map Bounds", row); row += 1
        self.lon_min, self.lon_max, self.lon_interval, self.lat_min, self.lat_max, self.lat_interval = self.bounds_group(group)

        group = self.group("Map-drawing options", row); row += 1
        self.vmin, self.vmax, self.value_interval = self.value_range(group, 0)
        self.cmap, self.cmap_min, self.cmap_max = self.cmap_group(group, 1)
        self.fig_width, self.fig_height = self.pair_entries(group, 3, "Figure size", "W", "H", "7", "6", width=6)
        self.label(group, "Basemap Resolution", 4)
        self.resolution = self.combo(group, 4, BASEMAP_RESOLUTIONS, "intermediate", width=14)
        self.label(group, "DPI", 6)
        self.dpi = self.entry(group, 6, "100")
        self.label(group, "Max arrows", 7)
        self.quiver_n = self.entry(group, 7, "20")
        self.label(group, "Scale", 8)
        self.scale = self.entry(group, 8, "400")
        self.label(group, "Missing color", 9)
        self.bad_color = self.combo(group, 9, ("white", "lightgray", "none", "black"), "white", width=12)
        self.show_coastline = tk.BooleanVar(value=True)
        self.show_gridlines = tk.BooleanVar(value=True)
        self.fill_continents = tk.BooleanVar(value=False)
        ttk.Checkbutton(group, text="Draw coastlines", variable=self.show_coastline).grid(row=10, column=1, sticky="w", padx=(4, 12), pady=3)
        ttk.Checkbutton(group, text="Draw gridlines", variable=self.show_gridlines).grid(row=10, column=2, sticky="w", padx=(4, 12), pady=3)
        ttk.Checkbutton(group, text="Fill continents", variable=self.fill_continents).grid(row=10, column=3, sticky="w", padx=(4, 12), pady=3)
        self.label(group, "Continent color", 11)
        self.continent_color = self.combo(group, 11, ("0.8", "lightgray", "white", "tan", "darkgray"), "0.8", width=12)
        self.label(group, "Lake color", 12)
        self.lake_color = self.combo(group, 12, ("white", "lightblue", "0.9"), "white", width=12)
        self.label(group, "Title", 13)
        self.title_entry = self.entry(group, 13, "", width=26)
        self.label(group, "Colorbar label", 14)
        self.cbar_label = self.entry(group, 14, "", width=26)

        self.draw_button = self.action(row, "Draw Combined Map", self.draw)
        self._on_scalar_change()
        self._on_vector_change()

    def _on_scalar_change(self):
        name = self.scalar_combo.get()
        if not name or self.ds is None or name not in self.ds.variables:
            return
        data = np.squeeze(self.ds.variables[name][:])
        if data.ndim == 3:
            self.set_combo_values(self.scalar_layer_combo, range(data.shape[0]), 0)
        else:
            self.set_combo_values(self.scalar_layer_combo, [0], 0)
        self.status_var.set("Combine scalar ready: {}".format(name))

    def _on_vector_change(self):
        u_name, v_name = self.u_combo.get(), self.v_combo.get()
        if not u_name or not v_name or self.ds is None:
            return
        if u_name not in self.ds.variables or v_name not in self.ds.variables:
            return
        u = np.squeeze(self.ds.variables[u_name][:])
        v = np.squeeze(self.ds.variables[v_name][:])
        nd = max(getattr(u, "ndim", 0), getattr(v, "ndim", 0))
        if nd == 3:
            self.set_combo_values(self.layer_combo, range(u.shape[0]), 0)
        else:
            self.set_combo_values(self.layer_combo, [0], 0)
        self.state = self.load_t_grid()

    def draw(self):
        s_name, u_name, v_name = self.scalar_combo.get(), self.u_combo.get(), self.v_combo.get()
        if not s_name or not u_name or not v_name:
            return
        root = self.busy("Drawing combined map...")
        self.draw_button.configure(state="disabled")
        try:
            self.state = self.load_t_grid()
            scalar_opts = {
                "layer": _safe_int(self.scalar_layer_combo.get(), 0),
                "lon_min": _safe_float(self.lon_min.get()),
                "lon_max": _safe_float(self.lon_max.get()),
                "lon_interval": _safe_float(self.lon_interval.get()),
                "lat_min": _safe_float(self.lat_min.get()),
                "lat_max": _safe_float(self.lat_max.get()),
                "lat_interval": _safe_float(self.lat_interval.get()),
                "vmin": _safe_float(self.vmin.get()),
                "vmax": _safe_float(self.vmax.get()),
                "value_interval": _safe_float(self.value_interval.get()),
                "cmap": self.cmap.get() or "jet",
                "cmap_min": _safe_float(self.cmap_min.get()),
                "cmap_max": _safe_float(self.cmap_max.get()),
                "resolution": _basemap_resolution_code(self.resolution.get()),
                "dpi": _safe_int(self.dpi.get(), 100),
                "fig_width": _safe_float(self.fig_width.get()) or 7,
                "fig_height": _safe_float(self.fig_height.get()) or 6,
                "show_coastline": self.show_coastline.get(),
                "fill_continents": self.fill_continents.get(),
                "continent_color": self.continent_color.get() or "0.8",
                "lake_color": self.lake_color.get() or "white",
                "show_gridlines": self.show_gridlines.get(),
                "n_ticks": 4,
                "bad_color": self.bad_color.get() or "white",
                "title": self.title_entry.get().strip() or None,
                "colorbar_label": self.cbar_label.get().strip() or None,
            }
            vector_opts = self._vector_opts()
            vector_opts["quiver_max_n"] = _safe_int(self.quiver_n.get(), 20)
            opts = {"scalar": scalar_opts, "vector": vector_opts}
            draw_map_combine(
                s_name,
                self.ds.variables[s_name],
                np.squeeze(self.ds.variables[u_name][:]),
                np.squeeze(self.ds.variables[v_name][:]),
                self.state.get("lon"),
                self.state.get("lat"),
                opts,
                self.state,
            )
            self.status_var.set("Done")
        except Exception as exc:
            self.status_var.set("Draw failed")
            messagebox.showerror("Error", "draw combined map failed:\n{}".format(exc))
        finally:
            self.draw_button.configure(state="normal")
            self.done(root, self.status_var.get())
