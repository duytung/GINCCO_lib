import os
import glob
import sys
from datetime import datetime, timedelta

import numpy as np
from netCDF4 import Dataset 

#############################
'''
This module usse to import files.

List of functions: 
* build_file_list: Build a list of NetCDF file paths between two dates.
* import_4D: import 3D file in time series (so it is 4D in output)
* import_3D: import 2D file in time series (3D in output)
* import_layer: import a layer of 3D file in time series (3D in output)
* import_surface: import the surface layer of 3D file in time series (3D in output)
* import_depth: import data at the specified depth from an 3D file in time series (3D in output)


Features: 
* Automatically load the correct grid indice (_u, _v, _w, ...)
* For multiple file, it will check if all the file is available or not, before really load the file to avoid crash in the middle. 
* You can choose to stop the script if any file is missing, or fill the data on that date with nan value

'''
#############################




def build_file_list(path, tstart, tend):
    """
    Build a list of NetCDF file paths between two dates.

    Parameters
    ----------
    path : str
        Directory containing the NetCDF files.
    tstart : datetime
        Start date (inclusive).
    tend : datetime
        End date (inclusive).

    Returns
    -------
    list of str
        A list of file paths, one entry per day between tstart and tend.
        - If a file exists, the full path is included.
        - If a file is missing, the entry is an empty string "".

    Raises
    ------
    FileNotFoundError
        If the first file cannot be found for tstart.
    RuntimeError
        If the filename does not contain the expected date string.
    """

    # Step 1: locate the first file to extract the filename pattern
    first_pattern = path + tstart.strftime("%Y%m%d") + "*"
    hits = glob.glob(first_pattern)
    if len(hits) == 0:
        raise FileNotFoundError(f"No file found for {tstart.strftime('%Y%m%d')} in {path}")

    # Step 2: extract prefix and suffix from the first file
    first_file = os.path.basename(hits[0])
    date_str = tstart.strftime("%Y%m%d")
    try:
        prefix, suffix = first_file.split(date_str, 1)
    except ValueError:
        raise RuntimeError(f"Cannot split date string {date_str} from filename {first_file}")

    # Step 3: generate the file list for each day
    flist = []
    t = tstart
    while t <= tend:
        fname = prefix + t.strftime("%Y%m%d") + suffix
        fpath = os.path.join(path, fname)

        # If file exists, add it; otherwise, append an empty string
        if os.path.exists(fpath):
            flist.append(fpath)
        else:
            print(f"Missing file for {t.strftime('%Y-%m-%d')}: {fpath}")
            flist.append("")  # keep the position consistent with date

        t += timedelta(days=1)

    return flist



#############################



