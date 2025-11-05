from dataclasses import dataclass, field, fields, is_dataclass
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

    metaInfo: MetaInfo = field(default_factory=MetaInfo)
    header: Header = field(default_factory=Header)
    properties: Properties = field(default_factory=Properties)
    baseGrid: List[BaseGrid] = field(default_factory=list)
    lineBreak: List[LineBreak] = field(default_factory=list)
    stave: List[Stave] = field(default_factory=lambda: [Stave()])
    quarterNoteLength: float = 256.0

    def __post_init__(self):
        # Initialize ID generator starting from 0:
        self._id = IDGenerator(start_id=0)

        # Ensure there's always a 'locked' lineBreak at time 0:
        if not self.lineBreak or not any(lb.time == 0.0 and lb.type == 'locked' for lb in self.lineBreak):
            self.lineBreak.insert(0, LineBreak(time=0.0, type='locked', id=self._next_id()))

        # ensure there's always one baseGrid:
        if not self.baseGrid:
            self.baseGrid.append(BaseGrid())
        
        # Sync staveRange objects in all lineBreaks to match number of staves
        self._sync_stave_ranges()
        # Normalize any fields that use a '?' JSON alias to booleans in Python
        try:
            self._coerce_bool_alias_fields()
        except Exception:
            pass

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
        return basegrid

    def new_linebreak(self, time: float = 0.0, type: Literal['manual', 'locked'] = 'manual') -> None:
        '''Add a new line break to the score.'''
        linebreak = LineBreak(id=self._next_id(), time=time, type=type)
        self.lineBreak.append(linebreak)
        # Ensure new linebreak has correct number of staveRange objects
        self._sync_stave_ranges()
        return linebreak
    
    def sync_stave_ranges(self) -> None:
        '''Manually sync all lineBreak staveRange objects with the number of staves.
        Call this if you modify staves or lineBreaks outside of the provided methods.'''
        self._sync_stave_ranges()
    
    def validate_cross_references(self) -> List[str]:
        '''Validate cross-references between objects and detect orphaned data.
        
        Returns:
            List of warning messages about reference issues
        '''
        warnings = []
        
        # Get all existing IDs in the score
        all_ids = set()
        id_to_object = {}  # For detailed reporting
        
        # Collect all IDs from all event types across all staves
        event_types = list(Event.__dataclass_fields__.keys())
        
        for stave_idx, stave in enumerate(self.stave):
            for event_type in event_types:
                event_list = getattr(stave.event, event_type)
                for event in event_list:
                    if hasattr(event, 'id'):
                        event_id = event.id
                        if event_id in all_ids:
                            warnings.append(f"Duplicate ID {event_id}: {event_type} in stave {stave_idx}")
                        all_ids.add(event_id)
                        id_to_object[event_id] = (event_type, stave_idx, event)
        
        # Add lineBreak IDs
        for i, line_break in enumerate(self.lineBreak):
            if hasattr(line_break, 'id'):
                if line_break.id in all_ids:
                    warnings.append(f"Duplicate ID {line_break.id}: lineBreak[{i}] conflicts with existing event")
                all_ids.add(line_break.id)
                id_to_object[line_break.id] = ('lineBreak', i, line_break)
        
        # Check for suspicious patterns that might indicate missing references
        
        # 1. Check for beams without nearby notes
        for stave_idx, stave in enumerate(self.stave):
            for beam in stave.event.beam:
                beam_time = beam.time
                # Look for notes within a reasonable time window
                nearby_notes = [
                    note for note in stave.event.note 
                    if abs(note.time - beam_time) <= beam.time + 256.0  # Within one quarter note
                ]
                if not nearby_notes:
                    warnings.append(f"Beam {beam.id} at time {beam_time} in stave {stave_idx} has no nearby notes")
        
        # 2. Check for slurs with invalid time ranges
        for stave_idx, stave in enumerate(self.stave):
            for slur in stave.event.slur:
                start_time = slur.time
                end_time = slur.y4_time
                
                if end_time <= start_time:
                    warnings.append(f"Slur {slur.id} in stave {stave_idx} has invalid time range: {start_time} to {end_time}")
                
                # Check if there are notes in the slur's time range
                notes_in_range = [
                    note for note in stave.event.note
                    if start_time <= note.time <= end_time
                ]
                if not notes_in_range:
                    warnings.append(f"Slur {slur.id} in stave {stave_idx} spans {start_time}-{end_time} but contains no notes")
        
        # 3. Check for notes with articulations that have score references
        for stave_idx, stave in enumerate(self.stave):
            for note in stave.event.note:
                if note.score is None:
                    warnings.append(f"Note {note.id} in stave {stave_idx} missing score reference")
                
                for art_idx, articulation in enumerate(note.articulation):
                    if articulation.score is None:
                        warnings.append(f"Articulation {art_idx} on note {note.id} in stave {stave_idx} missing score reference")
        
        # 4. Check lineBreak staveRange consistency (should be automatic now, but verify)
        expected_stave_count = len(self.stave)
        for lb_idx, line_break in enumerate(self.lineBreak):
            actual_range_count = len(line_break.staveRange)
            if actual_range_count != expected_stave_count:
                warnings.append(f"LineBreak {lb_idx} has {actual_range_count} staveRange objects but score has {expected_stave_count} staves")
        
        # 5. Check for overlapping events that might indicate data corruption
        for stave_idx, stave in enumerate(self.stave):
            # Check for notes with identical time and pitch (possible duplicates)
            notes = stave.event.note
            for i, note1 in enumerate(notes):
                for j, note2 in enumerate(notes[i+1:], i+1):
                    if (note1.time == note2.time and 
                        note1.pitch == note2.pitch and 
                        note1.hand == note2.hand):
                        warnings.append(f"Duplicate notes detected in stave {stave_idx}: {note1.id} and {note2.id} (time={note1.time}, pitch={note1.pitch})")
        
        return warnings
    
    def validate_data_integrity(self) -> List[str]:
        '''Comprehensive validation of score data integrity.
        
        Returns:
            List of all validation warnings and errors
        '''
        warnings = []
        
        # Cross-reference validation
        warnings.extend(self.validate_cross_references())
        
        # ID uniqueness within score context
        used_ids = set()
        for stave_idx, stave in enumerate(self.stave):
            event_types = list(Event.__dataclass_fields__.keys())
            for event_type in event_types:
                event_list = getattr(stave.event, event_type)
                for event in event_list:
                    if hasattr(event, 'id'):
                        if event.id == 0:
                            warnings.append(f"{event_type} in stave {stave_idx} has ID 0 (should be assigned)")
                        elif event.id in used_ids:
                            warnings.append(f"Duplicate ID {event.id} found in {event_type} in stave {stave_idx}")
                        used_ids.add(event.id)
        
        # Time-based validation
        for stave_idx, stave in enumerate(self.stave):
            for note in stave.event.note:
                if note.time < 0:
                    warnings.append(f"Note {note.id} in stave {stave_idx} has negative time: {note.time}")
                if note.duration <= 0:
                    warnings.append(f"Note {note.id} in stave {stave_idx} has invalid duration: {note.duration}")
                if not (1 <= note.pitch <= 88):
                    warnings.append(f"Note {note.id} in stave {stave_idx} has invalid pitch: {note.pitch} (should be 1-88)")
        
        # LineBreak validation
        for i, line_break in enumerate(self.lineBreak):
            if line_break.time < 0:
                warnings.append(f"LineBreak {i} has negative time: {line_break.time}")
            if line_break.type == 'locked' and line_break.time != 0.0:
                warnings.append(f"LineBreak {i} is 'locked' but time is {line_break.time} (should be 0.0)")
        
        return warnings
    
    # Convenience methods for managing staves
    def new_stave(self, name: str = None, scale: float = 1.0) -> int:
        '''Add a new stave and return its index.'''
        stave_name = name or f'Stave {len(self.stave) + 1}'
        self.stave.append(Stave(name=stave_name, scale=scale))
        # Sync staveRange objects in all lineBreaks
        self._sync_stave_ranges()
        return len(self.stave) - 1
    
    def remove_stave(self, index: int) -> bool:
        '''Remove stave by index and sync staveRange objects.'''
        if 0 <= index < len(self.stave):
            del self.stave[index]
            # Sync staveRange objects in all lineBreaks
            self._sync_stave_ranges()
            return True
        return False
    
    def _sync_stave_ranges(self) -> None:
        '''Ensure all lineBreaks have the correct number of staveRange objects.'''
        num_staves = len(self.stave)
        
        for line_break in self.lineBreak:
            # Adjust staveRange list to match number of staves
            current_ranges = len(line_break.staveRange)
            
            if current_ranges < num_staves:
                # Add missing staveRange objects
                for _ in range(num_staves - current_ranges):
                    line_break.staveRange.append(StaveRange())
            elif current_ranges > num_staves:
                # Remove excess staveRange objects
                line_break.staveRange = line_break.staveRange[:num_staves]
    
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
            # Write human-readable JSON with indentation
            # Ensure all alias-'?' fields are serialized as JSON booleans true/false
            try:
                data = self._to_dict_with_bool_aliases()
            except Exception:
                data = self.to_dict()
            json.dump(data, f, ensure_ascii=True, indent=4)
    
    @classmethod
    def load(cls, filename: str) -> 'SCORE':
        '''Load ScoreFile instance from JSON file with validation and default filling.'''
        from file.validation import full_score_validation
        
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate and fix missing fields + check cross-references
        fixed_data, warnings = full_score_validation(data)
        
        # Print warnings about missing/fixed fields
        if warnings:
            print(f"\n=== Validation warnings for '{filename}' ===")
            for warning in warnings:
                print(f"  ⚠ {warning}")
            print(f"=== {len(warnings)} warning(s) total ===\n")

        score = cls.from_dict(fixed_data)
        score.renumber_id()
        score._reattach_score_references()
        # Normalize any 0/1 values for '?' aliases to Python booleans
        try:
            score._coerce_bool_alias_fields()
        except Exception:
            pass
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

    # ------------------ Boolean alias normalization ------------------

    @staticmethod
    def _json_field_name(f) -> str:
        """Best effort to get the JSON alias for a dataclass field; falls back to the Python name."""
        try:
            meta = getattr(f, "metadata", None) or {}
            cfg = meta.get("dataclasses_json", None)
            if cfg is not None:
                if isinstance(cfg, dict):
                    name = cfg.get("field_name", None)
                    if isinstance(name, str) and name:
                        return name
                    # Try marshmallow field data_key
                    mm = cfg.get("mm_field", None)
                    try:
                        data_key = getattr(mm, "data_key", None)
                        if isinstance(data_key, str) and data_key:
                            return data_key
                    except Exception:
                        pass
                else:
                    name = getattr(cfg, "field_name", None)
                    if isinstance(name, str) and name:
                        return name
                    try:
                        mm = getattr(cfg, "mm_field", None)
                        data_key = getattr(mm, "data_key", None)
                        if isinstance(data_key, str) and data_key:
                            return data_key
                    except Exception:
                        pass
                # Fallback: parse string repr for data_key/field_name
                try:
                    s = str(cfg)
                    import re as _re
                    m = _re.search(r"data_key=['\"]([^'\"]+)['\"]", s)
                    if m:
                        return m.group(1)
                    m2 = _re.search(r"field_name=['\"]([^'\"]+)['\"]", s)
                    if m2:
                        return m2.group(1)
                except Exception:
                    pass
        except Exception:
            pass
        return f.name

    def _coerce_bool_alias_fields(self) -> None:
        """Traverse the SCORE object and coerce any fields whose JSON alias ends with '?' to Python bools.
        This keeps the in-memory model using True/False consistently, regardless of legacy 0/1 values.
        """
        def _walk(obj):
            if is_dataclass(obj):
                for f in fields(obj):
                    try:
                        val = getattr(obj, f.name)
                    except Exception:
                        continue
                    # Recurse into containers first
                    if is_dataclass(val) or isinstance(val, (list, dict)):
                        _walk(val)
                        continue
                    # Coerce scalar if alias ends with '?'
                    try:
                        jn = self._json_field_name(f)
                        is_bool_intended = isinstance(jn, str) and jn.endswith("?")
                        # Heuristic fallback: fields commonly used as visibility toggles
                        if not is_bool_intended and (f.name == "visible" or f.name.endswith("Visible")):
                            is_bool_intended = True
                        if is_bool_intended:
                            if val is None:
                                continue
                            # Only coerce ints/bools; never coerce floats/strings
                            if isinstance(val, bool):
                                setattr(obj, f.name, val)
                            elif isinstance(val, int) and not isinstance(val, bool):
                                setattr(obj, f.name, bool(val))
                    except Exception:
                        continue
                return
            if isinstance(obj, list):
                for it in obj:
                    _walk(it)
                return
            if isinstance(obj, dict):
                for it in obj.values():
                    _walk(it)
                return
            # scalars: nothing to do
        _walk(self)

    def _to_dict_with_bool_aliases(self) -> dict:
        """Return a dict suitable for JSON dump where any key ending with '?' has boolean values."""
        base = self.to_dict()

        def _convert(x):
            if isinstance(x, dict):
                out = {}
                for k, v in x.items():
                    cv = _convert(v)
                    if isinstance(k, str) and k.endswith("?"):
                        # Force to bool for primitives; leave containers unchanged (shouldn't happen for bool fields)
                        if isinstance(cv, (bool, int, float)):
                            out[k] = bool(cv)
                        else:
                            out[k] = cv
                    else:
                        out[k] = cv
                return out
            if isinstance(x, list):
                return [_convert(i) for i in x]
            return x

        return _convert(base)


# Auto-generate all event factory methods (new_note, new_grace_note, etc.)
setup_event_factories(SCORE)
