# draw_section.py
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from mpl_toolkits.basemap import Basemap
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import MaxNLocator
from tkinter import messagebox

from GINCCO_lib.commands.view.interpolate_to_t import interpolate_to_t
from GINCCO_lib.modules.import_daily import section_extract, _data_interp

try:
    from scipy.spatial import cKDTree as KDTree
except Exception:
    KDTree = None


def _truncate_colormap(cmap, minval=0.0, maxval=1.0, n=256):
    if isinstance(cmap, str):
        cmap = plt.get_cmap(cmap)
    minval = float(minval)
    maxval = float(maxval)
    if not (0 <= minval < maxval <= 1):
        minval, maxval = 0.0, 1.0
    new_cmap = mcolors.LinearSegmentedColormap.from_list(
        f"trunc({cmap.name},{minval:.2f},{maxval:.2f})",
        cmap(np.linspace(minval, maxval, n)),
    )
    return new_cmap


def _nice_ticks(vmin, vmax, n=4):
    ticks = np.linspace(vmin, vmax, n)
    step = (vmax - vmin) / max(1, (n - 1))
    try:
        digits = max(0, 2 - int(np.floor(np.log10(step)))) if step > 0 else 0
    except Exception:
        digits = 0
    return np.round(ticks, digits)




def import_section(lon_data, lat_data, depth_data, lon_min, lon_max, lat_min, lat_max, data, M, depth_interval, method):
    """
    Extract and interpolate a vertical section along a line in lon/lat space.

    The section can follow:
        - a constant longitude (meridional section),
        - a constant latitude (zonal section),
        - or an arbitrary diagonal line between (lon_min, lat_min) and
          (lon_max, lat_max).

    Parameters
    ----------
    lon_data : np.ndarray
        2D or 3D array of longitudes on the model grid.
    lat_data : np.ndarray
        2D or 3D array of latitudes on the model grid.
    depth_data : np.ndarray
        Depth levels associated with the data (e.g. 1D or 3D).
    lon_min, lon_max, lat_min, lat_max : float
        Coordinates of the section endpoints. If lon_min == lon_max, the
        section is taken along longitude; if lat_min == lat_max, along
        latitude; otherwise along the diagonal line.
    data : np.ndarray
        Original 3D data (depth × y × x) to interpolate along the section.
    M : int
        Number of horizontal points along the section line.
    depth_interval : float
        Vertical interpolation interval (e.g. 1.0 for 1 m).
    method : str
        Horizontal interpolation method, e.g. "Linear" or "IDW".

    Returns
    -------
    depth_out : np.ndarray of shape (K, M)
        Regular vertical depth grid (same for all horizontal positions).
    data_out : np.ndarray of shape (K, M)
        Data interpolated onto (depth_out, section coordinate).
    """


    # Setup the section
    if (lon_min == lon_max):
        if lat_min == lat_max:  
            print ('lon_min = lon_max and lat_min = lat_max. Not a section. Exiting...' )
            exit()
        else:
            lon_sec = np.full(M, lon_max)
            lat_sec = np.linspace(lat_min, lat_max, M) 
    elif lat_min == lat_max:
            lat_sec = np.full(M, lat_max)
            lon_sec = np.linspace(lon_min, lon_max, M) 
    else:
        lat_sec = np.linspace(lat_min, lat_max, M)      # lat section
        lon_sec = np.linspace(lon_min, lon_max, M)      # lon_section

    depth_sec, apply_interp = section_extract(lat_data, lon_data, depth_data, lat_sec, lon_sec, method=method)

    #interpolate data
    data_interpolation = apply_interp(data) # shape: (nz, M)

    #interpolate depth and data into 1m for better representation
    depth_out, data_out = _data_interp(depth_sec, data_interpolation, depth_interval=depth_interval)

    return depth_out, data_out




