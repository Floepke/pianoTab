from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from typing import List, TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from file.SCORE import SCORE

@dataclass_json
@dataclass
class CountLine:
    id: int = 0
    time: float = 0.0
    pitch1: int = 40
    pitch2: int = 44

    # Storage fields for inherited properties (serialize to JSON with clean names)
    _color: Optional[str] = field(default=None, metadata=config(field_name='color'))
    _dashPattern: Optional[List[int]] = field(default=None, metadata=config(field_name='dashPattern'))
    
    def __post_init__(self):
        """Initialize score reference as a non-dataclass attribute."""
        self.score: Optional['SCORE'] = None
    
    # Property: color
    @property
    def color(self) -> str:
        """Get color - inherits from globalCountLine.color if None."""
        if self._color is not None:
            return self._color
        if self.score is None:
            return '#000000'  # Fallback if no score reference
        return self.score.properties.globalCountLine.color
    
    @color.setter
    def color(self, value: Optional[str]):
        """Set color - use None to reset to inheritance."""
        self._color = value
    
    # Property: dashPattern
    @property
    def dashPattern(self) -> List[int]:
        """Get dashPattern - inherits from globalCountLine.dashPattern if None."""
        if self._dashPattern is not None:
            return self._dashPattern
        if self.score is None:
            return []  # Fallback if no score reference
        return self.score.properties.globalCountLine.dashPattern
    
    @dashPattern.setter
    def dashPattern(self, value: Optional[List[int]]):
        """Set dashPattern - use None to reset to inheritance."""
        self._dashPattern = value
