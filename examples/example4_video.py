import numpy as np
import GINCCO_lib as gc
from netCDF4 import Dataset 
from datetime import *
from pathlib import Path
import random

#Create multiple map and save it as video
tstart = datetime(2010,1,1)
tend = datetime(2010,1,10)

path = '/work/users/tungnd/GOT271/GOT_REF5/OFFLINE/'
session_id = random.randint(1E5, 1E6)

#--------#--------#--------#--------#--------#--------#
#import grid 
fgrid = Dataset(path + 'grid.nc', 'r')
lat_t = fgrid.variables['latitude_t'][:]
lon_t = fgrid.variables['longitude_t'][:]

#--------#--------#--------#--------#--------#--------#

#Example 1 
sal_surface = gc.import_surface(path, 'sal', tstart, tend, ignore_missing='False')
print (np.nanmin(sal_surface), np.nanmax(sal_surface))
data_min = np.nanpercentile(sal_surface, 5)
data_max = np.nanpercentile(sal_surface, 95)
for i in range(0, 10):
    gc.map_draw(
        lon_min=105, lon_max=111,
        lat_min=16.5, lat_max=22,
        title="surface salinity (example 3)",
        lon_data=lon_t,
        lat_data=lat_t,
        data_draw=sal_surface[i,:,:], 
        path_save="/prod/projects/data/tungnd/figure/",     # current folder
        name_save="demo_%s_%s" %(session_id, i),
        data_min = data_min, 
        data_max = data_max,
    )


print ('Create video...')
# === Load png saved file and covnert it into a video ===
gc.pngs_to_video("/prod/projects/data/tungnd/figure/demo_%s_*.png" %(session_id), 
                    "/prod/projects/data/tungnd/figure/clip_%s.mp4" %(session_id), fps=1)


# === Delete temporary file ===
for path in Path("/prod/projects/data/tungnd/figure").glob("demo_%s_*.png" %(session_id)):
    try:
        path.unlink()
        print(f"Deleted: {path}")
    except Exception as e:
        print(f"Error deleting {path}: {e}")



