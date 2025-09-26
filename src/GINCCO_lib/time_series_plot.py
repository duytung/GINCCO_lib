import os
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import random

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
    Plot daily time series for multiple points.

    Tick rules:
      * <= 100 days: daily ticks, format YYYYMMdd
      * <= 500 days: monthly ticks, format YYYYMM
      * > 500 days: yearly ticks, format YYYY
    Always show ~4–7 ticks for readability.
    """

    # Build daily time axis
    n_time = data_point.shape[1]
    times = [tstart + (tend - tstart) * i/(n_time-1) for i in range(n_time)]

    # Duration in days
    duration_days = (tend - tstart).days + 1

    # Choose tick frequency
    if duration_days <= 100:
        fmt = mdates.DateFormatter("%Y-%m-%d")
        locator = mdates.AutoDateLocator(minticks=4, maxticks=7)
    elif duration_days <= 500:
        fmt = mdates.DateFormatter("%Y-%m")
        locator = mdates.MonthLocator(bymonthday=1, interval=max(1, duration_days//180))
    else:
        fmt = mdates.DateFormatter("%Y")
        locator = mdates.YearLocator(base=max(1, duration_days//1500))

    # Plot
    fig, ax = plt.subplots(figsize=(9, 3))
    for i in range(data_point.shape[0]):
        label = point_labels[i] if (point_labels and i < len(point_labels)) else f"Point {i+1}"
        ax.plot(times, data_point[i, :], lw=1.5, label=label)

    ax.set_title(title)
    ax.set_xlim(times[0], times[-1])
    ax.set_ylabel("Value")
    ax.grid(True, alpha=0.3)
    ax.legend(ncol=1, fontsize=9, frameon=True)

    # Apply formatter
    ax.xaxis.set_major_formatter(fmt)
    ax.xaxis.set_major_locator(locator)
    plt.setp(ax.get_xticklabels(), rotation=0, ha="center")

    fig.tight_layout()
    os.makedirs(path_save, exist_ok=True)
    session_id = random.randint(10000, 99999)
    out_path = os.path.join(path_save, f"{name_save}_{session_id}.png")
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    return out_path

