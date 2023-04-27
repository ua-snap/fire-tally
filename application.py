# pylint: disable=C0103,C0301,E0401
"""
Template for SNAP Dash apps.
"""
import os
from datetime import datetime
import plotly.graph_objs as go
import dash
from dash.dependencies import Input, Output
import luts
import data
from gui import layout

app = dash.Dash(__name__)

# AWS Elastic Beanstalk looks for application by default,
# if this variable (application) isn't set you will get a WSGI error.
application = app.server

app.index_string = f"""
<!DOCTYPE html>
<html>
    <head>
        
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
        <script async defer 
            data-domains="snap.uaf.edu"
            data-website-id="03f1aa4a-4f5d-49e1-b69e-837c38bc0af7"
            src="https://umami.snap.uaf.edu/umami.js"
            data-do-not-track="true">
        </script>
          
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
    """Helper to build the string fragment stating time span in titles."""
    return str(
        datetime.strptime(str(day_range[0]), "%j").strftime("%B %-d")
        + "—"
        + datetime.strptime(str(day_range[1]), "%j").strftime("%B %-d")
    )


# Some reused configs in charts go here to reduce duplication.
yaxis_conf = dict(
    title="Area burned (acres)",
    fixedrange=True,
)
xaxis_conf = dict(
    tickformat="%B %-d",
    fixedrange=True,
)
hover_conf = "%{y:,} acres"  # hover format (D3 language)


@app.callback(Output("tally", "figure"), [Input("day_range", "value")])
def update_tally(day_range):
    """Generate daily tally count"""

    (tally, tally_zone, tally_zone_date_ranges) = data.fetch_data()
    data_traces = []

    #  Slice by day range.
    sliced = tally.loc[(tally.doy >= day_range[0]) & (tally.doy <= day_range[1])]

    grouped = sliced.groupby("FireSeason")
    for name, group in grouped:
        group = group.sort_values(["date_stacked"])

        if name in luts.important_years:
            hovertemplate = hover_conf
            hoverinfo = ""
            showlegend = True
        else:
            hovertemplate = None
            hoverinfo = "skip"
            showlegend = False

        data_traces.extend(
            [
                {
                    "x": group.date_stacked,
                    "y": round(group.TotalAcres),
                    "mode": "lines",
                    "name": str(name),
                    "line": {
                        "color": luts.years_lines_styles[str(name)]["color"],
                        "width": luts.years_lines_styles[str(name)]["width"],
                    },
                    "showlegend": showlegend,
                    "hoverinfo": hoverinfo,
                    "hovertemplate": hovertemplate,
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
        xaxis=xaxis_conf,
        yaxis=yaxis_conf,
        hovermode="x unified",
        hoverdistance=1,
    )
    return {"data": data_traces, "layout": graph_layout}


@app.callback(
    Output("tally-zone", "figure"),
    [Input("area", "value"), Input("day_range_zone", "value")],
)
def update_tally_zone(area, day_range):
    """Generate daily tally count for specified protection area"""
    (tally, tally_zone, tally_zone_date_ranges) = data.fetch_data()

    #  Slice by day range.
    sliced = tally_zone.loc[
        (tally_zone.doy >= day_range[0]) & (tally_zone.doy <= day_range[1])
    ]

    # Spatial clip
    de = sliced.loc[(sliced["ProtectionUnit"] == area)]

    data_traces = []
    grouped = de.groupby("FireSeason")
    for name, group in grouped:
        group = group.sort_values(["date_stacked"])
        group["TotalAcres"] = group["TotalAcres"].round(2)
        data_traces.extend(
            [
                {
                    "x": group.date_stacked,
                    "y": round(group.TotalAcres),
                    "mode": "lines",
                    "name": name,
                    "line": {
                        "color": luts.years_lines_styles[str(name)]["color"],
                        "width": luts.years_lines_styles[str(name)]["width"],
                    },
                    "hovertemplate": hover_conf,
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
        title="<b>Alaska Daily Tally Records, "
        + luts.zones[area]
        + ", 2004-Present</b><br>"
        + get_title_date_span(day_range),
        xaxis=xaxis_conf,
        yaxis=yaxis_conf,
        hovermode="x unified",
        hoverdistance=1,
    )
    return {"data": data_traces, "layout": graph_layout}


@app.callback(
    Output("tally-year", "figure"),
    [Input("year", "value"), Input("day_range_year", "value")],
)
def update_year_zone(year, day_range):
    """Generate daily tally count by area/year"""
    (tally, tally_zone, tally_zone_date_ranges) = data.fetch_data()

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
        group["TotalAcres"] = group["TotalAcres"].round(2)
        data_traces.extend(
            [
                {
                    "x": group.date_stacked,
                    "y": round(group.TotalAcres),
                    "mode": "lines",
                    "name": luts.zones[name],
                    "line": {"width": 2},
                    "hovertemplate": hover_conf,
                }
            ]
        )

    graph_layout = go.Layout(
        title="<b>Alaska Daily Tally Records by Year, "
        + str(year)
        + "</b><br>"
        + get_title_date_span(day_range),
        xaxis=xaxis_conf,
        yaxis=yaxis_conf,
        hovermode="x unified",
        hoverdistance=1,
    )
    return {"data": data_traces, "layout": graph_layout}


if __name__ == "__main__":
    application.run(debug=os.getenv("FLASK_DEBUG", default=False), port=8080)
