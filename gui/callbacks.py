"""
Centralized callback configuration for all UI elements.

This module contains all callback configurations for:
- Menu bar (File, Edit, View, Help menus)
- Toolbar buttons (sash buttons between editor and preview)
- Other UI action mappings

All callbacks are defined as dictionaries that map action names to their
corresponding handler functions. The actual handler functions should be
provided by the main application/GUI class.

Configuration format examples:
    - dict value: Creates dropdown menu (menu bar)
    - callable: Menu item or button callback
    - (callable, str): Callback with tooltip/shortcut hint
    - None: Disabled/placeholder action
    - '---' key: Separator (menu bar only)
"""

from typing import Callable, Dict, Optional, Tuple, Union, List


# Type aliases for clarity
MenuItemValue = Union[Callable[[], None], Tuple[Callable[[], None], str], None, Dict]
MenuConfig = Dict[str, MenuItemValue]
ButtonConfig = Dict[str, Callable[[], None]]


def create_menu_config(app_instance) -> MenuConfig:
    """
    Create menu bar configuration bound to application instance methods.
    
    Args:
        app_instance: The main application/GUI instance that provides callback methods
        
    Returns:
        Dictionary mapping menu names to their items and callbacks
        
    Example structure:
        {
            'File': {
                'New': app.on_new,
                'Open': (app.on_open, 'Ctrl+O'),
                '---': None,  # Separator
                'Exit': app.on_exit
            },
            'Help': app.on_help  # Direct button (no dropdown)
        }
    """
    return {
        'File': {
            'New': app_instance.on_new,
            'Load...': (app_instance.on_load, 'cmd / ctrl + o'),
            'Save': app_instance.on_save,
            'Save as...': app_instance.on_save_as,
            '---': None,  # Separator
            'Exit': app_instance.on_exit
        },
        'Edit': {
            'Undo': None,  # TODO: Implement
            'Redo': None,  # TODO: Implement
            '---': None,  # Separator
            'Cut': None,   # TODO: Implement
            'Copy': None,  # TODO: Implement
            'Paste': None  # TODO: Implement
        },
        'Help': {
            'About': app_instance.on_about
        }
    }


def create_button_config(app_instance) -> ButtonConfig:
    """
    Create toolbar button configuration bound to application instance methods.
    
    Args:
        app_instance: The main application/GUI instance that provides callback methods
        
    Returns:
        Dictionary mapping button keys (icon names) to their callbacks
        
    Notes:
        - Keys double as icon names (looked up in icons_data.ICONS)
        - If icon doesn't exist, key is used as button text
        - Values are callables invoked when button is pressed
        
    Example:
        {
            'note2left': app.move_note_to_left_hand,
            'note2right': app.move_note_to_right_hand,
            'note': app.add_note
        }
    """
    return {
        # Sash toolbar buttons (between editor and preview)
        "note2left": app_instance.on_note_to_left,
        "note2right": app_instance.on_note_to_right,
        "note": app_instance.on_add_note,
    }


def get_default_sash_buttons() -> List[str]:
    """
    Get the default list of buttons to show in the sash toolbar.
    
    Returns:
        List of button keys that should appear by default
        
    Notes:
        The ToolSash widget will automatically append any additional buttons
        from BUTTON_CONFIG that aren't in this list.
    """
    return [
        "note2left",
        "note2right",
    ]


# Placeholder implementations for demonstration
def _not_implemented(action: str) -> Callable[[], None]:
    """
    Create a placeholder callback for unimplemented actions.
    
    Args:
        action: Name of the action (for logging/debugging)
        
    Returns:
        A callable that prints a not-implemented message
    """
    def _cb():
        print(f"Action '{action}' not implemented")
    return _cb


# Legacy standalone configs for backwards compatibility
# (These should be replaced by calling the create_* functions with an app instance)

BUTTON_CONFIG: ButtonConfig = {
    "note2left": _not_implemented("note2left"),
    "note2right": _not_implemented("note2right"),
    "note": _not_implemented("note"),
}

DEFAULT_SASH_BUTTONS: List[str] = get_default_sash_buttons()


__all__ = [
    "create_menu_config",
    "create_button_config",
    "get_default_sash_buttons",
    "BUTTON_CONFIG",
    "DEFAULT_SASH_BUTTONS",
    "MenuConfig",
    "ButtonConfig",
]
