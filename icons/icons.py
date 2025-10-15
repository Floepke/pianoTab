"""
icons.py - Utility functions for loading icons as Tkinter/CustomTkinter images

Usage:
    from icons.icons import get_icon_image
    icon_img = get_icon_image('note', size=(24, 24))

Requires Pillow (PIL) and tkinter.
"""
import base64
import io
from PIL import Image, ImageTk
import sys

# Import the generated base64 icon data and loader
from .icons_data import ICONS, load_icon

def get_icon_image(icon_name, size=(24, 24), master=None):
    """
    Returns a Tkinter PhotoImage (or CustomTkinter-compatible image) for the given icon name.
    Args:
        icon_name (str): The icon name (e.g., 'note', 'engrave', ...)
        size (tuple): (width, height) in pixels
        master: Optional Tkinter master widget
    Returns:
        PhotoImage or None if not found
    """
    try:
        pil_img = load_icon(icon_name, size=size)
        return ImageTk.PhotoImage(pil_img, master=master)
    except Exception as e:
        print(f"[icons.py] Error loading icon '{icon_name}': {e}", file=sys.stderr)
        return None

def list_icons():
    """Return a list of available icon names."""
    return list(ICONS.keys())

def icon_exists(icon_name):
    """Check if an icon exists."""
    return icon_name in ICONS
