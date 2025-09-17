import numpy as np
from netCDF4 import Dataset 
from import_series_daily import *
from map_plot import *
from heatmap_plot import *
#--------#--------#--------#--------#--------#--------#
tstart = datetime(2010,1,1)
tend = datetime(2010,10,30)

path = '/work/users/tungnd/GOT271/GOT_REF5/OFFLINE/'


#--------#--------#--------#--------#--------#--------#
#import grid 
fgrid = Dataset(path + 'grid.nc', 'r')
lat_t = fgrid.variables['latitude_t'][:]
lon_t = fgrid.variables['longitude_t'][:]
mask_t = fgrid.variables['mask_t'][:,:,:] 
depth_t = fgrid.variables['depth_t'][:,:,:]
depth_t[mask_t == 0] = np.nan
#--------#--------#--------#--------#--------#--------#

#Example 1: 
lon_p = [106, 107, 108]
lat_p = [19, 19, 19]

map_draw_point(
    lon_min=105, lon_max=111,
    lat_min=16.5, lat_max=22,
    title="Locations of points and bathymetry (in m)",
    lon_data=lon_t,
    lat_data=lat_t,
    data_draw=depth_t[0,:,:], 
    lat_point = lat_p,
    lon_point = lon_p,
    path_save="/prod/projects/data/tungnd/figure/",     # current folder
    name_save="demo_11"
)

#import 3 points
data_draw = np.zeros(( len (lon_p),  (tend-tstart).days +1   , np.size(depth_t,0))) #time * depth
point_index = np.zeros(( len (lon_p), 2), dtype=int)

for i in range(0, len(lon_p)):
    data_draw[i,:], point_index[i,:] = import_profile(path, 'sal', tstart, tend, lat_p[i], lon_p[i], 
        ji = 'False', ignore_missing='False') #surface point


#now draw 3 heatmap plots
for i in range(0, len(lon_p)):
    print (data_draw[i,:,:].shape, depth_t[:,point_index[i,0], point_index[i,1]].shape)
    plot_heatmap(
        title="Salinity profile at %sE %sN" %(lon_p[i],lat_p[i]),
        tstart=tstart, 
        tend = tend, 
        data_draw = data_draw[i,:,:],
        depth = depth_t[:,point_index[i,0], point_index[i,1]],
        path_save="/prod/projects/data/tungnd/figure/",
        name_save="demo_11",
    )

