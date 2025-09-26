import os
import glob
import sys
from datetime import datetime, timedelta

import numpy as np
from netCDF4 import Dataset 

#############################
'''
This module usse to import a single file.

List of functions: 
* import_section: import vertical section along a line of longitude or latitude (output shape: [x,z])


Features: 
* Automatically load the correct grid indice (_u, _v, _w, ...)
* For multiple file, it will check if all the file is available or not, before really load the file to avoid crash in the middle. 
* You can choose to stop the script if any file is missing, or fill the data on that date with nan value

'''
#############################
import numpy as np

def section_extract(lat_array, lon_array, depth_array, lat, lon,
                    method="idw", power=2, max_iter=20, tol=1e-10, eps=1e-10):
    """
    Build a vertical section along given (lat, lon) points on a curvilinear grid,
    and return both the interpolated depth_array section and a callable to apply the
    same section to any 3-D scalar field on the same grid.

    Notes:
    Currently, we only support scalar fields (e.g., temperature, salinity), not vector fields.

    Algorithm:
    The data will be imported horizontally, layer by layer, and then all layers will be concatenated to form a section.
    First, the section will be divided into small parts. For example: lat = 10, lon = [10, 10.1, 10.2, …, 11].
    In this example, we will have about 10 points.
    For each point, we find the 4 surrounding grid corners and construct a distance-weighted function.
    Using this weighted function, we interpolate the value at that point.
    Repeat this process for all points in layer 1.
    Repeat for all layers.
    Since the locations of the points do not change across layers, the weighted function only needs to be calculated once.
    For each point, we must also apply the same procedure to interpolate the depth_array (not just the data).
    Because the depth_array varies across points and layers, we interpolate the depth_array grid to obtain the depth_array at each point along the section.
    Finally, we obtain both the data section and the depth_array section, which can then be plotted as standard 2D data.

    Parameters
    ----------
    lat_array : (ny, nx) array_like
        Grid node latitudes.
    lon_array : (ny, nx) array_like
        Grid node longitudes.
    depth_array : (nz, ny, nx) array_like
        depth_array values for each model layer on the grid.
    lat : (M,) array_like
        Latitudes of section points in order along the section.
    lon : (M,) array_like
        Longitudes of section points in order along the section.

    method : {"idw", "bilinear"}, optional
        Interpolation method for the horizontal step:
          - "idw": inverse-distance weighting using the 4 surrounding corners.
          - "bilinear": true bilinear interpolation inside the local cell.
        Default is "idw".
    power : float, optional
        Power for IDW distances. Ignored for "bilinear". Default 2.
    max_iter : int, optional
        Maximum Newton iterations for solving bilinear coordinates (s, t).
    tol : float, optional
        Convergence tolerance on position residual for bilinear solve.
    eps : float, optional
        Small number to avoid division by zero.

    Returns
    -------
    depth_array_section : (nz, M) ndarray
        Interpolated depth_array along the section.
    apply_to_data : callable
        Function `apply_to_data(data3d)` that returns a data section with shape
        (nz, M) for any scalar field `data3d` of shape (nz, ny, nx).

    Notes
    -----
    - Precomputes the surrounding cell and interpolation weights once.
    - For "bilinear", it solves for local cell coordinates (s, t) so that
      P(s, t) matches the query point inside that cell. Falls back to IDW if
      the solve fails for a point.
    - depth_array is interpolated with the same precomputed weights.
    """

    # -----------------------------
    # 0) Basic checks and shaping
    # -----------------------------
    lat = np.asarray(lat).ravel()
    lon = np.asarray(lon).ravel()
    lat_g = np.asarray(lat_array)
    lon_g = np.asarray(lon_array)
    depth_array = np.asarray(depth_array)

    if lat_g.shape != lon_g.shape:
        raise ValueError("lat_array and lon_array must have the same shape.")
    if depth_array.ndim != 3 or depth_array.shape[1:] != lat_g.shape:
        raise ValueError("depth_array must have shape (nz, ny, nx) matching the grid.")
    if lat.size != lon.size:
        raise ValueError("lat and lon must have the same length.")
    if method not in ("idw", "bilinear"):
        raise ValueError("method must be 'idw' or 'bilinear'.")

    nz, ny, nx = depth_array.shape
    M = lat.size

    # -----------------------------------------
    # 1) Utilities to locate the surrounding cell
    # -----------------------------------------

    # Flatten once for a simple nearest-node search
    lat_flat = lat_g.reshape(-1)
    lon_flat = lon_g.reshape(-1)

    def nearest_node_indices(lat_p, lon_p):
        """Return (iy, ix) of the nearest grid node by Euclidean distance in degree space."""
        d2 = (lat_flat - lat_p)**2 + (lon_flat - lon_p)**2
        k = np.argmin(d2)
        iy, ix = divmod(k, nx)
        return iy, ix


    # -----------------------------------------
    # 2) Prepare storage for geometry per point
    # -----------------------------------------
    # Corner order is:
    #   c00: (iy,   ix  )  top-left
    #   c10: (iy,   ix+1)  top-right
    #   c01: (iy+1, ix  )  bottom-left
    #   c11: (iy+1, ix+1)  bottom-right
    corner_ids = np.zeros((M, 4, 2), dtype=int)
    # For IDW we store per-point weights for the 4 corners
    idw_w = np.zeros((M, 4), dtype=float)
    # For bilinear we store (s, t) inside the local cell
    st = np.zeros((M, 2), dtype=float)
    # Mark which points ended up using IDW even if method="bilinear"
    fallback_idw = np.zeros(M, dtype=bool)

    # -----------------------------------------
    # 3) Build per-point local geometry
    #    a) pick a cell around the nearest node
    #    b) compute either IDW weights or solve bilinear (s, t)
    # -----------------------------------------
    for m in range(M):
        # 3a) Find a valid cell around the query point
        # note the problem about the cell story here. 
        iy, ix = nearest_node_indices(lat[m], lon[m])



        # Suppose nearest node is (iy0, ix0)
        if lon[m] > lon_g[iy, ix]:
            #Point at the right of nearest point
            ix0 = ix               # use [ix0, ix0+1]
        else:
            #Point at the left of nearest point
            ix0 = ix - 1           # use [ix0-1, ix0]

        if lat[m] > lat_g[iy, ix]:
            #Point higher than the nearest point
            iy0 = iy   # use [iy0, iy0+1]
        else:
            #Point lower than the nearest point
            iy0 = iy - 1           # use [iy0-1, iy0]

        # Clamp inside valid range
        iy0 = np.clip(iy0, 0, ny-2)
        ix0 = np.clip(ix0, 0, nx-2)

        # Corners of the enclosing cell
        corners = np.array([
            [iy0,     ix0    ],  # c00
            [iy0,     ix0 + 1],  # c10
            [iy0 + 1, ix0    ],  # c01
            [iy0 + 1, ix0 + 1]   # c11
        ], dtype=int)
        corner_ids[m] = corners

        # Extract corner coordinates
        y00, x00 = lat_g[iy0,     ix0],     lon_g[iy0,     ix0]
        y10, x10 = lat_g[iy0,     ix0 + 1], lon_g[iy0,     ix0 + 1]
        y01, x01 = lat_g[iy0 + 1, ix0],     lon_g[iy0 + 1, ix0]
        y11, x11 = lat_g[iy0 + 1, ix0 + 1], lon_g[iy0 + 1, ix0 + 1]

        # Distances to corners (used for IDW and for exact-hit shortcut)
        dy = np.array([y00, y10, y01, y11]) - lat[m]
        dx = np.array([x00, x10, x01, x11]) - lon[m]
        dist = np.hypot(dy, dx)

        # If the query hits a node exactly, make it a pure pick
        if np.any(dist < eps):
            w = np.zeros(4, dtype=float)
            w[np.argmin(dist)] = 1.0
            idw_w[m] = w
            st[m] = 0.0  # not used
            fallback_idw[m] = True if method == "bilinear" else False
            continue

        if method == "idw":
            # 3b-IDW) Inverse-distance weights on the 4 corners
            w = 1.0 / (dist**power)
            w /= w.sum()
            idw_w[m] = w

        else:
            # 3b-Bilinear) Solve for (s, t) in the bilinear mapping
            # Position function:
            #   X(s,t) = x00*(1-s)*(1-t) + x10*s*(1-t) + x01*(1-s)*t + x11*s*t
            #   Y(s,t) = y00*(1-s)*(1-t) + y10*s*(1-t) + y01*(1-s)*t + y11*s*t
            # Solve F(s,t) = [X(s,t)-xq, Y(s,t)-yq] = 0 by Newton iterations
            xq, yq = lon[m], lat[m]
            s = 0.5
            t = 0.5
            ok = False
            for _ in range(max_iter):
                # Evaluate mapping
                X = (x00*(1-s)*(1-t) + x10*s*(1-t) + x01*(1-s)*t + x11*s*t)
                Y = (y00*(1-s)*(1-t) + y10*s*(1-t) + y01*(1-s)*t + y11*s*t)
                rx = X - xq
                ry = Y - yq
                if abs(rx) + abs(ry) < tol:
                    ok = True
                    break

                # Jacobian entries
                dXds = (-(1-t)*x00 + (1-t)*x10 - t*x01 + t*x11)
                dXdt = (-(1-s)*x00 - s*x10 + (1-s)*x01 + s*x11)
                dYds = (-(1-t)*y00 + (1-t)*y10 - t*y01 + t*y11)
                dYdt = (-(1-s)*y00 - s*y10 + (1-s)*y01 + s*y11)

                # Solve 2x2 linear system J * [ds, dt]^T = -[rx, ry]^T
                det = dXds*dYdt - dXdt*dYds
                if abs(det) < eps:
                    ok = False
                    break
                ds = (-rx*dYdt + dXdt*ry) / det
                dt = (-dXds*ry + rx*dYds) / det

                # Update guess
                s += ds
                t += dt

                # Optional clamping helps keep iterations stable
                s = float(np.clip(s, -0.5, 1.5))
                t = float(np.clip(t, -0.5, 1.5))

            if ok and (0.0 - 1e-6 <= s <= 1.0 + 1e-6) and (0.0 - 1e-6 <= t <= 1.0 + 1e-6):
                # Store solved (s, t)
                st[m, 0] = s
                st[m, 1] = t
            else:
                # Fall back to IDW if the solve failed
                w = 1.0 / (dist**power)
                w /= w.sum()
                idw_w[m] = w
                fallback_idw[m] = True

    # -----------------------------------------
    # 4) Helper to combine corner values into a single interpolated value
    # -----------------------------------------
    def combine_layer(values4, m):
        """
        Combine 4 corner values for point m into one value according to method.

        values4 order: [c00, c10, c01, c11]
        """
        if method == "bilinear" and not fallback_idw[m]:
            s, t = st[m]
            # Bilinear weights
            w00 = (1 - s) * (1 - t)
            w10 = s * (1 - t)
            w01 = (1 - s) * t
            w11 = s * t
            return w00*values4[0] + w10*values4[1] + w01*values4[2] + w11*values4[3]
        else:
            # IDW path
            w = idw_w[m]
            return w[0]*values4[0] + w[1]*values4[1] + w[2]*values4[2] + w[3]*values4[3]

    # -----------------------------------------
    # 5) Interpolate the depth_array section using precomputed geometry
    # -----------------------------------------
    depth_section = np.empty((nz, M), dtype=depth_array.dtype)
    for k in range(nz):
        # Gather corner values for all points
        c00 = depth_array[k, corner_ids[:, 0, 0], corner_ids[:, 0, 1]]
        c10 = depth_array[k, corner_ids[:, 1, 0], corner_ids[:, 1, 1]]
        c01 = depth_array[k, corner_ids[:, 2, 0], corner_ids[:, 2, 1]]
        c11 = depth_array[k, corner_ids[:, 3, 0], corner_ids[:, 3, 1]]

        # Combine per point
        for m in range(M):
            depth_section[k, m] = combine_layer(
                np.array([c00[m], c10[m], c01[m], c11[m]]), m
            )

    # -----------------------------------------
    # 6) Return a callable for any scalar 3-D field
    # -----------------------------------------
    def apply_to_data(data3d):
        """
        Interpolate a scalar field on the same grid onto the pre-defined section.

        Parameters
        ----------
        data3d : (nz, ny, nx) array_like
            Scalar field (e.g., temperature, salinity).

        Returns
        -------
        data_section : (nz, M) ndarray
            Interpolated values along the section.
        """
        arr = np.asarray(data3d)
        if arr.shape != (nz, ny, nx):
            raise ValueError(f"data3d must have shape {(nz, ny, nx)}.")

        out = np.empty((nz, M), dtype=arr.dtype)
        for k in range(nz):
            c00 = arr[k, corner_ids[:, 0, 0], corner_ids[:, 0, 1]]
            c10 = arr[k, corner_ids[:, 1, 0], corner_ids[:, 1, 1]]
            c01 = arr[k, corner_ids[:, 2, 0], corner_ids[:, 2, 1]]
            c11 = arr[k, corner_ids[:, 3, 0], corner_ids[:, 3, 1]]
            for m in range(M):
                out[k, m] = combine_layer(
                    np.array([c00[m], c10[m], c01[m], c11[m]]), m
                )
        return out

    return depth_section, apply_to_data



