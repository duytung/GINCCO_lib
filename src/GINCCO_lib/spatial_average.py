import numpy as np

def spatial_average(
    data,
    dxdy,
    mask_ocean=None,
    lon_t=None,
    lat_t=None,
    lon_min=None,
    lon_max=None,
    lat_min=None,
    lat_max=None,
    
):
    """
    Compute an area-weighted spatial mean on a possibly non-regular grid,
    supporting both 2D and 3D data (time, lat, lon), geographic subsetting,
    and masking (e.g., land/ocean separation).

    Parameters
    ----------
    data : np.ndarray
        2-D array [Y, X] or 3-D array [T, Y, X] containing the field to average.
        NaNs are ignored.
    dxdy : np.ndarray
        Grid-cell weights or areas. Must match or broadcast to spatial shape [Y, X].
    mask_ocean : np.ndarray, optional
        Ocean mask where valid (ocean) cells are 1 and land cells are 0.
        Must match spatial shape [Y, X]. Only points with mask == 1 are used.
    lon_t : np.ndarray, optional
        Longitudes of grid. Required if lon/lat bounds are used.
    lat_t : np.ndarray, optional
        Latitudes of grid. Required if lon/lat bounds are used.
    lon_min, lon_max, lat_min, lat_max : float, optional
        Geographic subset boundaries.

    Returns
    -------
    np.ndarray or float
        Weighted spatial mean. If `data` is 2D → scalar; if 3D → 1D array [T].
    """
    data = np.asarray(data)
    dxdy = np.asarray(dxdy)

    if data.ndim not in (2, 3):
        raise ValueError("`data` must be 2D [Y, X] or 3D [T, Y, X].")

    spatial_shape = data.shape[-2:]

    if dxdy.shape != spatial_shape:
        raise ValueError(f"`dxdy` shape {dxdy.shape} must match spatial shape {spatial_shape}.")

    # --- Geographic mask ---
    region_mask = np.ones(spatial_shape, dtype=bool)
    if any(v is not None for v in (lon_min, lon_max, lat_min, lat_max)):
        if lon_t is None or lat_t is None:
            raise ValueError("lon_t and lat_t are required when specifying geographic bounds.")

        lon_t = np.asarray(lon_t)
        lat_t = np.asarray(lat_t)
        if lon_t.ndim == 1 and lat_t.ndim == 1:
            print ('Be careful. Shape of lon and lat are 1D. ')
            LON, LAT = np.meshgrid(lon_t, lat_t)
        else:
            LON, LAT = lon_t, lat_t

        if lon_min is not None:
            region_mask &= (LON >= lon_min)
        if lon_max is not None:
            region_mask &= (LON <= lon_max)
        if lat_min is not None:
            region_mask &= (LAT >= lat_min)
        if lat_max is not None:
            region_mask &= (LAT <= lat_max)

    # --- Ocean mask ---
    if mask_ocean is not None:
        mask_ocean = np.asarray(mask_ocean)
        if mask_ocean.shape != spatial_shape:
            raise ValueError(f"`mask_ocean` shape {mask_ocean.shape} must match {spatial_shape}.")
        region_mask &= (mask_ocean == 1)

    # --- Perform averaging ---
    def _weighted_mean(field):
        valid_mask = np.isfinite(field) & np.isfinite(dxdy) & (dxdy > 0) & region_mask
        num = np.nansum(field[valid_mask] * dxdy[valid_mask])
        den = np.nansum(dxdy[valid_mask])
        return num / den if den > 0 else np.nan

    if data.ndim == 2:
        return _weighted_mean(data)
    else:
        out = np.full(data.shape[0], np.nan)
        for t in range(data.shape[0]):
            out[t] = _weighted_mean(data[t])
        return out
