from dataclasses import dataclass, field
from dataclasses_json import dataclass_json

@dataclass_json
@dataclass
class StaveRange:
    '''
    Defines the key range for a stave in a particular line of music.
    The index of the StaveRange corresponds to the stave index it applies to.
    If both lowestKey and highestKey are 0, the range is determined by the music content.
    '''
    lowestKey: int = field(
        default=0,
        metadata={
            'tree_icon': 'note',
            'tree_tooltip': 'Lowest key (1-88, 0 = auto-determined by music content)',
            'tree_edit_type': 'int',
            'tree_edit_options': {
                'min': 0,
                'max': 88,
                'step': 1,
            }
        }
    )
    highestKey: int = field(
        default=0,
        metadata={
            'tree_icon': 'note',
            'tree_tooltip': 'Highest key (1-88, 0 = auto-determined by music content)',
            'tree_edit_type': 'int',
            'tree_edit_options': {
                'min': 0,
                'max': 88,
                'step': 1,
            }
        }
    )
