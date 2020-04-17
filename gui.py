# pylint: disable=C0103,C0301
"""
GUI for app
"""

import os
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

# Hidden for now, will probably need this later in dev tho.
# TODO -- consider this instead of the built-in version
# that doesn't work.
# range_slider = dcc.RangeSlider(
#     id="day_range", count=1, min=1, max=365, step=0.5, value=[1, 365]
# )
# range_slider_field = html.Div(
#     className="field hidden",
#     children=[
#         html.Label("Range Slider", className="label"),
#         html.Div(className="control", children=[range_slider]),
#     ],
# )

zone_dropdown = dcc.Dropdown(
    id="area",
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

main_section = html.Div(
    className="section",
    children=[
        html.Div(
            className="container",
            children=[
                zone_dropdown_field,
                html.Div(
                    className="graph",
                    children=[dcc.Graph(id="tally", config=fig_configs)],
                )
            ],
        )
    ],
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
            children=[about, main_section, after_chart],
        ),
        footer,
    ]
)
