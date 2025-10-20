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
mask_t = fgrid.variables['mask_t'][0,:,:]
sin_t  = fgrid.variables['gridrotsin_t'][:,:]
cos_t  = fgrid.variables['gridrotcos_t'][:,:]
# ============================================================
# EXAMPLE 3: import_surface velocity
# ============================================================

# Step 1: Import data
ssh = gc.import_3D(path, 'ssh_ib', tstart, tend, ignore_missing='False')


data_draw = ssh[0]
data_draw[mask_t==0] = np.nan

print (data_draw[0:10,0:10])


for i in range(0,11):
    print (i*10,  np.nanpercentile(data_draw, i*10))    


#Step 2: Choose a day and calculate
U1, V1 = gc.geostrophic_current(data_draw, lat_t, lon_t, sin_t, cos_t)

U1[mask_t==0] = np.nan
V1[mask_t==0] = np.nan

for i in range(0,11):
    print (i*10,  np.nanpercentile(U1, i*10),np.nanpercentile(V1, i*10))



print (V1[200:210, 200:210])


#Step 4: Draw
gc.map_draw_uv(
    lon_min=105, lon_max=111,
    lat_min=16.5, lat_max=22,
    title="Geotrophic current (example 7)",
    lon_data=lon_t,
    lat_data=lat_t,
    data_u= U1, data_v= V1,
    mask_ocean = mask_t,
    path_save="/prod/projects/data/tungnd/figure/",
    name_save="geotrophic_current_example7",
    quiver_max_n=20,   # ~max arrows per axis (auto step so arrows <= quiver_max_n x quiver_max_n)
    quiver_scale=6  # higher is shorter arrow. lower is longer arrow
)



