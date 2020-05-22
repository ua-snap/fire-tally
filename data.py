"""

Perform data pre-processing for the web app.

"""
# pylint: disable=C0103,C0301,E0401

import os
import ssl
from datetime import datetime
import numpy as np
import pandas as pd

# Bypass SSL certification check for the AICC server
# Remove if/when they address that configuration
# TODO -- verify if this is still needed after AICC update
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context

if "FLASK_DEBUG" in os.environ and os.environ["FLASK_DEBUG"] == "True":
    # TODO add logging
    print("Using debug mode.")  # keep until logging implemented
    TALLY_DATA_URL = "./data/test.csv"  # for local development
    TALLY_DATA_ZONES_URL = "./data/test-areas.csv"  # for local development
else:
    # in production, load from live URL
    # Probably this: https://fire.ak.blm.gov/content/aicc/Statistics%20Directory/Alaska%20Daily%20Stats%20-%202004%20to%20Present.csv
    TALLY_DATA_URL = os.environ["TALLY_DATA_URL"]
    # Probably this: https://fire.ak.blm.gov/content/aicc/Statistics%20Directory/Alaska%20Daily%20Stats%20by%20Protection-2004%20to%20Present.csv
    TALLY_DATA_ZONES_URL = os.environ["TALLY_DATA_ZONES_URL"]


def collapse_year(date):
    """
    Generate a synthetic datetime field,
    with all the same year.  This lets us
    give Plotly the x-axis as a date.
    """

    try:
        d = datetime.strptime(str(date), "%Y%m%d")
        d = d.replace(year=2020)
    except:
        # Invalid date, return a null to be dropped
        print("Invalid date found", date)
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

    df = df.dropna()
    df = df.drop(columns=["SitReportDate"])

    # Create day-of-year column for easy slicing
    df = df.assign(doy=df["date_stacked"].dt.strftime("%j").astype("int"))
    return df


# Ready & preprocess data
# TODO make this more resiliant when network exceptions occur
# TODO add logging
# TODO ensure this runs on a schedule in a long-running flask loop
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
        "Active Fires",
        "Staffed Fires",
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
        "PrepLevel",
        "StaffedFires",
    ]
)
tally_zone = preprocess_data(tally_zone_raw)

# Compute what years are available in the tally zone file.
tally_zone_date_ranges = tally_zone.FireSeason.unique()