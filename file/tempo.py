from pydantic import BaseModel, Field

class Tempo(BaseModel):
    '''A tempo marking in the score only for the midi playback.'''
    id: int = Field(default=0)
    time: float = Field(default=0.0)
    bpm: int = Field(default=120)  # where a beat is a quarter note