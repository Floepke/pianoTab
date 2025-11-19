'''
Icon loader utility for loading base64-encoded icons.
Provides a simple API to load icons from the generated icons_data.py
with optional accent color tinting for black-based icons.
'''

import base64
import io
from typing import Optional, Tuple
from kivy.core.image import Image as CoreImage
from PIL import Image as PILImage


class IconLoader:
    '''Loads icons from base64 data with optional accent color tinting.'''
    
    _icons_data = None
    # Icons that should be automatically tinted with ACCENT_COLOR
    _accent_tinted_icons = {'noteLeft', 'noteRight'}
    
    @classmethod
    def _load_icons_data(cls):
        '''Lazy load icons data.'''
        if cls._icons_data is None:
            try:
                from icons.icons_data import ICONS
                cls._icons_data = ICONS
            except ImportError:
                print('Warning: icons_data.py not found. Run icons/precompile_icons.py first.')
                cls._icons_data = {}
        return cls._icons_data
    
    @classmethod
    def _tint_icon(cls, image_data: bytes, tint_color: Tuple[float, float, float, float]) -> bytes:
        '''
        Tint black/dark pixels in an icon to the specified color.
        
        Args:
            image_data: PNG image bytes
            tint_color: RGBA tuple (0-1 range) for the tint color
            
        Returns:
            Tinted PNG image bytes
        '''
        try:
            # Load image with PIL
            img = PILImage.open(io.BytesIO(image_data))
            
            # Convert to RGBA if needed
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Get pixel data
            pixels = img.load()
            width, height = img.size
            
            # Convert tint color from 0-1 to 0-255
            tint_r = int(tint_color[0] * 255)
            tint_g = int(tint_color[1] * 255)
            tint_b = int(tint_color[2] * 255)
            
            # Process each pixel
            for y in range(height):
                for x in range(width):
                    r, g, b, a = pixels[x, y]
                    
                    # Only tint dark pixels (closer to black)
                    # Calculate luminance to determine if pixel is dark
                    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
                    
                    if luminance < 0.5:  # Dark pixel threshold
                        # Replace with tint color, preserve alpha
                        pixels[x, y] = (tint_r, tint_g, tint_b, a)
            
            # Save back to bytes
            output = io.BytesIO()
            img.save(output, format='PNG')
            return output.getvalue()
            
        except Exception as e:
            print(f'Warning: Failed to tint icon: {e}')
            return image_data  # Return original on error
    
    @classmethod
    def get_icon_names(cls):
        '''Get list of available icon names.'''
        icons = cls._load_icons_data()
        return list(icons.keys())
    
    @classmethod
    def load_icon(cls, icon_name: str, tint_color: Optional[Tuple[float, float, float, float]] = None) -> Optional[CoreImage]:
        '''
        Load an icon by name from base64 data with optional color tinting.
        
        Args:
            icon_name: Name of the icon (without .png extension)
            tint_color: Optional RGBA tuple (0-1 range) to tint black pixels.
                       If None and icon_name is in _accent_tinted_icons, ACCENT_COLOR is used.
        
        Returns:
            CoreImage object or None if icon not found
        '''
        icons = cls._load_icons_data()
        
        if icon_name not in icons:
            print(f'Warning: Icon "{icon_name}" not found in icons_data')
            return None
        
        # Decode base64 to bytes
        base64_data = icons[icon_name]
        image_data = base64.b64decode(base64_data)
        
        # Auto-apply ACCENT_COLOR tint for specific icons
        if tint_color is None and icon_name in cls._accent_tinted_icons:
            try:
                from gui.colors import ACCENT_COLOR
                tint_color = ACCENT_COLOR
            except ImportError:
                pass
        
        # Apply tinting if color specified
        if tint_color is not None:
            image_data = cls._tint_icon(image_data, tint_color)
        
        # Create image from bytes
        data = io.BytesIO(image_data)
        return CoreImage(data, ext='png')
    
    @classmethod
    def has_icon(cls, icon_name: str) -> bool:
        '''Check if an icon exists.'''
        icons = cls._load_icons_data()
        return icon_name in icons


# Convenience function
def load_icon(icon_name: str, tint_color: Optional[Tuple[float, float, float, float]] = None) -> Optional[CoreImage]:
    '''
    Load an icon by name with optional color tinting.
    
    Usage:
        # Load normal icon
        icon = load_icon('note')
        
        # Load with custom tint
        from gui.colors import ACCENT_COLOR
        icon = load_icon('myicon', tint_color=ACCENT_COLOR)
        
        # noteLeft and noteRight are auto-tinted with ACCENT_COLOR
        icon = load_icon('noteLeft')  # Automatically tinted
    '''
    return IconLoader.load_icon(icon_name, tint_color)


__all__ = ['IconLoader', 'load_icon']
