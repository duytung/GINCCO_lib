import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colors import BoundaryNorm

from GINCCO_lib.modules.import_daily import section_extract, _data_interp


def _safe_float(value):
    try:
        return float(value)
    except Exception:
        return None


def _truncate_colormap(cmap, minval=0.0, maxval=1.0, n=256):
    if isinstance(cmap, str):
        cmap = plt.get_cmap(cmap)
    minval = float(minval)
    maxval = float(maxval)
    if not (0 <= minval < maxval <= 1):
        minval, maxval = 0.0, 1.0
    return mcolors.LinearSegmentedColormap.from_list(
        "trunc({},{:.2f},{:.2f})".format(cmap.name, minval, maxval),
        cmap(np.linspace(minval, maxval, n)),
    )


def _nice_ticks(vmin, vmax, n=4):
    ticks = np.linspace(vmin, vmax, n)
    step = (vmax - vmin) / max(1, (n - 1))
    try:
        digits = max(0, 2 - int(np.floor(np.log10(step)))) if step > 0 else 0
    except Exception:
        digits = 0
    return np.round(ticks, digits)


def _normalize_method(method):
    method_map = {"linear": "bilinear", "bilinear": "bilinear", "idw": "idw"}
    normalized = method_map.get(str(method).lower())
    if normalized is None:
        raise ValueError("method must be 'bilinear'/'linear' or 'idw'.")
    return normalized


def _normalize_plot_type(plot_type):
    plot_type_map = {
        "contour": "contourf",
        "contourf": "contourf",
        "pcolor": "pcolormesh",
        "pcolormesh": "pcolormesh",
    }
    normalized = plot_type_map.get(str(plot_type).lower())
    if normalized is None:
        raise ValueError("plot_type must be 'contourf'/'contour' or 'pcolormesh'/'pcolor'.")
    return normalized


def _normalize_bottom_smoothing(method):
    method_map = {
        "none": "none",
        "off": "none",
        "median": "median",
        "moving average": "moving_average",
        "moving_average": "moving_average",
        "mean": "moving_average",
        "gaussian": "gaussian",
    }
    normalized = method_map.get(str(method).lower())
    if normalized is None:
        raise ValueError("bottom_smoothing must be 'none', 'median', 'moving_average', or 'gaussian'.")
    return normalized


def _window_size(window):
    window = int(window or 1)
    return max(1, window)


def _smooth_local_1d(values, method, window=5, sigma=1.0):
    values = np.asarray(values, dtype=float)
    out = np.full(values.shape, np.nan, dtype=float)
    if values.size == 0:
        return out

    method = _normalize_bottom_smoothing(method)
    if method == "none":
        return values.copy()

    window = _window_size(window)
    before = window // 2
    after = window - before - 1

    if method in ("median", "moving_average"):
        for i in range(values.size):
            lo = max(0, i - before)
            hi = min(values.size, i + after + 1)
            local = values[lo:hi]
            local = local[np.isfinite(local)]
            if local.size == 0:
                continue
            if method == "median":
                out[i] = np.nanmedian(local)
            else:
                out[i] = np.nanmean(local)
        return out

    sigma = float(sigma or 1.0)
    sigma = max(sigma, 1e-6)
    radius = max(1, int(np.ceil(3.0 * sigma)))
    offsets = np.arange(-radius, radius + 1, dtype=float)
    weights = np.exp(-0.5 * (offsets / sigma) ** 2)

    for i in range(values.size):
        lo = max(0, i - radius)
        hi = min(values.size, i + radius + 1)
        w_lo = radius - (i - lo)
        w_hi = w_lo + (hi - lo)
        local = values[lo:hi]
        local_weights = weights[w_lo:w_hi]
        valid = np.isfinite(local)
        if not np.any(valid):
            continue
        out[i] = np.sum(local[valid] * local_weights[valid]) / np.sum(local_weights[valid])
    return out


