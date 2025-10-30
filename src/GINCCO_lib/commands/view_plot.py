import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from tkinter import messagebox
from GINCCO_lib.commands.interpolate_to_t import interpolate_to_t

def draw_plot(varname, var, lon, lat, options, log_box, state=None, is_redraw=False):
    """
    Draw map or line depending on variable dimension and user options.
    options: dict with keys ('vmin', 'vmax', 'cmap', 'lon_min', 'lon_max', 'lat_min', 'lat_max', 'layer')
    """

    #  Chỉ đóng figure cũ nếu là redraw
    if is_redraw and state and state.get("fig") is not None:
        plt.close(state["fig"])
        state["fig"] = None

    #  Ghi log "đang vẽ"
    log_box.insert("end", f"Drawing {varname}... please wait\n")
    log_box.see("end")
    log_box.update_idletasks()  #  cập nhật GUI ngay lập tức

    try:
        data = np.squeeze(var[:])
        nd = data.ndim

        # If 3D → pick selected layer
        if nd == 3:
            layer = options.get("layer", 0)
            data = data[layer, :, :]

        cmap = options.get("cmap", "jet")
        vmin = options.get("vmin", None)
        vmax = options.get("vmax", None)
        lon_min = options.get("lon_min", None)
        lon_max = options.get("lon_max", None)
        lat_min = options.get("lat_min", None)
        lat_max = options.get("lat_max", None)
        dpi=options.get("dpi", 150)

        if nd == 1:
            plt.figure()
            plt.plot(data)
            plt.title(varname)
            log_box.insert("end", f"Done drawing {varname} \n")
            log_box.see("end")
            log_box.update_idletasks()
            plt.show()

        elif nd >= 2:
            if lon is not None and lat is not None and lon.shape == data.shape:
                fig, ax = plt.subplots(figsize=(7, 6), dpi=dpi)
                state["fig"] = fig
                lon_min = lon_min or np.nanmin(lon)
                lon_max = lon_max or np.nanmax(lon)
                lat_min = lat_min or np.nanmin(lat)
                lat_max = lat_max or np.nanmax(lat)

                m = Basemap(
                    projection="cyl",
                    llcrnrlon=lon_min,
                    urcrnrlon=lon_max,
                    llcrnrlat=lat_min,
                    urcrnrlat=lat_max,
                    resolution=options.get("resolution", "i"),
                    ax=ax
                )

                cs = m.pcolormesh(
                    lon, lat, data,
                    latlon=True, shading="auto",
                    cmap=cmap, vmin=vmin, vmax=vmax
                )
                m.drawcoastlines()
                m.drawparallels(np.arange(-90, 91, 1), labels=[1, 0, 0, 0], fontsize=8)
                m.drawmeridians(np.arange(0, 361, 1), labels=[0, 0, 0, 1], fontsize=8)
                plt.colorbar(cs, label=getattr(var, "units", ""))
                plt.title(varname)
                plt.tight_layout()
                log_box.insert("end", f"Done drawing {varname} \n")
                log_box.see("end")
                log_box.update_idletasks()
                plt.show()
            else:
                plt.figure()
                plt.pcolormesh(data, cmap=cmap, vmin=vmin, vmax=vmax)
                plt.colorbar(label=getattr(var, "units", ""))
                plt.title(varname)
                log_box.insert("end", f"Done drawing {varname} \n")
                log_box.see("end")
                log_box.update_idletasks()
                plt.show()

        log_box.insert("end", f"Plot complete: {varname}\n")
        log_box.see("end")

    except Exception as e:
        log_box.insert("end", f"Error plotting variable {varname}: {e}\n")
        log_box.see("end")
        messagebox.showerror("Plot Error", str(e))


