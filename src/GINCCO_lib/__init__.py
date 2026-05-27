'''
.. module:: GINCCO_lib
   :noindex:
'''

from importlib import import_module

__version__ = "0.7"

_EXPORTS = {
    # import-related functions
    "import_4D": ".modules.import_series_daily",
    "import_3D": ".modules.import_series_daily",
    "import_surface": ".modules.import_series_daily",
    "import_layer": ".modules.import_series_daily",
    "import_depth": ".modules.import_series_daily",
    "import_point": ".modules.import_series_daily",
    "import_profile": ".modules.import_series_daily",
    "import_section": ".modules.import_daily",

    # post-processing functions
    "interpolate_to_t": ".modules.interpolate_to_t",
    "interpolate_depth": ".modules.vertical_interpolation",
    "geostrophic_current": ".modules.geostrophic_current",
    "spatial_average": ".modules.spatial_average",
    "monthly_mean": ".modules.temporal_mean",
    "annual_mean": ".modules.temporal_mean",

    # plot-related functions
    "map_draw": ".modules.map_plot",
    "map_draw_point": ".modules.map_plot",
    "map_draw_uv": ".modules.map_plot",
    "map_draw_box": ".modules.map_plot",
    "plot_point": ".modules.time_series_plot",
    "plot_point_monthly": ".modules.time_series_plot",
    "plot_heatmap": ".modules.heatmap_plot",
    "plot_section": ".modules.heatmap_plot",
    "plot_section_contourf": ".modules.heatmap_plot",
    "draw_section_figure": ".modules.section_plot",
    "extract_section": ".modules.section_plot",

    # video-related function
    "pngs_to_video": ".modules.image_to_video",
}

__all__ = sorted(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError("module {!r} has no attribute {!r}".format(__name__, name))

    module = import_module(_EXPORTS[name], __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
