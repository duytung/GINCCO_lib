import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from GINCCO_lib.commands.interpolate_to_t import interpolate_to_t
from mpl_toolkits.basemap import Basemap

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
        cmap(np.linspace(minval, maxval, n))
    )
    return new_cmap


def _nice_ticks(vmin, vmax, n=4):
    ticks = np.linspace(vmin, vmax, n)
    step = (vmax - vmin) / max(1, (n - 1))
    # safe digits computation
    try:
        digits = max(0, 2 - int(np.floor(np.log10(step)))) if step > 0 else 0
    except Exception:
        digits = 0
    return np.round(ticks, digits)


def draw_vector_plot(u, v, lon, lat, opts, state, quiver_max_n=10):
    """
    Draw vector field using matplotlib only (no Cartopy).
    Parameters
    ----------
    u, v : ndarray
        2D arrays (j, i) or 3D arrays (level, j, i) or 4D with leading singleton dims.
    lon, lat : 1D or 2D arrays defining coordinates for T-grid nodes.
    opts : dict
        options like 'vmin','vmax','cmap','cmap_min','cmap_max','dpi','scale','layer',
        'lon_min','lon_max','lat_min','lat_max'
    state : dict
        must contain 'mask_t' (2D) and optionally 'sin_t','cos_t' for rotation.
    quiver_max_n : int
        downsample quiver resolution
    """
    # parse options
    vmin = opts.get("vmin", None)
    vmax = opts.get("vmax", None)
    cmap_name = opts.get("cmap", "YlOrBr")
    cmap_min = opts.get("cmap_min", 0)
    cmap_max = opts.get("cmap_max", 0.6)
    dpi = opts.get("dpi", 100)
    scale = opts.get("scale", 400)

    need_rotate = bool(opts.get("need_rotate", False))
    layer_idx = int(opts.get("layer", 0)) if str(opts.get("layer", "0")).isdigit() else 0

    # helper: squeeze only leading singleton dims to allow (1, level, j, i) -> (level, j, i)
    def _squeeze_leading(arr):
        a = np.asarray(arr)
        while a.ndim > 2 and a.shape[0] == 1:
            a = a[0]
        return a

    u = _squeeze_leading(u)
    v = _squeeze_leading(v)

    # if 3D assume (level, j, i)
    if u.ndim == 3:
        u = u[layer_idx, :, :]
    if v.ndim == 3:
        v = v[layer_idx, :, :]

    # mask: fallback to all-True so code continues
    mask_t = state.get("mask_t")
    if mask_t is None:
        print ('Cannot find mask_t')


    # interpolate staggered fields to T-grid if shapes don't match
    try:
        if u.shape != mask_t.shape:
            u = interpolate_to_t(u, stagger="u", mask_t=mask_t)
        if v.shape != mask_t.shape:
            v = interpolate_to_t(v, stagger="v", mask_t=mask_t)
    except Exception as e:
        print("Interpolation error:", e)
        return

    # ensure lon/lat are 2D arrays matching mask shape
    if lon is None or lat is None:
        print("Warning: lon/lat are None; aborting draw")
        return

    if getattr(lon, "ndim", 0) == 1 and getattr(lat, "ndim", 0) == 1:
        lon2d, lat2d = np.meshgrid(lon, lat)
    else:
        lon2d, lat2d = lon, lat

    # check shapes
    if lon2d.shape != mask_t.shape or lat2d.shape != mask_t.shape:
        print("Warning: lon/lat shape does not match mask/speed shape:",
            lon2d.shape, lat2d.shape, mask_t.shape)
        return

    # rotation if needed
    if need_rotate:
        sin_t = state.get("sin_t")
        cos_t = state.get("cos_t")
        U1 = u * cos_t + v * sin_t
        V1 = -u * sin_t + v * cos_t

    else:
        U1 = np.copy(u)
        V1 = np.copy(v)

    # apply mask: mask_t True = valid; False = land -> set nan
    U1 = np.where(mask_t, U1, np.nan)
    V1 = np.where(mask_t, V1, np.nan)

    speed = np.hypot(U1, V1)

    # prepare figure
    plt.close("all")
    fig, ax = plt.subplots(figsize=(7, 6), dpi=dpi)

    # --- Thiết lập Basemap theo lon/lat ---
    # (có thể auto-range nếu muốn)
    lon_min_user = (opts.get("lon_min"))
    lon_max_user = (opts.get("lon_max"))
    lat_min_user = (opts.get("lat_min"))
    lat_max_user = (opts.get("lat_max"))

    # lấy giá trị tự nhiên từ dữ liệu
    lon_min_data = float(np.nanmin(lon))
    lon_max_data = float(np.nanmax(lon))
    lat_min_data = float(np.nanmin(lat))
    lat_max_data = float(np.nanmax(lat))

    # nếu user không define → dùng data range
    lon_min = lon_min_user if lon_min_user is not None else lon_min_data
    lon_max = lon_max_user if lon_max_user is not None else lon_max_data
    lat_min = lat_min_user if lat_min_user is not None else lat_min_data
    lat_max = lat_max_user if lat_max_user is not None else lat_max_data

    # ---- chỉ padding nếu BOTH min & max của người dùng đều là None ----
    if lon_min_user is None and lon_max_user is None:
        lon_range = lon_max - lon_min
        pad = lon_range * 0.01
        lon_min -= pad
        lon_max += pad

    if lat_min_user is None and lat_max_user is None:
        lat_range = lat_max - lat_min
        pad = lat_range * 0.01
        lat_min -= pad
        lat_max += pad


    m = Basemap(
        projection="merc",
        llcrnrlon=lon_min, urcrnrlon=lon_max,
        llcrnrlat=lat_min, urcrnrlat=lat_max,
        resolution=opts.get("resolution", "i"), ax=ax
    )

    # vẽ bờ biển + lưới toạ độ
    m.drawcoastlines()
    parallels = _nice_ticks(lat_min, lat_max, n=4)
    meridians = _nice_ticks(lon_min, lon_max, n=4)
    m.drawparallels(parallels, labels=[1, 0, 0, 0], fontsize=8,
                    linewidth=0.5, dashes=[2, 4])
    m.drawmeridians(meridians, labels=[0, 0, 0, 1], fontsize=8,
                    linewidth=0.5, dashes=[2, 4])

    # --- Colormap ---
    cmap = _truncate_colormap(cmap_name, cmap_min, cmap_max)
    cmap.set_bad(color="white")

    # --- pcolormesh trên Basemap ---
    cs = m.pcolormesh(
        lon2d, lat2d, speed,
        latlon=True, cmap=cmap, shading="auto",
        vmin=vmin, vmax=vmax
    )

    # --- Quiver arrows for direction ---

    lon_small_1d = np.linspace(np.nanmin(lon2d), np.nanmax(lon2d), quiver_max_n)
    lat_small_1d = np.linspace(np.nanmin(lat2d), np.nanmax(lat2d), quiver_max_n)
    lon_small, lat_small = np.meshgrid(lon_small_1d, lat_small_1d)

    # --- Obtain nearest value from data_u, data_v ---

    dlon = np.nanmax(np.abs(np.diff(lon2d, axis=1)))
    dlat = np.nanmax(np.abs(np.diff(lat2d, axis=0)))
    max_dist = (max(dlon, dlat)) **2


    u_q = np.full_like(lon_small, np.nan, dtype=float)
    v_q = np.full_like(lon_small, np.nan, dtype=float)

    for j in range(lat_small.shape[0]):
        for i in range(lon_small.shape[1]):
            # tính khoảng cách (theo độ) tới toàn bộ grid gốc
            dist2 = (lon2d - lon_small[j, i])**2 + (lat2d - lat_small[j, i])**2
            idx = np.unravel_index(np.nanargmin(dist2), dist2.shape)
            if ((mask_t[idx] ==1) and (dist2[idx] < max_dist)):
                u_q[j, i] = U1[idx]
                v_q[j, i] = V1[idx]
                lon_small[j,i] = lon2d[idx]
                lat_small[j,i] = lat2d[idx]


    # --- Quiver trên Basemap ---
    m.quiver(
        lon_small, lat_small, u_q, v_q,
        latlon=True, zorder=11, scale=scale,
        width=0.004, headwidth=3, headlength=4,
        headaxislength=3.5, color="black"
    )

    # --- Colorbar & title ---
    cbar = fig.colorbar(cs, ax=ax, orientation="vertical")
    cbar.set_label("Speed")

    ax.set_title("Vector field")
    fig.tight_layout()
    plt.show(block=False)
