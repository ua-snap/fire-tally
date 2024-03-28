"""

Perform data pre-processing for the web app.

"""

# pylint: disable=C0103,C0301,E0401

import os
import ssl
import traceback
import logging
from datetime import datetime
import numpy as np
import pandas as pd
from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options

DASH_LOG_LEVEL = os.getenv("DASH_LOG_LEVEL", default="info")
logging.basicConfig(level=getattr(logging, DASH_LOG_LEVEL.upper(), logging.INFO))

# Set up cache.
CACHE_EXPIRE = int(os.getenv("DASH_CACHE_EXPIRE", default="43200"))
logging.info("Cache expire set to %s seconds", CACHE_EXPIRE)
cache_opts = {"cache.type": "memory"}
cache = CacheManager(**parse_cache_config_options(cache_opts))
data_cache = cache.get_cache("api_data", type="memory", expire=CACHE_EXPIRE)


# Bypass SSL certification check for the AICC server
# Remove if/when they address that configuration
# TODO -- verify if this is still needed after AICC update,
# unfortunately still true as of 4/20
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context


if os.getenv("FLASK_DEBUG") == "True":
    logging.info("Using debug mode.")
    TALLY_DATA_URL = "./data/test.csv"  # for local development
    TALLY_DATA_ZONES_URL = "./data/test-areas.csv"  # for local development
else:
    # in production, load from live URL
    # Probably this: https://fire.ak.blm.gov/content/aicc/Statistics%20Directory/Alaska%20Daily%20Stats%20-%202004%20to%20Present.csv
    logging.info("Production mode.")
    TALLY_DATA_URL = os.getenv(
        "TALLY_DATA_URL",
        default="https://fire.ak.blm.gov/content/aicc/Statistics%20Directory/Alaska%20Daily%20Stats%20-%202004%20to%20Present.csv",
    )
    # Probably this: https://fire.ak.blm.gov/content/aicc/Statistics%20Directory/Alaska%20Daily%20Stats%20by%20Protection-2004%20to%20Present.csv
    TALLY_DATA_ZONES_URL = os.getenv(
        "TALLY_DATA_ZONES_URL",
        default="https://fire.ak.blm.gov/content/aicc/Statistics%20Directory/Alaska%20Daily%20Stats%20by%20Protection-2004%20to%20Present.csv",
    )


def collapse_year(date):
    """
    Generate a synthetic datetime field,
    with all the same year.  This lets us
    give Plotly the x-axis as a date.
    """

    try:
        d = datetime.strptime(str(date), "%Y%m%d")
        d = d.replace(year=2023)
    except ValueError:
        # Invalid date, return a null to be dropped
        logging.error("Invalid date found, %s", date)
        d = np.NaN

    return d


def preprocess_data(csv):
    """
    Perform basic data preprocessing,
    mostly the same regardless of if it's
    coming from the statewide or aggregate data.
    """
    df = csv
    df = df.loc[(df["FireSeason"] >= 2004)]
    df = df.assign(
        date_stacked=pd.to_datetime(df["SitReportDate"].apply(collapse_year))
    )
    # Removes any columns coming from unnamed CSV columns in the data
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]
    df = df.dropna()
    df = df.drop(columns=["SitReportDate"])

    # Create day-of-year column for easy slicing
    df = df.assign(doy=df["date_stacked"].dt.strftime("%j").astype("int"))
    df["TotalAcres"] = df["TotalAcres"].round(2)
    return df


def fetch_api_data():
    """
    Fetch data from API (or local dev CSV),
    then do some initial sculpting and pass
    to preprocessing.
    """
    logging.info("Updating data from upstream API...")
    try:
        tally_raw = pd.read_csv(TALLY_DATA_URL, parse_dates=True)
        tally_raw = tally_raw.drop(
            columns=[
                "ID",
                "Month",
                "Day",
                "TotalFires",
                "HumanFires",
                "HumanAcres",
                "LightningFires",
                "LightningAcres",
                "PrepLevel",
            ]
        )
        tally = preprocess_data(tally_raw)

        tally_zone_raw = pd.read_csv(TALLY_DATA_ZONES_URL, parse_dates=True)
        tally_zone_raw = tally_zone_raw.drop(
            columns=[
                "ID",
                "Month",
                "Day",
                "NewFires",
                "OutFires",
                "ActiveFires",
                "TotalFires",
            ]
        )
        tally_zone = preprocess_data(tally_zone_raw)

        # Compute what years are available in the tally zone file.
        tally_zone_date_ranges = sorted(tally_zone.FireSeason.unique())
        logging.info("...data updated successfully.")
        return (tally, tally_zone, tally_zone_date_ranges)

    except Exception as e:
        # There could be a number of different network-
        # or data-based errors, just ensure they're written
        # to stdout logging.
        logging.error(traceback.format_exc())


def fetch_data():
    """Check cache for data & fetch from API if not present"""
    return data_cache.get(key="api_data", createfunc=fetch_api_data)
