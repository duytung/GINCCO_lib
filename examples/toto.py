import numpy as np
from map_plot import *
from animation import * 
from pathlib import Path


#Create multiple map and save it as video

# === Create sample lon/lat grid and data ===
lon = np.linspace(100, 120, 250)   # 100E–110E
lat = np.linspace(8, 24, 100)      # 8N–24N
lon2d, lat2d = np.meshgrid(lon, lat)

for i in range(0, 100):
	print (i)
	# Example data: a simple 2D Gaussian hill
	data = np.exp(-((lon2d-110+i/20)**2 + (lat2d-16)**2)/10)

	# === Call map_draw ===
	map_draw(
	    lon_min=100, lon_max=120,
	    lat_min=8, lat_max=24,
	    title="Demo Map: Gaussian Hill %2.0f" %(i),
	    lon_data=lon2d,
	    lat_data=lat2d,
	    data_draw=data,
	    path_save="/prod/projects/data/tungnd/figure/",     # current folder
	    name_save="demo_123456_%02.0f" %(i)
	)

print ('Create video...')
# === Load png saved file and covnert it into a video ===
pngs_to_video("/prod/projects/data/tungnd/figure/demo_123456_*.png", 
					"/prod/projects/data/tungnd/figure/clip.mp4", fps=3)


# === Delete temporary file ===
for path in Path("/prod/projects/data/tungnd/figure").glob("demo_123456_*.png"):
    try:
        path.unlink()
        print(f"Deleted: {path}")
    except Exception as e:
        print(f"Error deleting {path}: {e}")

