# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup -----------------------------------------------------

import os
import sys
sys.path.insert(0, os.path.abspath('../src'))


autodoc_mock_imports = [
     'mpl_toolkits', 'mpl_toolkits.basemap',
    'numpy', 'matplotlib', 'netCDF4', 'cartopy', 'Basemap', 'scipy', 'pandas', 'imageio', 'pillow'
]
add_module_names = False
autosummary_generate = True
# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'GINCCO_lib'
copyright = '2025, Tung Nguyen-Duy'
author = 'Tung Nguyen-Duy'
release = '0.5'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration


extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',  # for Google/NumPy-style docstrings
    'sphinx.ext.viewcode',  # optional: adds source links
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
