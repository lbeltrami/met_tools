def extract_points_1D(da, var, time_var, locations, source = None):
    """
    Extract data values at specific coordinates from an xarray.DataArray
    e.g. a GRIB or NetCDF file that has been already opened with xarray.open_dataset.

    The label "1D" means that lat/lon coordinates are 1-dimensional arrays, instead of
    being 2-dimensional arrays (e.g. NetCDF usually report latitude as a 2D field 
    with dims (west_east, sout_north)).

    Handles both single-layer variables (e.g. surface or 2m fields, which reduce to a
    scalar after selecting lat/lon) and multi-layer variables that still carry a
    'generalVerticalLayer' dimension after selecting lat/lon (e.g. ICON native-level
    fields such as pressure, temperature, specific humidity). In the multi-layer case,
    one row per level is returned and the level index is stored in a 'generalVerticalLayer'
    column.

    Args:
        da (xarray.DataArray): a DataArray object with
                                dimensions 'latitude', 'longitude' and attribute 'time'.
        var (str): Name of the variable to extract. BE AWARE: it does not necessarly coincide with
                    the shortName. Use 'da.variables' to check the eccodes-like name of the variables.
        time_var (str): Name of the date_time variable in the DataArray.
        locations (dict): Dictionary with names and coordinates of locations of interest stored as:
                            {'Name1': {'lat'0 xx, 'lon': yy}, 'Name2': {'lat': xx, 'lon': yy}, ...}.
        source (str): String reporting what is the source of the data e.g.
                        'Model ...', 'Instrument ...'.

    Returns:
        pandas.DataFrame: a DataFrame long-structured with columns:
                            ['time', 'location', 'source', 'variable', 'value'] for single-layer
                            variables, plus a 'generalVerticalLayer' column for multi-layer variables.
    """

    import pandas as pd

    records = []

    da = da[var]

    time_val = pd.Timestamp(da[time_var].values)

    level_dim = "generalVerticalLayer"
    has_levels = level_dim in da.dims

    for name, coords in locations.items():

        point = da.sel(
            latitude=coords['lat'],
            longitude=coords['lon'],
            method='nearest'
        )

        if has_levels:
            for level in point[level_dim].values:
                value = point.sel(**{level_dim: level}).values.item()

                records.append({
                    'time': time_val,
                    'location': name,
                    'source': source,
                    'variable': var,
                    level_dim: int(level),
                    'value': value
                })
        else:
            value = point.values.item()

            records.append({
                'time': time_val,
                'location': name,
                'source': source,
                'variable': var,
                'value': value
            })

    return pd.DataFrame(records)



def extract_points_2D(ds, var, time_var, locations, source = None):
    """
    Extract data values at specific coordinates from an xarray.Dataset
    e.g. a NetCDF file that has been already opened with xarray.open_dataset.

    The label "2D" means that lat/lon coordinates are 2-dimensional arrays, e.g. 
    NetCDF usually report latitude as a 2D field with dims (west_east, sout_north).

    Args:
        ds (xarray.Dataset): Dataset with dims ['Time', 'south_north', 'west_east']. 
        locations (dict): Dictionary with names and coordinates of locations of interest stored as: 
                            {'Name1': {'lat'0 xx, 'lon': yy}, 'Name2': {'lat': xx, 'lon': yy}, ...}.
        var (str): Name of the variable to extract.
        time_var (str): Name of the date_time variable in the DataArray.
        source (str): String reporting what is the source of the data e.g. 
                        'Model ...', 'Instrument ...'.
    Returns:
        pandas.DataFrame: a DataFrame long-structured with columns: 
                            ['time', 'location', 'source', 'variable', 'value'].
    """
    
    import numpy as np
    import pandas as pd

    ds_lat = ds["lat"].values
    ds_lon = ds["lon"].values
    ds_times = ds[time_var].values
    
    data = ds[var]

    records = []

    for t_idx, tval in enumerate(ds_times):
        for name, coords in locations.items():

            target_lat = coords['lat']
            target_lon = coords['lon']

            dist_sq = (ds_lat - target_lat)**2 + (ds_lon - target_lon)**2
            i, j = np.unravel_index(np.argmin(dist_sq), dist_sq.shape)

            value = data.isel(**{"Time": t_idx, "south_north": i, "west_east": j}).values.item()

            records.append({
                'time': tval,
                'location': name,
                'source': source,
                'variable': var,
                'value': value
            })

    return pd.DataFrame(records)