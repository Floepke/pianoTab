from pydantic import BaseModel, Field
from typing import TYPE_CHECKING, Optional
from file.inherit_field import InheritMixin
if TYPE_CHECKING:
    from file.SCORE import SCORE

class Articulation(InheritMixin, BaseModel):
    _INHERIT_CONFIG = {
        'color': ('_color', 'properties.globalArticulation.color', '#000000'),
    }
    
    # Core fields
    type: str = Field(default='staccato')
    xOffset: float = Field(default=0.0)
    yOffset: float = Field(default=0.0)
    
    # Private storage for inheritable fields
    _color: Optional[str] = Field(default=None, alias='color', description="Color, None to inherit from globalArticulation")
    
    # Score reference (not serialized to JSON)
    score: Optional['SCORE'] = Field(default=None, exclude=True)
    
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
            self.set_score_reference(score)
    
    def get_literal_value(self, field_name: str):
        """Get the actual stored value without inheritance."""
        private_name = f'_{field_name}' if not field_name.startswith('_') else field_name
        return getattr(self, private_name, None)