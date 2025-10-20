import numpy as np

def geostrophic_current(ssh, lat, lon, sin_t, cos_t):
    """
    Compute geostrophic surface currents (u, v) from sea surface height (SSH)
    on a 2D curvilinear grid.

    Parameters
    ----------
    ssh : 2D numpy array
        Sea surface height [m].
    lat : 2D numpy array
        Latitude [degrees].
    lon : 2D numpy array
        Longitude [degrees].

    Returns
    -------
    u : 2D numpy array
        Eastward geostrophic velocity [m/s].
    v : 2D numpy array
        Northward geostrophic velocity [m/s].
    """
    g = 9.81
    omega = 7.292115e-5
    R = 6371000.0



    # Convert masked arrays to plain arrays with NaN
    ssh = np.asarray(ssh, dtype=float)
    lat = np.asarray(lat, dtype=float)
    lon = np.asarray(lon, dtype=float)

    if np.ma.isMaskedArray(ssh): ssh = ssh.filled(np.nan)
    if np.ma.isMaskedArray(lat): lat = lat.filled(np.nan)
    if np.ma.isMaskedArray(lon): lon = lon.filled(np.nan)



    # Compute Coriolis parameter (same shape as grid)
    f = 2 * omega * np.sin(np.deg2rad(lat))

    # Convert lat/lon to meters for local spacing
    lat_rad = np.deg2rad(lat)
    lon_rad = np.deg2rad(lon)

    # Compute local metric terms (finite differences)
    dlat_dy, dlat_dx = np.gradient(lat_rad)
    dlon_dy, dlon_dx = np.gradient(lon_rad)

    # Grid spacing in meters (approximate)
    dx = R * np.sqrt((dlon_dx * np.cos(lat_rad))**2 + dlat_dx**2)
    dy = R * np.sqrt((dlon_dy * np.cos(lat_rad))**2 + dlat_dy**2)

    # SSH gradients
    dssh_dy, dssh_dx = np.gradient(ssh)

    # Convert gradients to per meter
    dssh_dx = dssh_dx / dx
    dssh_dy = dssh_dy / dy

    # Geostrophic velocities
    u = -g / f * dssh_dy
    v =  g / f * dssh_dx

    # Mask out low-latitude region (avoid f ≈ 0)
    mask = np.abs(f) < 1e-5
    u[mask] = np.nan
    v[mask] = np.nan

    #Rotate to N-S
    U1 =  u * cos_t + v * sin_t
    V1 = -u * sin_t + v * cos_t

    return U1, V1








