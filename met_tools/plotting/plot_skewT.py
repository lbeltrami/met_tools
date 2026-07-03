# accepted alternative names for each canonical column: the first match found is renamed
COLUMN_ALIASES = {
    "stnid": ["WMO station id", "WMO_station_id", "station", "location"],
    "time": ["datetime", "reftime"],
    "pressure": ["pres", "p"],
    "t": ["temperature"],
    "td": ["dewpoint", "dew_point"],
    "wind_speed": ["ws"],
    "wind_dir": ["wind_direction", "wd"],
}



def standardize_columns(sounding):
    """
    Rename known column aliases (e.g. 'pres' -> 'pressure', 'WMO station id' -> 'stnid')
    to the canonical names expected by the following plot_skewT function.

    Parameters
    ----------
    sounding : pandas.DataFrame
        Profile data with one row per vertical level.

    Returns
    -------
    pandas.DataFrame
        The same dataframe with canonical column names.

    Raises
    ------
    KeyError
        If a required column is missing under any known name.
    """

    rename = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        if canonical not in sounding.columns:
            for alias in aliases:
                if alias in sounding.columns:
                    rename[alias] = canonical
                    break

    sounding = sounding.rename(columns=rename)

    missing = [c for c in COLUMN_ALIASES if c not in sounding.columns]
    if missing:
        raise KeyError(f"Missing required column(s) {missing}: "
                       f"expected one of the names in {({c: COLUMN_ALIASES[c] for c in missing})}.")

    return sounding


def plot_skewT(sounding, out_png):
    """
    Plot a grid of SkewT-logP diagrams, one per (station, time) profile, and save it to file.

    Parameters
    ----------
    sounding : pandas.DataFrame
        Profile data with one row per vertical level and columns:
        'stnid', 'time', 'pressure' (Pa), 't' (K), 'td' (K),
        'wind_speed' (m/s), 'wind_dir' (deg).
        Known alternative column names (e.g. 'pres', 'WMO station id') are accepted too.
    out_png : str or pathlib.Path
        Path of the output PNG file.
    """

    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from metpy.plots import SkewT
    from metpy.units import units
    from metpy.calc import wind_components

    # map alternative column names to the canonical ones
    sounding = standardize_columns(sounding)

    # just to be sure, sort the sounding by station, datetime and pressure (descending)
    sounding = sounding.sort_values(["stnid", "time", "pressure"], ascending=[True, True, False])

    groups = list(sounding.groupby(["stnid", "time"]))
    n_plots = len(groups)
    if n_plots == 0:
        raise ValueError("No profiles found in the input dataframe.")
    n_cols = min(n_plots, max(1, int(np.round(np.sqrt(n_plots * 5 / 3)))))
    n_rows = int(np.ceil(n_plots / n_cols))
    fig = plt.figure(figsize=(3 * n_cols, 5 * n_rows))

    for i, ((wmo_id, dt), group) in enumerate(groups):

        skew = SkewT(fig, subplot=(n_rows, n_cols, i+1))

        # apply raw units to data
        pressure = group['pressure'].values * units.Pa
        temperature = group['t'].values * units.kelvin
        dewpoint = group['td'].values * units.kelvin
        wind_speed = group['wind_speed'].values * units('m/s')
        wind_dir = group['wind_dir'].values * units.degrees

        # convert units to the ones expected in a SkewT plot
        pressure = pressure.to(units.hPa)
        temperature = temperature.to(units.degC)
        dewpoint = dewpoint.to(units.degC)

        # calculate wind components for the barbs
        u, v = wind_components(wind_speed, wind_dir)

        # wind barbs are too dense and overlap each other: space them out
        df_barb = pd.DataFrame({'pressure': pressure.m, 'u': u.m, 'v': v.m})
        pressure_hpa = pressure.m
        pressure_hpa = pressure_hpa[~np.isnan(pressure_hpa)]
        bins = np.arange(pressure_hpa.min(), pressure_hpa.max() + 50, 50)
        df_barb['bin'] = pd.cut(df_barb['pressure'], bins)
        df_barb_mean = df_barb.groupby('bin', observed=True).mean()
        pressure_barb = df_barb_mean['pressure'].values * units.hPa
        u_barb = df_barb_mean['u'].values * units('m/s')
        v_barb = df_barb_mean['v'].values * units('m/s')

        # plot background grid: dry and moist adiabats
        skew.plot_dry_adiabats(linewidth=0.5)
        skew.plot_moist_adiabats(linewidth=0.5)

        # plot the profile and the wind barbs
        skew.plot(pressure, temperature, 'r', linewidth=1)
        skew.plot(pressure, dewpoint, 'g', linewidth=1)
        skew.plot_barbs(pressure_barb, u_barb, v_barb, length=5)

        skew.ax.set_title(f"{wmo_id} - {pd.to_datetime(dt):%Y-%m-%d %H UTC}")
        skew.ax.tick_params(axis='both', labelsize=7)

    plt.tight_layout()
    plt.savefig(out_png, dpi=300)
