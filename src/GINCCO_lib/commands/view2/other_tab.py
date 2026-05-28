"""Other analysis tab for the redesigned GINCCO viewer."""

import os
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

import numpy as np
from netCDF4 import Dataset

from GINCCO_lib.modules.geostrophic_current import geostrophic_current
from GINCCO_lib.modules.map_plot import map_draw_uv


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


class InvalidSSHVariable(ValueError):
    pass


def _load_grid(gridfile):
    state = {"lon": None, "lat": None, "mask": None, "dx": None, "dy": None, "sin": None, "cos": None}
    if not gridfile:
        return state
    try:
        with Dataset(gridfile) as grid:
            for key, var_name in (
                ("lon", "longitude_t"),
                ("lat", "latitude_t"),
                ("dx", "dx_t"),
                ("dy", "dy_t"),
                ("sin", "gridrotsin_t"),
                ("cos", "gridrotcos_t"),
            ):
                var = grid.variables.get(var_name)
                state[key] = var[:] if var is not None else None
            mask = grid.variables.get("mask_t")
            if mask is not None:
                mask_arr = mask[:]
                state["mask"] = mask_arr if mask_arr.ndim == 2 else mask_arr[0, :, :]
    except Exception:
        pass
    return state


class OtherTab:
    def __init__(self, parent, datafile, gridfile, status_var):
        self.parent = parent
        self.datafile = datafile
        self.gridfile = gridfile
        self.status_var = status_var
        self.frame = ttk.Frame(parent, padding=10)
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        self.ds = None
        self.grid_state = _load_grid(gridfile)
        self._open_dataset()
        self.content = self._scroll_content()
        self._build()

    def _open_dataset(self):
        try:
            self.ds = Dataset(self.datafile)
        except Exception as exc:
            messagebox.showerror("Error", "Cannot open file:\n{}".format(exc))
            self.ds = None

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

    def _group(self, title, row):
        group = ttk.LabelFrame(self.content, text=title, style="Panel.TLabelframe")
        group.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        for col in (1, 2, 3):
            group.grid_columnconfigure(col, weight=1, uniform="value_slots")
        return group

    def _label(self, parent, text, row):
        ttk.Label(parent, text=text).grid(row=row, column=0, sticky="e", padx=(0, 6), pady=3)

    def _entry(self, parent, row, default="", width=12):
        entry = ttk.Entry(parent, width=width)
        if default != "":
            entry.insert(0, str(default))
        entry.grid(row=row, column=1, sticky="w", padx=(4, 12), pady=3)
        return entry

    def _combo(self, parent, row, values, default="", width=26):
        values = list(values or [])
        if values and (default == "" or default not in values):
            default = values[0]
        combo = ttk.Combobox(parent, values=values, state="readonly", width=int(round(width * 1.3)))
        combo.set(default)
        combo.grid(row=row, column=1, sticky="w", padx=(4, 12), pady=3)
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
        self._label(parent, label, row)
        left = self._value_slot(parent, row, 1, left_label, left_default, width)
        right = self._value_slot(parent, row, 2, right_label, right_default, width)
        return left, right

    def _variables(self, allowed_ndim=(2, 3)):
        if self.ds is None:
            return []
        out = []
        for name, var in self.ds.variables.items():
            if _effective_ndim(getattr(var, "shape", ())) in allowed_ndim:
                out.append(name)
        return out

    def _reset_ssh_combo(self):
        valid = self._variables(allowed_ndim=(2,))
        self.ssh_combo.configure(values=valid)
        if valid:
            preferred = "ssh_ib" if "ssh_ib" in valid else valid[0]
            self.ssh_combo.set(preferred)
        else:
            self.ssh_combo.set("")

    def _build(self):
        row = 0
        group = self._group("Operation", row); row += 1
        self._label(group, "Operation", 0)
        self.operation_combo = self._combo(group, 0, ("Geostrophic current",), "Geostrophic current", width=24)
        ttk.Label(group, text="SSH variable").grid(row=0, column=2, sticky="e", padx=(12, 6), pady=3)
        vars_ = self._variables()
        self.ssh_combo = ttk.Combobox(group, values=vars_, state="readonly", width=34)
        if vars_:
            preferred = "ssh_ib" if "ssh_ib" in vars_ else vars_[0]
            self.ssh_combo.set(preferred)
        self.ssh_combo.grid(row=0, column=3, sticky="w", padx=(4, 12), pady=3)

        group = self._group("Map Bounds", row); row += 1
        self.lon_min, self.lon_max = self._pair_entries(group, 0, "Longitude", "Min", "Max")
        self.lat_min, self.lat_max = self._pair_entries(group, 1, "Latitude", "Min", "Max")

        group = self._group("Map-drawing options", row); row += 1
        self.data_min, self.data_max = self._pair_entries(group, 0, "Speed range", "Min", "Max")
        self._label(group, "Max arrows", 1)
        self.quiver_n = self._entry(group, 1, "20")
        self._label(group, "Quiver scale", 2)
        self.quiver_scale = self._entry(group, 2, "6")
        self._label(group, "Title", 3)
        self.title_entry = self._entry(group, 3, "Geostrophic current", width=28)
        self._label(group, "Output folder", 4)
        self.path_save = self._entry(group, 4, ".", width=28)
        self._label(group, "Output name", 5)
        self.name_save = self._entry(group, 5, "geostrophic_current", width=28)

        action = ttk.Frame(self.content)
        action.grid(row=row, column=0, sticky="ew")
        action.grid_columnconfigure(0, weight=1)
        self.draw_button = ttk.Button(action, text="Draw Map", style="Primary.TButton", command=self.draw)
        self.draw_button.grid(row=0, column=0, sticky="e")

    def _ssh_data(self, name):
        data = np.asarray(np.ma.filled(self.ds.variables[name][:], np.nan), dtype=float)
        while data.ndim > 2 and data.shape[0] == 1:
            data = data[0]
        if data.ndim != 2:
            raise InvalidSSHVariable("Geostrophic current requires a 2D SSH variable. Please choose another variable.")
        return data

    def _require_grid(self):
        missing = []
        for key, label in (
            ("lon", "longitude_t"),
            ("lat", "latitude_t"),
            ("mask", "mask_t"),
            ("dx", "dx_t"),
            ("dy", "dy_t"),
            ("sin", "gridrotsin_t"),
            ("cos", "gridrotcos_t"),
        ):
            if self.grid_state.get(key) is None:
                missing.append(label)
        if missing:
            raise ValueError("Grid file is missing required variables: {}".format(", ".join(missing)))

    def draw(self):
        if self.ds is None:
            return
        ssh_name = self.ssh_combo.get()
        if not ssh_name:
            messagebox.showerror("Error", "Please select an SSH variable.")
            return

        root = self.frame.winfo_toplevel()
        root.config(cursor="watch")
        self.draw_button.configure(state="disabled")
        self.status_var.set("Drawing geostrophic current...")
        root.update_idletasks()

        try:
            self._require_grid()
            ssh = self._ssh_data(ssh_name)
            mask = self.grid_state["mask"]
            ssh = np.array(ssh, copy=True)
            ssh[np.asarray(mask) == 0] = np.nan
            u, v = geostrophic_current(
                ssh,
                self.grid_state["lat"],
                self.grid_state["dx"],
                self.grid_state["dy"],
                self.grid_state["sin"],
                self.grid_state["cos"],
            )

            path_save = self.path_save.get().strip() or "."
            if not os.path.isdir(path_save):
                os.makedirs(path_save)

            lon = self.grid_state["lon"]
            lat = self.grid_state["lat"]
            map_draw_uv(
                lon_min=_safe_float(self.lon_min.get()) if self.lon_min.get().strip() else float(np.nanmin(lon)),
                lon_max=_safe_float(self.lon_max.get()) if self.lon_max.get().strip() else float(np.nanmax(lon)),
                lat_min=_safe_float(self.lat_min.get()) if self.lat_min.get().strip() else float(np.nanmin(lat)),
                lat_max=_safe_float(self.lat_max.get()) if self.lat_max.get().strip() else float(np.nanmax(lat)),
                title=self.title_entry.get().strip() or "Geostrophic current",
                lon_data=lon,
                lat_data=lat,
                data_u=u,
                data_v=v,
                mask_ocean=mask,
                path_save=path_save,
                name_save=self.name_save.get().strip() or "geostrophic_current",
                quiver_max_n=_safe_int(self.quiver_n.get(), 20),
                quiver_scale=_safe_float(self.quiver_scale.get()),
                data_min=_safe_float(self.data_min.get()),
                data_max=_safe_float(self.data_max.get()),
            )
            self.status_var.set("Done; map saved in {}".format(path_save))
        except InvalidSSHVariable as exc:
            self.status_var.set("Choose a 2D SSH variable")
            messagebox.showerror("Error", str(exc))
            self._reset_ssh_combo()
        except Exception as exc:
            self.status_var.set("Draw failed")
            messagebox.showerror("Error", "draw geostrophic current failed:\n{}".format(exc))
        finally:
            root.config(cursor="")
            self.draw_button.configure(state="normal")
            root.update_idletasks()
