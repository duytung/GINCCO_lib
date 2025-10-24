Example 4: Create video
=======================

This example demonstrates how to import file and create video with GINCCO_lib
using :func:`GINCCO_lib.image_to_video.pngs_to_video`.


Code Example
------------

Now we will import the library and the grid

.. code-block:: python

    # =========================
    # IMPORTS
    # =========================
    import numpy as np
    import GINCCO_lib as gc
    from netCDF4 import Dataset
    from datetime import *
    from pathlib import Path
    import random

    # =========================
    # CONFIGURATION
    # =========================
    tstart = datetime(2010, 7, 1)
    tend   = datetime(2010, 8, 31)

    path       = '/work/users/tungnd/GOT271/GOT_REF5/OFFLINE/'
    session_id = random.randint(10000, 99999)   # unique ID for file naming

    # =========================
    # LOAD GRID
    # =========================
    fgrid = Dataset(path + 'grid.nc', 'r')
    lat_t = fgrid.variables['latitude_t'][:]
    lon_t = fgrid.variables['longitude_t'][:]



Now import all wanted figures on map 

.. code-block:: python

    # ============================================================
    # EXAMPLE: Create multiple maps and combine them into a video
    # ============================================================

    # Step 1: Import surface salinity
    sal_surface = gc.import_surface(path, 'sal', tstart, tend, ignore_missing='False')
    print(np.nanmin(sal_surface), np.nanmax(sal_surface))

    # Define plotting range based on percentiles
    data_min = np.nanpercentile(sal_surface, 5)
    data_max = np.nanpercentile(sal_surface, 95)

    # Step 2: Generate daily maps (60 days)
    for i in range(60):
        tnow = tstart + timedelta(days=i)
        gc.map_draw(
            lon_min=105, lon_max=111,
            lat_min=16.5, lat_max=22,
            title="Surface salinity at %s" % (tnow.strftime('%Y-%b-%d')),
            lon_data=lon_t,
            lat_data=lat_t,
            data_draw=sal_surface[i, :, :],
            path_save="/prod/projects/data/tungnd/figure/",
            name_save="demo_%s_%03.0f" % (session_id, i),
            data_min=data_min,
            data_max=data_max,
        )

Here is an example of a figure

.. image:: ../_static/example4.png
   :width: 500px
   :align: center



Now creating a video

.. code-block:: python

    # Step 3: Convert saved PNGs into a video
    print('Creating video...')
    gc.pngs_to_video(
        "/prod/projects/data/tungnd/figure/demo_%s_*.png" % session_id,
        "/prod/projects/data/tungnd/figure/clip_%s.mp4" % session_id,
        fps=5
    )

    # Step 4: Delete temporary PNG files
    for path in Path("/prod/projects/data/tungnd/figure").glob("demo_%s_*.png" % session_id):
        try:
            path.unlink()
            print(f"Deleted: {path}")
        except Exception as e:
            print(f"Error deleting {path}: {e}")


.. raw:: html

   <div style="text-align:center">
     <iframe src="https://drive.google.com/file/d/1yxxuBXVnlyFXGMUCDDhNSR9g_fb6DEhy/preview"
             width="640" height="480"
             allow="autoplay">
     </iframe>
   </div>



