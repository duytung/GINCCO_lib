# GINCCO_lib

Utilities for:
- Reading a single NetCDF
- Opening multiple files along time
- Simple stats (mean/std/min/max)
- Quick map plots with `pcolormesh` (default `jet`)

## Install (from GitHub)

conda create -n gincco_test2 python=3.7

conda activate gincco_test2

conda install numpy scipy netcdf4

conda install matplotlib 

conda install basemap

pip install git+https://github.com/duytung/GINCCO_lib.git

If you would like to make video from the list of output, please install following library: 

pip install imageio[ffmpeg] imageio[pyav] pillow

## Notes
Please note that the examples are not included when install using pip. 