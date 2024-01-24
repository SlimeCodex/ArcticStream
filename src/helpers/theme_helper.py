# Desc: Style changer helper for multiple themes
# This file is part of ArcticStream Library.

from resources.theme_dark import *
from resources.theme_light import *

dark_theme_selected = True  # Initial flag for theme

def get_style(style_names):
	"""
	Fetches and concatenates the appropriate style strings based on the current theme.
	Accepts both a single style name or a list of style names.
	"""
	global dark_theme_selected
	styles = ""

	# Ensure style_names is a list even if a single style name is provided
	if not isinstance(style_names, list):
		style_names = [style_names]

	for style_name in style_names:
		if dark_theme_selected:
			module = __import__("resources.theme_dark", fromlist=[style_name])
		else:
			module = __import__("resources.theme_light", fromlist=[style_name])
		
		styles += getattr(module, style_name, "")

	return styles

def toggle_theme():
	"""
	Toggles the theme between light and dark.
	"""
	global dark_theme_selected
	dark_theme_selected = not dark_theme_selected