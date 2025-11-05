from dataclasses import dataclass
from dataclasses_json import dataclass_json

@dataclass_json
@dataclass
class StaveRange:
    '''
    Defines the key range for a stave in a particular line of music.
    The index of the StaveRange corresponds to the stave index it applies to.
    If both lowestKey and highestKey are 0, the range is determined by the music content.
    '''
    lowestKey: int = 0  # Lowest key (1-88, 0 means auto-determined by music)
    highestKey: int = 0  # Highest key (1-88, 0 means auto-determined by music)
