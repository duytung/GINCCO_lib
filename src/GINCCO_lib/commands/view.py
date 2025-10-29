"""
GINCCO_lib.commands.view (Tkinter version)
------------------------------------------
A lightweight NetCDF viewer that works over SSH.
Usage:
    gincco view <filename.nc>
"""

import tkinter as tk
from tkinter import messagebox, Listbox, END
import numpy as np
from netCDF4 import Dataset
import matplotlib
matplotlib.use("TkAgg")  # Use Tk backend
import matplotlib.pyplot as plt


def open_file(filename):
    """Main window: list variables and handle clicks."""
    root = tk.Tk()
    root.title(f"GINCCO Viewer - {filename}")
    root.geometry("400x500")

    try:
        ds = Dataset(filename)
    except Exception as e:
        messagebox.showerror("Error", f"Cannot open file:\n{e}")
        root.destroy()
        return

    tk.Label(root, text="Select a variable to plot").pack(pady=10)

    listbox = Listbox(root)
    for v in ds.variables.keys():
        listbox.insert(END, v)
    listbox.pack(fill="both", expand=True, padx=10, pady=10)

    def plot_var(event):
        varname = listbox.get(listbox.curselection())
        var = ds.variables[varname]
        data = np.squeeze(var[:])
        nd = data.ndim

        plt.figure()
        if nd == 1:
            plt.plot(data)
            plt.xlabel(var.dimensions[0])
        elif nd == 2:
            plt.pcolormesh(data)
            plt.colorbar(label=getattr(var, "units", ""))
        else:
            messagebox.showinfo("Unsupported", f"{varname} has {nd} dimensions")
            plt.close()
            return
        plt.title(f"{varname} ({', '.join(var.dimensions)})")
        plt.tight_layout()
        plt.show()

    listbox.bind("<Double-Button-1>", plot_var)

    root.mainloop()


# === CLI interface ===
def register_subparser(subparser):
    subparser.add_argument("filename", help="Path to NetCDF file")
    subparser.set_defaults(func=main)


def main(args):
    filename = args.filename
    open_file(filename)
