from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from typing import Literal, TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from file.SCORE import SCORE

@dataclass_json
@dataclass
class Beam:
    id: int = 0
    time: float = 0.0
    staff: float = 0.0
    hand: Literal['<', '>'] = '<'
    
    # Storage fields for inherited properties (serialize to JSON with clean names)
    _color: Optional[str] = field(default=None, metadata=config(field_name='color'))
    _width: Optional[float] = field(default=None, metadata=config(field_name='width'))
    _slant: Optional[float] = field(default=None, metadata=config(field_name='slant'))
    
    def __post_init__(self):
        """Initialize score reference as a non-dataclass attribute."""
        self.score: Optional['SCORE'] = None
    
    # Property: color
    @property
    def color(self) -> str:
        """Get color - inherits from globalBeam.color if None."""
        if self._color is not None:
            return self._color
        if self.score is None:
            print("Warning: Beam has no score reference for property inheritance.")
            return '#000000'  # Fallback if no score reference
        return self.score.properties.globalBeam.color
    
    @color.setter
    def color(self, value: Optional[str]):
        """Set color - use None to reset to inheritance."""
        self._color = value
    
    # Property: width
    @property
    def width(self) -> float:
        """Get width - inherits from globalBeam.width if None."""
        if self._width is not None:
            return self._width
        if self.score is None:
            print("Warning: Beam has no score reference for property inheritance.")
            return 4.0  # Fallback if no score reference
        return self.score.properties.globalBeam.width
    
    @width.setter
    def width(self, value: Optional[float]):
        """Set width - use None to reset to inheritance."""
        self._width = value
    
    # Property: slant
    @property
    def slant(self) -> float:
        """Get slant - inherits from globalBeam.slant if None."""
        if self._slant is not None:
            return self._slant
        if self.score is None:
            print("Warning: Beam has no score reference for property inheritance.")
            return 5.0  # Fallback if no score reference
        return self.score.properties.globalBeam.slant
    
    @slant.setter
    def slant(self, value: Optional[float]):
        """Set slant - use None to reset to inheritance."""
        self._slant = value