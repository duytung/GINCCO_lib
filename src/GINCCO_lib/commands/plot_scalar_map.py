import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from mpl_toolkits.basemap import Basemap



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





def interpolate_depth(data_3d, depth_3d, target_depth, mask_t=None):
    """
    Nội suy trường 3D 'data_3d' (nz, ny, nx) về một độ sâu cụ thể.

    Parameters
    ----------
    data_3d : np.ndarray
        Dữ liệu 3D (nz, ny, nx).
    depth_3d : np.ndarray
        Lưới độ sâu 3D (nz, ny, nx), giá trị âm (vd: -3, -10, ...).
    target_depth : float
        Độ sâu mong muốn (dương hoặc âm). Nếu dương sẽ tự đổi sang âm.
    mask_t : np.ndarray, optional
        Mask 2D (ny, nx), 1 = biển, 0 = đất. Nếu None thì không áp dụng.

    Returns
    -------
    data_2d : np.ndarray
        Trường 2D (ny, nx) đã nội suy tại target_depth, với NaN ở chỗ không nội suy được.
    """

    # Nếu target_depth > 0, chuyển sang âm cho cùng hệ với depth_3d
    depth = -abs(target_depth)

    nz, ny, nx = depth_3d.shape

    # tìm layer "dưới" và "trên" độ sâu cần nội suy
    # ví dụ depth = -5, depth_3d có -3 (trên), -10 (dưới)
    # max_array: chỉ số của lớp sâu hơn (giá trị nhỏ hơn, ví dụ -10)
    # min_array: chỉ số của lớp nông hơn (giá trị lớn hơn, ví dụ -3)

    # mask các lớp nông hơn depth (>-5) để tìm lớp sâu hơn gần nhất
    tmp = np.ma.masked_where(depth_3d > depth, depth_3d)
    max_array = np.argmax(tmp, axis=0)

    # mask các lớp sâu hơn depth (<-5) để tìm lớp nông hơn gần nhất
    tmp = np.ma.masked_where(depth_3d < depth, depth_3d)
    min_array = np.argmin(tmp, axis=0)

    # Mảng hệ số nhân cho từng lớp
    multiply_array = np.zeros_like(depth_3d, dtype="float64")

    # Mảng kiểm tra ô nào nội suy được
    check_depth_array = np.zeros((ny, nx), dtype="float64")

    for j in range(ny):
        for i in range(nx):
            kmin = min_array[j, i]
            kmax = max_array[j, i]
            if kmin != kmax:  # chỉ khi tìm được 2 lớp khác nhau
                zmax = depth_3d[kmax, j, i]
                zmin = depth_3d[kmin, j, i]
                dist = zmax - zmin   # nhớ là số âm, nhưng nhất quán với công thức gốc

                if dist == 0 or np.isnan(dist):
                    continue

                # hệ số đúng theo code gốc của Viet
                multiply_array[kmax, j, i] = 1 + (depth - zmax) / dist
                multiply_array[kmin, j, i] = 1 - (depth - zmin) / dist
                check_depth_array[j, i] = 1

    # nội suy: tổng (data * hệ số) theo chiều z
    data_interp = np.nansum(data_3d * multiply_array, axis=0)

    # nếu toàn NaN theo cột z, nansum trả 0 → sửa lại về NaN
    all_nan = np.all(np.isnan(data_3d), axis=0)
    data_interp[all_nan] = np.nan

    # chỗ không có cặp lớp trên/dưới hợp lệ → NaN
    data_interp[check_depth_array == 0] = np.nan

    # Áp dụng mask biển/đất nếu có
    if mask_t is not None:
        data_interp[mask_t == 0] = np.nan

    return data_interp









def draw_map_plot(varname, var, lon, lat, options, state=None):


    def safe_float(x):
        try:
            return float(x)
        except Exception:
            return None

    # --- dữ liệu ---
    data = np.squeeze(var[:])
    nd = data.ndim

    # --- Xử lý 3D: layer vs depth ---

    if nd == 3:
        depth_value = options.get("depth", None)
        layer_value = options.get("layer", None)

        if depth_value is not None:
            # dùng depth interpolation
            if state is None or "depth_levels" not in state:
                print("Warning: depth option set but no depth_levels in state. Fallback to layer 0.")
                data = data[0, :, :]
            else:
                depth_3d = state["depth_levels"]
                mask_t = state.get("mask_t", None)
                target_depth = float(depth_value)

                data = interpolate_depth(
                    data_3d=data,
                    depth_3d=depth_3d,
                    target_depth=target_depth,
                    mask_t=mask_t,
                )
        else:
            # không chọn depth -> dùng layer
            if layer_value is not None:
                layer = int(layer_value)
            else:
                layer = 0
            data = data[layer, :, :]

        # update nd
        nd =2



    # --- options ---
    cmap_name = options.get("cmap", "jet")
    vmin = safe_float(options.get("vmin"))
    vmax = safe_float(options.get("vmax"))

    lon_min_user = safe_float(options.get("lon_min"))
    lon_max_user = safe_float(options.get("lon_max"))
    lat_min_user = safe_float(options.get("lat_min"))
    lat_max_user = safe_float(options.get("lat_max"))

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



    dpi = int(options.get("dpi", 100))
    resolution = options.get("resolution", "i")

    cmap_min = safe_float(options.get("cmap_min"))
    cmap_min = cmap_min if cmap_min is not None else 0.0

    cmap_max = safe_float(options.get("cmap_max"))
    cmap_max = cmap_max if cmap_max is not None else 1.0

    # --- colormap truncation ---
    cmap = _truncate_colormap(cmap_name, cmap_min, cmap_max)

    print("Chosen options:", options)

    # --- 1D ---
    if nd == 1:
        plt.figure(dpi=dpi)
        plt.plot(data)
        plt.title(varname)
        plt.tight_layout()
        plt.show()
        return

    # --- 2D+ map ---
    fig, ax = plt.subplots(figsize=(7, 6), dpi=dpi)

    m = Basemap(
        projection="merc",
        llcrnrlon=lon_min, urcrnrlon=lon_max,
        llcrnrlat=lat_min, urcrnrlat=lat_max,
        resolution=resolution,
        ax=ax,
    )

    cs = m.pcolormesh(
        lon, lat, data,
        latlon=True,
        cmap=cmap,
        shading="auto",
        vmin=vmin,
        vmax=vmax,
    )

    m.drawcoastlines()

    # dùng _nice_ticks cho parallels / meridians
    parallels = _nice_ticks(lat_min, lat_max, n=4)
    meridians = _nice_ticks(lon_min, lon_max, n=4)

    m.drawparallels(parallels, labels=[1, 0, 0, 0],
                    fontsize=8, linewidth=0.5, dashes=[2, 4])
    m.drawmeridians(meridians, labels=[0, 0, 0, 1],
                    fontsize=8, linewidth=0.5, dashes=[2, 4])

    cbar = plt.colorbar(cs, ax=ax)
    cbar.set_label(getattr(var, "units", ""))

    plt.title(varname)
    plt.tight_layout()
    plt.show(block=False)


