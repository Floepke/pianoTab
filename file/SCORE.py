from pydantic import BaseModel, Field
import pprint
from typing import List, Literal, Optional
import json
import sys
from pathlib import Path

if __name__ == '__main__':
    # Add parent directory to path when running directly
    sys.path.insert(0, str(Path(__file__).parent.parent))

from file.metaInfo import Metainfo
from file.header import Header
from file.properties import Properties
from file.baseGrid import BaseGrid
from file.lineBreak import LineBreak
from file.note import Note
from file.graceNote import GraceNote
from file.countLine import CountLine
from file.startRepeat import StartRepeat
from file.endRepeat import EndRepeat
from file.section import Section
from file.beam import Beam
from file.text import Text
from file.slur import Slur
from file.tempo import Tempo
from file.id import IDGenerator


class Event(BaseModel):
    note: List[Note] = Field(default_factory=list)
    graceNote: List[GraceNote] = Field(default_factory=list)
    countLine: List[CountLine] = Field(default_factory=list)
    startRepeat: List[StartRepeat] = Field(default_factory=list)
    endRepeat: List[EndRepeat] = Field(default_factory=list)
    section: List[Section] = Field(default_factory=list)
    beam: List[Beam] = Field(default_factory=list)
    text: List[Text] = Field(default_factory=list)
    slur: List[Slur] = Field(default_factory=list)
    tempo: List[Tempo] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True

class Stave(BaseModel):
    name: str = Field(default='Stave 1')
    scale: float = Field(default=1.0)
    event: Event = Field(default_factory=Event)
    
    class Config:
        arbitrary_types_allowed = True

