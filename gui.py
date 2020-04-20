# pylint: disable=C0103,C0301
"""
GUI for app
"""

import os
from datetime import datetime
import dash_core_components as dcc
import dash_html_components as html
import luts

# For hosting
path_prefix = os.getenv("REQUESTS_PATHNAME_PREFIX") or "/"

# Used to make the chart exports nice
fig_download_configs = dict(filename="Daily_Tally_Count", width="1000", scale=2)
fig_configs = dict(
    displayModeBar=True,
    showSendToCloud=False,
    toImageButtonOptions=fig_download_configs,
    modeBarButtonsToRemove=[
        "zoom2d",
        "pan2d",
        "select2d",
        "lasso2d",
        "zoomIn2d",
        "zoomOut2d",
        "autoScale2d",
        "resetScale2d",
        "hoverClosestCartesian",
        "hoverCompareCartesian",
        "hoverClosestPie",
        "hoverClosest3d",
        "hoverClosestGl2d",
        "hoverClosestGeo",
        "toggleHover",
        "toggleSpikelines",
    ],
    displaylogo=False,
)

# We want this HTML structure to get the full-width background color:
# <div class="header">
#   <div class="container"> gives us the centered column
#     <div class="section"> a bit more padding to stay consistent with form
header = html.Div(
    className="header",
    children=[
        html.Div(
            className="section",
            children=[
                html.Div(
                    className="container header--section",
                    children=[
                        html.Div(
                            className="header--logo",
                            children=[
                                html.A(
                                    className="header--snap-link",
                                    href="#",
                                    children=[
                                        html.Img(
                                            src=path_prefix
                                            + "assets/SNAP_acronym_color_square.svg"
                                        )
                                    ],
                                )
                            ],
                        ),
                        html.Div(
                            className="header--titles",
                            children=[html.H1(luts.title, className="title is-3")],
                        ),
                    ],
                )
            ],
        )
    ],
)


def get_day_range_slider(element_id):
    """
    Helper to create day range sliders.
    `id` becomes the ID of the slider element.
    """

    # Control which allows user to specify a date range.
    # Mark the steps by day of year.
    date_ranges = [
        luts.get_doy(4, 1),
        luts.get_doy(5, 1),
        luts.get_doy(5, 1),
        luts.get_doy(6, 1),
        luts.get_doy(7, 1),
        luts.get_doy(8, 1),
        luts.get_doy(9, 1),
    ]
    date_names = list(
        map(lambda x: datetime.strptime(str(x), "%j").strftime("%-B"), date_ranges)
    )
    date_marks = dict(zip(date_ranges, date_names))
    range_slider = dcc.RangeSlider(
        id=element_id,
        marks=date_marks,
        count=1,
        min=91,
        max=275,
        step=1,
        pushable=45,  # minimum date range span
        value=[luts.default_date_range[0], luts.default_date_range[1]],
    )
    return html.Div(
        className="field",
        children=[
            html.Label("Select date range", className="label"),
            html.Div(className="control", children=[range_slider]),
        ],
    )


range_slider_field = get_day_range_slider("day_range")
range_slider_field_zone = get_day_range_slider("day_range_zone")
range_slider_field_year = get_day_range_slider("day_range_year")

# Control which lets user choose a protection area/management zone
zone_dropdown = dcc.Dropdown(
    id="area",
    className="dropdown-selector",
    options=[{"label": luts.zones[key], "value": key} for key in luts.zones],
    value="ALL",
)
zone_dropdown_field = html.Div(
    className="field",
    children=[
        html.Label("Protection Area", className="label"),
        html.Div(className="control", children=[zone_dropdown]),
    ],
)

# Control which lets user choose a year (2004-present).
# For now we only have data for 2004-2005, so only allow those choices.
year_dropdown = dcc.Dropdown(
    id="year",
    className="dropdown-selector",
    options=[{"label": year, "value": year} for year in range(2004, 2006)],
    value=2004,
)
year_dropdown_field = html.Div(
    className="field",
    children=[
        html.Label("Year", className="label"),
        html.Div(className="control", children=[year_dropdown]),
    ],
)


def wrap_in_section(content):
    """
    Helper function to wrap sections.
    Accepts an array of children which will be assigned within
    this structure:
    <section class="section">
        <div class="container">
            <div>[children]...
    """
    return html.Section(
        className="section",
        children=[
            html.Div(className="container", children=[html.Div(children=content)])
        ],
    )


# Daily Tally, statewide only
# TODO add header, info text, appropriate CSS
# TODO ensure all graph sizes are specified with height/widths
tally_graph = wrap_in_section(
    [dcc.Graph(id="tally", config=fig_configs), range_slider_field]
)

# Daily Tally by Protection Zone
# TODO add header, info text, appropriate CSS
tally_zone_graph = wrap_in_section(
    [
        zone_dropdown_field,
        html.Div(
            className="graph", children=[dcc.Graph(id="tally-zone", config=fig_configs)]
        ),
        range_slider_field_zone,
    ]
)

# Daily Tally by Year/Protection Zone
# TODO add header info text, appropriate CSS
year_zone_graph = wrap_in_section(
    [
        year_dropdown_field,
        html.Div(
            className="graph", children=[dcc.Graph(id="tally-year", config=fig_configs)]
        ),
        range_slider_field_year,
    ]
)


footer = html.Footer(
    className="footer has-text-centered",
    children=[
        html.Div(
            children=[
                html.A(
                    href="https://www.frames.gov/afsc/home",
                    children=[html.Img(src=path_prefix + "assets/AFSC_color.svg")],
                ),
                html.A(
                    href="https://snap.uaf.edu",
                    className="snap",
                    children=[html.Img(src=path_prefix + "assets/SNAP_color_all.svg")],
                ),
                html.A(
                    href="https://uaf.edu/uaf/",
                    children=[html.Img(src=path_prefix + "assets/UAF.svg")],
                ),
            ]
        ),
        dcc.Markdown(
            """
UA is an AA/EO employer and educational institution and prohibits illegal discrimination against any individual. [Statement of Nondiscrimination](https://www.alaska.edu/nondiscrimination/)
            """,
            className="content is-size-6",
        ),
    ],
)

about = html.Div(
    className="section about content is-size-5",
    children=[
        dcc.Markdown(
            """

This chart compares the current year's daily tally of acres burned to all high fire years (> 1 million acres burned) since daily tally records began in 2004.  Click camera icon at upper right of diagram to download chart.

"""
        )
    ],
)

after_chart = html.Div(
    className="section about-after content is-size-5",
    children=[
        dcc.Markdown(
            """

 * Daily tallies go up or down as improved estimates and data become available throughout the fire season.
 * Data provided by the [Alaska Interagency Coordination Center (AICC)](https://fire.ak.blm.gov).

"""
        )
    ],
)

layout = html.Div(
    children=[
        header,
        html.Div(
            className="container",
            children=[
                about,
                tally_graph,
                tally_zone_graph,
                year_zone_graph,
                after_chart,
            ],
        ),
        footer,
    ]
)
