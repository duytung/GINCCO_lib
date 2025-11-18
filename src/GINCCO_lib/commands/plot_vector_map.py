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
    lon_min = opts.get("lon_min", None)
    lon_max = opts.get("lon_max", None)
    lat_min = opts.get("lat_min", None)
    lat_max = opts.get("lat_max", None)
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
        mask_t = np.ones_like(u, dtype=bool)
    else:
        mask_t = np.asarray(mask_t, dtype=bool)

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
        # try transpose suspects: sometimes lon/lat swapped axes
        if lon2d.T.shape == mask_t.shape and lat2d.T.shape == mask_t.shape:
            lon2d = lon2d.T
            lat2d = lat2d.T
        else:
            print("Warning: lon/lat shape does not match mask/speed shape:",
                  lon2d.shape, lat2d.shape, mask_t.shape)
            # continue but pcolormesh will likely fail; we bail gracefully
            return

    # rotation if needed
    if need_rotate:
        sin_t = state.get("sin_t")
        cos_t = state.get("cos_t")
        if sin_t is None or cos_t is None:
            U1 = np.copy(u)
            V1 = np.copy(v)
        else:
            U1 = u * cos_t + v * sin_t
            V1 = -u * sin_t + v * cos_t
    else:
        U1 = np.copy(u)
        V1 = np.copy(v)

    # apply mask: mask_t True = valid; False = land -> set nan
    U1 = np.where(mask_t, U1, np.nan)
    V1 = np.where(mask_t, V1, np.nan)

    speed = np.hypot(U1, V1)

    # compute bounds if not provided
    try:
        lon_min = lon_min if lon_min is not None else np.nanmin(lon2d)
        lon_max = lon_max if lon_max is not None else np.nanmax(lon2d)
        lat_min = lat_min if lat_min is not None else np.nanmin(lat2d)
        lat_max = lat_max if lat_max is not None else np.nanmax(lat2d)
    except Exception:
        lon_min, lon_max, lat_min, lat_max = 0, 1, 0, 1

    # prepare figure
    plt.close("all")
    fig, ax = plt.subplots(figsize=(7, 6), dpi=dpi)

    # --- Thiết lập Basemap theo lon/lat ---
    # (có thể auto-range nếu muốn)
    lon_min = lon_min if lon_min is not None else float(np.nanmin(lon2d))
    lon_max = lon_max if lon_max is not None else float(np.nanmax(lon2d))
    lat_min = lat_min if lat_min is not None else float(np.nanmin(lat2d))
    lat_max = lat_max if lat_max is not None else float(np.nanmax(lat2d))

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

    # --- Prepare quiver sampling (giữ nguyên cấu trúc) ---
    valid = np.isfinite(lon2d) & np.isfinite(lat2d) & np.isfinite(U1) & mask_t
    if not np.any(valid):
        print("No valid points to plot quiver")
        cbar = fig.colorbar(cs, ax=ax, orientation="vertical")
        cbar.set_label("Speed")
        ax.set_title("Vector field")
        fig.tight_layout()
        plt.show()
        return

    pts_lon = lon2d[valid].ravel()
    pts_lat = lat2d[valid].ravel()
    pts_uv = np.column_stack((U1[valid].ravel(), V1[valid].ravel()))
    pts_xy = np.column_stack((pts_lon, pts_lat))

    lon_small_1d = np.linspace(np.nanmin(lon2d), np.nanmax(lon2d), quiver_max_n)
    lat_small_1d = np.linspace(np.nanmin(lat2d), np.nanmax(lat2d), quiver_max_n)
    grid_x, grid_y = np.meshgrid(lon_small_1d, lat_small_1d)
    grid_pts = np.column_stack((grid_x.ravel(), grid_y.ravel()))

    # --- KDTree nearest neighbor nếu có ---
    if KDTree is not None and pts_xy.size > 0:
        tree = KDTree(pts_xy)
        dists, idxs = tree.query(grid_pts, k=1)
        idxs = idxs.reshape(grid_x.shape)

        u_q = np.full(grid_x.shape, np.nan)
        v_q = np.full(grid_x.shape, np.nan)
        lon_q = np.full(grid_x.shape, np.nan)
        lat_q = np.full(grid_x.shape, np.nan)

        for j in range(grid_x.shape[0]):
            for i in range(grid_x.shape[1]):
                idx = idxs[j, i]
                u_q[j, i], v_q[j, i] = pts_uv[idx]
                lon_q[j, i], lat_q[j, i] = pts_xy[idx]
    else:
        # --- Brute force fallback ---
        u_q = np.full(grid_x.shape, np.nan)
        v_q = np.full(grid_x.shape, np.nan)
        lon_q = np.copy(grid_x)
        lat_q = np.copy(grid_y)

        if pts_xy.size > 0:
            for j in range(grid_x.shape[0]):
                for i in range(grid_x.shape[1]):
                    gx, gy = grid_x[j, i], grid_y[j, i]
                    dist2 = (pts_lon - gx) ** 2 + (pts_lat - gy) ** 2
                    idx = np.argmin(dist2)
                    u_q[j, i], v_q[j, i] = pts_uv[idx]
                    lon_q[j, i], lat_q[j, i] = pts_xy[idx]

    # --- Quiver trên Basemap ---
    m.quiver(
        lon_q, lat_q, u_q, v_q,
        latlon=True, zorder=11, scale=scale,
        width=0.004, headwidth=3, headlength=4,
        headaxislength=3.5, color="black"
    )

    # --- Colorbar & title ---
    cbar = fig.colorbar(cs, ax=ax, orientation="vertical")
    cbar.set_label("Speed")

    ax.set_title("Vector field")
    fig.tight_layout()
    plt.show()
