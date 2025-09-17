import numpy as np
from netCDF4 import Dataset 
from datetime import *
import GINCCO_lib as gc

#--------#--------#--------#--------#--------#--------#

tstart = datetime(2010,1,1)
tend = datetime(2010,1,20)

path = '/work/users/tungnd/GOT271/GOT_REF5/OFFLINE/'


#--------#--------#--------#--------#--------#--------#
#import grid 
fgrid = Dataset(path + 'grid.nc', 'r')
lat_t = fgrid.variables['latitude_t'][:]
lon_t = fgrid.variables['longitude_t'][:]
mask_t = fgrid.variables['mask_t'][0,:,:] 
depth_t = fgrid.variables['depth_t'][0,:,:] #only use the bottom depth
depth_t[mask_t == 0] = np.nan
#--------#--------#--------#--------#--------#--------#

#Example 1: Plot 3 lines for for the temporal variation of surface salinity
lon_p = [106, 107, 108]
lat_p = [19, 19, 19]

#First, plot where the points are located
gc.map_draw_point(
    lon_min=105, lon_max=111,
    lat_min=16.5, lat_max=22,
    title="Locations of points and bathymetry (in m)",
    lon_data=lon_t,
    lat_data=lat_t,
    data_draw=depth_t[:,:],  		# day 0, level 0
    lat_point = lat_p,
    lon_point = lon_p,
    path_save="/prod/projects/data/tungnd/figure/",     # current folder
    name_save="demo_11"
)


# Second, import data
data_draw = np.zeros(( len (lon_p),  (tend-tstart).days +1   ))
for i in range(0, len(lon_p)):
    data_draw[i,:] = gc.import_point(path, 'sal', tstart, tend, lat_p[i], lon_p[i], 
        ji = 'False', level = -1, ignore_missing='False') #surface point


# Thirs, draw results
gc.plot_point(
    title="surface sailinity in different points",
    tstart=tstart, 
    tend = tend, 
    data_point = data_draw,
    path_save="/prod/projects/data/tungnd/figure/",
    name_save="demo_11",
    point_labels=["1","2","3"]
)


