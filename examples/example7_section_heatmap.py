import numpy as np
from netCDF4 import Dataset 
from datetime import *
import GINCCO_lib as gc
#--------#--------#--------#--------#--------#--------#
tstart = datetime(2010,1,1)
tend = datetime(2010,10,30)

path = '/work/users/tungnd/GOT271/GOT_REF5/OFFLINE/'
file_name = '20150828_120000.symphonie.nc'

#--------#--------#--------#--------#--------#--------#
#import grid 
fgrid = Dataset(path + 'grid.nc', 'r')
lat_t = fgrid.variables['latitude_t'][:]
lon_t = fgrid.variables['longitude_t'][:]
mask_t = fgrid.variables['mask_t'][:,:,:] 
depth_t = fgrid.variables['depth_t'][:,:,:]
depth_t[mask_t == 0] = np.nan
#--------#--------#--------#--------#--------#--------#

lon_p = [106, 107.5,]
lat_p = [19, 20,]

gc.map_draw_point(
    lon_min=105, lon_max=111,
    lat_min=16.5, lat_max=22,
    title="Locations of points and bathymetry (in m)",
    lon_data=lon_t,
    lat_data=lat_t,
    data_draw=depth_t[0,:,:], 
    lat_point = lat_p,
    lon_point = lon_p,
    path_save="/prod/projects/data/tungnd/figure/",     # current folder
    name_save="demo_7"
)


#import a section
depth_out, data_out = import_section(path = path, 
                                    file_name = file_name, 
                                    var = 'sal', 
                                    lon_min = lon_p[0], lon_max = lon_p[1], 
                                    lat_min = lat_p[0], lat_max = lat_p[1], 
                                    M = 100, 
                                    depth_interval = 1)





#now draw heatmap




plot_section(
    title = 'Salinity section',
    data_draw = data_out,  
    depth_array = depth_out,       # np.ndarray, shape (depth, M)
    lon_min = lon_p[0], lon_max = lon_p[1], 
    lat_min = lat_p[0], lat_max = lat_p[1], 
    path_save="/prod/projects/data/tungnd/figure/",
    name_save="section",
    n_colors=100,       # number of discrete color bins
    n_ticks = 5
)




