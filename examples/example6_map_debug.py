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
mask_t = fgrid.variables['mask_t'][:,:]
#--------#--------#--------#--------#--------#--------#




fpath = path + '20221128_120000.symphonie.nc'
file1 = Dataset(fpath, 'r')   # fixed: previously 'ncfile'
data_toto = np.squeeze(file1.variables['sal'][:,:,:,:]).filled(np.nan)

print (data_toto.shape)
print (data_toto[0,-1,:])

print (data_toto[0,:,-1])

#data_toto2 = np.nansum(data_toto * multiply_array, axis=0)

#data_toto2[check_depth_array==0] = np.nan
#data_toto2[mask_t==0] = np.nan # mask land - sea value



