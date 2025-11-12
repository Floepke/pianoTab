"""
UI metadata utilities for SCORE model fields.

Provides a safe way to attach tooltip and editor hints to dataclass fields
without changing serialization or runtime behavior.
"""

from dataclasses import fields
from typing import Any, Optional


def get_field_tooltip(obj: Any, field_name: str) -> Optional[str]:
    """
    Extract tooltip from a dataclass field's metadata.
    
    Returns None if no tooltip is defined (safe fallback).
    
    Example:
        tooltip = get_field_tooltip(note, 'color')
        # Returns: "Color of the note head (inherits from globalNote.color if None)"
    """
    # Handle private fields with _ prefix
    actual_field_name = field_name
    if not field_name.startswith('_'):
        # Try both regular and private field names
        for f in fields(obj.__class__):
            if f.name == field_name or f.name == f'_{field_name}':
                actual_field_name = f.name
                break
    
    # Look up the field
    for f in fields(obj.__class__):
        if f.name == actual_field_name:
            metadata = f.metadata or {}
            return metadata.get('tree_tooltip')
    
    return None


def get_field_label(obj: Any, field_name: str) -> Optional[str]:
    """
    Extract custom label from a dataclass field's metadata.
    
    Returns None if no label is defined (will use field name).
    
    Example:
        label = get_field_label(note, 'duration')
        # Returns: "Duration (ticks)" or None
    """
    # Handle private fields with _ prefix
    actual_field_name = field_name
    if not field_name.startswith('_'):
        for f in fields(obj.__class__):
            if f.name == field_name or f.name == f'_{field_name}':
                actual_field_name = f.name
                break
    
    # Look up the field
    for f in fields(obj.__class__):
        if f.name == actual_field_name:
            metadata = f.metadata or {}
            return metadata.get('tree_label')
    
    return None
