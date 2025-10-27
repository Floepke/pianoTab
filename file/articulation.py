from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from typing import TYPE_CHECKING, Union, Literal, Optional
if TYPE_CHECKING:
    from file.SCORE import SCORE

@dataclass_json
@dataclass
class Articulation:
    # Core fields
    type: str = 'staccato'
    xOffset: float = 0.0
    yOffset: float = 0.0

    # Storage field for inherited property (serializes to JSON with clean name)
    _color: Optional[str] = field(default=None, metadata=config(field_name='color'))
    
    def __post_init__(self):
        """Initialize score reference as a non-dataclass attribute."""
        self.score: Optional['SCORE'] = None
    
    # Property: color
    @property
    def color(self) -> str:
        """Get color - inherits from globalArticulation.color if None."""
        if self._color is not None:
            return self._color
        if self.score is None:
            return '#000000'  # Fallback if no score reference
        return self.score.properties.globalArticulation.color
    
    @color.setter
    def color(self, value: Optional[str]):
        """Set color - use None to reset to inheritance."""
        self._color = value
