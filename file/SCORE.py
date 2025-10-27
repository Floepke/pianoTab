from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import List, Literal, Optional
import json
import time

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
from file.event_factory import setup_event_factories


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

    quarterNoteLength: float = 256.0
    metaInfo: MetaInfo = field(default_factory=MetaInfo)
    header: Header = field(default_factory=Header)
    properties: Properties = field(default_factory=Properties)
    baseGrid: List[BaseGrid] = field(default_factory=list)
    lineBreak: List[LineBreak] = field(default_factory=list)
    stave: List[Stave] = field(default_factory=lambda: [Stave()])

    def __post_init__(self):
        # Initialize ID generator starting from 0:
        self._id = IDGenerator(start_id=0)
        
        # Auto-save configuration (for runtime inspection)
        self._auto_save_enabled = False
        self._auto_save_path = 'current.pianotab'
        self._last_save_time = 0  # Track last save timestamp
        self._save_debounce = 1.0  # Don't save more than once per second

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
    
    def enable_auto_save(self, path: str = 'current.pianotab'):
        """Enable auto-save: writes to path whenever score changes."""
        self._auto_save_enabled = True
        self._auto_save_path = path
        self._auto_save()  # Write initial state
    
    def disable_auto_save(self):
        """Disable auto-save."""
        self._auto_save_enabled = False
    
    def _auto_save(self):
        """Internal: auto-save if enabled, with debouncing to prevent excessive writes."""
        if not self._auto_save_enabled:
            return
        
        current_time = time.time()
        if current_time - self._last_save_time < self._save_debounce:
            return  # Too soon, skip this save
        
        try:
            self.save(self._auto_save_path)
            self._last_save_time = current_time
        except Exception as e:
            # Silent fail to avoid disrupting app flow
            pass
    
    # Convenience methods for managing line breaks and base grids:
    def new_basegrid(self, 
                     numerator: int = 4,
                     denominator: int = 4,
                     gridTimes: List[float] = None,
                     measureAmount: int = 8,
                     timeSignatureIndicatorVisible: int = 1) -> None:
        '''Add a new baseGrid to the score.'''
        if gridTimes is None:
            gridTimes = [256.0, 512.0, 768.0]
        basegrid = BaseGrid(numerator=numerator,
                            denominator=denominator,
                            gridTimes=gridTimes,
                            measureAmount=measureAmount,
                            timeSignatureIndicatorVisible=timeSignatureIndicatorVisible)
        self.baseGrid.append(basegrid)
        self._auto_save()
        return basegrid

    def new_linebreak(self, time: float = 0.0, type: Literal['manual', 'locked'] = 'manual') -> None:
        '''Add a new line break to the score.'''
        linebreak = LineBreak(id=self._next_id(), time=time, type=type)
        self.lineBreak.append(linebreak)
        self._auto_save()
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
    
    # Auto-generated event factory methods are added by setup_event_factories()
    # Available methods: new_note, new_grace_note, new_beam, new_text, new_slur,
    # new_count_line, new_section, new_start_repeat, new_end_repeat, new_tempo
    # All accept stave_idx=0 and **kwargs matching the Event class fields
    
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
            # Use compact JSON (no indentation) for current.pianotab to reduce file size and parsing time
            indent = None if filename == self._auto_save_path else 4
            json.dump(self.to_dict(), f, ensure_ascii=True, separators=(',', ':'), indent=indent)
    
    @classmethod
    def load(cls, filename: str) -> 'SCORE':
        '''Load ScoreFile instance from JSON file with validation and default filling.'''
        from file.validation import validate_and_fix_score
        
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate and fix missing fields
        fixed_data, warnings = validate_and_fix_score(data)
        
        # Print warnings about missing/fixed fields
        if warnings:
            print(f"\n=== Validation warnings for '{filename}' ===")
            for warning in warnings:
                print(f"  ⚠ {warning}")
            print(f"=== {len(warnings)} warning(s) total ===\n")

        score = cls.from_dict(fixed_data)
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


# Auto-generate all event factory methods (new_note, new_grace_note, etc.)
setup_event_factories(SCORE)
