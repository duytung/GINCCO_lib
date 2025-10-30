import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from tkinter import messagebox


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
                fig, ax = plt.subplots(figsize=(7, 6))
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




def draw_vector_plot(u, v, lon, lat, options, log_box, state=None, step=5):
    plt.close('all')
    log_box.insert("end", "Drawing vector field...\n")
    log_box.see("end")
    log_box.update_idletasks()

    lon_min = options.get("lon_min", np.nanmin(lon))
    lon_max = options.get("lon_max", np.nanmax(lon))
    lat_min = options.get("lat_min", np.nanmin(lat))
    lat_max = options.get("lat_max", np.nanmax(lat))
    res = options.get("resolution", "c")

    fig, ax = plt.subplots(figsize=(7, 6))
    state["fig"] = fig
    m = Basemap(projection="cyl", llcrnrlon=lon_min, urcrnrlon=lon_max,
                llcrnrlat=lat_min, urcrnrlat=lat_max, resolution=res, ax=ax)

    m.drawcoastlines()
    cs = m.quiver(lon[::step, ::step], lat[::step, ::step],
                  u[::step, ::step], v[::step, ::step],
                  latlon=True, scale=400, color="blue")
    plt.title("Vector field")
    plt.tight_layout()
    plt.show()

    log_box.insert("end", "Done drawing vector field ✓\n")
    log_box.see("end")