# -----------------------------------------

def data_interp(depth_sec, data_sec, depth_interval=1.0):
    """
    Interpolate irregular-depth section data (nz, M) onto one shared regular depth grid.

    Assumptions
    ----------
    - Each column in depth_sec is ordered (shallow to deep).
    - No extrapolation: values outside a column's native range are NaN.

    Parameters
    ----------
    depth_sec : ndarray, shape (nz, M)
        Irregular depths for each column.
    data_sec : ndarray, shape (nz, M)
        Data at the given depths.
    depth_interval : float, optional
        Spacing for the target depth grid.

    Returns
    -------
    new_depth : ndarray, shape (K, M)
        Shared regular depth grid replicated across columns.
    data_out : ndarray, shape (K, M)
        Interpolated data on new_depth.
    """
    depth_sec = np.asarray(depth_sec, dtype=float)
    data_sec  = np.asarray(data_sec,  dtype=float)
    if depth_sec.shape != data_sec.shape:
        raise ValueError("depth_sec and data_sec must have the same shape (nz, M).")

    # Global min and max across the entire array
    global_min = np.nanmin(depth_sec)
    global_max = np.nanmax(depth_sec)
    if not np.isfinite(global_min) or not np.isfinite(global_max) or global_max <= global_min:
        raise ValueError("Invalid global depth bounds for target grid.")

    # Build shared target grid
    z1d = np.arange(global_min, global_max + 1e-12, float(depth_interval))
    K, M = z1d.size, depth_sec.shape[1]

    # Interpolate each column without extrapolation
    data_out = np.full((K, M), np.nan, dtype=float)
    for m in range(M):
        d = depth_sec[:, m]
        v = data_sec[:, m]
        mask = np.isfinite(d) & np.isfinite(v)
        d = d[mask]
        v = v[mask]
        if d.size < 2:
            continue
        col = np.interp(z1d, d, v)
        col[(z1d < d[0]) | (z1d > d[-1])] = np.nan
        data_out[:, m] = col

    # Depth grid replicated to (K, M)
    new_depth = np.tile(z1d[:, None], (1, M))
    return new_depth, data_out




