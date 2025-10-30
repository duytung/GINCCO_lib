import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from tkinter import messagebox
from GINCCO_lib.commands.interpolate_to_t import interpolate_to_t
import matplotlib.colors as mcolors


def _truncate_colormap(cmap, minval=0.0, maxval=1.0, n=256):
    if isinstance(cmap, str):
        cmap = plt.get_cmap(cmap)
    new_cmap = mcolors.LinearSegmentedColormap.from_list(
        f"trunc({cmap.name},{minval:.2f},{maxval:.2f})",
        cmap(np.linspace(minval, maxval, n))
    )
    return new_cmap


def _nice_ticks(lon_min, lon_max, n=4):
    """Generate exactly n 'nice' tick values between lon_min and lon_max."""
    ticks = np.linspace(lon_min, lon_max, n)
    # Làm tròn tick cho đẹp
    step = (lon_max - lon_min) / (n - 1)
    digits = max(0, 2 - int(np.log10(step)))  # làm tròn hợp lý
    return np.round(ticks, digits)



def draw_plot(varname, var, lon, lat, options, log_box, state=None, is_redraw=False):
    import matplotlib.pyplot as plt
    from mpl_toolkits.basemap import Basemap
    import numpy as np

    def safe_float(x):
        try:
            return float(x)
        except Exception:
            return None

    if is_redraw and state and state.get("fig") is not None:
        plt.close(state["fig"])
        state["fig"] = None

    log_box.insert("end", f"Drawing {varname}... please wait\n")
    log_box.see("end")
    log_box.update_idletasks()

    try:
        data = np.squeeze(var[:])
        nd = data.ndim

        if nd == 3:
            layer = int(options.get("layer", 0))
            data = data[layer, :, :]

        cmap = options.get("cmap", "jet")
        vmin = safe_float(options.get("vmin"))
        vmax = safe_float(options.get("vmax"))
        lon_min = safe_float(options.get("lon_min")) or np.nanmin(lon)
        lon_max = safe_float(options.get("lon_max")) or np.nanmax(lon)
        lat_min = safe_float(options.get("lat_min")) or np.nanmin(lat)
        lat_max = safe_float(options.get("lat_max")) or np.nanmax(lat)
        dpi = int(options.get("dpi", 100))


        print (options)



        if nd == 1:
            plt.figure()
            plt.plot(data)
            plt.title(varname)
            plt.show()
            log_box.insert("end", f"Done drawing {varname}\n")

        elif nd >= 2:
            fig, ax = plt.subplots(figsize=(7, 6), dpi=dpi)
            state["fig"] = fig

            m = Basemap(
                projection="cyl",
                llcrnrlon=lon_min, urcrnrlon=lon_max,
                llcrnrlat=lat_min, urcrnrlat=lat_max,
                resolution=options.get("resolution", "i"), ax=ax
            )

            cs = m.pcolormesh(lon, lat, data, latlon=True, cmap=cmap, shading="auto", vmin=vmin, vmax=vmax)
            m.drawcoastlines()

            parallels = np.linspace(lat_min, lat_max, 4)
            meridians = np.linspace(lon_min, lon_max, 4)
            m.drawparallels(parallels, labels=[1,0,0,0], fontsize=8, linewidth=0.5, dashes=[2,4], ax=ax)
            m.drawmeridians(meridians, labels=[0,0,0,1], fontsize=8, linewidth=0.5, dashes=[2,4], ax=ax)

            plt.colorbar(cs, label=getattr(var, "units", ""))
            plt.title(varname)
            plt.tight_layout()
            plt.show()
            state["fig"] = fig

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

    # --- Extract options from opts ---
    vmin = opts.get("vmin", None)
    vmax = opts.get("vmax", None)

    cmap = opts.get("cmap", "YlOrBr")
    cmap_min = opts.get("cmap_min", 0)
    cmap_max = opts.get("cmap_max", 0.6)

    dpi = opts.get("dpi", 100)
    resolution = opts.get("resolution", "i")
    scale = opts.get("scale", 400)
    lon_min = opts.get("lon_min")
    lon_max = opts.get("lon_max")
    lat_min = opts.get("lat_min")
    lat_max = opts.get("lat_max")
    need_rotate = opts.get("need_rotate")

    print (opts)
    
    # --- Convert to 2D if 3D ---
    if u.ndim == 3:
        layer = int(opts.get("layer", 0))
        u = u[layer, :, :]
    if v.ndim == 3:
        layer = int(opts.get("layer", 0))
        v = v[layer, :, :]

    # --- Mask
    mask_t = state.get("mask_t")
    if mask_t is None:
        mask_t = np.ones_like(u)

    # --- Interpolate staggered fields if needed ---
    try:
        if u.shape != mask_t.shape:
            log_box.insert("end", f"Interpolating U ({u.shape}) → T grid {mask_t.shape}\n")
            u = interpolate_to_t(u, stagger="u", mask_t=mask_t)
        if v.shape != mask_t.shape:
            log_box.insert("end", f"Interpolating V ({v.shape}) → T grid {mask_t.shape}\n")
            v = interpolate_to_t(v, stagger="v", mask_t=mask_t)
    except Exception as e:
        log_box.insert("end", f"Interpolation error: {e}\n")
        log_box.see("end")
        return

    # --- Ensure lon/lat 2D
    if lon.ndim == 1 and lat.ndim == 1:
        lon, lat = np.meshgrid(lon, lat)

 
    if need_rotate:
        print ('Rotating...')
        sin_t = opts.get("sint_t")
        cos_t = opts.get("cos_t")
        
        U1 =  u * cos_t + v * sin_t
        V1 = -u * sin_t + v * cos_t
    else: 
        U1 = np.copy(u)
        V1 = np.copy(v)

    U1 = np.where(mask_t == 0, np.nan, U1)
    V1 = np.where(mask_t == 0, np.nan, V1)


    speed = np.hypot(U1, V1)

    log_box.insert("end", f"Drawing, please wait...\n")
    log_box.see("end")

    plt.close('all')
    fig, ax = plt.subplots(figsize=(7, 6), dpi=dpi)

    # Auto range if not provided
    lon_min = lon_min or np.nanmin(lon)
    lon_max = lon_max or np.nanmax(lon)
    lat_min = lat_min or np.nanmin(lat)
    lat_max = lat_max or np.nanmax(lat)

    m = Basemap(
        projection="cyl",
        llcrnrlon=lon_min, urcrnrlon=lon_max,
        llcrnrlat=lat_min, urcrnrlat=lat_max,
        resolution=resolution, ax=ax
    )
    m.drawcoastlines()
    parallels = _nice_ticks(lat_min, lat_max, n=4)
    meridians = _nice_ticks(lon_min, lon_max, n=4)

    m.drawparallels(parallels, labels=[1, 0, 0, 0], fontsize=8, linewidth=0.5, dashes=[2, 4])
    m.drawmeridians(meridians, labels=[0, 0, 0, 1], fontsize=8, linewidth=0.5, dashes=[2, 4])


    # Colormap
    cmap = _truncate_colormap(cmap, cmap_min, cmap_max)
    cmap.set_bad(color='white')
    #norm = colors.Normalize(vmin=ticks[0], vmax=ticks[-1])

    cs = m.pcolormesh(lon, lat, speed, latlon=True, cmap=cmap, shading="auto", vmin=vmin, vmax=vmax)

    # --- Downsample quiver grid ---
    lon_small_1d = np.linspace(np.nanmin(lon), np.nanmax(lon), quiver_max_n)
    lat_small_1d = np.linspace(np.nanmin(lat), np.nanmax(lat), quiver_max_n)
    lon_small, lat_small = np.meshgrid(lon_small_1d, lat_small_1d)

    u_q = np.full_like(lon_small, np.nan, dtype=float)
    v_q = np.full_like(lon_small, np.nan, dtype=float)

    for j in range(lat_small.shape[0]):
        for i in range(lat_small.shape[1]):
            dist2 = (lon - lon_small[j, i])**2 + (lat - lat_small[j, i])**2
            idx = np.unravel_index(np.nanargmin(dist2), dist2.shape)
            if mask_t[idx] == 1:
                u_q[j, i], v_q[j, i] = U1[idx], V1[idx]
                lon_small[j, i], lat_small[j, i] = lon[idx], lat[idx]

    m.quiver(
        lon_small, lat_small, u_q, v_q,
        latlon=True, zorder=11, scale=scale,
        width=0.004, headwidth=3, headlength=4, headaxislength=3.5, color="black"
    )

    m.drawcoastlines()
    plt.colorbar(cs, ax=ax, label="Speed")
    plt.title("Vector field")
    plt.tight_layout()
    plt.show()

    log_box.insert("end", "Done.\n")
    log_box.see("end")

