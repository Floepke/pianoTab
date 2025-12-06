# ...existing code...
from dataclasses import dataclass
import colorsys

@dataclass
class Theme:
    hue_deg: float = 28.0          # single global hue control
    sat: float = 0.65              # base saturation (0-1)
    val_light: float = 1.00        # value for LIGHT
    val_dark: float = 0.25         # value for DARK
    contrast: float = 0.25         # how much to blend toward opposite for *_LIGHTER/DARKER
    accent_rgba: tuple | None = None  # optional manual accent override (r,g,b,a in 0..1)

    def _hsv_to_rgba(self, h, s, v, a=1.0):
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return (r, g, b, a)

    def _blend(self, c1, c2, amt):
        return tuple(c1[i] + (c2[i] - c1[i]) * amt for i in range(4))

    def compute(self):
        h = (self.hue_deg % 360) / 360.0
        light = self._hsv_to_rgba(h, self.sat, self.val_light, 1.0)
        dark  = self._hsv_to_rgba(h, self.sat, self.val_dark,  1.0)
        light_darker = self._blend(light, dark, self.contrast)
        dark_lighter = self._blend(dark, light, self.contrast)
        # Accent: manual override if provided, else derive from hue with higher saturation/value
        accent = self.accent_rgba if self.accent_rgba is not None else self._hsv_to_rgba(h, min(1.0, self.sat * 1.1), 0.95, 1.0)
        return {
            'LIGHT': light,
            'DARK': dark,
            'LIGHT_DARKER': light_darker,
            'DARK_LIGHTER': dark_lighter,
            'ACCENT': accent,
        }

def rgba_to_hex(rgba):
    r, g, b = rgba[:3]
    return f'#{int(r * 255):02X}{int(g * 255):02X}{int(b * 255):02X}'

def hex_to_rgba(hex_str, alpha=1.0):
    hex_str = hex_str.lstrip('#')
    lv = len(hex_str)
    if lv == 6:
        r = int(hex_str[0:2], 16) / 255.0
        g = int(hex_str[2:4], 16) / 255.0
        b = int(hex_str[4:6], 16) / 255.0
        return (r, g, b, alpha)
    elif lv == 8:
        r = int(hex_str[0:2], 16) / 255.0
        g = int(hex_str[2:4], 16) / 255.0
        b = int(hex_str[4:6], 16) / 255.0
        a = int(hex_str[6:8], 16) / 255.0
        return (r, g, b, a)
    else:
        raise ValueError("Hex string must be in format RRGGBB or RRGGBBAA")

# theme presets (name -> Theme kwargs)
THEMES = {
    "pianoTAB Light": dict(
        hue_deg=300,        # golden hue baseline
        sat=.1,          # gentle saturation
        val_light=0.97,    # near white background
        val_dark=0.36,     # deep text on light bg
        contrast=0.25,
        accent_rgba=hex_to_rgba("#d1773f"),  # solarized blue accent #d55c11
    ),
    'pianoTAB Dark': dict(
        hue_deg=45,
        sat=.15,
        val_light=0.75,
        val_dark=0.04,
        contrast=0.30,
        accent_rgba=hex_to_rgba("#d55c11"),  # brighter orange accent
    ),
}

# Select a dark theme preset
theme = Theme(**THEMES['pianoTAB Dark'])
COLORS = theme.compute()

LIGHT = COLORS['LIGHT']
DARK = COLORS['DARK']
LIGHT_DARKER = COLORS['LIGHT_DARKER']
DARK_LIGHTER = COLORS['DARK_LIGHTER']
ACCENT = COLORS['ACCENT']

LIGHT_HEX = rgba_to_hex(LIGHT)
DARK_HEX = rgba_to_hex(DARK)
LIGHT_DARKER_HEX = rgba_to_hex(LIGHT_DARKER)
DARK_LIGHTER_HEX = rgba_to_hex(DARK_LIGHTER)
ACCENT_HEX = rgba_to_hex(ACCENT)

__all__ = [
    'LIGHT', 'DARK', 'LIGHT_DARKER', 'DARK_LIGHTER', 'ACCENT',
    'LIGHT_HEX', 'DARK_HEX', 'LIGHT_DARKER_HEX', 'DARK_LIGHTER_HEX', 'ACCENT_HEX',
    'Theme', 'theme', 'rgba_to_hex'
]