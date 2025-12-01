'''
.. module:: GINCCO_lib
   :noindex:
'''

# import-related functions
from .modules.import_series_daily import (
    import_4D,
    import_3D,
    import_surface,
    import_layer,
    import_depth,
    import_point,
    import_profile,
)
from .modules.import_daily import import_section


# post-processing function
from .modules.interpolate_to_t import interpolate_to_t
from .modules.geostrophic_current import geostrophic_current
from .modules.spatial_average import spatial_average
from .modules.temporal_mean import monthly_mean, annual_mean


# plot-related functions
from .modules.map_plot import map_draw, map_draw_point, map_draw_uv, map_draw_box
from .modules.time_series_plot import plot_point, plot_point_monthly
from .modules.heatmap_plot import plot_heatmap, plot_section, plot_section_contourf


#video-related function
from .image_to_video import pngs_to_video

# define what is exposed when users do `from yourpkg import *`
__all__ = [
    # import functions
    "import_4D",
    "import_3D",
    "import_surface",
    "import_layer",
    "import_depth",
    "import_point",
    "import_profile",

    "import_section",


    # post-processing function
    "interpolate_to_t",


    # plot functions
    "map_draw",
    "map_draw_point",
    "map_draw_uv",
    
    "plot_point",
    "plot_heatmap",
    "plot_section",


    #video function
    "pngs_to_video",
]

__version__ = "0.7"
