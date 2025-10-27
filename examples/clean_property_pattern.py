"""
Clean inheritance pattern using @property with minimal boilerplate.
"""
from dataclasses import dataclass, field as dataclass_field
from dataclasses_json import dataclass_json
from typing import Optional, TYPE_CHECKING, Literal, Any
if TYPE_CHECKING:
    from file.SCORE import SCORE


def _make_inherit_property(field_name: str, inherit_path: str, fallback: Any = None):
    """
    Factory to create a property with inheritance logic.
    
    This reduces boilerplate - you define the path once, get both getter and setter.
    """
    private_name = f'_{field_name}'
    
    def getter(self) -> Any:
        value = getattr(self, private_name, None)
        if value is not None:
            return value
        
        # Resolve inheritance path
        score = getattr(self, '_score', None)
        if score:
            parts = inherit_path.split('.')
            current = score
            for part in parts:
                current = getattr(current, part, None)
                if current is None:
                    break
            if current is not None:
                return current
        
        return fallback
    
    def setter(self, value: Any):
        setattr(self, private_name, value)
    
    return property(getter, setter)


@dataclass_json
@dataclass
class Note:
    """Example using the clean property pattern."""
    id: int = 0
    time: float = 0.0
    pitch: int = 40
    
    # Private backing fields (will be serialized)
    _color: Optional[str] = None
    _colorMidiNote: Optional[str] = None
    _blackNoteDirection: Optional[Literal['^', 'v']] = None
    
    # Public properties with inheritance (3 lines each)
    color = _make_inherit_property('color', 'properties.globalNote.color', '#000000')
    colorMidiNote = _make_inherit_property('colorMidiNote', 'properties.globalNote.colorMidiNote', '#000000')
    blackNoteDirection = _make_inherit_property('blackNoteDirection', 'properties.globalNote.blackNoteDirection', 'v')


# Usage:
# note.color  # Auto-resolves if None
# note.color = '#FF0000'  # Set explicit
# note.color = None  # Back to inherit
