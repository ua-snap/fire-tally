# pylint: disable=C0103,E0401
"""
Template for SNAP Dash apps.
"""

import os
from datetime import datetime
import statsmodels.api as sm
import dash
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import luts
from gui import layout
import pandas as pd
import numpy as np

import ssl

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
    TALLY_DATA_URL = "./data/test-areas.csv"  # for local development
else:
    # in production, load from live URL
    # Probably here: https://fire.ak.blm.gov/content/aicc/Statistics%20Directory/Alaska%20Daily%20Stats%20by%20Protection-2004%20to%20Present.csv
    TALLY_DATA_URL = os.environ["TALLY_DATA_URL"]

# TODO I think this is unused, can remove during further review?
date_ranges = [91, 121, 152, 182, 213, 244]
date_names = list(
    map(lambda x: datetime.strptime(str(x), "%j").strftime("%B"), date_ranges)
)

# Perform basic data pre-processing
raw_data = pd.read_csv(TALLY_DATA_URL, parse_dates=True)

df = raw_data
df = df.drop(columns=["ID", "Month", "Day", "NewFires", "OutFires", "ActiveFires", "TotalFires", "PrepLevel", "StaffedFires"])
df = df.loc[(df["FireSeason"] >= 2004)]

# Generate a synthetic datetime field,
# with all the same year.  This lets us
# give Plotly the x-axis as a date.
def collapse_year(date):
    try:
        d = datetime.strptime(str(date), "%Y%m%d")
        d = d.replace(year=2020)
    except:
        # Invalid date, return a null to be dropped
        print("Invalid date found", date)
        d = np.NaN

    return d

df = df.assign(
    date_stacked=pd.to_datetime(
        df["SitReportDate"].apply(collapse_year)
    )
)
df = df.dropna()
df = df.drop(columns=["SitReportDate"])

# Create day-of-year column for easy slicing
df = df.assign(
    doy=df["date_stacked"].dt.strftime("%j").astype("int")
)

# A few more fields/flags
data_start_doy = 92  # April 1
apply_loess = False  # This filter can fail unless it has enough data values.

app = dash.Dash(__name__)

# AWS Elastic Beanstalk looks for application by default,
# if this variable (application) isn't set you will get a WSGI error.
application = app.server

# Customize this layout to include Google Analytics
gtag_id = os.environ["GTAG_ID"]
app.index_string = f"""
<!DOCTYPE html>
<html>
    <head>
        <!-- Global site tag (gtag.js) - Google Analytics -->
        <script async src="https://www.googletagmanager.com/gtag/js?id={gtag_id}"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){{dataLayer.push(arguments);}}
          gtag('js', new Date());

          gtag('config', '{gtag_id}');
        </script>
        {{%metas%}}
        <title>{{%title%}}</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">

        <!-- Schema.org markup for Google+ -->
        <meta itemprop="name" content="{luts.title}">
        <meta itemprop="description" content="{luts.description}">
        <meta itemprop="image" content="{luts.preview}">

        <!-- Twitter Card data -->
        <meta name="twitter:card" content="summary_large_image">
        <meta name="twitter:site" content="@SNAPandACCAP">
        <meta name="twitter:title" content="{luts.title}">
        <meta name="twitter:description" content="{luts.description}">
        <meta name="twitter:creator" content="@SNAPandACCAP">
        <!-- Twitter summary card with large image must be at least 280x150px -->
        <meta name="twitter:image:src" content="{luts.preview}">

        <!-- Open Graph data -->
        <meta property="og:title" content="{luts.title}" />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="{luts.url}" />
        <meta property="og:image" content="{luts.preview}" />
        <meta property="og:description" content="{luts.description}" />
        <meta property="og:site_name" content="{luts.title}" />

        <link rel="alternate" hreflang="en" href="{luts.url}" />
        <link rel="canonical" href="{luts.url}"/>
        {{%favicon%}}
        {{%css%}}
    </head>
    <body>
        {{%app_entry%}}
        <footer>
            {{%config%}}
            {{%scripts%}}
            {{%renderer%}}
        </footer>
    </body>
</html>
"""

app.title = luts.title
app.layout = layout


@app.callback(Output("tally", "figure"), [Input("area", "value")])
def update_tally(area):
    """ Generate daily tally count """

    # Slice for April 1 (Day 92) - today.  Show 45 days minimum.
    # TODO -- lines below are commented out for intial work,
    # but, we do need to be determining how this should work.
    # today_doy = int(datetime.now().strftime("%j"))
    # end_doy = today_doy if (today_doy - data_start_doy) >= 45 else data_start_doy + 45

    # Spatial clip
    if area == "ALL":
        de = df.groupby(["FireSeason", "doy", "date_stacked"]).sum().reset_index()
        print(de)
    else:
        de = df.loc[
            (de["ProtectionUnit"] == area)
        ]

    data_traces = []
    grouped = de.groupby("FireSeason")
    for name, group in grouped:
        group = group.sort_values(["date_stacked"])

        # If there's enough data points, smooth with LOESS.
        # We don't quite know the full criteria for this, so leave the
        # code in place but bypass for the moment.
        # TODO resolve how/when this is used.
        # Apply LOESS filter to smooth the data.
        # https://www.statsmodels.org/dev/generated/statsmodels.nonparametric.smoothers_lowess.lowess.html
        acres = group.TotalAcres
        if apply_loess:
            group = group.assign(
                SmoothedTotalAcres=sm.nonparametric.lowess(
                    group.TotalAcres,
                    group.date_stacked,
                    return_sorted=False,
                    frac=0.05,
                    it=1,
                    delta=3,
                )
            )
            # Handle some odd values that showed up in raw data.
            group["SmoothedTotalAcres"] = group["SmoothedTotalAcres"].apply(
                lambda x: x if x >= 0 else 0
            )
            acres = group.SmoothedTotalAcres


        # Only put high-fire years in the legend.
        if name in luts.important_years:
            hoverinfo = ""
            showlegend = True
        else:
            hoverinfo = "skip"
            showlegend = False

        data_traces.extend(
            [
                {
                    "x": group.date_stacked,
                    "y": acres,
                    "mode": "lines",
                    "name": str(name),
                    "line": {
                        "color": luts.years_lines_styles[str(name)]["color"],
                        # "shape": "spline",
                        # ^ TODO determine if/when to restore this,
                        # after figuring out the LOESS stuff.
                        # It can either look much better or much
                        # worse depending on the shape of the data.
                        "width": luts.years_lines_styles[str(name)]["width"],
                    },
                    "showlegend": showlegend,
                    "hoverinfo": hoverinfo,
                }
            ]
        )

    # Add dummy trace with legend entry for non-big years
    data_traces.extend(
        [
            go.Scatter(
                x=[None],
                y=[None],
                mode="lines",
                name="Other years",
                line={
                    "color": luts.default_style["color"],
                    "width": luts.default_style["width"],
                },
            )
        ]
    )

    graph_layout = go.Layout(
        title="Daily Tally Records, 2004-Present",
        showlegend=True,
        legend={"font": {"family": "Open Sans", "size": 10}},
        xaxis=dict(
            title="Date",
            tickformat="%B %d"
        ),
        yaxis={"title": "Acres burned", "hoverformat": ".3s"},
        height=650,
        margin={"l": 50, "r": 50, "b": 50, "t": 50, "pad": 4},
    )
    return {"data": data_traces, "layout": graph_layout}


if __name__ == "__main__":
    application.run(debug=os.environ["FLASK_DEBUG"], port=8080)
