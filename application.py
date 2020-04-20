# pylint: disable=C0103,C0301,E0401
"""
Template for SNAP Dash apps.
"""

import os
from datetime import datetime
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
        print("Invalid date found", date)  # keep until logging added
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

# A few more fields/flags
data_start_doy = 92  # April 1

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


def get_title_date_span(day_range):
    """ Helper to build the string fragment stating time span in titles. """
    return str(
        datetime.strptime(str(day_range[0]), "%j").strftime("%B %-d")
        + "—"
        + datetime.strptime(str(day_range[1]), "%j").strftime("%B %-d")
    )


def get_line_mode(day_range):
    """

    Returns "line" if day range is less than a
    certain threshold, otherwise "spline".  This
    prevents the charts from doing spline interpolation
    when heavily zoomed-in, which looks really bad.

    """
    if day_range[1] - day_range[0] > 90:
        return "spline"

    return "line"


@app.callback(Output("tally", "figure"), [Input("day_range", "value")])
def update_tally(day_range):
    """ Generate daily tally count """
    data_traces = []

    #  Slice by day range.
    sliced = tally.loc[(tally.doy >= day_range[0]) & (tally.doy <= day_range[1])]

    grouped = sliced.groupby("FireSeason")
    for name, group in grouped:
        group = group.sort_values(["date_stacked"])

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
                    "y": group.TotalAcres,
                    "mode": "lines",
                    "name": str(name),
                    "line": {
                        "color": luts.years_lines_styles[str(name)]["color"],
                        "shape": get_line_mode(day_range),
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
        title="<b>Alaska Statewide Daily Tally Records, 2004-Present,</b><br>"
        + get_title_date_span(day_range),
        showlegend=True,
        legend={"font": {"family": "Open Sans", "size": 10}},
        xaxis=dict(title="Date", tickformat="%B %-d"),
        # TODO hoverformat is giving weird numbers in some cases,
        # like "300m", what's up with that.
        # TODO yaxis needs to be smarter now that the date
        # ranges can be dynamic.
        yaxis={"title": "Acres burned (millions)", "hoverformat": ".3s"},
        height=650,
        margin={"l": 50, "r": 50, "b": 50, "t": 50, "pad": 4},
    )
    return {"data": data_traces, "layout": graph_layout}


@app.callback(
    Output("tally-zone", "figure"),
    [Input("area", "value"), Input("day_range_zone", "value")],
)
def update_tally_zone(area, day_range):
    """ Generate daily tally count for specified protection area """

    #  Slice by day range.
    sliced = tally_zone.loc[
        (tally_zone.doy >= day_range[0]) & (tally_zone.doy <= day_range[1])
    ]

    # Spatial clip
    if area == "ALL":
        de = sliced.groupby(["FireSeason", "doy", "date_stacked"]).sum().reset_index()
    else:
        de = sliced.loc[(sliced["ProtectionUnit"] == area)]

    data_traces = []
    grouped = de.groupby("FireSeason")
    for name, group in grouped:
        group = group.sort_values(["date_stacked"])

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
                    "y": group.TotalAcres,
                    "mode": "lines",
                    "name": name,
                    "line": {
                        "color": luts.years_lines_styles[str(name)]["color"],
                        "shape": get_line_mode(day_range),
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
        title="<b>Daily Tally Records, "
        + luts.zones[area]
        + ", 2004-Present</b><br>"
        + get_title_date_span(day_range),
        showlegend=True,
        legend={"font": {"family": "Open Sans", "size": 10}},
        xaxis=dict(title="Date", tickformat="%B %-d"),
        yaxis={"title": "Acres burned", "hoverformat": ".3s"},
        margin={"l": 50, "r": 50, "b": 50, "t": 50, "pad": 4},
    )
    return {"data": data_traces, "layout": graph_layout}


@app.callback(
    Output("tally-year", "figure"),
    [Input("year", "value"), Input("day_range_year", "value")],
)
def update_year_zone(year, day_range):
    """ Generate daily tally count by area/year """

    # Clip to day range
    sliced = tally_zone.loc[
        (tally_zone.doy >= day_range[0]) & (tally_zone.doy <= day_range[1])
    ]

    # Subset by selected year.
    de = sliced.loc[(sliced.FireSeason == year)]

    data_traces = []
    grouped = de.groupby("ProtectionUnit")
    for name, group in grouped:
        group = group.sort_values(["date_stacked"])
        data_traces.extend(
            [
                {
                    "x": group.date_stacked,
                    "y": group.TotalAcres,
                    "mode": "lines",
                    "name": luts.zones[name],
                    "line": {"shape": get_line_mode(day_range), "width": 2},
                }
            ]
        )

    graph_layout = go.Layout(
        title="<b>Daily Tally Records by Protection Area, "
        + str(year)
        + "</b><br>"
        + get_title_date_span(day_range),
        showlegend=True,
        legend={"font": {"family": "Open Sans", "size": 10}},
        xaxis=dict(title="Date", tickformat="%B %-d"),
        yaxis={"title": "Acres burned", "hoverformat": ".3s"},
        height=650,
        margin={"l": 50, "r": 50, "b": 50, "t": 50, "pad": 4},
    )
    return {"data": data_traces, "layout": graph_layout}


if __name__ == "__main__":
    application.run(debug=os.environ["FLASK_DEBUG"], port=8080)
