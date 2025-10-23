from dataclasses import dataclass, field
from file.articulation import Articulation
from typing import List, TYPE_CHECKING, Literal, Union
if TYPE_CHECKING:
    from file.SCORE import SCORE

@dataclass
class Note:
    id: int = 0
    time: float = 0.0
    duration: float = 256.0
    pitch: int = 40
    velocity: int = 80
    articulation: List[Articulation] = field(default_factory=list)
    hand: Literal['<', '>'] = '>'
    
    # looking to globalProperties for default values:
    color: Union[Literal['*'], str] = '*'  # '*' means inherit, otherwise a color string like '#RRGGBB'
    colorMidiNote: Union[Literal['*'], str] = '*'
    blackNoteDirection: Literal['*', '^', 'v'] = '*'  # '*' means inherit, '^' for up and 'v' for down

    @property
    def get_color(self, score: 'SCORE') -> str:
        '''Get the actual color to use, considering inheritance.'''
        if self.color != '*':
            return self.color
        return score.properties.globalNote.color
    
    @property
    def get_colorMidiNote(self, score: 'SCORE') -> str:
        '''Get the actual MIDI color to use, considering inheritance.'''
        if self.colorMidiNote != '*':
            return self.colorMidiNote
        else:
            if self.hand == '<':
                return score.properties.globalNote.colorLeftMidiNote
            elif self.hand == '>':
                return score.properties.globalNote.colorRightMidiNote
            
    @property
    def get_blackNoteDirection(self, score: 'SCORE') -> str:
        '''Get the actual black note direction to use, considering inheritance.'''
        if self.blackNoteDirection != '*':
            return self.blackNoteDirection
        return score.properties.globalNote.blackNoteDirection