def import_4D(path, var, tstart, tend, ignore_missing='False'):
    """
    Import a 4D variable from a sequence of daily NetCDF files.

    Parameters
    ----------
    path : str
        Directory containing the NetCDF files.
    var : str
        Variable name to read from each file (e.g., 'veloc_u_t').
    tstart : datetime
        Start date (inclusive).
    tend : datetime
        End date (inclusive).
    ignore_missing : str, optional
        If 'False' (default), the function exits when a file is missing.
        If 'True', missing days are allowed and filled with NaN.

    Returns
    -------
    numpy.ndarray
        A 4D array with shape (ntime, nz, ny, nx), dtype float64.
        Missing files are represented with NaN values.
    """

    duration = tend - tstart

    # Build the file list (length always equals number of days between tstart and tend).
    # Missing files are represented as empty strings "".
    file_list = build_file_list(path, tstart, tend)

    # If ignore_missing is 'False' and at least one file is missing → stop execution.
    if ignore_missing == 'False':
        if "" in file_list:
            sys.exit(1)

    # Open the grid file to determine depth dimensions
    grid = ''.join(glob.glob(path + 'grid.nc'))
    fgrid = Dataset(grid, 'r')
    try:
        mask_t = fgrid.variables['mask_%s' % (var[-1])][:]
    except KeyError:
        print('Could not find a grid suffix for %s. Using _t as default.' % (var))
        mask_t = fgrid.variables['mask_t'][:]

    # Prepare output array filled with zeros
    # Shape: [time, depth_z, depth_y, depth_x]
    print('Processing path: %s at %s' % (path, datetime.now()))
    data_array = np.zeros(
        (duration.days + 1, np.size(mask_t, 0), np.size(mask_t, 1), np.size(mask_t, 2)),
        dtype='float64'
    )

    # Loop through all files in the list
    for i, fpath in enumerate(file_list):
        tnow = tstart + timedelta(days=i)

        # Print the filename on the first day of each month (if available)
        if tnow.day == 1:
            if fpath:
                print(fpath)

        # If the file exists, read the variable into the output array
        if fpath:
            file1 = Dataset(fpath, 'r')   # fixed: previously 'ncfile'
            data_array[i, :, :, :] = np.squeeze(file1.variables[var][:, :, :, :]).filled(np.nan)
        # If the file is missing, fill with NaN values
        if not fpath:
            print(('File not found for:', str(tnow)), 'Missing values will be filled with NaN')
            data_array[i, :, :, :] = np.nan

    print('Import completed.')
    return data_array


#############################



def import_3D(path, var, tstart, tend, ignore_missing='False'):
    """
    Import a 3D variable from a sequence of daily NetCDF files.

    Parameters
    ----------
    path : str
        Directory containing the NetCDF files.
    var : str
        Variable name to read from each file (e.g., 'veloc_u_t').
    tstart : datetime
        Start date (inclusive).
    tend : datetime
        End date (inclusive).
    ignore_missing : str, optional
        If 'False' (default), the function exits when a file is missing.
        If 'True', missing days are allowed and filled with NaN.

    Returns
    -------
    numpy.ndarray
        A 3D surface array with shape (ntime, ny, nx), dtype float64.
        Missing files are represented with NaN values.
    """

    duration = tend - tstart

    # Build the file list (length always equals number of days between tstart and tend).
    # Missing files are represented as empty strings "".
    file_list = build_file_list(path, tstart, tend)

    # If ignore_missing is 'False' and at least one file is missing → stop execution.
    if ignore_missing == 'False':
        if "" in file_list:
            sys.exit(1)

    # Open the grid file to determine depth dimensions
    grid = ''.join(glob.glob(path + 'grid.nc'))
    fgrid = Dataset(grid, 'r')
    try:
        mask_t = fgrid.variables['mask_%s' % (var[-1])][:]
    except KeyError:
        print('Could not find a grid suffix for %s. Using _t as default.' % (var))
        mask_t = fgrid.variables['mask_t'][:]

    # Prepare output array filled with zeros
    # Shape: [time, depth_y, depth_x]
    print('Processing path: %s at %s' % (path, datetime.now()))
    data_array = np.zeros(
        (duration.days + 1, np.size(mask_t, 1), np.size(mask_t, 2)),
        dtype='float64'
    )

    # Loop through all files in the list
    for i, fpath in enumerate(file_list):
        tnow = tstart + timedelta(days=i)

        # Print the filename on the first day of each month (if available)
        if tnow.day == 1:
            if fpath:
                print(fpath)

        # If the file exists, read the variable into the output array
        if fpath:
            file1 = Dataset(fpath, 'r')   # fixed: previously 'ncfile'
            data_array[i, :, :] = np.squeeze(file1.variables[var][ :, :, :]).filled(np.nan)
            


        # If the file is missing, fill with NaN values
        if not fpath:
            print(('File not found for:', str(tnow)), 'Missing values will be filled with NaN')
            data_array[i, :, :] = np.nan

    print('Import completed.')
    return data_array


#############################


