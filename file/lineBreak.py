from pydantic import BaseModel, Field, validator
from typing import Literal, List
from file.staveRange import StaveRange

class LineBreak(BaseModel):
    """
    Describes a line of music in the document.
    Each lineBreak contains staveRange objects - one per stave in the score.
    The staveRange list must always match the number of staves in the score.
    """
    id: int = Field(default=0)
    time: float = Field(default=0.0)
    type: Literal['manual', 'locked'] = Field(default='manual')  # manual = user defined, locked = cannot be removed and has time 0.0 is essential for the score.
    staveRange: List[StaveRange] = Field(default_factory=list, description="Key ranges for each stave in this line (one per stave)")
    
    @validator('time', always=True)
    def ensure_locked_time_zero(cls, v, values):
        """Ensure 'locked' type always has time=0.0"""
        if values.get('type') == 'locked':
            return 0.0
        return v