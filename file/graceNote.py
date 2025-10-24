from pydantic import BaseModel, Field
from typing import TYPE_CHECKING, Optional
from file.inherit_field import InheritMixin
if TYPE_CHECKING:
    from file.SCORE import SCORE

class GraceNote(InheritMixin, BaseModel):
    # Core fields
    id: int = Field(default=0)
    time: float = Field(default=0.0)
    pitch: int = Field(default=60)
    velocity: int = Field(default=80)
    
    # Private storage for inheritable fields
    _color: Optional[str] = Field(default=None, alias='color', description="Color of the grace note, None to inherit from globalGraceNote")
    
    # Score reference (not serialized to JSON)
    score: Optional['SCORE'] = Field(default=None, exclude=True)

    # Inheritance configuration
    _INHERIT_CONFIG = {
        'color': ('_color', 'properties.globalGraceNote.color', '#000000'),
    }
    
    class Config:
        extra = 'ignore'
        use_enum_values = True
        arbitrary_types_allowed = True
        populate_by_name = True
    
    def __init__(self, **data):
        # Extract score reference to set after initialization
        score = data.pop('score', None)
        super().__init__(**data)
        if score is not None:
            object.__setattr__(self, 'score', score)
    
    # InheritMixin provides __getattribute__/__setattr__/set_score_reference
    
    def get_literal_value(self, field_name: str):
        """Get the actual stored value without inheritance."""
        private_name = f'_{field_name}' if not field_name.startswith('_') else field_name
        return super().__getattribute__(private_name)
    
    # set_score_reference inherited from InheritMixin