def import_surface(path, var, tstart, tend, ignore_missing='False'):
    """
    Import a surface variable from a sequence of daily NetCDF files.

    Parameters
    ----------
    path : str
        Directory containing the NetCDF files.
    var : str
        Variable name to read from each file (e.g., 'veloc_u_t').
    tstart : datetime
        Start date (inclusive).
    tend : datetime
        End date (inclusive).
    ignore_missing : str, optional
        If 'False' (default), the function exits when a file is missing.
        If 'True', missing days are allowed and filled with NaN.

    Returns
    -------
    numpy.ndarray
        A 3D array with shape (ntime, ny, nx), dtype float64.
        Missing files are represented with NaN values.
    """

    duration = tend - tstart

    # Build the file list (length always equals number of days between tstart and tend).
    # Missing files are represented as empty strings "".
    file_list = build_file_list(path, tstart, tend)

    # If ignore_missing is 'False' and at least one file is missing → stop execution.
    if ignore_missing == 'False':
        if "" in file_list:
            sys.exit(1)

    # Open the grid file to determine depth dimensions
    grid = ''.join(glob.glob(path + 'grid.nc'))
    fgrid = Dataset(grid, 'r')
    try:
        mask_t = fgrid.variables['mask_%s' % (var[-1])][:]
    except KeyError:
        print('Could not find a grid suffix for %s. Using _t as default.' % (var))
        mask_t = fgrid.variables['mask_t'][:]

    # Prepare output array filled with zeros
    # Shape: [time, depth_z, depth_y, depth_x]
    print('Processing path: %s at %s' % (path, datetime.now()))
    data_array = np.zeros((duration.days + 1, np.size(mask_t, 1), np.size(mask_t, 2)), dtype='float64')

    # Loop through all files in the list
    for i, fpath in enumerate(file_list):
        tnow = tstart + timedelta(days=i)

        # Print the filename on the first day of each month (if available)
        if tnow.day == 1:
            if fpath:
                print(fpath)

        # If the file exists, read the variable into the output array
        if fpath:
            file1 = Dataset(fpath, 'r')   # fixed: previously 'ncfile'
            data_array[i, :, :] = np.squeeze(file1.variables[var][:, -1, :, :]).filled(np.nan)

        # If the file is missing, fill with NaN values
        if not fpath:
            print(('File not found for:', str(tnow)), 'Missing values will be filled with NaN')
            data_array[i, :, :] = np.nan

    print('Import completed.')
    return data_array


#############################



def import_layer(path, var, tstart, tend, layer, ignore_missing='False'):
    """
    Import a surface variable from a sequence of daily NetCDF files.

    Parameters
    ----------
    path : str
        Directory containing the NetCDF files.
    var : str
        Variable name to read from each file (e.g., 'veloc_u_t').
    tstart : datetime
        Start date (inclusive).
    tend : datetime
        End date (inclusive).
    layer: int
        The layer to import
    ignore_missing : str, optional
        If 'False' (default), the function exits when a file is missing.
        If 'True', missing days are allowed and filled with NaN.

    Returns
    -------
    numpy.ndarray
        A 3D array with shape (ntime, ny, nx), dtype float64.
        Missing files are represented with NaN values.
    """

    duration = tend - tstart

    # Build the file list (length always equals number of days between tstart and tend).
    # Missing files are represented as empty strings "".
    file_list = build_file_list(path, tstart, tend)

    # If ignore_missing is 'False' and at least one file is missing → stop execution.
    if ignore_missing == 'False':
        if "" in file_list:
            sys.exit(1)

    # Open the grid file to determine depth dimensions
    grid = ''.join(glob.glob(path + 'grid.nc'))
    fgrid = Dataset(grid, 'r')
    try:
        mask_t = fgrid.variables['mask_%s' % (var[-1])][:]
    except KeyError:
        print('Could not find a grid suffix for %s. Using _t as default.' % (var))
        mask_t = fgrid.variables['mask_t'][:]

    # Prepare output array filled with zeros
    # Shape: [time, depth_z, depth_y, depth_x]
    print('Processing path: %s at %s' % (path, datetime.now()))
    data_array = np.zeros((duration.days + 1, np.size(mask_t, 1), np.size(mask_t, 2)), dtype='float64')

    # Loop through all files in the list
    for i, fpath in enumerate(file_list):
        tnow = tstart + timedelta(days=i)

        # Print the filename on the first day of each month (if available)
        if tnow.day == 1:
            if fpath:
                print(fpath)

        # If the file exists, read the variable into the output array
        if fpath:
            file1 = Dataset(fpath, 'r')   # fixed: previously 'ncfile'
            data_array[i, :, :] = np.squeeze(file1.variables[var][:, layer, :, :]).filled(np.nan)

        # If the file is missing, fill with NaN values
        if not fpath:
            print(('File not found for:', str(tnow)), 'Missing values will be filled with NaN')
            data_array[i, :, :] = nan

    print('Import completed.')
    return data_array



