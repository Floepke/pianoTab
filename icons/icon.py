"""
Icon loader utility for loading base64-encoded icons.
Provides a simple API to load icons from the generated icons_data.py
"""

import base64
import io
from typing import Optional
from kivy.core.image import Image as CoreImage


class IconLoader:
    """Loads icons from base64 data."""
    
    _icons_data = None
    
    @classmethod
    def _load_icons_data(cls):
        """Lazy load icons data."""
        if cls._icons_data is None:
            try:
                from icons.icons_data import ICONS
                cls._icons_data = ICONS
            except ImportError:
                print("Warning: icons_data.py not found. Run icons/precompile_icons.py first.")
                cls._icons_data = {}
        return cls._icons_data
    
    @classmethod
    def get_icon_names(cls):
        """Get list of available icon names."""
        icons = cls._load_icons_data()
        return list(icons.keys())
    
    @classmethod
    def load_icon(cls, icon_name: str) -> Optional[CoreImage]:
        """
        Load an icon by name from base64 data.
        
        Args:
            icon_name: Name of the icon (without .png extension)
        
        Returns:
            CoreImage object or None if icon not found
        """
        icons = cls._load_icons_data()
        
        if icon_name not in icons:
            print(f"Warning: Icon '{icon_name}' not found in icons_data")
            return None
        
        # Decode base64 to bytes
        base64_data = icons[icon_name]
        image_data = base64.b64decode(base64_data)
        
        # Create image from bytes
        data = io.BytesIO(image_data)
        return CoreImage(data, ext='png')
    
    @classmethod
    def has_icon(cls, icon_name: str) -> bool:
        """Check if an icon exists."""
        icons = cls._load_icons_data()
        return icon_name in icons


# Convenience function
def load_icon(icon_name: str) -> Optional[CoreImage]:
    """
    Load an icon by name.
    
    Usage:
        icon = load_icon('note')
        if icon:
            image_widget = Image(texture=icon.texture)
    """
    return IconLoader.load_icon(icon_name)


__all__ = ['IconLoader', 'load_icon']
