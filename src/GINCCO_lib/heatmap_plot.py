import os
import random
from datetime import timedelta
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import MaxNLocator
from dateutil.relativedelta import relativedelta

def _nice_interval(n_items, target_min=4, target_max=7):
    if n_items <= target_max:
        return 1
    return max(1, int(np.ceil(n_items / target_max)))

def _month_diff(t0, t1):
    return (t1.year - t0.year) * 12 + (t1.month - t0.month) + (1 if t1.day >= t0.day else 0)

def _nice_ticks(vmin, vmax):
    for nb in (6, 5, 7, 4):
        locator = MaxNLocator(nbins=nb, steps=[1, 2, 2.5, 5, 10], min_n_ticks=4)
        ticks = locator.tick_values(vmin, vmax)
        ticks = ticks[(ticks >= vmin) & (ticks <= vmax)]
        ticks = np.unique(np.round(ticks, 12))
        if 4 <= len(ticks) <= 7:
            return ticks
    return np.linspace(vmin, vmax, 5)

def plot_heatmap(
    title,
    tstart,            # datetime.datetime
    tend,              # datetime.datetime
    data_draw,         # np.ndarray, shape (n_time, depth)
    depth,             # np.ndarray, shape (depth,)
    path_save=".",
    name_save="figure",
    n_colors=100       # number of discrete color bins
):
    """
    Time–depth heatmap with pcolormesh.
    - Colormap: jet, BoundaryNorm with n_colors bins.
    - Color range: 5th to 95th percentile.
    - Colorbar: horizontal with 4–7 nice ticks.
    - X ticks: daily / monthly / yearly depending on span.
    - Output filename: name_save + "_" + random number + ".png"
    """
    if data_draw.ndim != 2:
        raise ValueError("data_draw must be 2D (n_time, depth).")
    n_time, n_depth = data_draw.shape
    if depth.ndim != 1 or depth.shape[0] != n_depth:
        raise ValueError("depth must be 1D with length equal to data_draw.shape[1].")
    if tend <= tstart:
        raise ValueError("tend must be after tstart.")
    if n_colors < 2:
        raise ValueError("n_colors must be >= 2.")

    # Time axis
    total_seconds = (tend - tstart).total_seconds()
    if n_time == 1:
        times = np.array([tstart])
    else:
        dt = total_seconds / (n_time - 1)
        times = np.array([tstart + timedelta(seconds=i * dt) for i in range(n_time)])

    # Color limits
    vmin = np.nanpercentile(data_draw, 5)
    vmax = np.nanpercentile(data_draw, 95)
    if not np.isfinite(vmin) or not np.isfinite(vmax) or vmin >= vmax:
        vmin = np.nanmin(data_draw)
        vmax = np.nanmax(data_draw)
        if not np.isfinite(vmin) or not np.isfinite(vmax) or vmin == vmax:
            vmin, vmax = -0.5, 0.5

    # Colormap
    boundaries = np.linspace(vmin, vmax, n_colors + 1)
    cmap = plt.get_cmap("jet", n_colors)
    norm = BoundaryNorm(boundaries, ncolors=cmap.N, clip=True)

    # Nice ticks
    ticks = _nice_ticks(vmin, vmax)

    # Plot
    fig, ax = plt.subplots(figsize=(9, 4), constrained_layout=True)
    mesh = ax.pcolormesh(times, depth, data_draw.T, cmap=cmap, norm=norm, shading="auto")

    ax.set_title(title)
    ax.set_xlabel("Time")
    ax.set_ylabel("Depth")
    ax.invert_yaxis()

    # X axis ticks
    n_days = (tend.date() - tstart.date()).days + 1
    if n_days <= 60:
        interval = _nice_interval(n_days)
        locator = mdates.DayLocator(interval=interval)
        fmt = mdates.DateFormatter("%Y%m%d")
    elif n_days <= 730:
        months = max(1, _month_diff(tstart, tend))
        interval = _nice_interval(months)
        locator = mdates.MonthLocator(bymonthday=1, interval=interval)
        fmt = mdates.DateFormatter("%Y%m")
    else:
        years = tend.year - tstart.year + 1
        interval = _nice_interval(years)
        locator = mdates.YearLocator(base=interval, month=1, day=1)
        fmt = mdates.DateFormatter("%Y")

    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(fmt)
    ax.invert_yaxis()
    ax.set_ylim(depth[0], 0)


    # Colorbar with nice ticks
    cbar_ax = fig.add_axes([0.15, 0.07, 0.7, 0.02])
    cb = fig.colorbar(mesh, cax=cbar_ax, ticks=ticks, orientation='horizontal')
    #cb.ax.tick_params(labelsize=20)
    cbar_ax.set_label("Value")

    fig.subplots_adjust(bottom=0.25, top=0.9, left=0.1, right=0.95, wspace=0.2, hspace=0.3)

    # Save with random number
    os.makedirs(path_save, exist_ok=True)
    rand_num = random.randint(10000, 99999)
    out_path = os.path.join(path_save, f"{name_save}_{rand_num}.png")
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    return out_path




