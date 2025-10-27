"""
Universal inheritance property factory for Event classes.

This module provides a clean way to define inheritable properties
that automatically resolve from globalProperties when None.

Usage in any Event class:
    from file.inherit_property import inherit_property
    
    @dataclass_json
    @dataclass
    class Note:
        color: Optional[str] = None  # Regular field for serialization
        
    # After class definition, enhance fields with inheritance
    Note.color = inherit_property('color', 'properties.globalNote.color', '#000000')
        
Then use naturally:
    note.color  # Auto-resolves if None
    note.color = '#FF0000'  # Set explicit
    note.color = None  # Back to inherit
"""
from typing import Any, Optional, Callable


def inherit_property(field_name: str, inherit_path: str, fallback: Any = None, 
                     resolver: Optional[Callable] = None):
    """
    Create a property that inherits from a score path when None.
    
    This wraps an existing dataclass field to add inheritance resolution.
    The original field remains for serialization compatibility.
    
    Args:
        field_name: Name of the dataclass field (e.g., 'color')
        inherit_path: Dot-notation path to inherit from (e.g., 'properties.globalNote.color')
                     Can also be a callable: lambda self, score: score.properties...
        fallback: Default value if score reference not available
        resolver: Optional custom function(self, score) -> value for complex logic
    
    Returns:
        A property object with getter/setter that handles inheritance
    
    Examples:
        # Simple path
        color = inherit_property('color', 'properties.globalNote.color', '#000000')
        
        # Custom resolver for complex logic
        def resolve_midi_color(self, score):
            if self.hand == '<':
                return score.properties.globalNote.colorLeftMidiNote
            return score.properties.globalNote.colorRightMidiNote
        
        colorMidiNote = inherit_property('colorMidiNote', None, '#000000', resolve_midi_color)
    """
    # Store the original field value in a private attribute
    private_name = f'_inherit_{field_name}'
    
    def getter(self) -> Any:
        """Get value, resolving inheritance if None."""
        # Get the actual field value
        value = getattr(self, private_name, None)
        if value is not None:
            return value
        
        # Try to resolve from score
        score = getattr(self, 'score', None)
        if score:
            # Use custom resolver if provided
            if resolver:
                result = resolver(self, score)
                if result is not None:
                    return result
            
            # Use path if provided
            elif inherit_path:
                # Navigate the path
                parts = inherit_path.split('.')
                current = score
                for part in parts:
                    current = getattr(current, part, None)
                    if current is None:
                        break
                if current is not None:
                    return current
        
        # Fallback if no score or path not found
        return fallback
    
    def setter(self, value: Any):
        """Set value. Use None to inherit."""
        setattr(self, private_name, value)
    
    return property(getter, setter)