#############################




def import_depth(path, var, tstart, tend, depth, ignore_missing='False'):
    """
    Import a variable in specified depth from daily NetCDF files.

    Parameters
    ----------
    path : str
        Directory containing the NetCDF files.
    var : str
        Variable name to read from each file (e.g., 'veloc_u_t').
    tstart : datetime
        Start date (inclusive).
    tend : datetime
        End date (inclusive).
    depth: float
        The depth to import
    ignore_missing : str, optional
        If 'False' (default), the function exits when a file is missing.
        If 'True', missing days are allowed and filled with NaN.

    Returns
    -------
    numpy.ndarray
        A 3D array with shape (ntime, ny, nx), dtype float64.
        Missing files are represented with NaN values.
    """

    duration = tend - tstart

    # Build the file list (length always equals number of days between tstart and tend).
    # Missing files are represented as empty strings "".
    file_list = build_file_list(path, tstart, tend)

    # If ignore_missing is 'False' and at least one file is missing → stop execution.
    if ignore_missing == 'False':
        if "" in file_list:
            sys.exit(1)

    # Open the grid file to determine depth dimensions
    grid = ''.join(glob.glob(path + 'grid.nc'))
    fgrid = Dataset(grid, 'r')
    try:
        depth_t = fgrid.variables['depth_%s' % (var[-1])][:]
        mask_ = fgrid.variables['mask_%s' % (var[-1])][:]
    except KeyError:
        print('Could not find a grid suffix for %s. Using _t as default.' % (var))
        depth_t = fgrid.variables['depth_t'][:]
        mask_ = fgrid.variables['mask_t'][:]

    if mask_.ndim == 3:
        mask_t = mask_[0, :, :]
    elif mask_.ndim == 2:
        mask_t = np.copy(mask_)



    print (depth_t.shape, mask_t.shape)

    # Prepare multiply array
    if depth > 0:
        depth = depth * -1
        
    # Find the indice of the min and max
    # For example, the interest depth = 5, => -5 . the depth of two layer is -3 and -10. 
    
    toto= np.ma.masked_where(depth_t>depth, depth_t)
    max_array= np.argmax(toto, axis=0) #because it is negative number, so it will return the nearest layer < depth (-10)
    toto= np.ma.masked_where(depth_t<depth, depth_t)
    min_array= np.argmin(toto, axis=0) #because it is negative number, so it will return the nearest layer > depth (-3)
    
    # Calculate the multiply factor:
    multiply_array=np.zeros((np.size(depth_t,0),np.size(depth_t,1),np.size(depth_t,2)),dtype='float64')
    for i in range(0, np.size(depth_t,1)):
        for j in range(0, np.size(depth_t,2)):
            if min_array[i,j] != max_array[i,j]:  #only take into account the point that have min and max indice
                dis_tance = depth_t[max_array[i,j],i,j]-depth_t[min_array[i,j],i,j] 
                multiply_array[max_array[i,j],i,j] = 1 +  (depth-depth_t[max_array[i,j],i,j])/dis_tance  #1+ -5/7 
                multiply_array[min_array[i,j],i,j] = 1 -  (depth-depth_t[min_array[i,j],i,j])/dis_tance  #1- 2/7
    
    #print ('Multiply array', multiply_array[:,200,200])

    check_depth_array=np.zeros((  np.size(depth_t,1), np.size(depth_t,2)     ),dtype='float64')
    for i in range(0, np.size(depth_t,1)):
        for j in range(0, np.size(depth_t,2)):
            if min_array[i,j]!=max_array[i,j]:  #only take into account the point that have min and max indice
                check_depth_array[i,j]=1




    # Prepare output array filled with zeros
    # Shape: [time, depth_z, depth_y, depth_x]
    print('Processing path: %s at %s' % (path, datetime.now()))
    data_array = np.zeros((duration.days + 1, np.size(depth_t, 1), np.size(depth_t, 2)), dtype='float64')

    # Loop through all files in the list
    for i, fpath in enumerate(file_list):
        tnow = tstart + timedelta(days=i)

        # Print the filename on the first day of each month (if available)
        if tnow.day == 1:
            if fpath:
                print(fpath)

        # If the file exists, read the variable into the output array
        if fpath:
            file1 = Dataset(fpath, 'r')   # fixed: previously 'ncfile'
            data_toto = np.squeeze(file1.variables[var][:,:,:,:]).filled(np.nan)

            print ('before calculate depth', data_toto[0,-1,:])
            print (data_toto[0,:,-1])
            
            data_toto2 = np.nansum(data_toto * multiply_array, axis=0)
            
            print ('after calculate depth', data_toto2[-1,:])
            print (data_toto2[:,-1])
            

            data_toto2[check_depth_array==0] = np.nan
            data_toto2[mask_t==0] = np.nan # mask land - sea value
            data_array[i,:,:] = np.copy(data_toto2)

        # If the file is missing, fill with NaN values
        if not fpath:
            print(('File not found for:', str(tnow)), 'Missing values will be filled with NaN')
            data_array[i, :, :] = nan

    print('Import completed.')
    return data_array




