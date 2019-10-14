"""
GUI for app
"""

import dash
import dash_core_components as dcc
import dash_html_components as html


navbar = html.Div(
    className="navbar",
    role="navigation",
    children=[
        html.Div(
            className="navbar-brand",
            children=[
                html.A(
                    className="navbar-item",
                    href="#",
                    children=[html.Img(src="assets/SNAP_acronym_color.svg")],
                )
            ],
        ),
    ],
)

range_slider = dcc.RangeSlider(id="day_range", count=1, min=1, max=365, step=0.5, value=[1, 365])
range_slider_field = html.Div(
    className="field",
    children=[
        html.Label("Range Slider", className="label"),
        html.Div(className="control", children=[range_slider]),
    ],
)

main_section = html.Div(
    className="section",
    children=[
        html.Div(className="graph", children=[dcc.Graph(id="tally")]),
        range_slider_field
    ],
)

footer = html.Footer(
    className="footer",
    children=[
        html.Div(
            className="content has-text-centered",
            children=[
                dcc.Markdown(
                    """
This is a page footer, where we'd put legal notes and other items.
                    """
                )
            ],
        )
    ],
)

layout = html.Div(
    className="container",
    children=[navbar, main_section, footer],
)