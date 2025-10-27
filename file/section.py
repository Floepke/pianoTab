from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from file.SCORE import SCORE

@dataclass_json
@dataclass
class Section:
    id: int = 0
    time: float = 0.0
    text: str = 'Section'
    
    # Storage fields for inherited properties (serialize to JSON with clean names)
    _color: Optional[str] = field(default=None, metadata=config(field_name='color'))
    _lineWidth: Optional[float] = field(default=None, metadata=config(field_name='lineWidth'))
    
    def __post_init__(self):
        """Initialize score reference as a non-dataclass attribute."""
        self.score: Optional['SCORE'] = None
    
    # Property: color
    @property
    def color(self) -> str:
        """Get color - inherits from globalSection.color if None."""
        if self._color is not None:
            return self._color
        if self.score is None:
            print("Warning: Section has no score reference for property inheritance.")
            return '#000000'  # Fallback if no score reference
        return self.score.properties.globalSection.color
    
    @color.setter
    def color(self, value: Optional[str]):
        """Set color - use None to reset to inheritance."""
        self._color = value
    
    # Property: lineWidth
    @property
    def lineWidth(self) -> float:
        """Get lineWidth - inherits from globalSection.lineWidth if None."""
        if self._lineWidth is not None:
            return self._lineWidth
        if self.score is None:
            print("Warning: Section has no score reference for property inheritance.")
            return 1.0  # Fallback if no score reference
        return self.score.properties.globalSection.lineWidth
    
    @lineWidth.setter
    def lineWidth(self, value: Optional[float]):
        """Set lineWidth - use None to reset to inheritance."""
        self._lineWidth = value