#---------#---------#---------#---------#---------#---------#



def plot_section(
    title,
    data_draw,         # np.ndarray, shape (depth, M)
    depth_array,       # np.ndarray, shape (depth, M)
    lon_min, lon_max, 
    lat_min, lat_max, 
    path_save=".",
    name_save="figure",
    n_colors=100 ,      # number of discrete color bins
    n_ticks = 5
):
    """
    Time–depth heatmap with pcolormesh.
    - Colormap: jet, BoundaryNorm with n_colors bins.
    - Color range: 5th to 95th percentile.
    - Colorbar: horizontal with 4–7 nice ticks.
    - X ticks: daily / monthly / yearly depending on span.
    - Output filename: name_save + "_" + random number + ".png"
    """
    if data_draw.ndim != 2:
        raise ValueError("data_draw must be 2D (n_time, depth).")
    n_depth, n_M = data_draw.shape

    if depth_array.ndim != 2 or depth_array.shape[1] != n_M or depth_array.shape[0] != n_depth :
        raise ValueError("depth must be 2D with shape equal to data_draw")

    if n_colors < 2:
        raise ValueError("n_colors must be >= 2.")

    M = np.size(depth_array, 1)
    # Color limits
    vmin = np.nanpercentile(data_draw, 5)
    vmax = np.nanpercentile(data_draw, 95)
    if not np.isfinite(vmin) or not np.isfinite(vmax) or vmin >= vmax:
        vmin = np.nanmin(data_draw)
        vmax = np.nanmax(data_draw)
        if not np.isfinite(vmin) or not np.isfinite(vmax) or vmin == vmax:
            vmin, vmax = -0.5, 0.5

    # Colormap
    boundaries = np.linspace(vmin, vmax, n_colors + 1)
    cmap = plt.get_cmap("jet", n_colors)
    norm = BoundaryNorm(boundaries, ncolors=cmap.N, clip=True)

    # Nice ticks
    ticks = _nice_ticks(vmin, vmax)



    # Plot
    fig, ax = plt.subplots(figsize=(9, 4), constrained_layout=True)
    X_axis = np.linspace (0, M -1, M)
    print (X_axis)
    Z_axis = depth_array[:,0]
    X_axis, Z_axis = np.meshgrid(X_axis, Z_axis)


    print (X_axis.shape, Z_axis.shape, (data_draw).shape)

    mesh = ax.pcolormesh(X_axis, Z_axis, data_draw, cmap=cmap, norm=norm, shading="auto")

    ax.set_title(title)
    ax.set_xlabel("Time")
    ax.set_ylabel("Depth")
    ax.invert_yaxis()

    # X axis ticks
    interval = M/n_ticks
    lat_list = np.linspace (lat_min,lat_max, M)
    lon_list = np.linspace (lon_min,lon_max, M)
    xtick = []
    xtick_label = []
    for i in range(0, M):
        if i%interval == 0:
            xtick.append(i)
            xtick_label.append('%.2fN\n%.2fE' %(lat_list[i],lon_list[i]))

    ax.set_xticks(xtick)
    ax.set_xticklabels(xtick_label)
    ax.invert_yaxis()
    ax.set_ylim(depth[0], 0)


    # Colorbar with nice ticks
    cbar_ax = fig.add_axes([0.15, 0.07, 0.7, 0.02])
    cb = fig.colorbar(mesh, cax=cbar_ax, ticks=ticks, orientation='horizontal')
    #cb.ax.tick_params(labelsize=20)
    cbar_ax.set_label("Value")

    fig.subplots_adjust(bottom=0.25, top=0.9, left=0.1, right=0.95, wspace=0.2, hspace=0.3)

    # Save with random number
    os.makedirs(path_save, exist_ok=True)
    rand_num = random.randint(10000, 99999)
    out_path = os.path.join(path_save, f"{name_save}_{rand_num}.png")
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    return out_path








