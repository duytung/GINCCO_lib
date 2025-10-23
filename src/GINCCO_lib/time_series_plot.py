import os
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import random

def _choose_locator(tstart, tend):
    duration_days = (tend - tstart).days

    if duration_days <= 100:  # short range
        locator = mdates.AutoDateLocator(minticks=5, maxticks=10)
        fmt = mdates.DateFormatter("%b-%d\n%Y")
    elif duration_days <= 3650:  # up to ~10 years
        months = max(1, duration_days / 30.44)
        interval = max(1, round(months / 8))
        locator = mdates.MonthLocator(bymonthday=1, interval=interval)
        fmt = mdates.DateFormatter("%b-%d\n%Y")
    else:  # very long range
        years = max(1, duration_days / 365)
        interval = max(1, round(years / 8))
        locator = mdates.YearLocator(base=interval)
        fmt = mdates.DateFormatter("%Y")
    return locator, fmt



def plot_point(
    title,
    tstart,            # datetime.datetime
    tend,              # datetime.datetime
    data_point,        # numpy array, shape (n_point, n_time)
    path_save=".",
    name_save="figure",
    point_labels=None  # optional list of names for each point
):
    """
    Plot daily time series for one or multiple points over a given time range.

    Parameters
    ----------
    title : str
        Title of the plot.
    tstart : datetime.datetime
        Start date of the time series.
    tend : datetime.datetime
        End date of the time series.
    data_point : np.ndarray
        Array of time series values.  
        Shape can be:
        * (n_time,) — single time series.
        * (n_point, n_time) — multiple time series.
    path_save : str, optional
        Directory where the figure will be saved. Default is the current directory ``"."``.
    name_save : str, optional
        Base filename (without extension) for the saved image. Default is ``"figure"``.
    point_labels : list of str, optional
        Optional list of labels for each time series.  
        If not provided, default names like “Point 1”, “Point 2”, etc. are used.

    Returns
    -------
    str
        Full path to the saved PNG image.
    """

    # Build daily time axis
    if data_point.ndim == 2:
        n_time = data_point.shape[1]
    elif data_point.ndim == 1:
        n_time = data_point.shape[0]
    else:
        raise ValueError("data_point must be 1D or 2D")
    
    times = [tstart + (tend - tstart) * i/(n_time-1) for i in range(n_time)]

    # Duration in days
    duration_days = (tend - tstart).days + 1


    # Plot
    fig, ax = plt.subplots(figsize=(9, 3))
    if data_point.ndim == 1:
        label = point_labels[0] if point_labels else "Point 1"
        ax.plot(times, data_point, lw=1.5, label=label)

    elif data_point.ndim == 2:
        for i in range(data_point.shape[0]):
            label = point_labels[i] if (point_labels and i < len(point_labels)) else f"Point {i+1}"
            ax.plot(times, data_point[i, :], lw=1.5, label=label)

    else:
        raise ValueError("data_point must be 1D or 2D")



    ax.set_title(title)
    ax.set_xlim(times[0], times[-1])
    ax.set_ylabel("Value")
    ax.grid(True, alpha=0.3)
    ax.legend(ncol=1, fontsize=9, frameon=True)

    # Apply formatter
    locator, fmt = _choose_locator(tstart, tend)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(fmt)

    plt.setp(ax.get_xticklabels(), rotation=0, ha="center")

    fig.tight_layout()
    os.makedirs(path_save, exist_ok=True)
    session_id = random.randint(10000, 99999)
    out_path = os.path.join(path_save, f"{name_save}_{session_id}.png")
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    return out_path


#--------#--------#--------#--------#--------#--------#


import os, random
import numpy as np
import matplotlib.pyplot as plt

