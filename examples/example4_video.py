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

#Example 1 
sal_surface = gc.import_surface(path, 'sal', tstart, tend, ignore_missing='False')
print (np.nanmin(sal_surface), np.nanmax(sal_surface))

for i in range(0, 10):
    gc.map_draw(
        lon_min=105, lon_max=111,
        lat_min=16.5, lat_max=22,
        title="surface salinity (example 3)",
        lon_data=lon_t,
        lat_data=lat_t,
        data_draw=sal_surface[0,:,:], 
        path_save="/prod/projects/data/tungnd/figure/",     # current folder
        name_save="demo_123456_%s" %(i)
    )


print ('Create video...')
# === Load png saved file and covnert it into a video ===
pngs_to_video("/prod/projects/data/tungnd/figure/demo_123456_*.png", 
                    "/prod/projects/data/tungnd/figure/clip_123.mp4", fps=1)


# === Delete temporary file ===
for path in Path("/prod/projects/data/tungnd/figure").glob("demo_123456_*.png"):
    try:
        path.unlink()
        print(f"Deleted: {path}")
    except Exception as e:
        print(f"Error deleting {path}: {e}")



