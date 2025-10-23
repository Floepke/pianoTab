from dataclasses import dataclass, field

@dataclass
class Tempo:
    '''A tempo marking in the score only for the midi playback.'''
    id: int = 0
    time: float = 0.0
    bpm: int = 120 # where a beat is a quarter note