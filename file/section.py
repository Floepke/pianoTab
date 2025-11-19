from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from file.SCORE import SCORE

@dataclass_json
@dataclass
class Section:
    id: int = field(
        default=0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Unique section marker identifier',
            'tree_edit_type': 'readonly',
        }
    )
    time: float = field(
        default=0.0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Time position for section marker',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'step': 1.0,
            }
        }
    )
    text: str = field(
        default='Section',
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Section label text',
            'tree_edit_type': 'text',
        }
    )
    
    # Storage fields for inherited properties (serialize to JSON with clean names)
    _color: Optional[str] = field(
        default=None,
        metadata={
            **config(field_name='color'),
            'tree_icon': 'colorproperty',
            'tree_tooltip': 'Section marker color (None = inherit from globalSection)',
            'tree_edit_type': 'color',
            'tree_edit_options': {
                'allow_none': True,
            }
        }
    )
    _lineWidth: Optional[float] = field(
        default=None,
        metadata={
            **config(field_name='lineWidth'),
            'tree_icon': 'property',
            'tree_tooltip': 'Section line width in mm (None = inherit from globalSection)',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'max': 10.0,
                'step': 0.1,
                'allow_none': True,
            }
        }
    )
    
    def __post_init__(self):
        '''Initialize score reference as a non-dataclass attribute.'''
        self.score: Optional['SCORE'] = None
    
    # Property: color
    @property
    def color(self) -> str:
        '''Get color - inherits from globalSection.color if None.'''
        if self._color is not None:
            return self._color
        if self.score is None:
            print('Warning: Section has no score reference for property inheritance.')
            return '#000000'  # Fallback if no score reference
        return self.score.properties.globalSection.color
    
    @color.setter
    def color(self, value: Optional[str]):
        '''Set color - use None to reset to inheritance.'''
        self._color = value
    
    # Property: lineWidth
    @property
    def lineWidth(self) -> float:
        '''Get lineWidth - inherits from globalSection.lineWidth if None.'''
        if self._lineWidth is not None:
            return self._lineWidth
        if self.score is None:
            print('Warning: Section has no score reference for property inheritance.')
            return 1.0  # Fallback if no score reference
        return self.score.properties.globalSection.lineWidth
    
    @lineWidth.setter
    def lineWidth(self, value: Optional[float]):
        '''Set lineWidth - use None to reset to inheritance.'''
        self._lineWidth = value