"""Integrated clipboard system for pianoTab.

Provides clipboard functionality that works entirely within the app,
with optional xclip integration when available on the system.

This is a MUSICAL CLIPBOARD for copying/pasting notes and musical elements.
Text entry widgets should use their native Kivy clipboard for Ctrl+C/V.
"""

import subprocess
import shutil
from typing import Optional, Any, Dict, List
import json


class AppClipboard:
    """Internal clipboard with optional system clipboard sync via xclip.
    
    This clipboard is specifically for musical elements (notes, beams, etc.),
    NOT for text input fields. Text fields use Kivy's native clipboard.
    """
    
    def __init__(self):
        self._data: Optional[Dict[str, Any]] = None
        self._has_xclip = shutil.which('xclip') is not None
        
        if self._has_xclip:
            print("AppClipboard: xclip available - will sync musical data to system clipboard")
        else:
            print("AppClipboard: xclip not available - using internal clipboard only")
    
    def copy(self, data: Dict[str, Any]) -> None:
        """Store musical data in internal clipboard and sync to system if xclip available.
        
        Args:
            data: Dictionary containing musical elements (notes, etc.)
                  Must have a 'type' key (e.g., 'notes', 'beams', etc.)
        """
        if not isinstance(data, dict) or 'type' not in data:
            print("AppClipboard: Invalid data format - must be dict with 'type' key")
            return
        
        # Store internally
        self._data = data
        print(f"AppClipboard: Stored {data.get('type')} data internally")
        
        # Sync to system clipboard if xclip available
        if self._has_xclip:
            try:
                # Serialize to JSON for system clipboard
                json_str = json.dumps(data, indent=2)
                subprocess.run(
                    ['xclip', '-selection', 'clipboard'],
                    input=json_str.encode('utf-8'),
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=1.0  # Prevent hanging
                )
                print("AppClipboard: Synced to system clipboard via xclip")
            except Exception as e:
                # Silent fail - internal clipboard still works
                print(f"AppClipboard: xclip sync failed (internal clipboard still works): {e}")
    
    def paste(self) -> Optional[Dict[str, Any]]:
        """Retrieve musical data from internal clipboard.
        
        Returns:
            The stored musical data dict, or None if clipboard is empty
        """
        return self._data
    
    def paste_from_system(self) -> Optional[Dict[str, Any]]:
        """Try to paste musical data from system clipboard via xclip.
        
        Returns:
            Parsed musical data dict from system clipboard, or None if unavailable
        """
        if not self._has_xclip:
            return None
        
        try:
            result = subprocess.run(
                ['xclip', '-selection', 'clipboard', '-o'],
                capture_output=True,
                text=True,
                check=True,
                timeout=1.0
            )
            # Try to parse as JSON
            data = json.loads(result.stdout)
            if isinstance(data, dict) and 'type' in data:
                return data
        except Exception:
            # Not valid musical data - ignore
            pass
        
        return None
    
    def clear(self) -> None:
        """Clear internal clipboard."""
        self._data = None
    
    def has_data(self) -> bool:
        """Check if clipboard contains musical data."""
        return self._data is not None
    
    def get_type(self) -> Optional[str]:
        """Get the type of data in clipboard (e.g., 'notes', 'beams')."""
        if self._data and 'type' in self._data:
            return self._data['type']
        return None


# Global clipboard instance for musical elements
_clipboard = AppClipboard()


def copy(data: Dict[str, Any]) -> None:
    """Copy musical data to clipboard.
    
    Args:
        data: Dict with 'type' key and musical element data
    """
    _clipboard.copy(data)


def paste() -> Optional[Dict[str, Any]]:
    """Paste musical data from clipboard.
    
    Returns:
        Musical data dict or None
    """
    return _clipboard.paste()


def paste_from_system() -> Optional[Dict[str, Any]]:
    """Paste musical data from system clipboard (if xclip available).
    
    Returns:
        Musical data dict or None
    """
    return _clipboard.paste_from_system()


def clear() -> None:
    """Clear clipboard."""
    _clipboard.clear()


def has_data() -> bool:
    """Check if clipboard has musical data."""
    return _clipboard.has_data()


def get_type() -> Optional[str]:
    """Get type of data in clipboard."""
    return _clipboard.get_type()
