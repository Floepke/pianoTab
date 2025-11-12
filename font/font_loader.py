"""
Embedded font loader for FiraCode-SemiBold.
Extracts the base64-encoded font and registers it with Kivy.
"""
import base64
import os
import tempfile
from kivy.core.text import LabelBase
from font.font_data import FIRACODE_SEMIBOLD_B64

# Font name that will be used throughout the app
FONT_NAME = 'FiraCode'

# Temporary file path for the extracted font
_font_file_path = None

def load_embedded_font():
    """
    Extract the embedded font from base64 and register it with Kivy.
    This should be called once at app startup, before creating any widgets.
    
    Returns:
        str: The font name to use in Kivy ('FiraCode')
    """
    global _font_file_path
    
    if _font_file_path is not None:
        # Already loaded
        return FONT_NAME
    
    try:
        # Decode base64 font data
        font_bytes = base64.b64decode(FIRACODE_SEMIBOLD_B64)
        
        # Create a temporary file for the font
        # We use delete=False because Kivy needs the file to persist
        temp_file = tempfile.NamedTemporaryFile(
            prefix='firacode_',
            suffix='.ttf',
            delete=False
        )
        _font_file_path = temp_file.name
        
        # Write font bytes to temporary file
        temp_file.write(font_bytes)
        temp_file.close()
        
        # Register font with Kivy
        LabelBase.register(
            name=FONT_NAME,
            fn_regular=_font_file_path
        )
        
        print(f"✓ Font '{FONT_NAME}' loaded and registered successfully")
        print(f"  Temp file: {_font_file_path}")
        
        return FONT_NAME
        
    except Exception as e:
        print(f"✗ Error loading embedded font: {e}")
        # Fall back to default Kivy font
        return 'Roboto'

def cleanup_font():
    """
    Clean up the temporary font file.
    Should be called when the app exits.
    """
    global _font_file_path
    
    if _font_file_path and os.path.exists(_font_file_path):
        try:
            os.unlink(_font_file_path)
            print(f"✓ Cleaned up temporary font file: {_font_file_path}")
        except Exception as e:
            print(f"✗ Error cleaning up font file: {e}")
        finally:
            _font_file_path = None

def get_font_name():
    """
    Get the registered font name.
    If the font hasn't been loaded yet, this will load it.
    
    Returns:
        str: The font name ('FiraCode' or 'Roboto' if loading failed)
    """
    if _font_file_path is None:
        return load_embedded_font()
    return FONT_NAME
