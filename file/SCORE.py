from dataclasses import dataclass, field
import pprint
from typing import List, Literal, Optional
import pickle
import sys
from pathlib import Path

if __name__ == '__main__':
    # Add parent directory to path when running directly
    sys.path.insert(0, str(Path(__file__).parent.parent))

from file.metaInfo import Metainfo
from file.header import Header
from file.properties import Properties
from file.baseGrid import Basegrid
from file.lineBreak import Linebreak
from file.note import Note
from file.graceNote import Gracenote
from file.countLine import Countline
from file.startRepeat import StartRepeat
from file.endRepeat import EndRepeat
from file.section import Section
from file.beam import Beam
from file.text import Text
from file.slur import Slur
from file.tempo import Tempo
from file.id import IDGenerator
from file.dataclass_repair import repair_missing_fields


@dataclass
class Event:
    note: List[Note] = field(default_factory=list)
    graceNote: List[Gracenote] = field(default_factory=list)
    countLine: List[Countline] = field(default_factory=list)
    startRepeat: List[StartRepeat] = field(default_factory=list)
    endRepeat: List[EndRepeat] = field(default_factory=list)
    section: List[Section] = field(default_factory=list)
    beam: List[Beam] = field(default_factory=list)
    text: List[Text] = field(default_factory=list)
    slur: List[Slur] = field(default_factory=list)
    tempo: List[Tempo] = field(default_factory=list)

@dataclass
class Stave:
    name: str = 'Stave 1'
    scale: float = 1.0
    event: Event = field(default_factory=Event)

