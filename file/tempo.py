from dataclasses import dataclass, field
from dataclasses_json import dataclass_json

@dataclass_json
@dataclass
class Tempo:
    '''A tempo marking in the score only for the midi playback.'''
    id: int = field(
        default=0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Unique tempo marker identifier',
            'tree_edit_type': 'readonly',
        }
    )
    time: float = field(
        default=0.0,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Time position for tempo change',
            'tree_edit_type': 'float',
            'tree_edit_options': {
                'min': 0.0,
                'step': 1.0,
            }
        }
    )
    bpm: int = field(
        default=120,
        metadata={
            'tree_icon': 'property',
            'tree_tooltip': 'Tempo in beats per minute (quarter note = 1 beat)',
            'tree_edit_type': 'int',
            'tree_edit_options': {
                'min': 20,
                'max': 300,
                'step': 1,
            }
        }
    )