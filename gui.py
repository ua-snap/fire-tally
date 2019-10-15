# pylint: disable=C0103
"""
GUI for app
"""

import os
import dash_core_components as dcc
import dash_html_components as html
import luts

# For hosting
path_prefix = os.environ["REQUESTS_PATHNAME_PREFIX"]

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

header = html.Div(
    className="header section",
    children=[
        html.Div(
            children=[
                html.A(
                    className="logo",
                    href="#",
                    children=[html.Img(src="assets/AFSC_color.svg")],
                ),
                html.H1(luts.title, className="title is-h4"),
            ]
        )
    ],
)

# Hidden for now, will probably need this later in dev tho.
range_slider = dcc.RangeSlider(
    id="day_range", count=1, min=1, max=365, step=0.5, value=[1, 365]
)
range_slider_field = html.Div(
    className="field hidden",
    children=[
        html.Label("Range Slider", className="label"),
        html.Div(className="control", children=[range_slider]),
    ],
)

main_section = html.Div(
    className="section",
    children=[
        html.Div(
            className="graph", children=[dcc.Graph(id="tally", config=fig_configs)]
        ),
        range_slider_field,
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

This visualization compares the current year's daily tally of acres burned to all high fire years (> 1 million acres burned) since daily tally records began in 2004.

 * Smaller fire seasons are shown in light grey.
 * Data are smoothed for improved appearance.
 * Click the camera icon in the upper-right of the diagram to download a high-res version of this chart.
 * The smaller graph with the blue background is a rangefinder which can be used to explore all date ranges.

Source: [Alaska Interagency Coordination Center (AICC)](https://fire.ak.blm.gov).

"""
        )
    ],
)

layout = html.Div(
    children=[
        header,
        html.Div(className="container", children=[about, main_section]),
        footer,
    ]
)
