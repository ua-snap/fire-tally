# pylint: disable=C0103,E0401
"""
Template for SNAP Dash apps.
"""

import os
from datetime import datetime
import numpy as np
import statsmodels.api as sm
import dash
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import luts
from gui import layout
import pandas as pd


date_ranges = [91, 121, 152, 182, 213, 244]
print(date_ranges)
date_names = list(
    map(lambda x: datetime.strptime(str(x), "%j").strftime("%B"), date_ranges)
)
print(date_names)

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
    """ Regenerate plot data for area burned """
    data_traces = []
    df = raw_data
    df["datetime"] = pd.to_datetime(
        df["SitReportDate"], format="%Y%m%d", errors="coerce"
    )

    def convert_to_doy(date):
        if date == np.datetime64("NaT"):
            return NaN
        return date.strftime("%-j")

    df["doy"] = df["datetime"].apply(convert_to_doy).astype(int)
    df = df.loc[(df["FireSeason"] >= 2004)]
    df.to_csv("t.csv")

    # print(day_range)
    # print(df)

    grouped = df.groupby("FireSeason")
    for name, group in grouped:
        group = group.sort_values(["doy"])
        z = sm.nonparametric.lowess(
            group.TotalAcres,
            group.doy,
            return_sorted=False,
            frac=0.05,
            it=1,
            delta=3
        )
        if name in luts.important_years:
            hoverinfo = ""
            showlegend = True
        else:
            hoverinfo = "skip"
            showlegend = False

        mode = "lines+markers" if name == 2019 else "lines"
        data_traces.extend(
            [
                {
                    "x": group.doy,
                    "y": z,
                    "mode": mode,
                    "name": str(name),
                    "line": {
                        "color": luts.years_lines_styles[str(name)]["color"],
                        "shape": "spline",
                        "width": luts.years_lines_styles[str(name)]["width"]
                    },
                    "showlegend": showlegend,
                    "hoverinfo": hoverinfo
                }
            ]
        )

    graph_layout = go.Layout(
        title="Daily Tally",
        showlegend=True,
        legend={"font": {"family": "Open Sans", "size": 10}},
        xaxis=dict(
            title="Date",
            range=[90, 260],
            tickmode="array",
            tickvals=date_ranges,
            ticktext=date_names,
        ),
        yaxis={"title": "Acres"},
        height=650,
        margin={"l": 50, "r": 50, "b": 50, "t": 50, "pad": 4},
    )
    return {"data": data_traces, "layout": graph_layout}


if __name__ == "__main__":
    application.run(debug=os.environ["FLASK_DEBUG"], port=8080)
