"""
Color system for PianoTab application.
Generates a 4-color palette from two base colors.
"""


class ColorScheme:
    """Manages application color palette."""
    
    def __init__(self, color_light=(1.0, 1.0, 1.0, 1.0), color_dark=(0.0, 0.0, 0.0, 1.0)):
        """
        Initialize color scheme with base colors.
        
        Args:
            color_light: Base light color (R, G, B, A) - default white
            color_dark: Base dark color (R, G, B, A) - default black
        """
        self.color_light = color_light
        self.color_dark = color_dark
        
        # Generate intermediate colors (25% blend)
        self.color_light_darker = self._blend(color_light, color_dark, 0.25)
        self.color_dark_lighter = self._blend(color_dark, color_light, 0.25)
    
    @staticmethod
    def _blend(color1, color2, amount):
        """
        Blend two colors.
        
        Args:
            color1: Base color (R, G, B, A)
            color2: Target color to blend towards
            amount: Blend amount (0.0 to 1.0), where 0.25 = 25% towards color2
        
        Returns:
            Blended color (R, G, B, A)
        """
        return tuple(
            color1[i] + (color2[i] - color1[i]) * amount
            for i in range(4)
        )
    
    def get_all(self):
        """Return all four colors as a dictionary."""
        return {
            'light': self.color_light,
            'light_darker': self.color_light_darker,
            'dark_lighter': self.color_dark_lighter,
            'dark': self.color_dark,
        }


# Default color scheme instance
default_colors = ColorScheme(
    color_light=(1.0, 1.0, 1.0, 1.0),      # White
    color_dark=(0.2, 0.2, 0.2, 1.0)     # Near-black (matches Window.clearcolor)
)

# Easy access to colors throughout the app
LIGHT = default_colors.color_light              # (1.0, 1.0, 1.0, 1.0)
LIGHT_DARKER = default_colors.color_light_darker  # (0.775, 0.775, 0.78, 1.0)
DARK_LIGHTER = default_colors.color_dark_lighter  # (0.325, 0.325, 0.33, 1.0)
DARK = default_colors.color_dark                # (0.10, 0.10, 0.12, 1.0)


__all__ = [
    'ColorScheme',
    'default_colors',
    'LIGHT',
    'LIGHT_DARKER',
    'DARK_LIGHTER',
    'DARK'
]
