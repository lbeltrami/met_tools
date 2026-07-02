def sond_download_bufr(output_path, start, end, blo=16, sta=None):
    """
    Download radiosonde BUFR data from  SIMC-Arkimet (http://arkimet.metarpa:8090)
    using arki-query Bash function (https://arpa-simc.github.io/arkimet/)

    This function queries the Arkimet database and downloads BUFR-format
    radiosonde observations for Italian stations over a specified time period.
    An optional station filter can be applied using the last three digits
    of the WMO station ID.

    BE AWARE: the function requires arki-query to be installed and available in the system PATH.

    Parameters
    ----------
    output_path : str
        Path where the BUFR file will be saved.
    start : str
        Start date in YYYY-MM-DD format.
    end : str
        End date in YYYY-MM-DD format.
    blo : int or str, optional
        WMO block number (default = 16, which is Italy)
    sta : int or str or None, optional
        WMO station number. If None, all country's stations are taken.
    Returns
    -------
    None
    """

    import subprocess

    # validate station filter
    if sta is not None:
        if isinstance(sta, (int, str)):
            sta = str(sta)
            if not sta.isdigit():
                raise ValueError("sta must contain only digits (e.g. 144)")
        else:
            raise TypeError("sta must be int, str, or None")

    # compose the arki-query
    query = f"reftime:>={start},<={end}; proddef:GRIB:blo={blo}"
    if sta is not None:
        query += f",sta={sta}"

    # Run arki-query to download the BUFR data from Arkimet
    cmd = [
        "arki-query",
        "--data",
        "-o", output_path,
        query,
        "http://arkimet.metarpa:8090/dataset/gts_temp"
    ]

    subprocess.run(cmd, check=True)


