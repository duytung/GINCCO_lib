import numpy as np
import GINCCO_lib as gc
from netCDF4 import Dataset 
from datetime import *
#Create multiple map and save it as video
tstart = datetime(2010,1,1)
tend = datetime(2010,1,10)

path = '/work/users/tungnd/GOT271/GOT_REF5/OFFLINE/'


#--------#--------#--------#--------#--------#--------#
#import grid 
fgrid = Dataset(path + 'grid.nc', 'r')
lat_t = fgrid.variables['latitude_t'][:]
lon_t = fgrid.variables['longitude_t'][:]

#--------#--------#--------#--------#--------#--------#

#Example 1: 
sal_full = gc.import_4D(path, 'sal', tstart, tend, ignore_missing='False')
print (np.nanmin(sal_full), np.nanmax(sal_full))


gc.map_draw(
    lon_min=105, lon_max=111,
    lat_min=16.5, lat_max=22,
    title="Bottom salinity (example 1)",
    lon_data=lon_t,
    lat_data=lat_t,
    data_draw=sal_full[0,0,:,:],  		# day 0, level 0
    path_save="/prod/projects/data/tungnd/figure/",     # current folder
    name_save="demo_01"
)

print ('#--------#--------#--------#--------#--------#--------#')


#Example 2: 
ssh = gc.import_3D(path, 'ssh_ib', tstart, tend, ignore_missing='False')
print (ssh.shape)
print (np.nanmin(ssh), np.nanmax(ssh))
gc.map_draw(
    lon_min=105, lon_max=111,
    lat_min=16.5, lat_max=22,
    title="ssh (example 2)",
    lon_data=lon_t,
    lat_data=lat_t,
    data_draw=ssh[0,:,:], 
    path_save="/prod/projects/data/tungnd/figure/",     # current folder
    name_save="demo_02"
)

print ('#--------#--------#--------#--------#--------#--------#')
#Example 3: 
sal_surface = gc.import_surface(path, 'sal', tstart, tend, ignore_missing='False')
print (np.nanmin(sal_surface), np.nanmax(sal_surface))

gc.map_draw(
    lon_min=105, lon_max=111,
    lat_min=16.5, lat_max=22,
    title="surface salinity (example 3)",
    lon_data=lon_t,
    lat_data=lat_t,
    data_draw=sal_surface[0,:,:], 
    path_save="/prod/projects/data/tungnd/figure/",     # current folder
    name_save="demo_03"
)

print ('#--------#--------#--------#--------#--------#--------#')
#Example 4: 
sal_layer = gc.import_layer(path, 'sal', tstart, tend, 10, ignore_missing='False')
gc.map_draw(
    lon_min=105, lon_max=111,
    lat_min=16.5, lat_max=22,
    title="salinity at layer 10 (example 4)",
    lon_data=lon_t,
    lat_data=lat_t,
    data_draw=sal_layer[0,:,:], 
    path_save="/prod/projects/data/tungnd/figure/",     # current folder
    name_save="demo_04"
)

print ('#--------#--------#--------#--------#--------#--------#')
#Example 5: 

sal_depth = gc.import_depth(path, 'sal', tstart, tend, 40, ignore_missing='False')
gc.map_draw(
    lon_min=105, lon_max=111,
    lat_min=16.5, lat_max=22,
    title="salinity at 40m (example 5)",
    lon_data=lon_t,
    lat_data=lat_t,
    data_draw=sal_depth[0,:,:], #day 1
    path_save="/prod/projects/data/tungnd/figure/",     # current folder
    name_save="demo_05"
)







