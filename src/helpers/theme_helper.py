# Desc: Style changer helper for multiple themes
# This file is part of ArcticStream Library.

from resources.theme_dark import *
from resources.theme_light import *

selected_theme = ""

def select_theme(theme_name):
    """
    Selects a theme based on the provided theme name.
    """
    global selected_theme
    selected_theme = theme_name

def get_style(style_names):
    """
    Fetches and concatenates the appropriate style strings based on the current theme.
    Accepts both a single style name or a list of style names.
    """
    global selected_theme
    styles = ""

    # Ensure style_names is a list even if a single style name is provided
    if not isinstance(style_names, list):
        style_names = [style_names]

    for style_name in style_names:
        module = __import__(f"resources.theme_{selected_theme}", fromlist=[style_name])

        styles += getattr(module, style_name, "")

    return styles