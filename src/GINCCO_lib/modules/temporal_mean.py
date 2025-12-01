import numpy as np
from datetime import datetime

def _to_np_day(d: datetime) -> np.datetime64:
    """Convert Python datetime to numpy datetime64 at day resolution."""
    return np.datetime64(d.date(), 'D')

def monthly_mean(data: np.ndarray, tstart: datetime, tend: datetime, time_axis: int = 0):
    """
    Compute monthly means for daily, contiguous data in [tstart, tend] (inclusive).

    Parameters
    ----------
    data : np.ndarray
        Input array. One axis is time (daily).
    tstart, tend : datetime.datetime
        Inclusive range of the data.
    time_axis : int
        Axis that represents time in `data`.

    Returns
    -------
    monthly : np.ndarray
        Monthly means with time axis replaced by number of months.
    month_labels : np.ndarray of datetime64[M]
        Month labels for each output slice.
    """
    # Normalize time axis to front
    x = np.moveaxis(data, time_axis, 0)

    start_d = _to_np_day(tstart)
    end_d   = _to_np_day(tend)

    # Expected number of days (inclusive)
    n_days = int((end_d - start_d) / np.timedelta64(1, 'D')) + 1
    if x.shape[0] != n_days:
        raise ValueError(f"Expected {n_days} days from {tstart.date()} to {tend.date()}, got {x.shape[0]}.")

    # Daily timestamps
    time_vec = start_d + np.arange(n_days).astype('timedelta64[D]')

    # Month labels
    y1, m1 = tstart.year, tstart.month
    y2, m2 = tend.year, tend.month
    n_months = (y2 - y1) * 12 + (m2 - m1) + 1
    month0 = np.datetime64(f"{y1:04d}-{m1:02d}", 'M')
    month_labels = month0 + np.arange(n_months).astype('timedelta64[M]')

    # Map each day to its month
    time_months = time_vec.astype('datetime64[M]')

    # Aggregate
    out = np.empty((n_months,) + x.shape[1:], dtype=float)
    for i, m in enumerate(month_labels):
        sel = (time_months == m)
        out[i] = np.nanmean(x[sel, ...], axis=0)

    # Restore original axis layout
    monthly = np.moveaxis(out, 0, time_axis)
    return monthly, month_labels


def annual_mean(data: np.ndarray, tstart: datetime, tend: datetime, time_axis: int = 0):
    """
    Compute annual means for daily, contiguous data in [tstart, tend] (inclusive).

    Partial first or last years are averaged over the available days.

    Parameters
    ----------
    data : np.ndarray
        Input array. One axis is time (daily).
    tstart, tend : datetime.datetime
        Inclusive range of the data.
    time_axis : int
        Axis that represents time in `data`.

    Returns
    -------
    yearly : np.ndarray
        Annual means with time axis replaced by number of years.
    year_labels : np.ndarray of datetime64[Y]
        Year labels for each output slice.
    """
    x = np.moveaxis(data, time_axis, 0)

    start_d = _to_np_day(tstart)
    end_d   = _to_np_day(tend)

    n_days = int((end_d - start_d) / np.timedelta64(1, 'D')) + 1
    if x.shape[0] != n_days:
        raise ValueError(f"Expected {n_days} days from {tstart.date()} to {tend.date()}, got {x.shape[0]}.")

    time_vec = start_d + np.arange(n_days).astype('timedelta64[D]')

    y1, y2 = tstart.year, tend.year
    n_years = (y2 - y1) + 1
    year0 = np.datetime64(f"{y1:04d}", 'Y')
    year_labels = year0 + np.arange(n_years).astype('timedelta64[Y]')

    time_years = time_vec.astype('datetime64[Y]')

    out = np.empty((n_years,) + x.shape[1:], dtype=float)
    for i, y in enumerate(year_labels):
        sel = (time_years == y)
        out[i] = np.nanmean(x[sel, ...], axis=0)

    yearly = np.moveaxis(out, 0, time_axis)
    return yearly, year_labels
