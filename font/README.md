# Embedded Font System

This directory contains the embedded FiraCode-SemiBold font system for pianoTab.

## Files

- **FiraCode-SemiBold.ttf** - The original font file
- **encode_font.py** - Script to convert the font to base64
- **font_data.py** - Auto-generated base64 encoded font data (DO NOT EDIT)
- **font_loader.py** - Loads and registers the embedded font with Kivy
- **apply_font.py** - Configures Kivy widgets to use the font by default
- **__init__.py** - Package exports

## How It Works

1. **Encoding**: The `encode_font.py` script reads `FiraCode-SemiBold.ttf` and converts it to base64, saving the result in `font_data.py`.

2. **Loading**: At app startup, `font_loader.py`:
   - Decodes the base64 font data
   - Writes it to a temporary file
   - Registers it with Kivy as 'FiraCode'

3. **Application**: `apply_font.py` monkey-patches Kivy's Label, Button, and TextInput classes to use 'FiraCode' as their default font.

4. **Cleanup**: When the app closes, the temporary font file is deleted.

## Usage

The font system is automatically initialized in `pianotab.py`:

```python
from font import load_embedded_font, apply_default_font, cleanup_font

# In build():
load_embedded_font()
apply_default_font()

# In on_stop():
cleanup_font()
```

All text widgets will automatically use FiraCode unless you explicitly specify a different `font_name`.

## Updating the Font

If you replace `FiraCode-SemiBold.ttf` with a new version:

```bash
cd font
python3 encode_font.py
```

This will regenerate `font_data.py` with the new font data.

## Manual Font Usage

If you need to explicitly use the font (though this shouldn't be necessary):

```python
from font import FONT_NAME

Label(text='Hello', font_name=FONT_NAME)
```

## Benefits

- ✓ No external font dependencies
- ✓ Font is embedded in the compiled application
- ✓ Consistent appearance across all platforms
- ✓ Automatic application to all text widgets
- ✓ Easy to update the font file
