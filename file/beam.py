from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from typing import Literal, TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from file.SCORE import SCORE

@dataclass_json
@dataclass
class Beam:
    id: int = field(
        default=0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Unique beam identifier',
            'tree_edit_type': 'readonly',
        }
    )
    time: float = field(
        default=0.0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Start time in time units',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'step': 1.0,
            }
        }
    )
    duration: float = field(
        default=0.0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Duration in time units',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'step': 1.0,
            }
        }
    )
    hand: Literal['<', '>'] = field(
        default='<',
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Hand assignment: < = left hand, > = right hand',
            'tree_edit_type': 'choice',
            'tree_edit_options': {
                'choices': ['<', '>'],
                'choice_labels': ['Left Hand', 'Right Hand'],
                'choice_icons': ['noteLeft', 'noteRight'],
            }
        }
    )
    
    # Storage fields for inherited properties (serialize to JSON with clean names)
    _color: Optional[str] = field(
        default=None,
        metadata={
            **config(field_name='color'),
            'tree_icon': 'colorproperty',
            'tree_tooltip': 'Beam color (None = inherit from globalBeam)',
            'tree_edit_type': 'color',
            'tree_edit_options': {
                'allow_none': True,
            }
        }
    )
    _width: Optional[float] = field(
        default=None,
        metadata={
            **config(field_name='width'),
            'tree_icon': 'property',
            'tree_tooltip': 'Beam width in millimeters (None = inherit from globalBeam)',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'max': 20.0,
                'step': 0.5,
                'allow_none': True,
            }
        }
    )
    _height: Optional[float] = field(
        default=None,
        metadata={
            **config(field_name='slant'),
            'tree_icon': 'property',
            'tree_tooltip': 'Beam slant angle in degrees (None = inherit from globalBeam)',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'max': 45.0,
                'step': 1.0,
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
        '''Get color - inherits from globalBeam.color if None.'''
        if self._color is not None:
            return self._color
        if self.score is None:
            print('Warning: Beam has no score reference for property inheritance.')
            return '#000000'  # Fallback if no score reference
        return self.score.properties.globalBeam.color
    
    @color.setter
    def color(self, value: Optional[str]):
        '''Set color - use None to reset to inheritance.'''
        self._color = value
    
    # Property: width
    @property
    def width(self) -> float:
        '''Get width - inherits from globalBeam.width if None.'''
        if self._width is not None:
            return self._width
        if self.score is None:
            print('Warning: Beam has no score reference for property inheritance.')
            return 4.0  # Fallback if no score reference
        return self.score.properties.globalBeam.width
    
    @width.setter
    def width(self, value: Optional[float]):
        '''Set width - use None to reset to inheritance.'''
        self._width = value
    
    # Property: slant
    @property
    def height(self) -> float:
        '''Get slant - inherits from globalBeam.slant if None.'''
        if self._height is not None:
            return self._height
        if self.score is None:
            print('Warning: Beam has no score reference for property inheritance.')
            return 5.0  # Fallback if no score reference
        return self.score.properties.globalBeam.slant
    
    @height.setter
    def height(self, value: Optional[float]):
        '''Set slant - use None to reset to inheritance.'''
        self._height = value