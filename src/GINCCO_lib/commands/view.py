"""
GINCCO_lib.commands.view
------------------------
Open ncview-style GUI viewer for NetCDF files.

Usage:
    gincco view <filename.nc>
"""

import sys
import numpy as np
from netCDF4 import Dataset
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QListWidget,
    QVBoxLayout, QWidget, QMessageBox, QLabel
)
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt


class NcViewer(QMainWindow):
    def __init__(self, filename):
        super().__init__()
        self.setWindowTitle(f"GINCCO Viewer - {filename}")
        self.resize(600, 600)

        try:
            self.dataset = Dataset(filename)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Cannot open file:\n{e}")
            sys.exit(1)

        self.var_list = QListWidget()
        self.info_label = QLabel("Select a variable to plot")
        self.info_label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.info_label)
        layout.addWidget(self.var_list)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.var_list.addItems(list(self.dataset.variables.keys()))
        self.var_list.itemClicked.connect(self.show_variable)

    def show_variable(self, item):
        varname = item.text()
        var = self.dataset.variables[varname]
        data = np.squeeze(var[:])
        dims = getattr(var, "dimensions", ())
        nd = data.ndim

        plt.figure()
        if nd == 1:
            plt.plot(data)
            plt.xlabel(dims[0] if dims else "")
        elif nd == 2:
            plt.pcolormesh(data)
            plt.colorbar(label=getattr(var, "units", ""))
        else:
            QMessageBox.information(
                self, "Unsupported variable",
                f"'{varname}' has {nd} dimensions (only 1D or 2D supported)."
            )
            plt.close()
            return

        plt.title(f"{varname} ({', '.join(dims)})")
        plt.tight_layout()
        plt.show()


# -----------------------------
# CLI registration functions
# -----------------------------

def register_subparser(subparser):
    """Called by cli.py to add arguments for this command."""
    subparser.add_argument(
        "filename",
        help="Path to NetCDF file to open in the viewer"
    )
    subparser.set_defaults(func=main)


def main(args):
    """Entry point when 'gincco view' is called."""
    filename = args.filename
    app = QApplication(sys.argv)
    viewer = NcViewer(filename)
    viewer.show()
    sys.exit(app.exec_())
