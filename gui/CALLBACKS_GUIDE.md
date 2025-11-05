# Callback Configuration Guide

This guide explains how to add new menu items and toolbar buttons to pianoTAB using the centralized callback system.

## Overview

All UI callbacks are now centralized in `gui/callbacks.py`. This provides a single place to:
- Define menu bar configurations
- Define toolbar button configurations
- Map action names to their implementations

## File Structure

```
gui/
├── callbacks.py          # Centralized callback configurations
├── menu_bar.py          # MenuBar widget (uses configs)
├── split_view.py        # SplitView with ToolSash (uses button configs)
└── toolsash.py          # Main GUI (implements callback methods)
```

## Adding a New Menu Item

### Step 1: Define the configuration in `callbacks.py`

Edit the `create_menu_config()` function:

```python
def create_menu_config(app_instance) -> MenuConfig:
    return {
        'File': {
            'New': app_instance.on_new,
            'Open': (app_instance.on_open, 'Ctrl+O'),  # With keyboard shortcut
            '---': None,  # Separator
            'Export': {  # Submenu
                'PDF': app_instance.on_export_pdf,
                'PNG': app_instance.on_export_png,
            },
            'Exit': app_instance.on_exit
        },
        # Add more menus...
    }
```

### Step 2: Implement the method in `toolsash.py`

Add the corresponding method to the `pianoTABGUI` class:

```python
def on_export_pdf(self):
    """Export current score to PDF."""
    print("Exporting to PDF...")
    # Your implementation here
```

## Adding a New Toolbar Button

### Step 1: Ensure the icon exists

Check if your icon exists in `icons/icons_data.py` under the `ICONS` dictionary.

If not, create the icon:
1. Create an `.ezdraw` file in `icons/icondesign/`
2. Run `python icons/precompile_icons.py` to generate the icon data

### Step 2: Add to button configuration in `callbacks.py`

Edit the `create_button_config()` function:

```python
def create_button_config(app_instance) -> ButtonConfig:
    return {
        "note2left": app_instance.on_note_to_left,
        "note2right": app_instance.on_note_to_right,
        "note": app_instance.on_add_note,
        "gracenote": app_instance.on_add_grace_note,  # New button!
    }
```

### Step 3: (Optional) Add to default buttons list

If you want the button to appear by default (not just when referenced in config):

```python
def get_default_sash_buttons() -> List[str]:
    return [
        "note2left",
        "note2right",
        "gracenote",  # Will appear by default
    ]
```

### Step 4: Implement the method in `toolsash.py`

Add the corresponding method:

```python
def on_add_grace_note(self):
    """Add a grace note at current position."""
    print("Adding grace note")
    # Your implementation here
```

## Configuration Format Reference

### Menu Items

```python
{
    'Menu Name': {
        # Simple menu item
        'Item': callback_function,
        
        # Menu item with keyboard shortcut/tooltip
        'Item': (callback_function, 'Ctrl+S'),
        
        # Disabled/placeholder item
        'Item': None,
        
        # Separator
        '---': None,
        
        # Submenu
        'Submenu': {
            'SubItem1': callback_function,
            'SubItem2': callback_function,
        }
    },
    
    # Direct button (no dropdown)
    'Help': callback_function
}
```

### Button Config

```python
{
    # Key is used as:
    # 1. Icon name lookup in icons_data.ICONS
    # 2. Fallback button text if icon not found
    "icon_name": callback_function,
    "another_button": callback_function,
}
```

## How It Works

### Menu Bar
1. `pianoTABGUI.__init__()` creates the GUI instance
2. `setup_layout()` calls `create_menu_config(self)` to get menu configuration
3. Configuration is passed to `MenuBar(menu_config)`
4. MenuBar creates buttons/dropdowns based on the config
5. When user clicks, the bound callback method is invoked on `self` (the GUI instance)

### Toolbar Buttons
1. `SplitView` creates a `ToolSash` widget
2. `ToolSash.__init__()` reads `BUTTON_CONFIG` from `callbacks.py`
3. For each button key, it:
   - Looks up the icon in `icons_data.ICONS`
   - Creates an `IconButton` or text `Button`
   - Binds the callback from `BUTTON_CONFIG`
4. When user clicks, the callback is invoked

## Example: Adding a "Tempo" Button

### 1. Create icon (optional, can use text fallback)
```bash
# Create icons/icondesign/tempo.ezdraw with your icon
python icons/precompile_icons.py
```

### 2. Add to `callbacks.py`
```python
def create_button_config(app_instance) -> ButtonConfig:
    return {
        "note2left": app_instance.on_note_to_left,
        "note2right": app_instance.on_note_to_right,
        "note": app_instance.on_add_note,
        "tempo": app_instance.on_set_tempo,  # NEW!
    }
```

### 3. Implement in `toolsash.py`
```python
def on_set_tempo(self):
    """Open tempo setting dialog."""
    print("Setting tempo...")
    # Show tempo input dialog
    # Update score with new tempo
```

### 4. Done!
The button will now appear automatically in the sash toolbar.

## Benefits of This Approach

✅ **Single Source of Truth**: All UI action mappings in one place
✅ **Easy to Extend**: Just add config + implement method
✅ **Type Safety**: Using type hints for clarity
✅ **Automatic Discovery**: Buttons auto-appear when added to config
✅ **Clean Separation**: Config separate from implementation
✅ **No Legacy Code**: Clean architecture without deprecated files
