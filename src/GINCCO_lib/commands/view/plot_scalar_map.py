import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from mpl_toolkits.basemap import Basemap
from GINCCO_lib.modules.vertical_interpolation import interpolate_depth



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
    fig_width = safe_float(options.get("fig_width")) or 7.0
    fig_height = safe_float(options.get("fig_height")) or 6.0
    show_coastline = bool(options.get("show_coastline", True))
    fill_continents = bool(options.get("fill_continents", False))
    continent_color = options.get("continent_color") or "0.8"
    lake_color = options.get("lake_color") or "white"
    show_gridlines = bool(options.get("show_gridlines", True))
    n_ticks = int(options.get("n_ticks", 4)) if str(options.get("n_ticks", "4")).isdigit() else 4
    title = options.get("title") or varname
    colorbar_label = options.get("colorbar_label")
    if colorbar_label is None:
        colorbar_label = getattr(var, "units", "")
    bad_color = options.get("bad_color") or "white"

    cmap_min = safe_float(options.get("cmap_min"))
    cmap_min = cmap_min if cmap_min is not None else 0.0

    cmap_max = safe_float(options.get("cmap_max"))
    cmap_max = cmap_max if cmap_max is not None else 1.0

    # --- colormap truncation ---
    cmap = _truncate_colormap(cmap_name, cmap_min, cmap_max)
    try:
        cmap.set_bad(color=bad_color)
    except Exception:
        pass

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
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)

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

    if fill_continents:
        m.fillcontinents(color=continent_color, lake_color=lake_color, zorder=10)
    if show_coastline:
        m.drawcoastlines(zorder=11)

    if show_gridlines:
        parallels = _nice_ticks(lat_min, lat_max, n=n_ticks)
        meridians = _nice_ticks(lon_min, lon_max, n=n_ticks)

        m.drawparallels(parallels, labels=[1, 0, 0, 0],
                        fontsize=8, linewidth=0.5, dashes=[2, 4])
        m.drawmeridians(meridians, labels=[0, 0, 0, 1],
                        fontsize=8, linewidth=0.5, dashes=[2, 4])

    # Keep the map frame visible after filled continent polygons.
    try:
        m.drawmapboundary(linewidth=1.0, color="black", zorder=20)
    except TypeError:
        m.drawmapboundary(linewidth=1.0, color="black")
    for spine in ax.spines.values():
        spine.set_zorder(21)

    cbar = plt.colorbar(cs, ax=ax)
    cbar.set_label(colorbar_label)

    plt.title(title)
    plt.tight_layout()
    plt.show(block=False)