#############################
def find_nearest_index_haversine(lat, lon, lat_p, lon_p):
    """
    Find the index (i, j) of the nearest grid point in 2D arrays `lat` and `lon`
    to a given target coordinate (lat_p, lon_p) using great-circle (Haversine) distance.

    Parameters
    ----------
    lat : np.ndarray
        2D array of latitude values (degrees).
    lon : np.ndarray
        2D array of longitude values (degrees).
    lat_p : float
        Target latitude (degrees).
    lon_p : float
        Target longitude (degrees).

    Returns
    -------
    tuple
        (i, j) index of the nearest grid point.
    """
    # Convert degrees to radians
    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    lat_p_rad = np.radians(lat_p)
    lon_p_rad = np.radians(lon_p)

    # Haversine formula
    dlat = lat_rad - lat_p_rad
    dlon = lon_rad - lon_p_rad
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat_p_rad) * np.cos(lat_rad) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.sqrt(a))

    # Earth's radius (km) – absolute value of distance is enough for comparison
    dist = 6371.0 * c  

    # Find index of minimum distance
    idx_flat = np.argmin(dist)
    i, j = np.unravel_index(idx_flat, lat.shape)

    return i, j




def import_point(path, var, tstart, tend, lat_j, lon_i, ji = 'False', level = -1, ignore_missing='False'):
    """
    Import a data point from a variable of daily NetCDF files.

    Parameters
    ----------
    path : str
        Directory containing the NetCDF files.
    var : str
        Variable name to read from each file (e.g., 'veloc_u_t').
    tstart : datetime
        Start date (inclusive).
    tend : datetime
        End date (inclusive).
    lat_j : float or int
        Latitude or j to import
    lon_j : float or int
        Longitude or i to import
    ji : str, optional
        If 'False' (default), the function will find i and j based on lat and lon provided
        If 'True', the function will use i and j directly to import
    level : int, optinal
        level that we want to import. Only support for 3D field. Default is surface layer
    ignore_missing : str, optional
        If 'False' (default), the function exits when a file is missing.
        If 'True', missing days are allowed and filled with NaN.

    Returns
    -------
    numpy.ndarray
        A 3D array with shape (ntime, ny, nx), dtype float64.
        Missing files are represented with NaN values.
    """

    duration = tend - tstart

    # Build the file list (length always equals number of days between tstart and tend).
    # Missing files are represented as empty strings "".
    file_list = build_file_list(path, tstart, tend)

    # If ignore_missing is 'False' and at least one file is missing → stop execution.
    if ignore_missing == 'False':
        if "" in file_list:
            sys.exit(1)

    # Open the grid file to determine depth dimensions
    grid = ''.join(glob.glob(path + 'grid.nc'))
    fgrid = Dataset(grid, 'r')
    try:
        lat_t = fgrid.variables['latitude_%s' % (var[-1])][:]
        lon_t = fgrid.variables['longitude_%s' % (var[-1])][:]
    except KeyError:
        print('Could not find a grid suffix for %s. Using _t as default.' % (var))
        lat_t = fgrid.variables['latitude_t'][:]
        lon_t = fgrid.variables['longitude_t'][:]




    # Prepare output array filled with zeros
    # Shape: [time, depth_z, depth_y, depth_x]
    print('Processing path: %s at %s' % (path, datetime.now()))
    data_array = np.zeros((duration.days + 1), dtype='float64')
    kount_print=0
    # Loop through all files in the list
    for i, fpath in enumerate(file_list):
        tnow = tstart + timedelta(days=i)

        # Print the filename on the first day of each month (if available)
        if tnow.day == 1:
            if fpath:
                print(fpath)

        # If the file exists, read the variable into the output array
        if fpath:
            file1 = Dataset(fpath, 'r')   # fixed: previously 'ncfile'

            # Check if data is 2D or 3D
            kount = 0
            if kount ==0: 
                data_toto = np.squeeze(file1.variables[var][:])
                data_dim = data_toto.ndim
                kount+=1

            # Case 1: load 2D var:
            if data_dim ==2:
                if ji == 'True':
                    data_array[i] = np.squeeze(file1.variables[var][:, j, i])
                else:
                    j_ind, i_ind = find_nearest_index_haversine(lat_t, lon_t, lat_j, lon_i)
                    if kount_print ==0:
                        print ('Original location and nearest point location')
                        print ('Lat', lat_j, lat_t[j_ind, i_ind])
                        print ('Lon', lon_i, lon_t[j_ind, i_ind])
                        kount_print+=1
                    data_array[i] = np.squeeze(file1.variables[var][:, j_ind, i_ind])

            # Case 2: load 3D var
            elif data_dim ==3:
                if ji == 'True':
                    data_array[i] = np.squeeze(file1.variables[var][:, level, j, i])
                else:
                    j_ind, i_ind = find_nearest_index_haversine(lat_t, lon_t, lat_j, lon_i)
                    if kount_print ==0:
                        print ('Lat', lat_j, 'Nearest point', lat_t[j_ind, i_ind])
                        print ('Lon', lon_i, 'Nearest point', lon_t[j_ind, i_ind])
                        kount_print +=1
                    data_array[i] = np.squeeze(file1.variables[var][:, level, j_ind, i_ind])

        # If the file is missing, fill with NaN values
        if not fpath:
            print(('File not found for:', str(tnow)), 'Missing values will be filled with NaN')
            data_array[i] = nan

    print('Import completed.')
    return data_array



