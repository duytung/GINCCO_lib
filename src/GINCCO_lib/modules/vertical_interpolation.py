import numpy as np


def interpolate_depth(data_3d, depth_3d, target_depth, mask_t=None):
    """Interpolate a 3D field (nz, ny, nx) to one target depth.

    Parameters
    ----------
    data_3d : ndarray
        Data values with shape (nz, ny, nx).
    depth_3d : ndarray
        Depth values with shape (nz, ny, nx), conventionally negative below sea level.
    target_depth : float
        Requested depth. Positive values are converted to negative values.
    mask_t : ndarray, optional
        2D mask where 1/True is valid ocean and 0/False is invalid land.

    Returns
    -------
    ndarray
        Interpolated 2D field with shape (ny, nx). Points that cannot be
        interpolated are NaN.
    """
    data_3d = np.asarray(np.ma.filled(data_3d, np.nan), dtype=float)
    depth_3d = np.asarray(np.ma.filled(depth_3d, np.nan), dtype=float)

    if data_3d.ndim != 3 or depth_3d.ndim != 3:
        raise ValueError("data_3d and depth_3d must both be 3D arrays.")
    if data_3d.shape != depth_3d.shape:
        raise ValueError("data_3d and depth_3d must have the same shape.")

    depth = -abs(float(target_depth))
    nz, ny, nx = depth_3d.shape

    deeper_candidates = np.ma.masked_where(depth_3d > depth, depth_3d)
    deeper_idx = np.argmax(deeper_candidates, axis=0)

    shallower_candidates = np.ma.masked_where(depth_3d < depth, depth_3d)
    shallower_idx = np.argmin(shallower_candidates, axis=0)

    weights = np.zeros((nz, ny, nx), dtype=float)
    can_interpolate = np.zeros((ny, nx), dtype=bool)

    for j in range(ny):
        for i in range(nx):
            k_shallow = shallower_idx[j, i]
            k_deep = deeper_idx[j, i]
            if k_shallow == k_deep:
                continue

            z_deep = depth_3d[k_deep, j, i]
            z_shallow = depth_3d[k_shallow, j, i]
            distance = z_deep - z_shallow
            if distance == 0 or not np.isfinite(distance):
                continue

            weights[k_deep, j, i] = 1 + (depth - z_deep) / distance
            weights[k_shallow, j, i] = 1 - (depth - z_shallow) / distance
            can_interpolate[j, i] = True

    data_interp = np.nansum(data_3d * weights, axis=0)
    data_interp[np.all(np.isnan(data_3d), axis=0)] = np.nan
    data_interp[~can_interpolate] = np.nan

    if mask_t is not None:
        mask_t = np.asarray(mask_t)
        if mask_t.shape != data_interp.shape:
            raise ValueError("mask_t must match the horizontal data shape.")
        data_interp[mask_t == 0] = np.nan

    return data_interp
