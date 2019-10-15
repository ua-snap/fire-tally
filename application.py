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


date_ranges = [91, 121, 152, 182, 213, 244]
date_names = list(
    map(lambda x: datetime.strptime(str(x), "%j").strftime("%B"), date_ranges)
)

raw_data = pd.read_csv("data/test.csv", index_col=0, parse_dates=True)

# We set the requests_pathname_prefix to enable
# custom URLs.
# https://community.plot.ly/t/dash-error-loading-layout/8139/6
app = dash.Dash(
    __name__, requests_pathname_prefix=os.environ["REQUESTS_PATHNAME_PREFIX"]
)

# AWS Elastic Beanstalk looks for application by default,
# if this variable (application) isn't set you will get a WSGI error.
application = app.server

# The next config sets a relative base path so we can deploy
# with custom URLs.
# https://community.plot.ly/t/dash-error-loading-layout/8139/6

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


@app.callback(Output("tally", "figure"), [Input("day_range", "value")])
def update_tally(day_range):
    """ Generate daily tally count """
    data_traces = []
    df = raw_data
    df = df.loc[(df["FireSeason"] >= 2004)]

    # Generate a synthetic datetime field,
    # with all the same year.  This lets us
    # give Plotly the x-axis as a date.
    def collapse_year(date):
        stacked_date = "2000/{}/{}".format(date.month, date.day)
        return datetime.strptime(stacked_date, "%Y/%m/%d")

    df = df.assign(
        datetime=pd.to_datetime(df["SitReportDate"], format="%Y%m%d", errors="coerce")
    )
    df = df.assign(
        date_stacked=pd.to_datetime(
            df["datetime"].apply(collapse_year), format="%Y-%m-%d"
        )
    )

    grouped = df.groupby("FireSeason")
    for name, group in grouped:
        group = group.sort_values(["date_stacked"])

        # Apply LOESS filter to smooth the data.
        # https://www.statsmodels.org/dev/generated/statsmodels.nonparametric.smoothers_lowess.lowess.html
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
        group["SmoothedTotalAcres"] = group["SmoothedTotalAcres"].apply(
            lambda x: x if x >= 0 else 0
        )

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
                    "y": group.SmoothedTotalAcres,
                    "mode": "lines",
                    "name": str(name),
                    "line": {
                        "color": luts.years_lines_styles[str(name)]["color"],
                        "shape": "spline",
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
            tickformat="%B %d",
            rangeslider=dict(
                visible=True,
                bgcolor="#dfffff",
                thickness=0.10,
                bordercolor="#aaaaaa",
                borderwidth=1,
            ),
            range=[
                datetime.strptime("20000615", "%Y%m%d"),
                datetime.strptime("20000920", "%Y%m%d"),
            ]
        ),
        yaxis={
            "title": "Acres burned (millions)",
            "hoverformat": ".3s"
        },
        height=650,
        margin={"l": 50, "r": 50, "b": 50, "t": 50, "pad": 4},
    )
    return {"data": data_traces, "layout": graph_layout}


if __name__ == "__main__":
    application.run(debug=os.environ["FLASK_DEBUG"], port=8080)
