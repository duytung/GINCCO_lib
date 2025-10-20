import numpy as np

def monthly_mean(data: np.ndarray, tstart, tend, time_axis: int = 0):
    """
    Compute monthly means for daily continuous data between tstart and tend.

    Parameters
    ----------
    data : np.ndarray
        Input array. One axis represents time (daily data).
    tstart : datetime.datetime
        Start date (inclusive).
    tend : datetime.datetime
        End date (inclusive).
    time_axis : int, optional
        Axis representing time (default=0).

    Returns
    -------
    monthly_data : np.ndarray
        Array of monthly means with the same shape as input but time replaced by number of months.
    month_labels : np.ndarray of datetime64[M]
        Labels for each month.
    """
    # Move time axis to the front
    x = np.moveaxis(data, time_axis, 0)

    # Convert to datetime64 for easier computation
    start_d = np.datetime64(tstart.date())
    end_d = np.datetime64(tend.date())

    # Number of days expected
    n_days = int((end_d - start_d).astype('timedelta64[D]')) + 1
    if x.shape[0] != n_days:
        raise ValueError(f"Expected {n_days} days but got {x.shape[0]} along the time axis.")

    # Create daily timestamps
    time_vec = start_d + np.arange(n_days).astype('timedelta64[D]')

    # Monthly grouping
    y1, m1 = tstart.year, tstart.month
    y2, m2 = tend.year, tend.month
    n_months = (y2 - y1) * 12 + (m2 - m1) + 1
    month_starts = np.datetime64(f"{y1:04d}-{m1:02d}", 'M') + np.arange(n_months).astype('timedelta64[M]')

    # Convert daily timestamps to months
    time_months = time_vec.astype('datetime64[M]')

    # Output array
    out_shape = (n_months,) + x.shape[1:]
    monthly = np.empty(out_shape, dtype=float)

    for i, m in enumerate(month_starts):
        sel = (time_months == m)
        monthly[i] = np.nanmean(x[sel, ...], axis=0)

    # Move time axis back
    monthly = np.moveaxis(monthly, 0, time_axis)
    return monthly, month_starts






#######-----------#########----------#######-----------#########



import numpy as np

def annual_mean(data: np.ndarray, tstart, tend, time_axis: int = 0):
    """
    Compute annual means for daily continuous data between tstart and tend (inclusive).

    Parameters
    ----------
    data : np.ndarray
        Input array. One axis is time (daily, contiguous).
    tstart : datetime.datetime
        Start date (inclusive).
    tend : datetime.datetime
        End date (inclusive).
    time_axis : int, optional
        Axis representing time in `data` (default 0).

    Returns
    -------
    yearly_data : np.ndarray
        Array of annual means with the same shape as `data` but with the time
        dimension replaced by the number of years in [tstart, tend].
    year_labels : np.ndarray of datetime64[Y]
        Year labels corresponding to each output slice.
    """
    # Move time axis to the front for easy processing
    x = np.moveaxis(data, time_axis, 0)

    # Convert to numpy datetime64[D] for arithmetic and build daily timestamps
    start_d = np.datetime64(tstart.date())
    end_d = np.datetime64(tend.date())
    n_days = int((end_d - start_d).astype('timedelta64[D]')) + 1

    if x.shape[0] != n_days:
        raise ValueError(
            f"Expected {n_days} daily samples between {tstart.date()} and {tend.date()}, "
            f"but got {x.shape[0]} along the time axis."
        )

    time_vec = start_d + np.arange(n_days).astype('timedelta64[D]')

    # Determine year buckets
    y1, y2 = tstart.year, tend.year
    n_years = (y2 - y1) + 1
    year_labels = np.datetime64(f"{y1:04d}", 'Y') + np.arange(n_years).astype('timedelta64[Y]')

    # Map each day to its year
    time_years = time_vec.astype('datetime64[Y]')

    # Allocate output and compute annual means
    out_shape = (n_years,) + x.shape[1:]
    yearly = np.empty(out_shape, dtype=float)

    for i, y in enumerate(year_labels):
        sel = (time_years == y)
        # It is possible the first or last year is partial; that is fine.
        yearly[i] = np.nanmean(x[sel, ...], axis=0)

    # Restore original axis order
    yearly = np.moveaxis(yearly, 0, time_axis)
    return yearly, year_labels






