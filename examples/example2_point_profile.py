# =========================
# IMPORTS
# =========================
import numpy as np
from netCDF4 import Dataset
from datetime import *
import GINCCO_lib as gc

# =========================
# CONFIGURATION
# =========================
tstart = datetime(2010, 1, 1)
tend   = datetime(2010, 1, 20)

path = '/work/users/tungnd/GOT271/GOT_REF5/OFFLINE/'

# =========================
# LOAD GRID AND DEPTH
# =========================
fgrid   = Dataset(path + 'grid.nc', 'r')
lat_t   = fgrid.variables['latitude_t'][:]
lon_t   = fgrid.variables['longitude_t'][:]
mask_t  = fgrid.variables['mask_t'][0, :, :]
depth_t = fgrid.variables['depth_t'][0, :, :]  # only bottom depth

# Apply mask: set land values to NaN
depth_t[mask_t == 0] = np.nan

# ============================================================
# EXAMPLE 1: Plot temporal variation of surface salinity
# ============================================================

# Step 1: Define three points along latitude 19N
lon_p = [106, 107, 108]
lat_p = [19, 19, 19]

# Step 2: Plot locations of the points on the map with bathymetry
gc.map_draw_point(
    lon_min=105, lon_max=111,
    lat_min=16.5, lat_max=22,
    title="Locations of points and bathymetry (in m)",
    lon_data=lon_t,
    lat_data=lat_t,
    data_draw=depth_t[:, :],
    lat_point=lat_p,
    lon_point=lon_p,
    path_save="/prod/projects/data/tungnd/figure/",
    name_save="demo_11"
)

# Step 3: Import salinity at the defined points
# data_draw shape = (number of points, number of days)
data_draw = np.zeros((len(lon_p), (tend - tstart).days + 1))
for i in range(len(lon_p)):
    data_draw[i, :] = gc.import_point(
        path, 'sal', tstart, tend,
        lat_p[i], lon_p[i],
        ji='False', level=-1, ignore_missing='False'  # surface point
    )

# Step 4: Plot temporal salinity variation for the 3 points
gc.plot_point(
    title="Surface salinity at different points",
    tstart=tstart,
    tend=tend,
    data_point=data_draw,
    path_save="/prod/projects/data/tungnd/figure/",
    name_save="demo_11",
    point_labels=["1", "2", "3"]
)
