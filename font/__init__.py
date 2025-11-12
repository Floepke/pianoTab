"""
Font package for embedded FiraCode-SemiBold font.
"""
from font.font_loader import load_embedded_font, get_font_name, cleanup_font, FONT_NAME
from font.apply_font import apply_default_font

__all__ = [
    'load_embedded_font', 
    'get_font_name', 
    'cleanup_font', 
    'FONT_NAME', 
    'apply_default_font',
]
