import numpy as np

from GINCCO_lib.modules.section_plot import (
    draw_section_figure,
    extract_section as _extract_section,
)


def _safe_float(value):
    try:
        return float(value)
    except Exception:
        return None


def import_section(lon_data, lat_data, depth_data, lon_min, lon_max, lat_min, lat_max, data, M, depth_interval, method):
    """Compatibility wrapper for older viewer imports."""
    return _extract_section(
        lon_data=lon_data,
        lat_data=lat_data,
        depth_data=depth_data,
        lon_min=lon_min,
        lon_max=lon_max,
        lat_min=lat_min,
        lat_max=lat_max,
        data=data,
        M=M,
        depth_interval=depth_interval,
        method=method,
    )


def draw_section(var_name, var_data, opts, state):
    """GUI adapter for drawing a section from `gincco view`.

    The extraction and plotting implementation lives in
    `GINCCO_lib.modules.section_plot.draw_section_figure`.
    """
    if hasattr(var_data, "__getitem__") and not isinstance(var_data, np.ndarray):
        data = np.squeeze(var_data[:])
    else:
        data = np.squeeze(var_data)

    lon = state.get("lon")
    lat = state.get("lat")
    depth = state.get("depth")

    if lon is None or lat is None or depth is None:
        raise ValueError("lon/lat/depth not available in state; cannot build section.")

    depth_interval = _safe_float(opts.get("depth_interval"))
    if depth_interval is None or depth_interval <= 0:
        depth_interval = 1.0

    dpi = int(opts.get("dpi", 100)) if str(opts.get("dpi", "")).isdigit() else 100
    number_point = int(opts.get("number_point", 100))

    draw_section_figure(
        title="Section of {}".format(var_name),
        data=data,
        lon=lon,
        lat=lat,
        depth=depth,
        lon_min=_safe_float(opts.get("lon_p1")),
        lon_max=_safe_float(opts.get("lon_p2")),
        lat_min=_safe_float(opts.get("lat_p1")),
        lat_max=_safe_float(opts.get("lat_p2")),
        number_point=number_point,
        depth_interval=depth_interval,
        method=opts.get("interp_method", "bilinear"),
        fig_width=_safe_float(opts.get("fig_width")) or 7.0,
        fig_height=_safe_float(opts.get("fig_height")) or 4.0,
        dpi=dpi,
        cmap_name=opts.get("cmap", "jet"),
        cmap_min=_safe_float(opts.get("cmap_min")),
        cmap_max=_safe_float(opts.get("cmap_max")),
        vmin=_safe_float(opts.get("vmin")),
        vmax=_safe_float(opts.get("vmax")),
        dv=_safe_float(opts.get("dv")),
        plot_type=opts.get("plot_type", "contourf"),
        bottom_smoothing=opts.get("bottom_smoothing", "none"),
        bottom_smoothing_window=int(opts.get("bottom_smoothing_window", 5)),
        bottom_smoothing_sigma=_safe_float(opts.get("bottom_smoothing_sigma")) or 1.0,
        show=True,
    )
