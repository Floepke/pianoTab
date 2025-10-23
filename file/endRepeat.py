from pydantic import BaseModel, Field
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from file.SCORE import SCORE

class EndRepeat(BaseModel):
    # Core fields
    id: int = Field(default=0)
    time: float = Field(default=0.0)
    
    # Inheritable fields - None means inherit from global properties
    color: Optional[str] = Field(default=None, description="Color, None to inherit from globalEndrepeat")
    lineWidth: Optional[float] = Field(default=None, description="Line width, None to inherit from globalEndrepeat")
    
    # Score reference (not serialized to JSON)
    score: Optional['SCORE'] = Field(default=None, exclude=True)
    
    class Config:
        extra = 'forbid'
        use_enum_values = True
        arbitrary_types_allowed = True
    
    def __init__(self, **data):
        # Extract score reference to set after initialization
        score = data.pop('score', None)
        super().__init__(**data)
        if score is not None:
            object.__setattr__(self, 'score', score)
    
    def __getattribute__(self, name: str):
        """Handle property inheritance transparently."""
        # Allow access to private/special attributes and methods
        if (name.startswith('_') or name in ('dict', 'json', 'copy', '__fields__', 'Config', 'score') or
            hasattr(BaseModel, name)):
            return super().__getattribute__(name)
        
        # Get the stored value
        value = super().__getattribute__(name)
        
        # Check if this field should inherit (value is None)
        if value is None and name in ['color', 'lineWidth']:
            return self._get_inherited_value(name)
        
        return value
    
    def _get_inherited_value(self, field_name: str):
        """Get the inherited value from global properties."""
        score = super().__getattribute__('score')
        if score is None:
            return self._get_default_value(field_name)
        
        if field_name == 'color':
            return score.properties.globalEndrepeat.color
        elif field_name == 'lineWidth':
            return score.properties.globalEndrepeat.lineWidth
        
        return self._get_default_value(field_name)
    
    def _get_default_value(self, field_name: str):
        """Get default values when no score reference."""
        defaults = {
            'color': '#000000',
            'lineWidth': 2.0
        }
        return defaults.get(field_name, None)
    
    def get_literal_value(self, field_name: str):
        """Get the actual stored value without inheritance."""
        return super().__getattribute__(field_name)
    
    def set_score_reference(self, score: 'SCORE'):
        """Set the score reference for inheritance."""
        object.__setattr__(self, 'score', score)