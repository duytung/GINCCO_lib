import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors
from mpl_toolkits.basemap import Basemap
import random
 


#########################################################
#these function below set a nice tick for color bar
def _nice_num(x, round_to_nearest):
    # Returns a "nice" number approximately equal to x.
    # If round_to_nearest is True, round; else ceil.
    if x == 0 or not np.isfinite(x):
        return 0.0
    expv = np.floor(np.log10(abs(x)))
    f = abs(x) / (10**expv)  # fraction in [1,10)
    if round_to_nearest:
        if f < 1.5:
            nf = 1.0
        elif f < 3.0:
            nf = 2.0
        elif f < 7.0:
            nf = 5.0
        else:
            nf = 10.0
    else:
        if f <= 1.0:
            nf = 1.0
        elif f <= 2.0:
            nf = 2.0
        elif f <= 5.0:
            nf = 5.0
        else:
            nf = 10.0
    return np.sign(x) * nf * (10**expv)

def _pretty_ticks(dmin, dmax, prefer_counts=(6,7,8,9,10), fallback=(5,11,12)):
    """
    Build "nice" ticks covering [dmin, dmax] with about 5–12 ticks.
    """
    if not np.isfinite(dmin) or not np.isfinite(dmax):
        # Fallback if data are all NaN
        return np.array([0, 1])

    if dmin == dmax:
        # Expand a degenerate range
        if dmin == 0:
            dmin, dmax = -1, 1
        else:
            pad = abs(dmin) * 0.1 if dmin != 0 else 1.0
            dmin, dmax = dmin - pad, dmax + pad

    rng = dmax - dmin

    # Try preferred counts first
    for n in prefer_counts:
        d = _nice_num(rng / (n - 1), round_to_nearest=True)
        gmin = np.floor(dmin / d) * d
        gmax = np.ceil(dmax / d) * d
        ticks = np.arange(gmin, gmax + 0.5 * d, d)
        if 5 <= len(ticks) <= 12:
            return ticks

    # Then try fallbacks
    for n in fallback:
        d = _nice_num(rng / (n - 1), round_to_nearest=True)
        gmin = np.floor(dmin / d) * d
        gmax = np.ceil(dmax / d) * d
        ticks = np.arange(gmin, gmax + 0.5 * d, d)
        if 5 <= len(ticks) <= 12:
            return ticks

    # Absolute fallback
    d = _nice_num(rng / 7, round_to_nearest=True)
    gmin = np.floor(dmin / d) * d
    gmax = np.ceil(dmax / d) * d
    return np.arange(gmin, gmax + 0.5 * d, d)

def _pad_10pct(minv, maxv):
    # Interpret “0.9 of min to 1.1 of max”, but handle negatives gracefully:
    lo = minv * 0.9 if minv >= 0 else minv * 1.1
    hi = maxv * 1.1 if maxv >= 0 else maxv * 0.9
    # If min == 0 or max == 0, still get some padding
    if minv == 0:
        hi_abs = abs(maxv) if maxv != 0 else 1.0
        lo = -0.1 * hi_abs
    if maxv == 0:
        lo_abs = abs(minv) if minv != 0 else 1.0
        hi = 0.1 * lo_abs
    if not np.isfinite(lo) or not np.isfinite(hi) or lo == hi:
        lo, hi = -1.0, 1.0
    return min(lo, hi), max(lo, hi)

#########################################################
# these function below set a nice tick for 

def nice_ticks_1d(dmin, dmax, max_ticks=5):
    """
    Return a list of 'nice' tick values between dmin and dmax.
    The number of ticks will be <= max_ticks (default=5).
    """
    if not np.isfinite(dmin) or not np.isfinite(dmax):
        return [0]

    if dmin == dmax:
        # Degenerate case: expand slightly
        if dmin == 0:
            dmin, dmax = -1, 1
        else:
            pad = abs(dmin) * 0.1
            dmin, dmax = dmin - pad, dmax + pad

    rng = dmax - dmin
    if rng == 0:
        rng = abs(dmin) if dmin != 0 else 1.0

    # Initial step size
    raw_step = rng / (max_ticks - 1)

    # Get a "nice" step
    expv = np.floor(np.log10(raw_step))
    frac = raw_step / (10**expv)

    if frac <= 1:
        nice_frac = 1
    elif frac <= 2:
        nice_frac = 2
    elif frac <= 5:
        nice_frac = 5
    else:
        nice_frac = 10

    step = nice_frac * 10**expv

    # Round range to multiples of step
    start = np.floor(dmin / step) * step
    end = np.ceil(dmax / step) * step

    ticks = np.arange(start, end + 0.5 * step, step)

    # If too many ticks, thin them out
    if len(ticks) > max_ticks:
        stride = int(np.ceil(len(ticks) / max_ticks))
        ticks = ticks[::stride]

    return ticks.tolist()




