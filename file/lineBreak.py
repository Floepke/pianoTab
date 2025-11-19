from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import Literal, List
from file.staveRange import StaveRange

@dataclass_json
@dataclass
class LineBreak:
    '''
    Describes a line of music in the document.
    Each lineBreak contains staveRange objects - one per stave in the score.
    The staveRange list must always match the number of staves in the score.
    '''
    id: int = field(
        default=0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Unique line break identifier',
            'tree_edit_type': 'readonly',
        }
    )
    time: float = field(
        default=0.0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Time position for line break',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'step': 1.0,
            }
        }
    )
    type: Literal['manual', 'locked'] = field(
        default='manual',
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Line break type: manual = user-defined, locked = essential (time=0.0)',
            'tree_edit_type': 'choice',
            'tree_edit_options': {
                'choices': ['manual', 'locked'],
                'choice_labels': ['Manual', 'Locked'],
            }
        }
    )
    staveRange: List[StaveRange] = field(
        default_factory=list,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Stave ranges for each stave in this line',
            'tree_edit_type': 'list',
        }
    )
    
    def __post_init__(self):
        '''Ensure 'locked' type always has time=0.0'''
        if self.type == 'locked':
            object.__setattr__(self, 'time', 0.0)