from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import Literal

@dataclass_json
@dataclass
class Linebreak:
    id: int = 0
    time: float = 0.0
    type: Literal['manual', 'locked'] = 'manual' # manual = user defined, locked = cannot be removed and has time 0.0 is essential for the score.
    
    def __post_init__(self):
        """Ensure 'locked' type always has time=0.0"""
        if self.type == 'locked':
            self.time = 0.0