def draw_vector_plot(u, v, lon, lat, opts, log_box, state, quiver_max_n=10):
    import numpy as np
    import matplotlib.pyplot as plt
    from mpl_toolkits.basemap import Basemap
    from GINCCO_lib.commands.interpolate_to_t import interpolate_to_t

    log_box.insert("end", "Preparing vector field...\n")
    log_box.see("end")

    # --- Convert to 2D if 3D (choose layer)
    if u.ndim == 3:
        layer = int(opts.get("layer", 0))
        u = u[layer, :, :]
    if v.ndim == 3:
        layer = int(opts.get("layer", 0))
        v = v[layer, :, :]

    # --- Get mask_t if available
    mask_t = state.get("mask_t")
    if mask_t is None:
        mask_t = np.ones_like(u)

    # --- Interpolate staggered U/V to T grid if needed
    try:
        if u.shape != mask_t.shape:
            log_box.insert("end", f"Interpolating U ({u.shape}) to T grid {mask_t.shape}\n")
            u = interpolate_to_t(u, stagger="u", mask_t=mask_t)
        if v.shape != mask_t.shape:
            log_box.insert("end", f"Interpolating V ({v.shape}) to T grid {mask_t.shape}\n")
            v = interpolate_to_t(v, stagger="v", mask_t=mask_t)
    except Exception as e:
        log_box.insert("end", f"Interpolation error: {e}\n")
        log_box.see("end")
        return

    # --- Ensure lon/lat are 2D
    if lon.ndim == 1 and lat.ndim == 1:
        lon, lat = np.meshgrid(lon, lat)

    # --- Apply mask (optional)
    u = np.where(mask_t == 0, np.nan, u)
    v = np.where(mask_t == 0, np.nan, v)

    # --- Compute speed for background color
    speed = np.hypot(u, v)
    cmap = opts.get("cmap", "jet")

    log_box.insert("end", "Drawing vector map...\n")
    log_box.see("end")

    plt.close('all')
    fig, ax = plt.subplots(figsize=(7, 6), dpi=opts.get("dpi", 150))

    lon_min, lon_max = np.nanmin(lon), np.nanmax(lon)
    lat_min, lat_max = np.nanmin(lat), np.nanmax(lat)

    m = Basemap(
        projection="cyl",
        llcrnrlon=lon_min, urcrnrlon=lon_max,
        llcrnrlat=lat_min, urcrnrlat=lat_max,
        resolution=opts.get("resolution", "i"),
        ax=ax
    )

    # --- Background color mesh
    cs = m.pcolormesh(lon, lat, speed, latlon=True, cmap=cmap, shading="auto")

    # --- Quiver arrows (fixed max N)
    lon_small_1d = np.linspace(np.nanmin(lon), np.nanmax(lon), quiver_max_n)
    lat_small_1d = np.linspace(np.nanmin(lat), np.nanmax(lat), quiver_max_n)
    lon_small, lat_small = np.meshgrid(lon_small_1d, lat_small_1d)

    u_q = np.full_like(lon_small, np.nan, dtype=float)
    v_q = np.full_like(lon_small, np.nan, dtype=float)

    for j in range(lat_small.shape[0]):
        for i in range(lon_small.shape[1]):
            # khoảng cách đến grid gốc
            dist2 = (lon - lon_small[j, i])**2 + (lat - lat_small[j, i])**2
            idx = np.unravel_index(np.nanargmin(dist2), dist2.shape)
            if mask_t[idx] == 1:
                u_q[j, i] = u[idx]
                v_q[j, i] = v[idx]
                lon_small[j, i] = lon[idx]
                lat_small[j, i] = lat[idx]

    m.quiver(
        lon_small, lat_small, u_q, v_q,
        latlon=True, zorder=11,
        scale=opts.get("scale", 400),
        width=0.004,
        headwidth=3, headlength=4, headaxislength=3.5,
        color="black"
    )

    m.drawcoastlines()
    plt.colorbar(cs, ax=ax, label="Speed")
    plt.title("Vector field")
    plt.tight_layout()
    plt.show()

    log_box.insert("end", "Done.\n")
    log_box.see("end")
