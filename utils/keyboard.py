"""Keyboard utilities for cross-platform key mapping.

Handles platform-specific key mappings, especially macOS cmd/ctrl equivalence.

USAGE IN YOUR CODE:
-------------------
Just use 'ctrl+x' in your shortcut definitions, and this module automatically
handles both Ctrl+X and Cmd+X on macOS:

    from utils.keyboard import matches_shortcut
    
    def on_key_press(self, key, x, y, modifiers):
        if matches_shortcut(key, modifiers, 'c', 'ctrl+c'):
            # This works with:
            # - Just 'C' on all platforms
            # - Ctrl+C on Linux/Windows
            # - BOTH Ctrl+C AND Cmd+C on macOS
            self.copy()
            
        elif matches_shortcut(key, modifiers, 'ctrl+v'):
            # This works with:
            # - Ctrl+V on Linux/Windows
            # - BOTH Ctrl+V AND Cmd+V on macOS
            self.paste()

No need to think about macOS separately - it just works!
"""

import sys
from typing import List, Tuple


def normalize_key(key: str, modifiers: List[str] = None) -> Tuple[str, str]:
    """Normalize key and modifiers for cross-platform compatibility.
    
    On macOS, both 'ctrl' and 'cmd' (meta) modifiers are treated as equivalent.
    This allows shortcuts like 'ctrl+c' to work with both Ctrl+C and Cmd+C on macOS.
    
    Args:
        key: The key name (e.g., 'c', 'ctrl+c', 'x')
        modifiers: List of active modifiers from Kivy (e.g., ['ctrl'], ['meta'])
        
    Returns:
        Tuple of (normalized_key, modifier_key)
        - normalized_key: Just the letter/key without modifiers (e.g., 'c')
        - modifier_key: The key with platform-normalized modifier (e.g., 'ctrl+c')
    """
    if modifiers is None:
        modifiers = []
    
    is_macos = sys.platform == 'darwin'
    
    # Check if key already has ctrl+ prefix
    has_ctrl_prefix = key.startswith('ctrl+')
    base_key = key.replace('ctrl+', '') if has_ctrl_prefix else key
    
    # Normalize modifiers for macOS: treat 'meta' (cmd) same as 'ctrl'
    normalized_modifiers = set(modifiers)
    if is_macos:
        # On macOS, if either ctrl or meta (cmd) is pressed, treat as ctrl
        if 'meta' in normalized_modifiers or 'ctrl' in normalized_modifiers:
            normalized_modifiers.add('ctrl')
    
    # Build the modifier key string
    if 'ctrl' in normalized_modifiers or has_ctrl_prefix:
        modifier_key = f'ctrl+{base_key}'
    else:
        modifier_key = base_key
    
    return base_key, modifier_key


def matches_shortcut(key: str, modifiers: List[str], *shortcuts: str) -> bool:
    """Check if a key+modifiers combination matches any of the given shortcuts.
    
    On macOS, both Ctrl and Cmd (meta) are treated as equivalent for 'ctrl+' shortcuts.
    
    Args:
        key: The key name from Kivy event
        modifiers: List of modifier keys currently pressed
        *shortcuts: One or more shortcut strings to match against (e.g., 'c', 'ctrl+c')
        
    Returns:
        True if the key combination matches any of the shortcuts
        
    Examples:
        >>> # On macOS with Cmd+C pressed:
        >>> matches_shortcut('c', ['meta'], 'c', 'ctrl+c')
        True
        
        >>> # On macOS with Ctrl+C pressed:
        >>> matches_shortcut('c', ['ctrl'], 'c', 'ctrl+c')
        True
        
        >>> # On Linux with Ctrl+C pressed:
        >>> matches_shortcut('c', ['ctrl'], 'c', 'ctrl+c')
        True
        
        >>> # Just 'c' pressed (no modifiers):
        >>> matches_shortcut('c', [], 'c', 'ctrl+c')
        True  # Matches 'c' shortcut
    """
    base_key, modifier_key = normalize_key(key, modifiers)
    
    # Check if either the base key or modifier key matches any shortcut
    for shortcut in shortcuts:
        if shortcut == base_key or shortcut == modifier_key:
            return True
        
        # Also check if the shortcut itself is a ctrl+ variant and we have the modifier
        if shortcut.startswith('ctrl+'):
            shortcut_base = shortcut.replace('ctrl+', '')
            if base_key == shortcut_base and 'ctrl' in (modifiers or []):
                return True
            # On macOS, also check for meta (cmd) key
            if sys.platform == 'darwin':
                if base_key == shortcut_base and 'meta' in (modifiers or []):
                    return True
    
    return False


def get_shortcut_display(shortcut: str) -> str:
    """Get the display string for a shortcut on the current platform.
    
    On macOS, shows Cmd instead of Ctrl for ctrl+ shortcuts.
    
    Args:
        shortcut: The shortcut string (e.g., 'ctrl+c')
        
    Returns:
        Platform-appropriate display string (e.g., 'Cmd+C' on macOS, 'Ctrl+C' elsewhere)
    """
    if sys.platform == 'darwin':
        # Replace ctrl with Cmd symbol or text for macOS
        shortcut = shortcut.replace('ctrl+', '⌘')
    
    # Capitalize the key
    parts = shortcut.split('+')
    if len(parts) > 1:
        parts[-1] = parts[-1].upper()
        return '+'.join(parts)
    else:
        return shortcut.upper()
