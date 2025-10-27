from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from file.articulation import Articulation
from typing import List, TYPE_CHECKING, Literal, Optional
if TYPE_CHECKING:
    from file.SCORE import SCORE

@dataclass_json
@dataclass
class Note:
    id: int = 0
    time: float = 0.0
    duration: float = 256.0
    pitch: int = 40
    velocity: int = 80
    articulation: List[Articulation] = field(default_factory=list)
    hand: Literal['<', '>'] = '>'
    
    # Serializable fields with None for inheritance
    color: Optional[str] = inherit_from_if_none(inherit_path='globalProperties.color', initial_value=None)
    colorMidiNote: Optional[str] = inherit_from_if_none(inherit_path='globalProperties.colorMidiNote', initial_value=None)
    blackNoteDirection: Optional[Literal['^', 'v']] = inherit_from_if_none(inherit_path='globalProperties.blackNoteDirection', initial_value=None)

    # here code whatever you need to accomplish the task