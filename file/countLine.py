from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from typing import List, TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from file.SCORE import SCORE

@dataclass_json
@dataclass
class CountLine:
    id: int = field(
        default=0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Unique count line identifier',
            'tree_edit_type': 'readonly',
        }
    )
    time: float = field(
        default=0.0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Time position for count line',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'step': 1.0,
            }
        }
    )
    pitch1: int = field(
        default=40,
        metadata={
            'tree_icon': 'note',
            'tree_tooltip': 'Start pitch (key 1-88, C4=40)',
            'tree_edit_type': 'int',
            'tree_edit_options': {
                'min': 1,
                'max': 88,
                'step': 1,
            }
        }
    )
    pitch2: int = field(
        default=44,
        metadata={
            'tree_icon': 'note',
            'tree_tooltip': 'End pitch (key 1-88, C4=40)',
            'tree_edit_type': 'int',
            'tree_edit_options': {
                'min': 1,
                'max': 88,
                'step': 1,
            }
        }
    )

    # Storage fields for inherited properties (serialize to JSON with clean names)
    _color: Optional[str] = field(
        default=None,
        metadata={
            **config(field_name='color'),
            'tree_icon': 'colorproperty',
            'tree_tooltip': 'Count line color (None = inherit from globalCountLine)',
            'tree_edit_type': 'color',
            'tree_edit_options': {
                'allow_none': True,
            }
        }
    )
    _dashPattern: Optional[List[float]] = field(
        default=None,
        metadata={
            **config(field_name='dashPattern'),
            'tree_icon': 'property',
            'tree_tooltip': 'Dash pattern (None = inherit from globalCountLine)',
            'tree_edit_type': 'list',
            'tree_edit_options': {
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
        '''Get color - inherits from globalCountLine.color if None.'''
        if self._color is not None:
            return self._color
        if self.score is None:
            print('Warning: CountLine has no score reference for property inheritance.')
            return '#000000'  # Fallback if no score reference
        return self.score.properties.globalCountLine.color
    
    @color.setter
    def color(self, value: Optional[str]):
        '''Set color - use None to reset to inheritance.'''
        self._color = value
    
    # Property: dashPattern
    @property
    def dashPattern(self) -> List[int]:
        '''Get dashPattern - inherits from globalCountLine.dashPattern if None.'''
        if self._dashPattern is not None:
            return self._dashPattern
        if self.score is None:
            print('Warning: CountLine has no score reference for property inheritance.')
            return []  # Fallback if no score reference
        return self.score.properties.globalCountLine.dashPattern
    
    @dashPattern.setter
    def dashPattern(self, value: Optional[List[int]]):
        '''Set dashPattern - use None to reset to inheritance.'''
        self._dashPattern = value
