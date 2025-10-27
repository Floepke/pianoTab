"""
Inheritance field system for automatic None-based property resolution.

This allows fields to automatically resolve to a path in the score when None:
    color: Optional[str] = inherit_field('properties.globalNote.color')

Access works naturally:
    note.color  # Returns '#FF0000' if None, resolving from globalNote.color
    note.color = '#AAAAAA'  # Set explicit value
    note.color = None  # Reset to inherit
"""
from dataclasses import field
from typing import Any, Optional


def inherit_field(inherit_path: str, default: Any = None):
    """
    Create a dataclass field that inherits from a score path when None.
    
    Args:
        inherit_path: Dot-notation path to inherit from (e.g., 'properties.globalNote.color')
        default: Default value (should be None for inheritance)
    
    Returns:
        A dataclass field with metadata for inheritance resolution
    
    Example:
        color: Optional[str] = inherit_field('properties.globalNote.color')
    """
    return field(
        default=default,
        metadata={
            'inherit_path': inherit_path,
            'is_inheritable': True
        }
    )


def resolve_inherit_path(obj: Any, path: str) -> Any:
    """
    Resolve a dot-notation path on an object.
    
    Args:
        obj: Object to start from (usually a SCORE instance)
        path: Dot-notation path (e.g., 'properties.globalNote.color')
    
    Returns:
        The value at the path, or None if not found
    """
    parts = path.split('.')
    current = obj
    
    for part in parts:
        if current is None:
            return None
        current = getattr(current, part, None)
    
    return current