#############################



def import_profile(path, var, tstart, tend, lat_j, lon_i, ji = 'False', ignore_missing='False'):
    """
    Import a data point from a variable of daily NetCDF files.

    Parameters
    ----------
    path : str
        Directory containing the NetCDF files.
    var : str
        Variable name to read from each file (e.g., 'veloc_u_t').
    tstart : datetime
        Start date (inclusive).
    tend : datetime
        End date (inclusive).
    lat_j : float or int
        Latitude or j to import
    lon_j : float or int
        Longitude or i to import
    ji : str, optional
        If 'False' (default), the function will find i and j based on lat and lon provided
        If 'True', the function will use i and j directly to import
    level : int, optinal
        level that we want to import. Only support for 3D field. Default is surface layer
    ignore_missing : str, optional
        If 'False' (default), the function exits when a file is missing.
        If 'True', missing days are allowed and filled with NaN.

    Returns
    -------
    numpy.ndarray
        A 3D array with shape (ntime, ny, nx), dtype float64.
        Missing files are represented with NaN values.
    """

    duration = tend - tstart

    # Build the file list (length always equals number of days between tstart and tend).
    # Missing files are represented as empty strings "".
    file_list = build_file_list(path, tstart, tend)

    # If ignore_missing is 'False' and at least one file is missing → stop execution.
    if ignore_missing == 'False':
        if "" in file_list:
            sys.exit(1)

    # Open the grid file to determine depth dimensions
    grid = ''.join(glob.glob(path + 'grid.nc'))
    fgrid = Dataset(grid, 'r')
    try:
        lat_t = fgrid.variables['latitude_%s' % (var[-1])][:]
        lon_t = fgrid.variables['longitude_%s' % (var[-1])][:]
        depth_t = fgrid.variables['depth_%s' % (var[-1])][:]
    except KeyError:
        print('Could not find a grid suffix for %s. Using _t as default.' % (var))
        lon_t = fgrid.variables['longitude_t'][:]
        lat_t = fgrid.variables['latitude_t'][:]
        depth_t = fgrid.variables['depth_t'][:]


    # Prepare output array filled with zeros
    # Shape: [time, depth_z, depth_y, depth_x]
    print('Processing path: %s at %s' % (path, datetime.now()))
    data_array = np.zeros((duration.days + 1, np.size(depth_t,0)), dtype='float64')
    index = np.zeros((2))   # contain index
    kount_print=0
    # Loop through all files in the list
    for i, fpath in enumerate(file_list):
        tnow = tstart + timedelta(days=i)

        # Print the filename on the first day of each month (if available)
        if tnow.day == 1:
            if fpath:
                print(fpath)

        # If the file exists, read the variable into the output array
        if fpath:
            file1 = Dataset(fpath, 'r')   # fixed: previously 'ncfile'

            # Check if data is 2D or 3D
            kount = 0
            if kount ==0: 
                data_toto = np.squeeze(file1.variables[var][:])
                data_dim = data_toto.ndim
                kount+=1

            # Case 1: load 2D var:
            if data_dim ==2:
                print ('Data dimension = 2. Please check again...')
                exit()

            # Case 2: load 3D var
            elif data_dim ==3:
                if ji == 'True':
                    data_array[i] = np.squeeze(file1.variables[var][:, :, j, i])
                else:
                    j_ind, i_ind = find_nearest_index_haversine(lat_t, lon_t, lat_j, lon_i)
                    index[0] = j_ind
                    index[1] = i_ind
                    if kount_print ==0:
                        print ('Original location and nearest point location')
                        print ('Lat', lat_j, lat_t[j_ind, i_ind])
                        print ('Lon', lon_i, lon_t[j_ind, i_ind])
                        kount_print +=1
                    data_array[i,:] = np.squeeze(file1.variables[var][:, :, j_ind, i_ind])

        # If the file is missing, fill with NaN values
        if not fpath:
            print(('File not found for:', str(tnow)), 'Missing values will be filled with NaN')
            data_array[i] = nan

    print('Import completed.')
    return data_array, index















