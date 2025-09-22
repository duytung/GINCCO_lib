import numpy as np
import GINCCO_lib as gc
from netCDF4 import Dataset 
from datetime import *
#Create multiple map and save it as video
tstart = datetime(2022,11,27)
tend = datetime(2022,11,30)

path = '/data/projects/LOTUS/tungnd/Nadia_sample/'


#--------#--------#--------#--------#--------#--------#
#import grid 
fgrid = Dataset(path + 'grid.nc', 'r')
lat_t = fgrid.variables['latitude_t'][:]
lon_t = fgrid.variables['longitude_t'][:]

#--------#--------#--------#--------#--------#--------#

#Example 5: 

for k in range(0,4):
    sal_depth = gc.import_depth(path, 'sal', tstart, tend, 35, ignore_missing='False')
    gc.map_draw(
        lon_min=105, lon_max=111,
        lat_min=16.5, lat_max=22,
        title="salinity at 15m (Nadia new file) ",
        lon_data=lon_t,
        lat_data=lat_t,
        data_draw=sal_depth[k,:,:], #day 1
        path_save="/prod/projects/data/tungnd/figure/",     # current folder
        name_save="demo_05_%s" %(k)
    )

#--------#--------#--------#--------#--------#--------#

tstart = datetime(2010,1,1)
tend = datetime(2010,1,10)

path = '/work/users/tungnd/GOT271/GOT_REF5/OFFLINE/'

sal_depth = gc.import_depth(path, 'sal', tstart, tend, 35, ignore_missing='False')
gc.map_draw(
    lon_min=105, lon_max=111,
    lat_min=16.5, lat_max=22,
    title="salinity at 15m (Tung old file)",
    lon_data=lon_t,
    lat_data=lat_t,
    data_draw=sal_depth[0,:,:], #day 1
    path_save="/prod/projects/data/tungnd/figure/",     # current folder
    name_save="demo_05"
)