def _apply_bottom_smoothing_mask(data_draw, depth_section, method="none", window=5, sigma=1.0):
    method = _normalize_bottom_smoothing(method)
    if method == "none":
        return data_draw

    data_out = np.asarray(data_draw, dtype=float).copy()
    depth_abs = np.abs(np.asarray(depth_section, dtype=float))
    if data_out.shape != depth_abs.shape:
        raise ValueError("data_draw and depth_section must have the same shape.")

    n_depth, n_points = data_out.shape
    raw_bottom = np.full(n_points, np.nan, dtype=float)
    for m in range(n_points):
        valid = np.isfinite(data_out[:, m]) & np.isfinite(depth_abs[:, m])
        if np.any(valid):
            raw_bottom[m] = np.nanmax(depth_abs[valid, m])

    smooth_bottom = _smooth_local_1d(raw_bottom, method, window=window, sigma=sigma)

    for m in range(n_points):
        if not np.isfinite(raw_bottom[m]) or not np.isfinite(smooth_bottom[m]):
            continue
        bottom_limit = min(raw_bottom[m], smooth_bottom[m])
        data_out[depth_abs[:, m] > bottom_limit, m] = np.nan

    return data_out


def extract_section(lon_data, lat_data, depth_data, lon_min, lon_max, lat_min, lat_max, data, M, depth_interval=1.0, method="bilinear"):
    """Extract and interpolate a vertical section from gridded 3D data.

    Returns
    -------
    depth_out, data_out : ndarray
        Arrays with shape (nz_out, M).
    """
    method = _normalize_method(method)
    M = int(M)
    if M < 2:
        raise ValueError("M must be >= 2 for a section.")

    if lon_min == lon_max:
        if lat_min == lat_max:
            raise ValueError("lon_min = lon_max and lat_min = lat_max. Not a section.")
        lon_sec = np.full(M, lon_max)
        lat_sec = np.linspace(lat_min, lat_max, M)
    elif lat_min == lat_max:
        lat_sec = np.full(M, lat_max)
        lon_sec = np.linspace(lon_min, lon_max, M)
    else:
        lat_sec = np.linspace(lat_min, lat_max, M)
        lon_sec = np.linspace(lon_min, lon_max, M)

    depth_sec, apply_interp = section_extract(lat_data, lon_data, depth_data, lat_sec, lon_sec, method=method)
    data_interpolation = apply_interp(data)

    # A single vertical level has no depth range to remap. Return the raw
    # transect so callers can draw it as a line plot.
    if depth_sec.shape[0] < 2:
        return depth_sec, data_interpolation

    return _data_interp(depth_sec, data_interpolation, depth_interval=depth_interval)