def draw_section(var_name, var_data, opts, state):
    """
    Draw a vertical section for a given variable using GUI options and state.

    Parameters
    ----------
    var_name : str
        Name of the variable being plotted (for the title and logging).
    var_data : np.ndarray or netCDF variable
        Data array for the selected variable. Can be a NumPy array or a
        netCDF4 variable; in both cases it will be squeezed to remove
        singleton dimensions.
    opts : dict
        Plotting options collected from the GUI, including for example:
            - "vmin", "vmax"
            - "fig_width", "fig_height"
            - "cmap", "cmap_min", "cmap_max"
            - "lon_p1", "lon_p2", "lat_p1", "lat_p2"
            - "dpi"
            - "interp_method"  ("Linear" or "IDW")
            - "number_point"   (int, number of points along section)
            - "depth_interval" (float, vertical resolution)
    state : dict
        Metadata/state set by the tab, typically including:
            - "lon", "lat", "depth", "mask"
            - "var_name"
    """
    # ---------- Data ----------
    if hasattr(var_data, "__getitem__") and not isinstance(var_data, np.ndarray):
        data = np.squeeze(var_data[:])
    else:
        data = np.squeeze(var_data)

    # ---------- Grid (lon/lat/depth/mask) ----------
    lon = state.get("lon")
    lat = state.get("lat")
    depth = state.get("depth")
    mask = state.get("mask")

    def safe_float(x):
        try:
            return float(x)
        except Exception:
            return None

    # ---------- Options ----------
    interp_method = opts.get("interp_method", "Linear")
    number_point = int(opts.get("number_point", 100))  # sensible default
    depth_interval = safe_float(opts.get("depth_interval"))
    if depth_interval is None or depth_interval <= 0:
        depth_interval = 1.0

    fig_width = safe_float(opts.get("fig_width")) or 7.0
    fig_height = safe_float(opts.get("fig_height")) or 4.0

    cmap_name = opts.get("cmap", "jet")
    cmap_min = safe_float(opts.get("cmap_min"))
    cmap_max = safe_float(opts.get("cmap_max"))

    lon_min_user = safe_float(opts.get("lon_p1"))
    lon_max_user = safe_float(opts.get("lon_p2"))
    lat_min_user = safe_float(opts.get("lat_p1"))
    lat_max_user = safe_float(opts.get("lat_p2"))

    dpi = int(opts.get("dpi", 100)) if str(opts.get("dpi", "")).isdigit() else 100

    v_min_user = safe_float(opts.get("vmin"))
    v_max_user = safe_float(opts.get("vmax"))

    # Fallback coordinates from grid if user left them empty
    if lon is None or lat is None or depth is None:
        raise ValueError("lon/lat/depth not available in state; cannot build section.")

    lon_min = lon_min_user if lon_min_user is not None else float(np.nanmin(lon))
    lon_max = lon_max_user if lon_max_user is not None else float(np.nanmax(lon))
    lat_min = lat_min_user if lat_min_user is not None else float(np.nanmin(lat))
    lat_max = lat_max_user if lat_max_user is not None else float(np.nanmax(lat))

    # ---------- Build section ----------
    depth_section, data_draw = import_section(
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
        method=interp_method,
    )

    # ---------- Value range from data / user ----------
    vmin_data = np.nanpercentile(data_draw, 5)
    vmax_data = np.nanpercentile(data_draw, 95)
    vmin = v_min_user if v_min_user is not None else vmin_data
    vmax = v_max_user if v_max_user is not None else vmax_data

    # ---------- Colormap ----------
    n_colors = 20
    levels = np.linspace(vmin, vmax, n_colors + 1)
    cmap = plt.get_cmap(cmap_name, n_colors)

    if cmap_min is not None or cmap_max is not None:
        # Optional truncation of the colormap range
        lo = 0.0 if cmap_min is None else cmap_min
        hi = 1.0 if cmap_max is None else cmap_max
        cmap = _truncate_colormap(cmap, lo, hi, n=n_colors)

    norm = BoundaryNorm(levels, ncolors=cmap.N, clip=True)
    ticks = _nice_ticks(vmin, vmax)


    # ---------- Figure ----------
    plt.close("all")
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)

    n_depth, n_M = data_draw.shape

    X_axis = np.arange(n_M)
    Z_axis = depth_section[:, 0]
    X_axis, Z_axis = np.meshgrid(X_axis, Z_axis)

    cf = ax.contourf(
        X_axis, Z_axis, data_draw,
        levels=levels, cmap=cmap, norm=norm, extend="both"
    )

    title = f"Section of {var_name}"
    ax.set_title(title)
    ax.set_xlabel("Position along section")
    ax.set_ylabel("Depth (m)")
    # ax.invert_yaxis()  # uncomment if depth is positive downward

    # X-axis ticks: show combined Lat/Lon at a few positions
    n_ticks = 5
    lat_list = np.linspace(lat_min, lat_max, n_M)
    lon_list = np.linspace(lon_min, lon_max, n_M)
    xtick = np.linspace(0, n_M - 1, n_ticks, dtype=int)
    xtick_label = [f"{lat_list[i]:.2f}N\n{lon_list[i]:.2f}E" for i in xtick]
    ax.set_xticks(xtick)
    ax.set_xticklabels(xtick_label)

    # Colorbar
    cbar_ax = fig.add_axes([0.15, 0.07, 0.7, 0.02])
    cb = fig.colorbar(cf, cax=cbar_ax, ticks=ticks, orientation="horizontal")
    cbar_ax.set_label(var_name)

    fig.subplots_adjust(bottom=0.3, top=0.9, left=0.1, right=0.95, wspace=0.2, hspace=0.3)
    fig.tight_layout()
    plt.show(block=False)

