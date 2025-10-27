from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import List, Literal, Optional
import json

from file.metaInfo import MetaInfo
from file.header import Header
from file.properties import Properties
from file.baseGrid import BaseGrid
from file.lineBreak import LineBreak
from file.staveRange import StaveRange
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


@dataclass_json
@dataclass
class Event:
    note: List[Note] = field(default_factory=list)
    graceNote: List[GraceNote] = field(default_factory=list)
    countLine: List[CountLine] = field(default_factory=list)
    startRepeat: List[StartRepeat] = field(default_factory=list)
    endRepeat: List[EndRepeat] = field(default_factory=list)
    section: List[Section] = field(default_factory=list)
    beam: List[Beam] = field(default_factory=list)
    text: List[Text] = field(default_factory=list)
    slur: List[Slur] = field(default_factory=list)
    tempo: List[Tempo] = field(default_factory=list)

@dataclass_json
@dataclass
class Stave:
    name: str = 'Stave 1'
    scale: float = 1.0
    event: Event = field(default_factory=Event)

@dataclass_json
@dataclass
class SCORE:
    '''The main SCORE class; contains all data for a piano tab score.'''
    
    metaInfo: MetaInfo = field(default_factory=MetaInfo)
    header: Header = field(default_factory=Header)
    properties: Properties = field(default_factory=Properties)
    baseGrid: List[BaseGrid] = field(default_factory=list)
    lineBreak: List[LineBreak] = field(default_factory=list)
    stave: List[Stave] = field(default_factory=lambda: [Stave()])

    def __post_init__(self):
        # Initialize ID generator starting from 0:
        self._id = IDGenerator(start_id=0)

        # Ensure there's always a 'locked' lineBreak at time 0:
        if not self.lineBreak or not any(lb.time == 0.0 and lb.type == 'locked' for lb in self.lineBreak):
            self.lineBreak.insert(0, LineBreak(time=0.0, type='locked', id=self._next_id()))

        # ensure there's always one baseGrid:
        if not self.baseGrid:
            self.baseGrid.append(BaseGrid())

    def _next_id(self) -> int:
        """Get the next unique ID for this score."""
        return self._id.new()
    
    def reset_ids(self, start_id: int = 1):
        """Reset the ID generator to start from a specific ID."""
        self._id.reset(start_id)
    
    # Convenience methods for managing line breaks and base grids:
    def new_basegrid(self, 
                     numerator: int = 4,
                     denominator: int = 4,
                     gridTimes: List[float] = None,
                     measureAmount: int = 8,
                     timeSignatureIndicatorVisible: bool = True) -> None:
        '''Add a new baseGrid to the score.'''
        if gridTimes is None:
            gridTimes = [256.0, 512.0, 768.0]
        basegrid = BaseGrid(numerator=numerator,
                            denominator=denominator,
                            gridTimes=gridTimes,
                            measureAmount=measureAmount,
                            timeSignatureIndicatorVisible=timeSignatureIndicatorVisible)
        self.baseGrid.append(basegrid)
        return basegrid

    def new_linebreak(self, time: float = 0.0, type: Literal['manual', 'locked'] = 'manual') -> None:
        '''Add a new line break to the score.'''
        linebreak = LineBreak(id=self._next_id(), time=time, type=type)
        self.lineBreak.append(linebreak)
        # Ensure there's always a 'locked' lineBreak at time 0:
        if not any(lb.time == 0.0 and lb.type == 'locked' for lb in self.lineBreak):
            self.lineBreak.insert(0, LineBreak(time=0.0, type='locked', id=self._next_id()))
        return linebreak
    
    # Convenience methods for managing staves
    def new_stave(self, name: str = None, scale: float = 1.0) -> int:
        '''Add a new stave and return its index.'''
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
                 color: str = None,
                 colorMidiNote: str = None,
                 blackNoteDirection: str = None) -> Note:
        '''Add a note to the specified stave. Use None for inherited properties.'''
        
        note = Note(id=self._next_id(), 
                    time=time, 
                    duration=duration, 
                    pitch=pitch, 
                    velocity=velocity,
                    articulation=articulation, 
                    hand=hand, 
                    _color=color,
                    _colorMidiNote=colorMidiNote, 
                    _blackNoteDirection=blackNoteDirection)
        
        # Attach score reference for property resolution
        note.score = self
        
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
                              _color=color)
        grace_note.score = self
        
        self.get_stave(stave_idx).event.graceNote.append(grace_note)
        return grace_note

    def new_count_line(self, 
                       time: float = 0.0,
                       pitch1: int = 40, 
                       pitch2: int = 44, 
                       color: str = None, 
                       dashPattern: List[int] = None,
                       stave_idx: int = 0) -> CountLine:
        '''Add a count line to the specified stave.'''
        count_line = CountLine(id=self._next_id(), 
                               time=time,
                               pitch1=pitch1,
                               pitch2=pitch2,
                               _color=color,
                               _dashPattern=dashPattern)
        count_line.score = self
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
        
        text_obj = Text(id=self._next_id(),
                       time=time,
                       side=side,
                       distFromSide=distFromSide,
                       text=text,
                       _fontSize=fontSize,
                       _color=color)
        text_obj.score = self

        self.get_stave(stave_idx).event.text.append(text_obj)
        return text_obj

    def new_beam(self,
                 stave_idx: int = 0,
                 time: float = 0.0,
                 staff: float = 0.0,
                 hand: str = '<',
                 color: str = None,
                 width: float = None,
                 slant: float = None) -> Beam:
        '''Add a beam to the specified stave.'''
        
        beam = Beam(id=self._next_id(),
                   time=time,
                   staff=staff,
                   hand=hand,
                   _color=color,
                   _width=width,
                   _slant=slant)
        beam.score = self
        
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
                 middleWidth: float = None) -> Slur:
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
                   _color=color,
                   _startEndWidth=startEndWidth,
                   _middleWidth=middleWidth)
        slur.score = self
        
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
                         lineWidth: float = None) -> StartRepeat:
        '''Add a start repeat to the specified stave.'''
        
        start_repeat = StartRepeat(id=self._next_id(),
                                  time=time,
                                  _color=color,
                                  _lineWidth=lineWidth)
        start_repeat.score = self
        
        self.get_stave(stave_idx).event.startRepeat.append(start_repeat)
        return start_repeat

    def new_end_repeat(self,
                       stave_idx: int = 0,
                       time: float = 0.0,
                       color: str = None,
                       lineWidth: float = None) -> EndRepeat:
        '''Add an end repeat to the specified stave.'''
        
        end_repeat = EndRepeat(id=self._next_id(),
                              time=time,
                              _color=color,
                              _lineWidth=lineWidth)
        end_repeat.score = self
        
        self.get_stave(stave_idx).event.endRepeat.append(end_repeat)
        return end_repeat

    def new_section(self,
                    stave_idx: int = 0,
                    time: float = 0.0,
                    text: str = 'Section',
                    color: str = None,
                    lineWidth: float = None) -> Section:
        '''Add a section to the specified stave.'''
        
        section = Section(id=self._next_id(),
                         time=time,
                         text=text,
                         _color=color,
                         _lineWidth=lineWidth)
        section.score = self
        
        self.get_stave(stave_idx).event.section.append(section)
        return section
    
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

    # Convenience methods for JSON operations
    def save(self, filename: str) -> None:
        '''Save SCORE instance to JSON file.'''
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=True, separators=(',', ':'), indent=None)
    
    @classmethod
    def load(cls, filename: str) -> 'SCORE':
        '''Load ScoreFile instance from JSON file.'''
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        score = cls.from_dict(data)
        score.renumber_id()
        score._reattach_score_references()
        return score
    
    def _reattach_score_references(self):
        '''Reattach score references to all events after loading from JSON.'''
        for stave in self.stave:
            # Reattach to all notes
            for note in stave.event.note:
                note.score = self
                # Also reattach to articulations within notes
                for articulation in note.articulation:
                    articulation.score = self
            
            # Reattach to all other event types
            for grace_note in stave.event.graceNote:
                grace_note.score = self
            
            for beam in stave.event.beam:
                beam.score = self
            
            for text in stave.event.text:
                text.score = self
            
            for slur in stave.event.slur:
                slur.score = self
            
            for count_line in stave.event.countLine:
                count_line.score = self
            
            for start_repeat in stave.event.startRepeat:
                start_repeat.score = self
            
            for end_repeat in stave.event.endRepeat:
                end_repeat.score = self
            
            for section in stave.event.section:
                section.score = self
