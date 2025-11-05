'''
Validation and migration utilities for SCORE JSON files.
Handles field name mapping and missing field detection.
'''

from dataclasses import fields, MISSING
from typing import Dict, Any, List, Tuple, Type
import json


def get_field_mappings(cls: Type) -> Dict[str, str]:
    '''
    Extract code→JSON field name mappings from dataclass metadata.
    
    Returns:
        Dict mapping Python field names to JSON field names.
        Example: {'duration': 'dur', 'velocity': 'vel', 'color': 'color', ...}
        Note: Storage fields like _color map to their JSON name without underscore.
    '''
    mappings = {}
    for field_obj in fields(cls):
        # Get JSON name from metadata
        metadata = field_obj.metadata.get('dataclasses_json', {})
        json_name = metadata.get('field_name', field_obj.name)
        
        # For storage fields (like _color), keep the underscore in the code name
        # because that's how it's defined in the dataclass
        code_name = field_obj.name
        
        mappings[code_name] = json_name
    
    return mappings


def get_field_defaults(cls: Type) -> Dict[str, Any]:
    '''
    Extract default values for all fields in a dataclass.
    
    Returns:
        Dict mapping JSON field names to their default values.
        Example: {'pitch': 40, 'dur': 256.0, 'color': None, ...}
    '''
    defaults = {}
    mappings = get_field_mappings(cls)
    
    for field_obj in fields(cls):
        code_name = field_obj.name
        json_name = mappings.get(code_name, field_obj.name)
        
        # Get default value
        if field_obj.default is not MISSING:
            defaults[json_name] = field_obj.default
        elif field_obj.default_factory is not MISSING:
            # Call factory to get default (like list, dict, etc.)
            defaults[json_name] = field_obj.default_factory()
        else:
            # No default specified - field is required
            defaults[json_name] = MISSING
    
    return defaults


def validate_and_fix_object(obj_dict: Dict[str, Any], cls: Type, obj_type: str = None) -> Tuple[Dict[str, Any], List[str]]:
    '''
    Validate a loaded JSON object and fill in missing fields with defaults.
    
    Args:
        obj_dict: The loaded JSON object as a dictionary
        cls: The dataclass type this object should match
        obj_type: Optional name for better error messages (e.g., 'Note', 'Slur')
    
    Returns:
        Tuple of (fixed_dict, warnings_list)
        - fixed_dict: The object with missing fields filled in
        - warnings_list: List of warning messages about missing/added fields
    '''
    if obj_type is None:
        obj_type = cls.__name__
    
    warnings = []
    fixed_dict = obj_dict.copy()
    
    # Get mappings and defaults
    mappings = get_field_mappings(cls)
    defaults = get_field_defaults(cls)
    
    # Reverse mapping: JSON name → code name
    json_to_code = {json_name: code_name for code_name, json_name in mappings.items()}
    
    # Check for unexpected fields in JSON
    expected_json_names = set(mappings.values())
    actual_json_names = set(obj_dict.keys())
    
    unexpected = actual_json_names - expected_json_names
    if unexpected:
        warnings.append(f'{obj_type}: Unexpected fields in JSON: {unexpected}')
    
    # Check for missing fields and fill with defaults
    missing = expected_json_names - actual_json_names
    for json_name in missing:
        if json_name in defaults:
            default_value = defaults[json_name]
            if default_value is not MISSING:
                fixed_dict[json_name] = default_value
                code_name = json_to_code.get(json_name, json_name)
                warnings.append(
                    f'{obj_type}: Missing field '{json_name}' (code: '{code_name}'), '
                    f'using default: {default_value}'
                )
            else:
                # Required field with no default
                warnings.append(
                    f'{obj_type}: REQUIRED field '{json_name}' is missing and has no default!'
                )
    
    return fixed_dict, warnings