def draw_section_figure(
    title,
    data,
    lon,
    lat,
    depth,
    lon_min=None,
    lon_max=None,
    lat_min=None,
    lat_max=None,
    number_point=400,
    depth_interval=1.0,
    method="bilinear",
    fig_width=7.0,
    fig_height=4.0,
    dpi=100,
    cmap_name="jet",
    cmap_min=None,
    cmap_max=None,
    vmin=None,
    vmax=None,
    dv=None,
    n_ticks=5,
    plot_type="contourf",
    bottom_smoothing="none",
    bottom_smoothing_window=6,
    bottom_smoothing_sigma=3.0,
    show=True,
    ax=None,
):
    """Draw a section figure from gridded data.

    This is the shared plotting core used by both scripts and the `gincco view` UI.
    It draws a contourf or pcolormesh section when at least two vertical levels
    are available, and a transect line plot for single-level data.
    """
    plot_type = _normalize_plot_type(plot_type)
    if lon is None or lat is None or depth is None:
        raise ValueError("lon/lat/depth are required to build a section.")

    data = np.squeeze(np.asarray(np.ma.filled(data, np.nan)))
    lon = np.asarray(lon)
    lat = np.asarray(lat)
    depth = np.squeeze(np.asarray(np.ma.filled(depth, np.nan)))

    if data.ndim == 2:
        data = data[np.newaxis, :, :]
    if depth.ndim == 2:
        depth = depth[np.newaxis, :, :]

    lon_min = float(np.nanmin(lon)) if lon_min is None else float(lon_min)
    lon_max = float(np.nanmax(lon)) if lon_max is None else float(lon_max)
    lat_min = float(np.nanmin(lat)) if lat_min is None else float(lat_min)
    lat_max = float(np.nanmax(lat)) if lat_max is None else float(lat_max)

    depth_section, data_draw = extract_section(
        lon_data=lon,
        lat_data=lat,
        depth_data=depth,
        lon_min=lon_min,
        lon_max=lon_max,
        lat_min=lat_min,
        lat_max=lat_max,
        data=data,
        M=number_point,
        depth_interval=depth_interval,
        method=method,
    )
    data_draw = _apply_bottom_smoothing_mask(
        data_draw,
        depth_section,
        method=bottom_smoothing,
        window=bottom_smoothing_window,
        sigma=bottom_smoothing_sigma,
    )

    vmin_data = np.nanpercentile(data_draw, 5)
    vmax_data = np.nanpercentile(data_draw, 95)
    vmin = vmin if vmin is not None else vmin_data
    vmax = vmax if vmax is not None else vmax_data
    if not np.isfinite(vmin) or not np.isfinite(vmax) or vmin >= vmax:
        vmin, vmax = np.nanmin(data_draw), np.nanmax(data_draw)
        if not np.isfinite(vmin) or not np.isfinite(vmax) or vmin == vmax:
            vmin, vmax = -0.5, 0.5

    n_colors = 200
    levels = np.linspace(vmin, vmax, n_colors + 1)
    cmap = plt.get_cmap(cmap_name, n_colors)
    if cmap_min is not None or cmap_max is not None:
        lo = 0.0 if cmap_min is None else float(cmap_min)
        hi = 1.0 if cmap_max is None else float(cmap_max)
        cmap = _truncate_colormap(cmap, lo, hi, n=n_colors)

    norm = BoundaryNorm(levels, ncolors=cmap.N, clip=True)
    ticks = _nice_ticks(vmin, vmax)
    if dv is not None:
        ticks = np.arange(vmin, vmax + dv, dv)

    created_fig = ax is None
    if created_fig:
        fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)
    else:
        fig = ax.figure

    n_depth, n_M = data_draw.shape
    x_axis = np.arange(n_M)
    z_axis = depth_section[:, 0]
    x_mesh, z_mesh = np.meshgrid(x_axis, z_axis)

    ax.set_title(title)
    if n_depth < 2:
        mesh = None
        ax.plot(x_axis, data_draw[0, :], marker="o" if n_M < 20 else None)
        ax.set_xlabel("Position along section")
        ax.set_ylabel(title)
    elif plot_type == "pcolormesh":
        mesh = ax.pcolormesh(x_mesh, z_mesh, data_draw, cmap=cmap, norm=norm, shading="auto")
        ax.set_xlabel("Position along section")
        ax.set_ylabel("Depth (m)")
    else:
        mesh = ax.contourf(x_mesh, z_mesh, data_draw, levels=levels, cmap=cmap, norm=norm, extend="both")
        ax.set_xlabel("Position along section")
        ax.set_ylabel("Depth (m)")

    n_ticks = max(1, min(int(n_ticks), n_M))
    lat_list = np.linspace(lat_min, lat_max, n_M)
    lon_list = np.linspace(lon_min, lon_max, n_M)
    xtick = np.linspace(0, n_M - 1, n_ticks, dtype=int)
    xtick_label = ["{:.2f}N\n{:.2f}E".format(lat_list[i], lon_list[i]) for i in xtick]
    ax.set_xticks(xtick)
    ax.set_xticklabels(xtick_label)

    if mesh is not None:
        cbar_ax = fig.add_axes([0.15, 0.07, 0.7, 0.02])
        fig.colorbar(mesh, cax=cbar_ax, ticks=ticks, orientation="horizontal")
        cbar_ax.set_label(title)

    fig.subplots_adjust(bottom=0.3, top=0.9, left=0.1, right=0.95, wspace=0.2, hspace=0.3)
    if show:
        plt.show(block=False)

    return fig, ax, depth_section, data_draw
