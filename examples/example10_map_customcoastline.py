# =========================
# IMPORTS
# =========================
import numpy as np
import GINCCO_lib as gc
from netCDF4 import Dataset
from datetime import *

# =========================
# CONFIGURATION
# =========================
tstart = datetime(2010, 1, 1)
tend   = datetime(2010, 1, 10)

path = '/work/users/tungnd/GOT271/GOT_REF5/OFFLINE/'

# =========================
# LOAD GRID
# =========================
fgrid = Dataset(path + 'grid.nc', 'r')
lat_t = fgrid.variables['latitude_t'][:]
lon_t = fgrid.variables['longitude_t'][:]

# ============================================================
# EXAMPLE 1: import_4D (time, depth, lat, lon) -> plot level 0, day 0
# ============================================================
sal_full = gc.import_4D(path, 'sal', tstart, tend, ignore_missing='False')

gc.map_draw(
    lon_min=105, lon_max=111,
    lat_min=16.5, lat_max=22,
    title="Bottom salinity (example 1)",
    lon_data=lon_t,
    lat_data=lat_t,
    data_draw=sal_full[0, 0, :, :],  # day 0, level 0
    path_save="/prod/projects/data/tungnd/figure/",
    name_save="demo_01", 
    custom_coastline = "/data/projects/LOTUS/tungnd/openstreetmap-coastline/lines", 
    layer_name= "lines",
)