def _choose_monthly_tick_indices(n_time: int, n_xticks_desired: int):
    """
    Pick visually nice tick indices for monthly data of length n_time.

    Strategy:
      1) Try k in [3..12] 'regular ticks' where (n_time % k == 0) for nice integer step = n_time // k.
         Use the k that minimizes |k - n_xticks_desired|. Regular ticks are [0, step, 2*step, ...],
         then we ALWAYS append the last index (n_time-1) if it is not already included.
      2) If nothing divides nicely, fall back to a rounded step from desired.
    Always deduplicate and keep indices sorted and within [0, n_time-1].
    """
    n_time = int(n_time)
    desired = max(3, int(n_xticks_desired))

    best_k = None
    best_gap = 1e9
    # Prefer tidy segment counts from 3 to 12
    for k in range(3, 13):
        if n_time % k == 0:  # integer step
            gap = abs(k - desired)
            if gap < best_gap:
                best_gap = gap
                best_k = k

    if best_k is not None:
        step = n_time // best_k
        idx = list(range(0, n_time, step))
        # Ensure last index is present
        if idx[-1] != n_time - 1:
            idx.append(n_time - 1)
        # Keep ticks roughly 4..9 when possible
        if len(idx) < 4 and step > 1:
            # add more ticks by halving step if possible
            half = max(1, step // 2)
            idx = list(range(0, n_time, half))
            if idx[-1] != n_time - 1:
                idx.append(n_time - 1)
        return sorted(set(idx))

    # Fallback: pick a step based on desired count
    # We want about desired ticks including the last, so aim for desired-1 intervals
    if desired <= 1:
        desired = 2
    base_step = max(1, int(round((n_time - 1) / (desired - 1))))
    idx = list(range(0, n_time - 1, base_step))
    idx.append(n_time - 1)
    idx = sorted(set(i for i in idx if 0 <= i < n_time))
    return idx

def plot_point_monthly(
    title,
    time_label,         # sequence of str or anything convertible to str, len = n_time
    data_point,         # numpy array, shape (n_point, n_time) or (n_time,)
    n_xticks_desired=6, # user suggestion; function will adjust for nice spacing
    path_save=".",
    name_save="figure",
    point_labels=None   # optional list of names for each point
):
    """
    Plot monthly time series for one or multiple points using custom tick labels.

    Parameters
    ----------
    title : str
        Title of the figure.
    time_label : sequence of str
        Sequence of labels for the x-axis, typically months or years.
        Length must match the time dimension of ``data_point``.
    data_point : np.ndarray
        Time series data array.  
        Shape can be:
          * (n_time,) — single time series.
          * (n_point, n_time) — multiple time series.
    n_xticks_desired : int, optional
        Desired number of x-axis ticks. The function adjusts this automatically
        to achieve clean and evenly spaced labels. Default is 6.
    path_save : str, optional
        Directory path where the output image will be saved. Default is ``"."``.
    name_save : str, optional
        Base name (without extension) for the saved image. Default is ``"figure"``.
    point_labels : list of str, optional
        Optional list of names for each time series.  
        If not provided, default names like “Point 1”, “Point 2”, etc. are used.

    Returns
    -------
    str
        Full path to the saved PNG image.
    """

    # Validate shapes
    time_label = [str(x) for x in time_label]
    if np.ndim(data_point) == 1:
        n_time = data_point.shape[0]
        n_series = 1
    elif np.ndim(data_point) == 2:
        n_series, n_time = data_point.shape
    else:
        raise ValueError("data_point must be 1D or 2D")

    if len(time_label) != n_time:
        raise ValueError(f"len(time_label)={len(time_label)} does not match time axis n_time={n_time}")

    # Indices for plotting
    x = np.arange(n_time, dtype=int)

    # Choose tick indices
    tick_idx = _choose_monthly_tick_indices(n_time, n_xticks_desired)
    tick_labels = [time_label[i] for i in tick_idx]

    # Plot
    fig, ax = plt.subplots(figsize=(9, 3))
    if np.ndim(data_point) == 1:
        label = point_labels[0] if point_labels else "Point 1"
        ax.plot(x, data_point, lw=1.5, label=label)
    else:
        for i in range(n_series):
            label = point_labels[i] if (point_labels and i < len(point_labels)) else f"Point {i+1}"
            ax.plot(x, data_point[i, :], lw=1.5, label=label)

    ax.set_title(title)
    ax.set_xlim(0, n_time - 1)
    ax.set_ylabel("Value")
    ax.grid(True, alpha=0.3)
    ax.legend(ncol=1, fontsize=9, frameon=True)

    # Apply ticks
    ax.set_xticks(tick_idx)
    ax.set_xticklabels(tick_labels, rotation=0, ha="center")

    fig.tight_layout()
    os.makedirs(path_save, exist_ok=True)
    session_id = random.randint(10000, 99999)
    out_path = os.path.join(path_save, f"{name_save}_{session_id}.png")
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    return out_path





