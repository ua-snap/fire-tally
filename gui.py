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

main_section = html.Div(
    className="section",
    children=[],
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