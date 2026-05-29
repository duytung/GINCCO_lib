"""Preview Tk fonts for the GINCCO view interface.

Run with:
    python examples/view_font_preview.py
"""

import subprocess
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk


SAMPLE_TEXT = "GINCCO Viewer - Scalar Vector Combine Section"
UI_TEXT = "Variable  temperature_t    Layer  0    Draw Scalar Map"


def _configure_base_style(root, family, size):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    base = (family, size)
    bold = (family, size, "bold")
    style.configure(".", font=base)
    style.configure("TLabel", font=base)
    style.configure("TButton", font=base)
    style.configure("TCheckbutton", font=base)
    style.configure("TRadiobutton", font=base)
    style.configure("TEntry", font=base)
    style.configure("TCombobox", font=base)
    style.configure("TNotebook.Tab", font=bold, padding=(12, 6))
    style.configure("Panel.TLabelframe", padding=10)
    style.configure("Panel.TLabelframe.Label", font=bold)
    style.configure("Primary.TButton", font=bold, padding=(12, 6))


class FontPreview:
    def __init__(self, root):
        self.root = root
        self.root.title("Tk Font Preview")
        self.root.geometry("980x760")
        self.root.minsize(760, 520)

        self.tk_families = sorted(set(tkfont.families(root)), key=str.lower)
        self.scalable_families = self._fontconfig_families()
        self.all_families = self.scalable_families or self._filtered_tk_families()
        preferred = self._preferred_font()
        self.family_var = tk.StringVar(value=preferred)
        self.size_var = tk.IntVar(value=11)
        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar()

        _configure_base_style(root, preferred, self.size_var.get())
        self._build()
        self._refresh_rows()
        self._apply_selected_font()

    def _preferred_font(self):
        for name in (
            "Noto Sans",
            "Inter",
            "Segoe UI",
            "Ubuntu",
            "Cantarell",
            "Liberation Sans",
            "Arial",
            "DejaVu Sans",
        ):
            if name in self.all_families:
                return name
        return self.all_families[0] if self.all_families else "TkDefaultFont"

    def _fontconfig_families(self):
        try:
            output = subprocess.check_output(["fc-list", ":", "family"], universal_newlines=True)
        except Exception:
            return []

        families = set()
        for line in output.splitlines():
            for name in line.split(","):
                name = name.strip()
                if name and name in self.tk_families:
                    families.add(name)
        return sorted(families, key=str.lower)

    def _filtered_tk_families(self):
        skip = (
            "cursor",
            "fixed",
            "nil",
            "nil2",
            "open look cursor",
            "open look glyph",
        )
        families = []
        for name in self.tk_families:
            lname = name.lower()
            if lname.startswith("@") or lname in skip:
                continue
            families.append(name)
        return families

    def _build(self):
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        top = ttk.Frame(self.root, padding=10)
        top.grid(row=0, column=0, sticky="ew")
        top.grid_columnconfigure(1, weight=1)

        ttk.Label(top, text="Search").grid(row=0, column=0, sticky="w", padx=(0, 6))
        search = ttk.Entry(top, textvariable=self.search_var, width=24)
        search.grid(row=0, column=1, sticky="ew", padx=(0, 12))
        search.bind("<KeyRelease>", lambda _event: self._refresh_rows())

        ttk.Label(top, text="Selected").grid(row=0, column=2, sticky="w", padx=(0, 6))
        self.family_combo = ttk.Combobox(top, textvariable=self.family_var, values=self.all_families, width=28)
        self.family_combo.grid(row=0, column=3, sticky="w", padx=(0, 12))
        self.family_combo.bind("<<ComboboxSelected>>", lambda _event: self._apply_selected_font())

        ttk.Label(top, text="Size").grid(row=0, column=4, sticky="w", padx=(0, 6))
        size = ttk.Spinbox(top, from_=8, to=18, textvariable=self.size_var, width=4, command=self._apply_selected_font)
        size.grid(row=0, column=5, sticky="w", padx=(0, 12))
        size.bind("<KeyRelease>", lambda _event: self._apply_selected_font())

        ttk.Button(top, text="Apply to Sample", command=self._apply_selected_font).grid(row=0, column=6, sticky="e")

        main = ttk.PanedWindow(self.root, orient="vertical")
        main.grid(row=1, column=0, sticky="nsew")

        sample = ttk.LabelFrame(main, text="view-style sample", style="Panel.TLabelframe")
        sample.grid_columnconfigure(0, weight=1)
        main.add(sample, weight=0)

        self.sample_title = ttk.Label(sample, text=SAMPLE_TEXT)
        self.sample_title.grid(row=0, column=0, sticky="w", pady=(0, 8))

        controls = ttk.Frame(sample)
        controls.grid(row=1, column=0, sticky="ew")
        controls.grid_columnconfigure(1, weight=1)
        ttk.Label(controls, text="Variable").grid(row=0, column=0, sticky="e", padx=(0, 6), pady=3)
        ttk.Combobox(controls, values=("temperature_t", "salinity_t", "u_velocity_u"), width=28).grid(
            row=0, column=1, sticky="w", padx=(4, 12), pady=3
        )
        ttk.Label(controls, text="Layer").grid(row=1, column=0, sticky="e", padx=(0, 6), pady=3)
        ttk.Entry(controls, width=8).grid(row=1, column=1, sticky="w", padx=(4, 12), pady=3)
        ttk.Button(controls, text="Draw Scalar Map", style="Primary.TButton").grid(row=2, column=1, sticky="w", pady=(8, 0))

        list_frame = ttk.Frame(main, padding=(10, 8, 10, 0))
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        main.add(list_frame, weight=1)

        self.canvas = tk.Canvas(list_frame, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.rows = ttk.Frame(self.canvas)
        self.rows_window = self.canvas.create_window((0, 0), window=self.rows, anchor="nw")
        self.rows.bind("<Configure>", lambda _event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfigure(self.rows_window, width=event.width))

        status = ttk.Label(self.root, textvariable=self.status_var, anchor="w", padding=(10, 4))
        status.grid(row=2, column=0, sticky="ew")

    def _filtered_families(self):
        query = self.search_var.get().strip().lower()
        if not query:
            return self.all_families
        return [family for family in self.all_families if query in family.lower()]

    def _refresh_rows(self):
        for child in self.rows.winfo_children():
            child.destroy()

        families = self._filtered_families()
        for row, family in enumerate(families):
            item = ttk.Frame(self.rows, padding=(0, 4))
            item.grid(row=row, column=0, sticky="ew")
            item.grid_columnconfigure(1, weight=1)

            ttk.Button(item, text="Use", width=6, command=lambda name=family: self._select_family(name)).grid(
                row=0, column=0, sticky="w", padx=(0, 8)
            )
            label = ttk.Label(item, text="{0}    {1}".format(family, UI_TEXT), anchor="w")
            label.grid(row=0, column=1, sticky="ew")

        self.status_var.set(
            "{0} of {1} scalable fonts shown; {2} Tk font names available total".format(
                len(families), len(self.all_families), len(self.tk_families)
            )
        )

    def _select_family(self, family):
        self.family_var.set(family)
        self._apply_selected_font()

    def _apply_selected_font(self):
        family = self.family_var.get() or self._preferred_font()
        try:
            size = int(self.size_var.get())
        except Exception:
            size = 11
        _configure_base_style(self.root, family, size)
        self.sample_title.configure(font=(family, size + 2, "bold"))
        self.status_var.set("Selected font: {0}, size {1}".format(family, size))


def main():
    root = tk.Tk()
    FontPreview(root)
    root.mainloop()


if __name__ == "__main__":
    main()
