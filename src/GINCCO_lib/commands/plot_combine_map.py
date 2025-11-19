# draw_combine.py
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from mpl_toolkits.basemap import Basemap
from GINCCO_lib.commands.interpolate_to_t import interpolate_to_t

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


def draw_map_combine(scalar_name, scalar_var, u, v, lon, lat, opts, state):
    """
    Vẽ bản đồ kết hợp:
      - Nền scalar bằng pcolormesh
      - Vector (u, v) bằng quiver

    Parameters
    ----------
    scalar_name : str
        Tên biến scalar (dùng cho title).
    scalar_var : netCDF4.Variable
        Biến scalar trong NetCDF (để đọc data & units).
    u, v : ndarray
        Trường vector (có thể 2D hoặc 3D, hoặc thêm chiều singleton bên ngoài).
    lon, lat : 1D hoặc 2D
        Toạ độ lưới T.
    opts : dict
        {
          "scalar": { ... scalar options ... },
          "vector": { ... vector options ... }
        }
    state : dict
        Có thể chứa 'mask_t', 'sin_t', 'cos_t'.
    """

    scalar_opts = opts.get("scalar", {}) or {}
    vector_opts = opts.get("vector", {}) or {}

    # ---------- Scalar data ----------
    data = np.squeeze(scalar_var[:])
    layer_s = int(scalar_opts.get("layer", 0)) if str(scalar_opts.get("layer", "0")).isdigit() else 0

    if data.ndim == 3:
        # dùng đúng layer do người dùng chọn
        if 0 <= layer_s < data.shape[0]:
            data = data[layer_s, :, :]
        else:
            data = data[0, :, :]


    # ---------- Lon/lat ----------
    if lon is None or lat is None:
        print("draw_map_combine: lon/lat are None, abort.")
        return

    if getattr(lon, "ndim", 0) == 1 and getattr(lat, "ndim", 0) == 1:
        lon2d, lat2d = np.meshgrid(lon, lat)
    else:
        lon2d, lat2d = lon, lat

    # ---------- Scalar options ----------
    def safe_float(x):
        try:
            return float(x)
        except Exception:
            return None

    vmin_s = safe_float(scalar_opts.get("vmin"))
    vmax_s = safe_float(scalar_opts.get("vmax"))
    cmap_name = scalar_opts.get("cmap", "jet")

    lon_min = safe_float(scalar_opts.get("lon_min"))
    lon_max = safe_float(scalar_opts.get("lon_max"))
    lat_min = safe_float(scalar_opts.get("lat_min"))
    lat_max = safe_float(scalar_opts.get("lat_max"))

    try:
        lon_min = lon_min if lon_min is not None else float(np.nanmin(lon2d))
        lon_max = lon_max if lon_max is not None else float(np.nanmax(lon2d))
        lat_min = lat_min if lat_min is not None else float(np.nanmin(lat2d))
        lat_max = lat_max if lat_max is not None else float(np.nanmax(lat2d))
    except Exception:
        lon_min, lon_max, lat_min, lat_max = 0, 1, 0, 1

    dpi = int(scalar_opts.get("dpi", 100))
    resolution = scalar_opts.get("resolution", "i")

    # Cho phép truncate colormap nếu muốn sau này
    cmap_min = 0.0
    cmap_max = 1.0
    cmap = _truncate_colormap(cmap_name, cmap_min, cmap_max)
    cmap.set_bad(color="white")

    # ---------- Mask ----------
    mask_t = state.get("mask_t")
    if mask_t is not None:
        mask_t = np.asarray(mask_t, dtype=bool)
        if mask_t.shape == data.shape:
            data = np.where(mask_t, data, np.nan)

    # ---------- Figure + Basemap ----------
    plt.close("all")
    fig, ax = plt.subplots(figsize=(7, 6), dpi=dpi)

    m = Basemap(
        projection="merc",
        llcrnrlon=lon_min,
        urcrnrlon=lon_max,
        llcrnrlat=lat_min,
        urcrnrlat=lat_max,
        resolution=resolution,
        ax=ax,
    )

    # Vẽ scalar background
    cs = m.pcolormesh(
        lon2d,
        lat2d,
        data,
        latlon=True,
        cmap=cmap,
        shading="auto",
        vmin=vmin_s,
        vmax=vmax_s,
    )

    m.drawcoastlines()
    parallels = _nice_ticks(lat_min, lat_max, n=4)
    meridians = _nice_ticks(lon_min, lon_max, n=4)
    m.drawparallels(
        parallels,
        labels=[1, 0, 0, 0],
        fontsize=8,
        linewidth=0.5,
        dashes=[2, 4],
    )
    m.drawmeridians(
        meridians,
        labels=[0, 0, 0, 1],
        fontsize=8,
        linewidth=0.5,
        dashes=[2, 4],
    )

    cbar = fig.colorbar(cs, ax=ax, orientation="vertical")
    cbar.set_label(getattr(scalar_var, "units", ""))

    # ---------- Vector field ----------
    def _squeeze_leading(arr):
        a = np.asarray(arr)
        while a.ndim > 2 and a.shape[0] == 1:
            a = a[0]
        return a

    u = _squeeze_leading(u)
    v = _squeeze_leading(v)

    layer_idx = int(vector_opts.get("layer", 0)) if str(vector_opts.get("layer", "0")).isdigit() else 0

    if u.ndim == 3:
        u = u[layer_idx, :, :]
    if v.ndim == 3:
        v = v[layer_idx, :, :]

    # mask fallback
    if mask_t is None:
        mask_t_use = np.ones_like(u, dtype=bool)
    else:
        mask_t_use = mask_t
        if mask_t_use.shape != u.shape:
            # cố gắng broadcast nếu không khớp
            try:
                mask_t_use = np.broadcast_to(mask_t_use, u.shape)
            except Exception:
                mask_t_use = np.ones_like(u, dtype=bool)

    # interpolate staggered -> T-grid nếu cần
    try:
        if u.shape != mask_t_use.shape:
            u = interpolate_to_t(u, stagger="u", mask_t=mask_t_use)
        if v.shape != mask_t_use.shape:
            v = interpolate_to_t(v, stagger="v", mask_t=mask_t_use)
    except Exception as e:
        print("Interpolation error in draw_map_combine:", e)
        # vẫn tiếp tục nhưng có thể không khớp
        pass

    # đảm bảo u/v cùng shape với mask_t_use
    if u.shape != mask_t_use.shape or v.shape != mask_t_use.shape:
        print("draw_map_combine: shape mismatch u/v vs mask:", u.shape, v.shape, mask_t_use.shape)
        # cố gắng dùng min shape
        ny = min(u.shape[0], v.shape[0], mask_t_use.shape[0])
        nx = min(u.shape[1], v.shape[1], mask_t_use.shape[1])
        u = u[:ny, :nx]
        v = v[:ny, :nx]
        mask_t_use = mask_t_use[:ny, :nx]
        lon2d = lon2d[:ny, :nx]
        lat2d = lat2d[:ny, :nx]

    need_rotate = bool(vector_opts.get("need_rotate", False))
    if need_rotate:
        sin_t = state.get("sin_t")
        cos_t = state.get("cos_t")
        if sin_t is not None and cos_t is not None:
            sin_t = np.asarray(sin_t)
            cos_t = np.asarray(cos_t)
            if sin_t.shape != u.shape:
                try:
                    sin_t = np.broadcast_to(sin_t, u.shape)
                    cos_t = np.broadcast_to(cos_t, u.shape)
                except Exception:
                    print("Could not broadcast sin_t/cos_t; skipping rotation.")
                    sin_t, cos_t = None, None
            if sin_t is not None and cos_t is not None:
                U1 = u * cos_t + v * sin_t
                V1 = -u * sin_t + v * cos_t
            else:
                U1, V1 = u.copy(), v.copy()
        else:
            U1, V1 = u.copy(), v.copy()
    else:
        U1, V1 = u.copy(), v.copy()

    U1 = np.where(mask_t_use, U1, np.nan)
    V1 = np.where(mask_t_use, V1, np.nan)

    speed = np.hypot(U1, V1)

    # ----------------- Quiver sampling -----------------
    quiver_max_n = int(vector_opts.get("quiver_max_n", 10))
    scale = vector_opts.get("scale", 400)

    valid = np.isfinite(lon2d) & np.isfinite(lat2d) & np.isfinite(U1) & mask_t_use
    if not np.any(valid):
        print("draw_map_combine: no valid vector points, only scalar is plotted.")
        ax.set_title(f"Scalar + Vector (no valid vectors) - {scalar_name}")
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

    m.quiver(
        lon_q,
        lat_q,
        u_q,
        v_q,
        latlon=True,
        zorder=11,
        scale=scale,
        width=0.004,
        headwidth=3,
        headlength=4,
        headaxislength=3.5,
        color="black",
    )

    ax.set_title(f"Scalar + Vector field - {scalar_name}")
    fig.tight_layout()
    plt.show(block=False)
