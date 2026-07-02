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

# ---------------------------------------------------------------------------------------------------

def split_bufr(path, n_chunks, outdir):
    """
    Split a BUFR file into n_chunks files of (almost) equal message count.

    Splitting is useful to parallelize the decoding of large BUFR files: eccodes has no
    partial/lazy unpack, so the full message must be decoded before any key can be read,
    but the raw, still-undecoded messages are cheap to split.

    Args:
        path (str): Path to the input BUFR file.
        n_chunks (int): Number of chunk files to split the input into.
        outdir (str): Directory where the chunk files will be written.

    Returns:
        list of pathlib.Path: Paths to the chunk files, in message order.
    """

    from pathlib import Path
    import eccodes

    outdir = Path(outdir)

    with open(path, "rb") as fin:
        n_total = 0
        while eccodes.codes_bufr_new_from_file(fin) is not None:
            n_total += 1

    chunk_size = -(-n_total // n_chunks)  # ceil division
    chunk_paths = [outdir / f"chunk_{i:03d}.bufr" for i in range(n_chunks)]
    chunk_files = [open(p, "wb") for p in chunk_paths]

    with open(path, "rb") as fin:
        i = 0
        while True:
            msg = eccodes.codes_bufr_new_from_file(fin)
            if msg is None:
                break
            chunk_files[min(i // chunk_size, n_chunks - 1)].write(eccodes.codes_get_message(msg))
            eccodes.codes_release(msg)
            i += 1

    for f in chunk_files:
        f.close()

    return chunk_paths

# ---------------------------------------------------------------------------------------------------

def read_bufr_chunk(path, columns, filters, reader="temp"):
    """
    Decode a single BUFR chunk file into a DataFrame using pdbufr (https://pdbufr.readthedocs.io/en/latest/).

    Meant to be run in a worker process by sond_decode_bufr, once per chunk file produced by split_bufr.

    Args:
        path (str or pathlib.Path): Path to the BUFR chunk file.
        columns (list of str): pdbufr columns to decode, see pdbufr.read_bufr.
        filters (dict): pdbufr filters to apply while decoding, see pdbufr.read_bufr.
        reader (str, optional): pdbufr reader name (default = "temp").

    Returns:
        pandas.DataFrame: Decoded BUFR data for this chunk.
    """

    import pdbufr

    return pdbufr.read_bufr(str(path), reader=reader, columns=columns,
                             geopotential='both', filters=filters)

# ---------------------------------------------------------------------------------------------------

def bufr_std_columns_set():
    """
    Standard set of pdbufr columns to decode from a TEMP sounding BUFR message.
    Documentation at https://pdbufr.readthedocs.io/en/latest/guide/readers/temp.html
    'time': datetime of sounding start
    'stnid': WMO station id code
    'latlon': latitude and longitude of station location
    'elevation': station eleveton above mean sea level.
    'plev_offset': all vertical measurements of pressure, temperature, dew-point temperature,
                    wind speed, wind direction.

    Returns:
        list of str: ["time", "stnid", "latlon", "elevation", "plev_offset"].
    """

    return ["time", "stnid", "latlon", "elevation", "plev_offset"]

# ---------------------------------------------------------------------------------------------------

def sond_decode_bufr(path, columns=None, filters=None, n_workers=8, reader="temp"):
    """

    Decode a BUFR sounding file into a DataFrame, parallelizing the decoding across
    worker processes.

    Decoding the BUFR data section is what makes pdbufr.read_bufr slow on large files.
    The file is first split into n_workers chunks without decoding (cheap, see
    split_bufr), then each chunk is decoded in its own process.

    Args:
        path (str): Path to the input BUFR file.
        columns (list of str): pdbufr columns to decode, see pdbufr.read_bufr.
        filters (dict): pdbufr filters to apply while decoding, see pdbufr.read_bufr.
        n_workers (int, optional): Number of worker processes (default = 8).
        reader (str, optional): pdbufr reader name (default = "temp").

    Returns:
        pandas.DataFrame: Decoded BUFR data, concatenated across all chunks.
    """

    import tempfile
    from pathlib import Path
    from functools import partial
    from concurrent.futures import ProcessPoolExecutor

    import pandas as pd

    if columns is None:
        columns = bufr_std_columns_set()

    with tempfile.TemporaryDirectory(dir=str(Path(path).parent)) as tmpdir:
        chunk_paths = split_bufr(path, n_workers, tmpdir)

        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            parts = list(executor.map(
                partial(read_bufr_chunk, columns=columns, filters=filters, reader=reader),
                chunk_paths
            ))

    return pd.concat(parts, ignore_index=True)

