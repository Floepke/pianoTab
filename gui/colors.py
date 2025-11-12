'''
Color system for pianoTAB with global hue adjustment.
'''
import colorsys

class ColorSchemeHue:
    '''Manages color palette with global hue control.'''
    def __init__(self, color_light=(1.0, 1.0, 1.0, 1.0), color_dark=(0.0, 0.0, 0.0, 1.0), accent_color=(0.2, 1, .6, 1.0), hue=30.0):
        # Store original colors in HSV
        self._orig = {}
        for name, rgba in [('light', color_light), ('dark', color_dark), ('accent', accent_color)]:
            r, g, b, a = rgba
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            self._orig[name] = (h, s, v, a)
        self.hue = hue / 360.0  # Store as 0-1
        self.update_colors()
    
    def update_colors(self):
        # Shift all colors to new hue, keep S/V/A
        self.color_light = self._hue_rgba('light')
        self.color_dark = self._hue_rgba('dark')
        self.accent_color = self._hue_rgba('accent')
        self.color_light_darker = self._blend(self.color_light, self.color_dark, 0.25)
        self.color_dark_lighter = self._blend(self.color_dark, self.color_light, 0.25)
    
    def set_hue(self, hue_deg):
        self.hue = hue_deg / 360.0
        self.update_colors()
    
    def _hue_rgba(self, name):
        h, s, v, a = self._orig[name]
        r, g, b = colorsys.hsv_to_rgb(self.hue, s, v)
        return (r, g, b, a)
    
    @staticmethod
    def _blend(color1, color2, amount):
        return tuple(color1[i] + (color2[i] - color1[i]) * amount for i in range(4))
    
    def get_all(self):
        return {
            'light': self.color_light,
            'light_darker': self.color_light_darker,
            'dark_lighter': self.color_dark_lighter,
            'dark': self.color_dark,
            'accent': self.accent_color,
        }

def rgba_to_hex(rgba):
    '''Convert Kivy RGBA tuple (0-1 range) to hex color string.
    
    Args:
        rgba: Tuple of (r, g, b, a) where each component is 0-1
        
    Returns:
        Hex color string like '#RRGGBB' (alpha is ignored)
    '''
    r, g, b = rgba[0], rgba[1], rgba[2]
    return f'#{int(r * 255):02X}{int(g * 255):02X}{int(b * 255):02X}'

# Example usage: lock S/V balance, change hue only
# Initial colors from your current theme
hue_theme = ColorSchemeHue(
    color_light=(1.0, 1.0, 1.0, 1.0),
    color_dark=(0.215, 0.169, 0.125, 1.0),
    accent_color=(0.757, 0.267, 0.024, .75),
    hue=150.0  # initial hue in degrees
)

# To change theme hue, call:
# hue_theme.set_hue(new_hue_deg)

# Kivy color tuples (RGBA 0-1 range)
LIGHT = hue_theme.color_light
LIGHT_DARKER = hue_theme.color_light_darker
DARK_LIGHTER = hue_theme.color_dark_lighter
DARK = hue_theme.color_dark
ACCENT_COLOR = hue_theme.accent_color

# Hex color strings for canvas drawing
LIGHT_HEX = rgba_to_hex(LIGHT)
LIGHT_DARKER_HEX = rgba_to_hex(LIGHT_DARKER)
DARK_LIGHTER_HEX = rgba_to_hex(DARK_LIGHTER)
DARK_HEX = rgba_to_hex(DARK)
ACCENT_COLOR_HEX = rgba_to_hex(ACCENT_COLOR)

__all__ = [
    # Kivy RGBA tuples
    'LIGHT',
    'LIGHT_DARKER',
    'DARK_LIGHTER',
    'DARK',
    'ACCENT_COLOR',
    # Hex strings for canvas
    'LIGHT_HEX',
    'LIGHT_DARKER_HEX',
    'DARK_LIGHTER_HEX',
    'DARK_HEX',
    'ACCENT_COLOR_HEX',
    # Utilities
    'rgba_to_hex',
    'hue_theme'
]