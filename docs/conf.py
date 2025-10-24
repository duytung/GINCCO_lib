# Configuration file for the Sphinx documentation builder.

import os
import sys
import re
import glob

# -- Path setup -----------------------------------------------------
sys.path.insert(0, os.path.abspath('../src'))

# Mock heavy imports so autodoc can build on ReadTheDocs
autodoc_mock_imports = [
    'mpl_toolkits', 'mpl_toolkits.basemap', 'dateutil', 'PIL',
    'numpy', 'matplotlib', 'netCDF4', 'cartopy', 'Basemap',
    'scipy', 'pandas', 'imageio', 'pillow'
]

# -- Project information --------------------------------------------
project = 'GINCCO_lib'
copyright = '2025, Tung Nguyen-Duy'
author = 'Tung Nguyen-Duy'
release = '0.5'

# -- General configuration ------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
]

add_module_names = False
autosummary_generate = True
napoleon_google_docstring = False
napoleon_numpy_docstring = True


exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Helper: clean .rst titles -------------------------------------
def clean_rst_titles():
    """Remove 'GINCCO_lib.' prefix and 'module' from generated .rst titles."""
    pattern = re.compile(r'^GINCCO\\_lib\.([A-Za-z0-9\\_]+)\s+module', flags=re.MULTILINE)
    rst_dir = os.path.dirname(__file__)
    for path in glob.glob(os.path.join(rst_dir, "GINCCO_lib.*.rst")):
        with open(path, "r+", encoding="utf-8") as f:
            text = f.read()
            new_text, n = pattern.subn(lambda m: m.group(1).replace("\\_", "_"), text, count=1)
            if n > 0:
                f.seek(0)
                f.write(new_text)
                f.truncate()
                print(f"[conf.py] Cleaned title: {os.path.basename(path)}")

# -- Auto-generate one page per function/class ----------------------
from sphinx.ext.autosummary.generate import generate_autosummary_docs


def setup(app):
    app.connect("builder-inited", lambda app: clean_rst_titles())

# -- HTML output ----------------------------------------------------
html_theme = "pydata_sphinx_theme"
html_theme_options = {
    "logo": {"text": "GINCCO_lib"},
    "navigation_depth": 3,
    "collapse_navigation": False,
    "show_nav_level": 3,
    "navbar_align": "left",
    "show_prev_next": False,
    "external_links": [
        {"url": "https://github.com/duytung/GINCCO_lib", "name": "GitHub"},
    ],
}
html_sidebars = {"**": ["search-field.html", "sidebar-nav-bs.html"]}

html_css_files = ["custom.css"]

