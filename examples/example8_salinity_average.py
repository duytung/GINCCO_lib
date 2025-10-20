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
depth_t   = fgrid.variables['depth_t'][0,:,:]
dxy_t   = fgrid.variables['dxdy_t'][:]
mask_t  = fgrid.variables['mask_t'][0, :, :]

depth_t[mask_t==0] = np.nan

# ============================================================
# EXAMPLE 1: Plot temporal variation of surface salinity
# ============================================================

# Step 1: Define a box
lon_min_box = 106
lon_max_box = 107
lat_min_box = 20
lat_max_box = 21


# Step 2: Plot boxes
gc.map_draw_box(
    lon_min=105, lon_max=111,
    lat_min=16.5, lat_max=22,
    title="Locations of points and bathymetry (in m)",
    lon_data=lon_t,
    lat_data=lat_t,
    data_draw=depth_t[:, :],
    lon_min_box = lon_min_box, 
    lon_max_box = lon_max_box, 
    lat_min_box = lat_min_box, 
    lat_max_box = lat_max_box,
    path_save="/prod/projects/data/tungnd/figure/",
    name_save="map_box"
)


# Step 3: Import salinity map
# data_draw shape = (number of points, number of days)
sal_surface = gc.import_surface(path, 'sal', tstart, tend, ignore_missing='False')

# Step 4: Calculate salinity mean
sal_mean = gc.spatial_average(sal_surface,
    dxy_t,
    mask_ocean=mask_t,
    lon_t=lon_t,
    lat_t=lat_t,
    lon_min=lon_min,
    lon_max=lon_max,
    lat_min=lat_min,
    lat_max=lat_max,   
)



# Step 5: Plot temporal salinity variation for the 3 points
gc.plot_point(
    title="Surface salinity at different points",
    tstart=tstart,
    tend=tend,
    data_point=sal_mean,
    path_save="/prod/projects/data/tungnd/figure/",
    name_save="demo_11",
    point_labels=["Region 1"]
)