class SCORE(BaseModel):
    '''The main SCORE class; contains all data for a piano tab score.'''

    # Default is 256.0 ticks per quarter note. All time values in this file are based on this value.
    quarterNote: float = Field(default=256.0)
    metaInfo: Metainfo = Field(default_factory=Metainfo)
    header: Header = Field(default_factory=Header)
    properties: Properties = Field(default_factory=Properties)
    baseGrid: List[BaseGrid] = Field(default_factory=list)
    lineBreak: List[LineBreak] = Field(default_factory=list)
    stave: List[Stave] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        super().__init__(**data)
        # Initialize ID generator starting from 0:
        object.__setattr__(self, '_id', IDGenerator(start_id=0))

        # Ensure there's always a 'locked' lineBreak at time 0:
        if not self.lineBreak or not any(lb.time == 0.0 and lb.type == 'locked' for lb in self.lineBreak):
            self.lineBreak.insert(0, LineBreak(time=0.0, type='locked', id=self._next_id()))

        # ensure there's always one baseGrid:
        if not self.baseGrid:
            self.baseGrid.append(BaseGrid())
        
        # ensure there's always one stave:
        if not self.stave:
            self.stave.append(Stave())

    def _next_id(self) -> int:
        """Get the next unique ID for this score."""
        return self._id.new()
    
    def reset_ids(self, start_id: int = 1):
        """Reset the ID generator to start from a specific ID."""
        self._id.reset(start_id)
    
    # Convenience methods for managing line breaks and base grids:
    def add_basegrid(self, numerator: int = 4,
                     denominator: int = 4,
                     gridTimes: List[float] = [256.0, 512.0, 768.0],
                     measureAmount: int = 8,
                     timeSignatureIndicatorVisible: bool = True) -> None:
        '''Add a new baseGrid to the score.'''
        basegrid = BaseGrid(numerator=numerator,
                            denominator=denominator,
                            gridTimes=gridTimes,
                            measureAmount=measureAmount,
                            timeSignatureIndicatorVisible=timeSignatureIndicatorVisible)
        self.baseGrid.append(basegrid)

    def add_linebreak(self, time: float = 0.0, type: Literal['manual', 'locked'] = 'manual', 
                      lowestKey: int = 0, highestKey: int = 0) -> None:
        '''Add a new line break to the score.
        
        Args:
            time: Time position for the line break
            type: Type of line break ('manual' or 'locked')
            lowestKey: Lowest key in range for this line (0 = determined by music content)
            highestKey: Highest key in range for this line (0 = determined by music content)
        '''
        linebreak = LineBreak(id=self._next_id(), time=time, type=type, 
                             lowestKey=lowestKey, highestKey=highestKey)
        self.lineBreak.append(linebreak)
        # Ensure there's always a 'locked' lineBreak at time 0:
        if not any(lb.time == 0.0 and lb.type == 'locked' for lb in self.lineBreak):
            self.lineBreak.insert(0, LineBreak(time=0.0, type='locked', id=self._next_id()))
    
    # Convenience methods for managing staves
    def add_stave(self, name: str = None, scale: float = 1.0) -> int:
        '''Add a new stave and return its index.
        
        Args:
            name: Name for the stave (defaults to "Stave N")
            scale: Draw scale for this stave (defaults to 1.0)
        '''
        stave_name = name or f'Stave {len(self.stave) + 1}'
        self.stave.append(Stave(name=stave_name, scale=scale))
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
                 color: Optional[str] = None,
                 colorMidiNote: Optional[str] = None,
                 blackNoteDirection: Optional[str] = None) -> Note:
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
                    blackNoteDirection=blackNoteDirection,
                    score=self)
        
        self.get_stave(stave_idx).event.note.append(note)
        return note

    def new_grace_note(self, 
                       stave_idx: int = 0, 
                       time: float = 0.0,
                       pitch: int = 40, 
                       velocity: int = 80, 
                       color: str = None) -> GraceNote:
        '''Add a grace note to the specified stave.'''

        grace_note = GraceNote(id=self._next_id(), 
                              time=time,
                              pitch=pitch,
                              velocity=velocity,
                              color=color,
                              score=self)
        
        self.get_stave(stave_idx).event.graceNote.append(grace_note)
        return grace_note

    def new_count_line(self,
                       stave_idx: int = 0,
                       time: float = 0.0,
                       pitch1: int = 40, 
                       pitch2: int = 44, 
                       color: str = None, 
                       width: float = None,
                       dashPattern: List[int] = None) -> CountLine:
        '''Add a count line to the specified stave.'''
        count_line = CountLine(id=self._next_id(), 
                               time=time,
                               pitch1=pitch1,
                               pitch2=pitch2,
                               color=color,
                               width=width,
                               dashPattern=dashPattern,
                               score=self)
        self.get_stave(stave_idx).event.countLine.append(count_line)
        return count_line

    def new_text(self,
                 stave_idx: int = 0,
                 time: float = 0.0,
                 side: Literal['<', '>'] = '>',
                 distFromSide: float = 10.0,
                 text: str = 'Text',
                 fontSize: int = None,
                 color: str = None) -> Text:
        '''Add text to the specified stave.'''
        
        text = Text(id=self._next_id(),
                       time=time,
                       side=side,
                       distFromSide=distFromSide,
                       text=text,
                       fontSize=fontSize,
                       color=color,
                       score=self)

        self.get_stave(stave_idx).event.text.append(text)
        return text

    def new_beam(self,
                 stave_idx: int = 0,
                 time: float = 0.0,
                 staff: float = 0.0,
                 hand: str = '<',
                 color: str = None,
                 width: float = None,
                 slant: float = None) -> None:
        '''Add a beam to the specified stave.'''
        
        beam = Beam(id=self._next_id(),
                   time=time,
                   staff=staff,
                   hand=hand,
                   color=color,
                   width=width,
                   slant=slant,
                   score=self)
        
        self.get_stave(stave_idx).event.beam.append(beam)
        return beam

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
                 color: str = None,
                 startEndWidth: float = None,
                 middleWidth: float = None) -> None:
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
                   middleWidth=middleWidth,
                   score=self)
        
        # No need to set time separately - it's now a regular field
        
        self.get_stave(stave_idx).event.slur.append(slur)
        return slur

    def new_tempo(self,
                  stave_idx: int = 0,
                  time: float = 0.0,
                  bpm: int = 120) -> None:
        '''Add a tempo marking to the specified stave.'''
        
        tempo = Tempo(id=self._next_id(),
                     time=time,
                     bpm=bpm)
        
        self.get_stave(stave_idx).event.tempo.append(tempo)
        return tempo

    def new_start_repeat(self,
                         stave_idx: int = 0,
                         time: float = 0.0,
                         color: str = None,
                         lineWidth: float = None) -> None:
        '''Add a start repeat to the specified stave.'''
        
        start_repeat = StartRepeat(id=self._next_id(),
                                  time=time,
                                  color=color,
                                  lineWidth=lineWidth,
                                  score=self)
        
        self.get_stave(stave_idx).event.startRepeat.append(start_repeat)
        return start_repeat

    def new_end_repeat(self,
                       stave_idx: int = 0,
                       time: float = 0.0,
                       color: str = None,
                       lineWidth: float = None) -> None:
        '''Add an end repeat to the specified stave.'''
        
        end_repeat = EndRepeat(id=self._next_id(),
                              time=time,
                              color=color,
                              lineWidth=lineWidth,
                              score=self)
        
        self.get_stave(stave_idx).event.endRepeat.append(end_repeat)
        return end_repeat

    def new_section(self,
                    stave_idx: int = 0,
                    time: float = 0.0,
                    text: str = 'Section',
                    color: str = None,
                    lineWidth: float = None) -> None:
        '''Add a section to the specified stave.'''
        
        section = Section(id=self._next_id(),
                         time=time,
                         text=text,
                         color=color,
                         lineWidth=lineWidth,
                         score=self)
        
        self.get_stave(stave_idx).event.section.append(section)
        return section
    
    def find_by_id(self, target_id: int) -> Optional[Event]:
        '''Find any event by ID across all staves and return the event object.'''
        # Get event type names from the Pydantic model fields
        event_types = list(Event.__fields__.keys())
        
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
        # Get event type names from the Pydantic model fields
        event_types = list(Event.__fields__.keys())
        
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
        self._id.reset(1)
        
        # Renumber linebreaks (they have IDs)
        for linebreak in self.lineBreak:
            if hasattr(linebreak, 'id'):
                linebreak.id = self._next_id()
        
        # Note: basegrids don't have IDs, so we skip them
        
        # Get event type names from the Pydantic model fields
        event_types = list(Event.__fields__.keys())
        
        # renumber all events in all staves
        for stave in self.stave:
            for event_type in event_types:
                event_list = getattr(stave.event, event_type)
                for event in event_list:
                    if hasattr(event, 'id'):
                        event.id = self._next_id()

    # Convenience methods for JSON operations
    def save(self, filename: str) -> None:
        '''Save SCORE instance to JSON file.'''
        # Set score references for all notes before saving
        self._set_score_references()
        
        with open(filename, 'w', encoding='utf-8') as f:
            # Exclude private attributes from serialization
            json.dump(self.dict(exclude={'_id'}), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls, filename: str) -> 'SCORE':
        '''Load SCORE instance from JSON file.'''
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        score = cls.parse_obj(data)
        
        # Recreate ID generator after loading
        object.__setattr__(score, '_id', IDGenerator(start_id=0))
        
        # Set score references for all events after loading
        score._set_score_references()
        
        # Renumber IDs to ensure consistency
        score.renumber_id()
        return score
    
    def _set_score_references(self):
        '''Set score references for all events to enable inheritance.'''
        for stave in self.stave:
            # Set score references for all event types that have inheritance
            for note in stave.event.note:
                note.set_score_reference(self)
            for grace_note in stave.event.graceNote:
                grace_note.set_score_reference(self)
            for text in stave.event.text:
                text.set_score_reference(self)
            for count_line in stave.event.countLine:
                count_line.set_score_reference(self)
            for beam in stave.event.beam:
                beam.set_score_reference(self)
            for slur in stave.event.slur:
                slur.set_score_reference(self)
            # Skip tempo - it doesn't have inheritance
            for start_repeat in stave.event.startRepeat:
                start_repeat.set_score_reference(self)
            for end_repeat in stave.event.endRepeat:
                end_repeat.set_score_reference(self)
            for section in stave.event.section:
                section.set_score_reference(self)


if __name__ == '__main__':
    ... # Example usage
    score = SCORE()
    score.quarterNote = 256.0
    score.metaInfo.author = "Composer Name"
    score.metaInfo.description = "A sample pianoTab score."

    print("Adding staves...")
    stave1_idx = score.add_stave(name="Organ pedal")