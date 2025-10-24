from pydantic import BaseModel, Field
from typing import Literal, TYPE_CHECKING, Optional
from file.inherit_field import InheritMixin
if TYPE_CHECKING: 
    from file.SCORE import SCORE

class Text(InheritMixin, BaseModel):
    # Inheritance configuration
    _INHERIT_CONFIG = {
        'fontSize': ('_fontSize', 'properties.globalText.fontSize', 12),
        'color': ('_color', 'properties.globalText.color', '#000000'),
    }
    # Core fields
    id: int = Field(default=0)
    time: float = Field(default=0.0, description="time y position")
    side: Literal['<', '>'] = Field(default='>', description="left or right of staff")
    distFromSide: float = Field(default=10.0, description="distance from side in mm")
    text: str = Field(default='Text')
    
    # Private storage for inheritable fields
    _fontSize: Optional[int] = Field(default=None, alias='fontSize', description="Font size, None to inherit from globalText")
    _color: Optional[str] = Field(default=None, alias='color', description="Color, None to inherit from globalText")
    
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
            object.__setattr__(self, 'score', score)
    
    # InheritMixin provides __getattribute__/__setattr__/set_score_reference

    def get_literal_value(self, field_name: str):
        """Get the actual stored value without inheritance."""
        private_name = f'_{field_name}' if not field_name.startswith('_') else field_name
        return super().__getattribute__(private_name)
    
    # set_score_reference inherited from InheritMixin
