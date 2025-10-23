from pydantic import BaseModel, Field, validator
from typing import Literal

class LineBreak(BaseModel):
    id: int = Field(default=0)
    time: float = Field(default=0.0)
    type: Literal['manual', 'locked'] = Field(default='manual')  # manual = user defined, locked = cannot be removed and has time 0.0 is essential for the score.
    lowestKey: int = Field(default=0)  # Range of stave in this line - 0 means determined by music content
    highestKey: int = Field(default=0)  # Range of stave in this line - 0 means determined by music content
    
    @validator('time', always=True)
    def ensure_locked_time_zero(cls, v, values):
        """Ensure 'locked' type always has time=0.0"""
        if values.get('type') == 'locked':
            return 0.0
        return v