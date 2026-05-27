import numpy as np

def geostrophic_current(ssh, lat, dx, dy, sin_t, cos_t):
    """
    Compute geostrophic currents when dx, dy (in meters) are already known.

    Parameters
    ----------
    ssh : 2D array [m]
        Sea surface height.
    lat : 2D array [deg]
        Latitude (only used to mask low-latitude values if needed).
    f : 2D array [s^-1]
        Coriolis parameter (2*omega*sin(lat)).
    dx, dy : 2D arrays [m]
        Grid spacing in x (zonal) and y (meridional) directions.

    Returns
    -------
    u, v : 2D arrays [m/s]
        Eastward (u) and northward (v) geostrophic velocities.
    """
    g = 9.81
    omega = 7.292115e-5

    ssh = np.asarray(np.ma.filled(ssh, np.nan), dtype=float)
    lat = np.asarray(np.ma.filled(lat, np.nan), dtype=float)
    dx = np.asarray(np.ma.filled(dx, np.nan), dtype=float)
    dy = np.asarray(np.ma.filled(dy, np.nan), dtype=float)
    sin_t = np.asarray(np.ma.filled(sin_t, np.nan), dtype=float)
    cos_t = np.asarray(np.ma.filled(cos_t, np.nan), dtype=float)

    # Compute Coriolis parameter (same shape as grid)
    f = 2 * omega * np.sin(np.deg2rad(lat))

    # Gradients of SSH (finite differences)
    dssh_dy, dssh_dx = np.gradient(ssh)
    dssh_dx = dssh_dx / dx
    dssh_dy = dssh_dy / dy

    # Geostrophic currents
    u = -g / f * dssh_dy
    v =  g / f * dssh_dx

    # Mask near equator and invalid data
    u[np.abs(f) < 1e-5] = np.nan
    v[np.abs(f) < 1e-5] = np.nan
    u[np.isnan(ssh)] = np.nan
    v[np.isnan(ssh)] = np.nan

    #Rotate to N-S
    U1 =  u * cos_t + v * sin_t
    V1 = -u * sin_t + v * cos_t

    return U1, V1