#########################################################

def map_draw(lon_min, lon_max, lat_min, lat_max, title, lon_data, lat_data, data_draw, path_save, name_save):
    dlon = lon_max - lon_min
    dlat = lat_max - lat_min
    dy = np.around(dlat/dlon, 1)
    if dy >= 2:
        dy = 1.5
    elif dy < 0.5:
        dy = 0.8

    fig = plt.figure(figsize=(7,7*dy))
    ax = fig.add_subplot(1,1,1)
    ax.set_title('%s' % (title))

    map2 = Basemap(projection='merc', llcrnrlon=lon_min, llcrnrlat=lat_min,
                   urcrnrlon=lon_max, urcrnrlat=lat_max, resolution='l', epsg=4326)

    parallels = nice_ticks_1d(np.nanmin(lat_data), np.nanmax(lat_data))  #horizontal line
    meridians = nice_ticks_1d(np.nanmin(lon_data), np.nanmax(lon_data))  #vertical line
    map2.drawparallels(parallels, linewidth=0.5, dashes=[2,8], labels=[1,0,0,0], fontsize=15, zorder=12)
    map2.drawmeridians(meridians, linewidth=0.5, dashes=[2,8], labels=[0,0,0,1], fontsize=15, zorder=12)
    map2.drawcoastlines(zorder=10)

    # -------- Auto colorbar limits and nice ticks --------
    finite_vals = np.asarray(data_draw)[np.isfinite(data_draw)]
    if finite_vals.size == 0:
        data_min, data_max = 0.0, 1.0
    else:
        data_min, data_max = float(np.min(finite_vals)), float(np.max(finite_vals))

    vmin_pad, vmax_pad = _pad_10pct(data_min, data_max)
    ticks = _pretty_ticks(vmin_pad, vmax_pad)

    # Colormap and normalization
    color_map = plt.get_cmap('jet')
    color_map.set_bad(color='white')
    norm = colors.Normalize(vmin=ticks[0], vmax=ticks[-1])

    # Grid shift for cell corners (as you had)
    dlon_cell = (lon_data[0,1] - lon_data[0,0]) / 2.0
    dlat_cell = (lat_data[1,0] - lat_data[0,0]) / 2.0

    cm = plt.pcolormesh(lon_data - dlon_cell, lat_data - dlat_cell, data_draw,
                        norm=norm, cmap='jet')

    # Colorbar with nice ticks
    cbar_ax = fig.add_axes([0.15, 0.06, 0.7, 0.02])
    cb = fig.colorbar(cm, cax=cbar_ax, ticks=ticks, orientation='horizontal')
    cb.ax.tick_params(labelsize=20)

    # Layout and save
    fig.subplots_adjust(bottom=0.15, top=0.9, left=0.15, right=0.90, wspace=0.2, hspace=0.3)
    session_id = random.randint(1E5, 1E6)
    plt.savefig('%s/%s_%s.png' % (path_save, name_save, session_id), dpi=250)
    plt.close()



'''

# Test function (map)

# === Create sample lon/lat grid and data ===
lon = np.linspace(100, 120, 250)   # 100E–110E
lat = np.linspace(8, 24, 100)      # 8N–24N
lon2d, lat2d = np.meshgrid(lon, lat)

# Example data: a simple 2D Gaussian hill
data = np.exp(-((lon2d-110)**2 + (lat2d-16)**2)/10)

# === Call map_draw ===
map_draw(
    lon_min=100, lon_max=120,
    lat_min=8, lat_max=24,
    title="Demo Map: Gaussian Hill",
    lon_data=lon2d,
    lat_data=lat2d,
    data_draw=data,
    path_save="/prod/projects/data/tungnd/figure/",     # current folder
    name_save="demo"
)



'''







