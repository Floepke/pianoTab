"""
Inheritance using __getattribute__ override.
WARNING: This is complex and can cause issues with dataclasses-json!
"""
from dataclasses import dataclass, field, fields
from dataclasses_json import dataclass_json
from typing import Optional, Literal, Any, TYPE_CHECKING
if TYPE_CHECKING:
    from file.SCORE import SCORE


# Registry of inherit paths
INHERIT_PATHS = {
    'color': 'properties.globalNote.color',
    'colorMidiNote': 'properties.globalNote.colorMidiNote',
    'blackNoteDirection': 'properties.globalNote.blackNoteDirection',
}


@dataclass_json
@dataclass
class Note:
    """Using __getattribute__ to intercept attribute access."""
    id: int = 0
    time: float = 0.0
    pitch: int = 40
    
    # These fields can be None
    color: Optional[str] = None
    colorMidiNote: Optional[str] = None
    blackNoteDirection: Optional[Literal['^', 'v']] = None
    
    def __getattribute__(self, name: str) -> Any:
        # Get the actual value using object.__getattribute__ to avoid recursion
        value = object.__getattribute__(self, name)
        
        # If it's an inheritable field and value is None
        if name in INHERIT_PATHS and value is None:
            score = object.__getattribute__(self, '_score') if hasattr(self, '_score') else None
            if score:
                # Resolve the path
                path = INHERIT_PATHS[name]
                parts = path.split('.')
                current = score
                for part in parts:
                    current = getattr(current, part, None)
                    if current is None:
                        break
                if current is not None:
                    return current
        
        return value


# PROBLEMS with this approach:
# 1. __getattribute__ is called on EVERY attribute access - slow!
# 2. Can break dataclasses-json serialization
# 3. Hard to debug
# 4. Can cause infinite recursion if not careful
# 5. Breaks IDE autocomplete and type checking
