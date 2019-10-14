# pylint: disable=C0103
"""
Common shared text strings and lookup tables.
"""

title = "Alaska Wildfire Daily Tally Count, 2004-Present"
url = "http://snap.uaf.edu/tools/demo"
preview = "http://snap.uaf.edu/tools/demo/assets/preview.png"
description = "This visualization compares the current year to all high fire years (> 1 million acres burned) since daily tally records began in 2004."

default_style = {"color": "rgba(0, 0, 0, 0.25)", "width": 1}

important_years = [2004, 2005, 2009, 2013, 2015, 2019]
years_lines_styles = {
    "2004": {"color": "rgba(57, 106, 177, 1)", "width": "2"},
    "2005": {"color": "rgba(218, 124, 48, 1)", "width": "2"},
    "2006": default_style,
    "2007": default_style,
    "2008": default_style,
    "2009": {"color": "rgba(62, 150, 81, 1)", "width": "2"},
    "2010": default_style,
    "2011": default_style,
    "2012": default_style,
    "2013": {"color": "rgba(204, 37, 41, 1)", "width": "2"},
    "2014": default_style,
    "2015": {"color": "rgba(148, 139, 61, 1)", "width": "2"},
    "2016": default_style,
    "2017": default_style,
    "2018": default_style,
    "2019": {"color": "rgba(0, 0, 0, 1)", "width": "3"},
}