def validate_and_fix_score(score_dict: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    '''
    Validate entire SCORE structure recursively and fix missing fields.
    
    Args:
        score_dict: The loaded SCORE JSON as a dictionary
    
    Returns:
        Tuple of (fixed_score_dict, all_warnings)
    '''
    from file.SCORE import SCORE
    from file.note import Note
    from file.graceNote import GraceNote
    from file.beam import Beam
    from file.text import Text
    from file.slur import Slur
    from file.countLine import CountLine
    from file.section import Section
    from file.startRepeat import StartRepeat
    from file.endRepeat import EndRepeat
    from file.tempo import Tempo
    from file.articulation import Articulation
    from file.baseGrid import BaseGrid
    from file.lineBreak import LineBreak
    from file.staveRange import StaveRange
    from file.properties import Properties
    from file.globalProperties import (
        GlobalNote, GlobalArticulation, GlobalBeam, GlobalGraceNote,
        GlobalCountLine, GlobalSlur, GlobalText, GlobalBarline,
        GlobalBasegrid, GlobalStave, GlobalPage, GlobalSection,
        GlobalStartRepeat, GlobalEndRepeat
    )
    from file.metaInfo import MetaInfo
    from file.header import Header
    
    all_warnings = []
    fixed_score = score_dict.copy()
    
    # Validate top-level SCORE fields
    # (Skip this for now, as SCORE itself doesn't have field_name mappings)
    
    # Validate metaInfo
    if 'metaInfo' in fixed_score:
        fixed_score['metaInfo'], warnings = validate_and_fix_object(
            fixed_score['metaInfo'], MetaInfo, 'MetaInfo'
        )
        all_warnings.extend(warnings)
    
    # Validate header
    if 'header' in fixed_score:
        fixed_score['header'], warnings = validate_and_fix_object(
            fixed_score['header'], Header, 'Header'
        )
        all_warnings.extend(warnings)
    
    # Validate properties
    if 'properties' in fixed_score:
        props = fixed_score['properties']
        
        # Validate each global properties object
        global_classes = {
            'globalNote': GlobalNote,
            'globalArticulation': GlobalArticulation,
            'globalBeam': GlobalBeam,
            'globalGraceNote': GlobalGraceNote,
            'globalCountLine': GlobalCountLine,
            'globalSlur': GlobalSlur,
            'globalText': GlobalText,
            'globalBarline': GlobalBarline,
            'globalBasegrid': GlobalBasegrid,
            'globalStave': GlobalStave,
            'globalPage': GlobalPage,
            'globalSection': GlobalSection,
            'globalStartRepeat': GlobalStartRepeat,
            'globalEndRepeat': GlobalEndRepeat,
        }
        
        for prop_name, prop_class in global_classes.items():
            if prop_name in props:
                props[prop_name], warnings = validate_and_fix_object(
                    props[prop_name], prop_class, prop_name
                )
                all_warnings.extend(warnings)
    
    # Validate baseGrid
    if 'baseGrid' in fixed_score:
        for i, bg in enumerate(fixed_score['baseGrid']):
            fixed_score['baseGrid'][i], warnings = validate_and_fix_object(
                bg, BaseGrid, f'BaseGrid[{i}]'
            )
            all_warnings.extend(warnings)
    
    # Validate lineBreak
    if 'lineBreak' in fixed_score:
        for i, lb in enumerate(fixed_score['lineBreak']):
            fixed_score['lineBreak'][i], warnings = validate_and_fix_object(
                lb, LineBreak, f'LineBreak[{i}]'
            )
            all_warnings.extend(warnings)
            
            # Validate staveRange within lineBreak
            if 'staveRange' in lb:
                for j, sr in enumerate(lb['staveRange']):
                    lb['staveRange'][j], warnings = validate_and_fix_object(
                        sr, StaveRange, f'LineBreak[{i}].StaveRange[{j}]'
                    )
                    all_warnings.extend(warnings)
    
    # Validate staves and their events
    if 'stave' in fixed_score:
        event_classes = {
            'note': Note,
            'graceNote': GraceNote,
            'beam': Beam,
            'text': Text,
            'slur': Slur,
            'countLine': CountLine,
            'section': Section,
            'startRepeat': StartRepeat,
            'endRepeat': EndRepeat,
            'tempo': Tempo,
        }
        
        for stave_idx, stave in enumerate(fixed_score['stave']):
            if 'event' not in stave:
                continue
            
            events = stave['event']
            
            for event_type, event_class in event_classes.items():
                if event_type not in events:
                    continue
                
                event_list = events[event_type]
                for event_idx, event in enumerate(event_list):
                    fixed_event, warnings = validate_and_fix_object(
                        event, event_class, f'Stave[{stave_idx}].{event_type}[{event_idx}]'
                    )
                    events[event_type][event_idx] = fixed_event
                    all_warnings.extend(warnings)
                    
                    # Validate articulations within notes
                    if event_type == 'note' and 'art' in fixed_event:
                        for art_idx, art in enumerate(fixed_event['art']):
                            fixed_art, art_warnings = validate_and_fix_object(
                                art, Articulation, 
                                f'Stave[{stave_idx}].Note[{event_idx}].Articulation[{art_idx}]'
                            )
                            fixed_event['art'][art_idx] = fixed_art
                            all_warnings.extend(art_warnings)
    
    return fixed_score, all_warnings


def validate_score_integrity(score_instance) -> List[str]:
    '''
    Validate a loaded SCORE instance for data integrity and cross-references.
    
    Args:
        score_instance: A SCORE instance (not a dict)
    
    Returns:
        List of validation warnings and errors
    '''
    if hasattr(score_instance, 'validate_data_integrity'):
        return score_instance.validate_data_integrity()
    else:
        return ['Warning: SCORE instance does not support integrity validation']


def full_score_validation(score_data: dict) -> tuple[dict, list[str]]:
    '''
    Complete validation pipeline: structural validation + cross-reference validation.
    
    Args:
        score_data: Raw score data from JSON
    
    Returns:
        Tuple of (validated_score_dict, all_warnings)
    '''
    # First do structural validation
    fixed_data, structural_warnings = validate_and_fix_score(score_data)
    
    # Convert to SCORE instance for cross-reference validation
    try:
        from file.SCORE import SCORE
        score_instance = SCORE.from_dict(fixed_data)
        score_instance.renumber_id()
        score_instance._reattach_score_references()
        
        # Run integrity validation
        integrity_warnings = validate_score_integrity(score_instance)
        
        # Combine all warnings
        all_warnings = structural_warnings + integrity_warnings
        
        return fixed_data, all_warnings
        
    except Exception as e:
        structural_warnings.append(f'Could not perform cross-reference validation: {e}')
        return fixed_data, structural_warnings