@dataclass
class SCORE:
    '''The main SCORE class; contains all data for a piano tab score.'''

    pianoTick: float = 256.0 # Default is 256.0 ticks per quarter note. All time values in this file are based on this.
    metaInfo: Metainfo = field(default_factory=Metainfo)
    header: Header = field(default_factory=Header)
    properties: Properties = field(default_factory=Properties)
    baseGrid: List[Basegrid] = field(default_factory=list)
    lineBreak: List[Linebreak] = field(default_factory=list)
    stave: List[Stave] = field(default_factory=lambda: [Stave()])

    def __post_init__(self):
        # Initialize ID generator starting from 0:
        self._id = IDGenerator(start_id=0)

        # Ensure there's always a 'locked' lineBreak at time 0:
        if not self.lineBreak or not any(lb.time == 0.0 and lb.type == 'locked' for lb in self.lineBreak):
            self.lineBreak.insert(0, Linebreak(time=0.0, type='locked', id=self._next_id()))

        # ensure there's always one baseGrid:
        if not self.baseGrid:
            self.baseGrid.append(Basegrid())

    def _next_id(self) -> int:
        """Get the next unique ID for this score."""
        return self._id.new()
    
    def reset_ids(self, start_id: int = 1):
        """Reset the ID generator to start from a specific ID."""
        self._id.reset(start_id)
    
    # Convenience methods for managing line breaks and base grids:
    def add_basegrid(self, gridlineColor: str = '#000000',
                     barlineColor: str = '#000000',
                     gridlineWidth: float = 0.5,
                     barlineWidth: float = 1.0,
                     basegridDashPattern: List[int] = [],
                     visible: bool = True) -> None:
        '''Add a new baseGrid to the score.'''
        basegrid = Basegrid(id=self._next_id(),
                            gridlineColor=gridlineColor,
                            barlineColor=barlineColor,
                            gridlineWidth=gridlineWidth,
                            barlineWidth=barlineWidth,
                            basegridDashPattern=basegridDashPattern,
                            visible=visible)
        self.baseGrid.append(basegrid)

    def add_linebreak(self, time: float = 0.0, type: Literal['manual', 'locked'] = 'manual') -> None:
        '''Add a new line break to the score.'''
        linebreak = Linebreak(id=self._next_id(), time=time, type=type)
        self.lineBreak.append(linebreak)
        # Ensure there's always a 'locked' lineBreak at time 0:
        if not any(lb.time == 0.0 and lb.type == 'locked' for lb in self.lineBreak):
            self.lineBreak.insert(0, Linebreak(time=0.0, type='locked', id=self._next_id()))
    
    # Convenience methods for managing staves
    def add_stave(self, name: str = None) -> int:
        '''Add a new stave and return its index.'''
        stave_name = name or f'Stave {len(self.stave) + 1}'
        self.stave.append(Stave(name=stave_name))
        return len(self.stave) - 1
    
    def get_stave(self, index: int = 0) -> Stave:
        '''Get stave by index (default: first stave).'''
        if 0 <= index < len(self.stave):
            return self.stave[index]
        raise IndexError(f'Stave index {index} out of range')

    # Convenience methods for adding events to staves
    def new_note(self,
                 stave_idx: int = 0,
                 time: float = 0.0,
                 duration: float = 256.0,
                 pitch: int = 40,
                 velocity: int = 80,
                 articulation: List = [],
                 hand: str = '>',
                 color: str = '*',
                 colorMidiNote: str = '*',
                 blackNoteDirection: str = '*') -> None:
        '''Add a note to the specified stave.'''
        
        note = Note(id=self._next_id(), 
                    time=time, 
                    duration=duration, 
                    pitch=pitch, 
                    velocity=velocity,
                    articulation=articulation, 
                    hand=hand, 
                    color=color,
                    colorMidiNote=colorMidiNote, 
                    blackNoteDirection=blackNoteDirection)
        
        return self.get_stave(stave_idx).event.note.append(note)

    def new_grace_note(self, 
                       stave_idx: int = 0, 
                       time: float = 0.0,
                       pitch: int = 40, 
                       velocity: int = 80, 
                       color: str = '*') -> None:
        '''Add a grace note to the specified stave.'''

        grace_note = Gracenote(id=self._next_id(), 
                              time=time,
                              pitch=pitch,
                              velocity=velocity,
                              color=color)
        
        return self.get_stave(stave_idx).event.graceNote.append(grace_note)

    def new_count_line(self, 
                       time: float = 0.0,
                       pitch1: int = 40, 
                       pitch2: int = 44, 
                       color: str = '*', 
                       width: float = 1.0, 
                       dashPattern: List[int] = [],
                       stave_idx: int = 0) -> None:
        '''Add a count line to the specified stave.'''
        count_line = Countline(id=self._next_id(), 
                               time=time,
                               pitch1=pitch1,
                               pitch2=pitch2,
                               color=color,
                               width=width,
                               dashPattern=dashPattern)
        return self.get_stave(stave_idx).event.countLine.append(count_line)

    def new_text(self,
                 stave_idx: int = 0,
                 time: float = 0.0,
                 side: Literal['<', '>'] = '>',
                 distFromSide: float = 10.0,
                 text: str = 'Text',
                 fontSize: int = 0,
                 color: str = '*') -> None:
        '''Add text to the specified stave.'''
        
        text = Text(id=self._next_id(),
                       time=time,
                       side=side,
                       distFromSide=distFromSide,
                       text=text,
                       fontSize=fontSize,
                       color=color)

        return self.get_stave(stave_idx).event.text.append(text)

    def new_beam(self,
                 stave_idx: int = 0,
                 time: float = 0.0,
                 staff: float = 0.0,
                 hand: str = '<',
                 color: str = '*',
                 width: float = 1.0,
                 slant: float = 5.0) -> None:
        '''Add a beam to the specified stave.'''
        
        beam = Beam(id=self._next_id(),
                   time=time,
                   staff=staff,
                   hand=hand,
                   color=color,
                   width=width,
                   slant=slant)
        
        return self.get_stave(stave_idx).event.beam.append(beam)

    def new_slur(self,
                 stave_idx: int = 0,
                 time: float = 0.0,
                 x1_semitonesFromC4: int = 0,
                 x2_semitonesFromC4: int = 0,
                 y2_time: float = 0.0,
                 x3_semitonesFromC4: int = 0,
                 y3_time: float = 0.0,
                 x4_semitonesFromC4: int = 0,
                 y4_time: float = 0.0,
                 color: str = '*',
                 startEndWidth: float = 0,
                 middleWidth: float = 0) -> None:
        '''Add a slur to the specified stave.'''
        
        slur = Slur(id=self._next_id(),
                   time=time,
                   x1_semitonesFromC4=x1_semitonesFromC4,
                   x2_semitonesFromC4=x2_semitonesFromC4,
                   y2_time=y2_time,
                   x3_semitonesFromC4=x3_semitonesFromC4,
                   y3_time=y3_time,
                   x4_semitonesFromC4=x4_semitonesFromC4,
                   y4_time=y4_time,
                   color=color,
                   startEndWidth=startEndWidth,
                   middleWidth=middleWidth)
        
        # No need to set time separately - it's now a regular field
        
        return self.get_stave(stave_idx).event.slur.append(slur)

    def new_tempo(self,
                  stave_idx: int = 0,
                  time: float = 0.0,
                  bpm: int = 120) -> None:
        '''Add a tempo marking to the specified stave.'''
        
        tempo = Tempo(id=self._next_id(),
                     time=time,
                     bpm=bpm)
        
        return self.get_stave(stave_idx).event.tempo.append(tempo)

    def new_start_repeat(self,
                         stave_idx: int = 0,
                         time: float = 0.0,
                         color: str = '*',
                         lineWidth: float = 0) -> None:
        '''Add a start repeat to the specified stave.'''
        
        start_repeat = StartRepeat(id=self._next_id(),
                                  time=time,
                                  color=color,
                                  lineWidth=lineWidth)
        
        return self.get_stave(stave_idx).event.startRepeat.append(start_repeat)

    def new_end_repeat(self,
                       stave_idx: int = 0,
                       time: float = 0.0,
                       color: str = '*',
                       lineWidth: float = 0) -> None:
        '''Add an end repeat to the specified stave.'''
        
        end_repeat = EndRepeat(id=self._next_id(),
                              time=time,
                              color=color,
                              lineWidth=lineWidth)
        
        return self.get_stave(stave_idx).event.endRepeat.append(end_repeat)

    def new_section(self,
                    stave_idx: int = 0,
                    time: float = 0.0,
                    text: str = 'Section',
                    color: str = '*',
                    lineWidth: float = 0) -> None:
        '''Add a section to the specified stave.'''
        
        section = Section(id=self._next_id(),
                         time=time,
                         text=text,
                         color=color,
                         lineWidth=lineWidth)
        
        return self.get_stave(stave_idx).event.section.append(section)
    
    def find_by_id(self, target_id: int) -> Optional[Event]:
        '''Find any event by ID across all staves and return the event object.'''
        # Get event type names directly from the Event dataclass
        event_types = list(Event.__dataclass_fields__.keys())
        
        # find the event with the matching ID
        for stave in self.stave:
            for event_type in event_types:
                event_list = getattr(stave.event, event_type)
                for event in event_list:
                    if hasattr(event, 'id') and event.id == target_id:
                        return event

        return None  # ID not found

    def delete_by_id(self, id: int) -> bool:
        '''Delete any event by ID across all staves. Returns True if deleted, False if not found.'''
        # Get event type names directly from the Event dataclass
        event_types = list(Event.__dataclass_fields__.keys())
        
        # find and delete the event with the matching ID
        for stave in self.stave:
            for event_type in event_types:
                event_list = getattr(stave.event, event_type)
                for i, event in enumerate(event_list):
                    if hasattr(event, 'id') and event.id == id:
                        del event_list[i]
                        return True  # Successfully deleted
        
        return False  # ID not found

    def renumber_id(self) -> None:
        '''Renumber all events across all staves with sequential IDs.'''
        self._id.reset(0)
        
        # Get event type names directly from the Event dataclass
        event_types = list(Event.__dataclass_fields__.keys())
        
        # renumber all events
        for stave in self.stave:
            for event_type in event_types:
                event_list = getattr(stave.event, event_type)
                for event in event_list:
                    if hasattr(event, 'id'):
                        event.id = self._next_id()

    # Convenience methods for pickle operations
    def save(self, filename: str) -> None:
        '''Save SCORE instance to pickle file.'''
        with open(filename, 'wb') as f:
            pickle.dump(self, f)
    
    @classmethod
    def load(cls, filename: str) -> 'SCORE':
        '''Load SCORE instance from pickle file.'''
        with open(filename, 'rb') as f:
            score = pickle.load(f)

        # Fill any missing dataclass fields with defaults to keep backward compatibility
        repair_missing_fields(score)
        
        # Renumber IDs to ensure consistency
        score.renumber_id()
        return score


if __name__ == '__main__':
    # Simple test: create a SCORE, add some events, save and load
    print("Creating test SCORE...")
    score = SCORE()
    score.metaInfo.title = 'Test Song'
    score.metaInfo.composer = 'Test Composer'
    
    print("Adding notes...")
    score.new_note(stave_idx=0, time=0.0, duration=256.0, pitch=60)
    score.new_grace_note(stave_idx=0, time=128.0, pitch=62)
    score.new_text(stave_idx=0, time=0.0, text='Hello World')
    
    print("Saving to pickle...")
    score.save('test_score.pianotab')
    
    print("Loading from pickle...")
    score = SCORE.load('test_score.pianotab')
    
    pprint.pprint(score)