def import_section(path, file_name, var, lon_min, lon_max, lat_min, lat_max, M, depth_interval):
    """
    Import a vertical section from a file. Support all kind of section: along lat, along lon, and diagonal line. 
    This is the control for the whole function

    Parameters
    ----------
    path : str
        Path to file. This path should contain the grid.nc as well
    file_name : str
        Name of the file
    var : str
        Name of the variable
    lon_min, lon_max, lat_min, lat_max : float    
        limit of the line: if lon_min = lon_max, it will understand it as a line along the longitude, and vice versa. 
    M: int
        the number of point in the section following its direction from A to B
    depth_interval: float
        the interval of Z. 

    Returns
    -------
    new_depth : ndarray, shape (K, M)
        Shared regular depth grid replicated across columns.
    data_out : ndarray, shape (K, M)
        Interpolated data on new_depth.
    """

    # Open the grid file to determine depth dimensions
    grid = ''.join(glob.glob(path + '/grid.nc'))
    fgrid = Dataset(grid, 'r')
    try:
        lat_t = fgrid.variables['latitude_%s' % (var[-1])][:]
        lon_t = fgrid.variables['longitude_%s' % (var[-1])][:]
        depth_t = fgrid.variables['depth_%s' % (var[-1])][:]
    except KeyError:
        print('Could not find a grid suffix for %s. Using _t as default.' % (var))
        lat_t = fgrid.variables['latitude_t'][:]
        lon_t = fgrid.variables['longitude_t'][:]
        depth_t = fgrid.variables['depth_t'][:]
    
    nc_file = Dataset(path + file_name, 'r')
    data = np.squeeze(nc_file.variables[var][:])


    # Setup the section
    if (lon_min == lon_max):
        if lat_min == lat_max:  
            print ('lon_min = lon_max and lat_min = lat_max. Not a section. Exiting...' )
            exit()
        else:
            lon_sec = np.full(M, lon_max)
            lat_sec = np.linspace(lat_min, lat_max, M) 
    elif lat_min == lat_max:
            lat_sec = np.full(M, lat_max)
            lon_sec = np.linspace(lon_min, lon_max, M) 
    else:
        lat_sec = np.linspace(lat_min, lat_max, M)      # lat section
        lon_sec = np.linspace(lon_min, lon_max, M)      # lon_section

    depth_sec, apply_interp = section_extract(lat_t, lon_t, depth_t, lat_sec, lon_sec, method="bilinear")

    #interpolate data
    data_interpolation = apply_interp(data) # shape: (nz, M)

    #interpolate depth and data into 1m for better representation
    depth_out, data_out = data_interp(depth_sec, data_interpolation, depth_interval=depth_interval)

    return depth_out, data_out











