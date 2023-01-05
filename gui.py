# pylint: disable=C0103,C0301
"""
GUI for app
"""

import os
from datetime import datetime
from dash import dcc
from dash import html
import dash_dangerously_set_inner_html as ddsih
import luts
import data

(tally, tally_zone, tally_zone_date_ranges) = data.fetch_data()

# For hosting
path_prefix = os.getenv("DASH_REQUESTS_PATHNAME_PREFIX") or "/"

# Used to make the chart exports nice
fig_download_configs = dict(
    filename="Daily_Tally_Count", width="1000", height="650", scale=2
)
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


# Helper functions
def wrap_in_section(content, section_classes="", container_classes="", div_classes=""):
    """
    Helper function to wrap sections.
    Accepts an array of children which will be assigned within
    this structure:
    <section class="section">
        <div class="container">
            <div>[children]...
    """
    return html.Section(
        className="section " + section_classes,
        children=[
            html.Div(
                className="container " + container_classes,
                children=[html.Div(className=div_classes, children=content)],
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


header = ddsih.DangerouslySetInnerHTML(
    f"""
<div class="container">
<nav class="navbar" role="navigation" aria-label="main navigation">

  <div class="navbar-brand">
    <a class="navbar-item" href="https://www.snap.uaf.edu">
      <img src="{path_prefix}assets/SNAP_mapventures_header.svg">
    </a>

    <a role="button" class="navbar-burger burger" aria-label="menu" aria-expanded="false" data-target="navbarBasicExample">
      <span aria-hidden="true"></span>
      <span aria-hidden="true"></span>
      <span aria-hidden="true"></span>
    </a>
  </div>

  <div class="navbar-menu">
    <div class="navbar-end">
      <div class="navbar-item">
        <div class="buttons">
          <a target="_blank" rel="noopener noreferrer" href="https://uaf-iarc.typeform.com/to/mN7J5cCK#tool=Alaska%20Fire%20Tally" class="button is-link">
            <strong>Feedback</strong>
          </a>
        </div>
      </div>
    </div>
  </div>
</nav>
</div>
"""
)

about = wrap_in_section(
    [
        ddsih.DangerouslySetInnerHTML(
            f"""
<h1 class="title is-3">{luts.title}</h1>
<p> These charts compare the current year's daily tally of acres burned to high fire years (> 1 million acres burned) since daily tally records began in 2004.</p>
<p class="camera-icon">Click the <span>
<svg viewBox="0 0 1000 1000" class="icon" height="1em" width="1em"><path d="m500 450c-83 0-150-67-150-150 0-83 67-150 150-150 83 0 150 67 150 150 0 83-67 150-150 150z m400 150h-120c-16 0-34 13-39 29l-31 93c-6 15-23 28-40 28h-340c-16 0-34-13-39-28l-31-94c-6-15-23-28-40-28h-120c-55 0-100-45-100-100v-450c0-55 45-100 100-100h800c55 0 100 45 100 100v450c0 55-45 100-100 100z m-400-550c-138 0-250 112-250 250 0 138 112 250 250 250 138 0 250-112 250-250 0-138-112-250-250-250z m365 380c-19 0-35 16-35 35 0 19 16 35 35 35 19 0 35-16 35-35 0-19-16-35-35-35z" transform="matrix(1 0 0 -1 0 850)"></path></svg>
</span> icon in the upper&ndash;right of each chart to download it.  Below each chart is a slider that can be used to select the date range shown in the chart.</p>
<p>This tool was developed by the <a href="https://www.snap.uaf.edu">Scenarios Network for Alaska and Arctic Planning (SNAP)</a>.  Data are provided by the <a href="https://fire.ak.blm.gov">Alaska Interagency Coordination Center (AICC)</a>.
            """
        )
    ],
    div_classes="content is-size-5",
)


# Daily Tally, statewide only
range_slider_field = get_day_range_slider("day_range")
tally_graph = wrap_in_section(
    [
        html.H3("Statewide daily tally", className="title is-4"),
        html.P(
            """
Daily tallies go up or down as improved estimates and data become available throughout the fire season.
    """,
            className="content is-size-5",
        ),
        dcc.Graph(id="tally", config=fig_configs),
        range_slider_field,
    ],
    section_classes="graph",
)

# Daily Tally by Protection Zone
range_slider_field_zone = get_day_range_slider("day_range_zone")
zone_dropdown = dcc.Dropdown(
    id="area",
    className="dropdown-selector",
    options=[{"label": luts.zones[key], "value": key} for key in luts.zones],
    value="CGF",
)
zone_dropdown_field = html.Div(
    className="field",
    children=[
        html.Label("Choose a protection area", className="label"),
        html.Div(className="control", children=[zone_dropdown]),
    ],
)
tally_zone_graph = wrap_in_section(
    [
        html.H3("Daily tally by protection area", className="title is-4"),
        ddsih.DangerouslySetInnerHTML(
            """
<p class="content is-size-5">This chart shows the daily tally for one protection area (<a href="https://fire.ak.blm.gov/content/maps/aicc/Large%20Maps/Alaska_Fire_Management_Zones.pdf">see this map of wildland fire protection areas</a> to see which areas cover which parts of the state).  These data are still being updated and not all years may be present yet.</p><br>
        """
        ),
        zone_dropdown_field,
        html.Div(
            className="graph", children=[dcc.Graph(id="tally-zone", config=fig_configs)]
        ),
        range_slider_field_zone,
    ],
    section_classes="graph",
)


# Daily Tally by Year/Protection Zone
range_slider_field_year = get_day_range_slider("day_range_year")
year_dropdown = dcc.Dropdown(
    id="year",
    className="dropdown-selector",
    options=[{"label": year, "value": year} for year in tally_zone_date_ranges],
    value=2004,
)
year_dropdown_field = html.Div(
    className="field",
    children=[
        html.Label("Select a year", className="label"),
        html.Div(className="control", children=[year_dropdown]),
    ],
)
year_zone_graph = wrap_in_section(
    [
        html.H3("Daily tally by year", className="title is-4"),
        html.P(
            """
This chart shows the daily tally for each protection area for a given year.  These data are still being updated and not all years may be present yet.
        """,
            className="content is-size-5",
        ),
        year_dropdown_field,
        html.Div(
            className="graph", children=[dcc.Graph(id="tally-year", config=fig_configs)]
        ),
        range_slider_field_year,
    ],
    section_classes="graph",
)

# Used in copyright date
current_year = datetime.now().year

footer = html.Footer(
    className="footer",
    children=[
        ddsih.DangerouslySetInnerHTML(
            f"""
<div class="container">
    <div class="columns">
        <div class="logo column is-one-fifth">
            <img src="{path_prefix}assets/UAF.svg" alt="UAF Logo" />
        </div>
        <div class="column is-four-fifths">
            <p>The Alaska Wildfire Daily Tally Count was developed from data provided by the <a href="https://fire.ak.blm.gov/predsvcs/maps.php">Alaska Interagency Coordination Center</a>. This website was developed by the <a href="https://www.frames.gov/afsc/home">Alaska Fire Science Consortium</a> and the <a href="https://www.snap.uaf.edu/" title="SNAP 👍">Scenarios Network for Alaska and Arctic Planning</a>, research groups at the <a href="https://uaf-iarc.org/">International Arctic Research Center</a>.</p>
            <p>Copyright &copy; {current_year} University of Alaska Fairbanks.  All rights reserved.</p>
            <p>UA is an AA/EO employer and educational institution and prohibits illegal discrimination against any individual. <a href="https://www.alaska.edu/nondiscrimination/"
              >Statement of Nondiscrimination</a> and <a href="https://www.alaska.edu/records/records/compliance/gdpr/ua-privacy-statement/">Privacy Statement</a>
            </p>
            <p>UA is committed to providing accessible websites.  <a href="https://www.alaska.edu/webaccessibility/">Learn more about UA&rsquo;s notice of web accessibility</a>.  If we can help you access this website’s content, email us at <a href="mailto:uaf-snap-data-tools@alaska.edu">uaf-snap-data-tools@alaska.edu</a>!
            </p>
        </div>
    </div>
</div>
            """
        ),
    ],
)

layout = html.Div(
    children=[
        header,
        html.Div(children=[about, tally_graph, tally_zone_graph, year_zone_graph]),
        footer,
    ]
)
