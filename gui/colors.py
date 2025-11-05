'''
Color system for pianoTAB application.
Generates a 4-color palette from two base colors.
'''


class ColorScheme:
    '''Manages application color palette.'''
    
    @staticmethod
    def hex_to_rgba(hex_color, alpha=1.0):
        '''
        Convert hex color code to normalized RGBA tuple for Kivy.
        
        Args:
            hex_color: Hex color string (e.g., '#FFFFFF', '#FFF', 'FFFFFF', 'FFF')
            alpha: Alpha value (0.0 to 1.0), default 1.0
        
        Returns:
            Tuple of (R, G, B, A) with values normalized to 0.0-1.0
        
        Examples:
            >>> ColorScheme.hex_to_rgba('#FFFFFF')
            (1.0, 1.0, 1.0, 1.0)
            >>> ColorScheme.hex_to_rgba('#FF0000', alpha=0.5)
            (1.0, 0.0, 0.0, 0.5)
            >>> ColorScheme.hex_to_rgba('0A0A0C')
            (0.039, 0.039, 0.047, 1.0)
        '''
        # Remove '#' if present
        hex_color = hex_color.lstrip('#')
        
        # Handle 3-character shorthand (e.g., 'FFF' -> 'FFFFFF')
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        
        # Validate length
        if len(hex_color) != 6:
            raise ValueError(f'Invalid hex color: {hex_color}. Expected 6 characters.')
        
        # Convert to RGB (0-255) then normalize to 0.0-1.0
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        
        return (r, g, b, alpha)
    
    @staticmethod
    def rgb_to_rgba(r, g, b, a=1.0):
        '''
        Convert RGB values (0-255) to normalized RGBA tuple for Kivy.
        
        Args:
            r: Red value (0-255)
            g: Green value (0-255)
            b: Blue value (0-255)
            a: Alpha value (0.0-1.0), default 1.0
        
        Returns:
            Tuple of (R, G, B, A) with values normalized to 0.0-1.0
        
        Examples:
            >>> ColorScheme.rgb_to_rgba(255, 255, 255)
            (1.0, 1.0, 1.0, 1.0)
            >>> ColorScheme.rgb_to_rgba(255, 0, 0, 0.5)
            (1.0, 0.0, 0.0, 0.5)
        '''
        return (r / 255.0, g / 255.0, b / 255.0, a)
    
    def __init__(self, color_light=(1.0, 1.0, 1.0, 1.0), color_dark=(0.0, 0.0, 0.0, 1.0), 
                 accent_color=(0.2, 1, .6, 1.0)):
        '''
        Initialize color scheme with base colors.
        
        Args:
            color_light: Base light color - RGBA tuple (0.0-1.0) or hex string
            color_dark: Base dark color - RGBA tuple (0.0-1.0) or hex string
            accent_color: Accent color for selections - RGBA tuple (0.0-1.0) or hex string
        
        Examples:
            >>> ColorScheme('#FFFFFF', '#000000', '#3399FF')
            >>> ColorScheme((1.0, 1.0, 1.0, 1.0), (0.0, 0.0, 0.0, 1.0))
        '''
        # Convert hex strings to RGBA tuples if needed
        if isinstance(color_light, str):
            color_light = self.hex_to_rgba(color_light)
        if isinstance(color_dark, str):
            color_dark = self.hex_to_rgba(color_dark)
        if isinstance(accent_color, str):
            accent_color = self.hex_to_rgba(accent_color)
        
        self.color_light = color_light
        self.color_dark = color_dark
        self.accent_color = accent_color
        
        # Generate intermediate colors (25% blend)
        self.color_light_darker = self._blend(color_light, color_dark, 0.25)
        self.color_dark_lighter = self._blend(color_dark, color_light, 0.25)
    
    @staticmethod
    def _blend(color1, color2, amount):
        '''
        Blend two colors.
        
        Args:
            color1: Base color (R, G, B, A)
            color2: Target color to blend towards
            amount: Blend amount (0.0 to 1.0), where 0.25 = 25% towards color2
        
        Returns:
            Blended color (R, G, B, A)
        '''
        return tuple(
            color1[i] + (color2[i] - color1[i]) * amount
            for i in range(4)
        )
    
    def get_all(self):
        '''Return all five colors as a dictionary.'''
        return {
            'light': self.color_light,
            'light_darker': self.color_light_darker,
            'dark_lighter': self.color_dark_lighter,
            'dark': self.color_dark,
            'accent': self.accent_color,
        }


'''
    Here the app colors are defined.

    The colors are used throughout the app for consistent styling.
    The ColorScheme class generates two extra colors (lighter/darker variants)
    based on the provided light and dark base colors.
'''
default_colors = ColorScheme(
    color_light='#FFFFFF',
    color_dark="#373620",
    accent_color="#a8c106"
)

# Easy access to colors throughout the app
LIGHT = default_colors.color_light              # (1.0, 1.0, 1.0, 1.0)
LIGHT_DARKER = default_colors.color_light_darker  # lighter variant of light
DARK_LIGHTER = default_colors.color_dark_lighter  # lighter variant of dark
DARK = default_colors.color_dark                # base dark

# Accent color derives directly from the configured ColorScheme so changing
# the 'accent_color' parameter above updates selection/pressed states app-wide.
ACCENT_COLOR = default_colors.accent_color


__all__ = [
    'LIGHT',
    'LIGHT_DARKER',
    'DARK_LIGHTER',
    'DARK',
    'ACCENT_COLOR'
]
