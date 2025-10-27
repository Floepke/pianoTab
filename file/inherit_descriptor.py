"""
Descriptor for inherited properties that resolve to None-based inheritance.
Allows intuitive usage: note.color = '#aaaaaa' or note.color = None
"""
from typing import Optional, Callable, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from file.SCORE import SCORE


class InheritDescriptor:
    """
    Descriptor that provides None-based inheritance with automatic resolution.
    
    Usage in dataclass:
        color: Optional[str] = None
        _color_inherit = InheritDescriptor('color', lambda self, score: score.properties.globalNote.color)
    
    Then use as:
        note.color = '#FF0000'  # Set explicit value
        note.color = None       # Inherit from global
        print(note.color)       # Automatically resolves inheritance
    """
    
    def __init__(self, field_name: str, inherit_path: Callable[[Any, 'SCORE'], Any], default: Any = None):
        """
        Args:
            field_name: Name of the dataclass field (e.g., 'color')
            inherit_path: Function that takes (self, score) and returns the inherited value
            default: Fallback value if no score reference exists
        """
        self.field_name = field_name
        self.private_name = f'_{field_name}'
        self.inherit_path = inherit_path
        self.default = default
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        
        # Get the private backing field value
        value = getattr(obj, self.private_name, None)
        
        # If not None, return the explicit value
        if value is not None:
            return value
        
        # Try to inherit from score
        score = getattr(obj, '_score', None)
        if score:
            return self.inherit_path(obj, score)
        
        # Fallback
        return self.default
    
    def __set__(self, obj, value):
        # Set the private backing field
        setattr(obj, self.private_name, value)
