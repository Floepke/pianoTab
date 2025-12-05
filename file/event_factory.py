'''
Event factory generator for SCORE class.
Auto-generates new_* methods from Event dataclass definitions.
Auto-generates SCORE.pyi stub file for IDE type hints.
'''

from dataclasses import fields, MISSING
from typing import Type, Any, Dict, get_type_hints
import os


def _generate_event_factory(event_class: Type, event_list_name: str):
    '''
    Generate a factory method for creating and adding events to a SCORE.
    
    Args:
        event_class: The Event dataclass (Note, GraceNote, etc.)
        event_list_name: Name of the list in Event dataclass ('note', 'graceNote', etc.)
    
    Returns:
        A factory method that can be assigned to SCORE
    '''
    
    def factory_method(self, stave_idx: int = 0, **kwargs) -> Any:
        '''
        Auto-generated factory method.
        Creates an event, attaches score reference, and adds to stave.
        
        Args:
            stave_idx: Index of stave to add event to (default 0)
            **kwargs: Field values for the event (use Python field names)
        
        Returns:
            The created event instance
        '''
        # Map parameter names to field names
        # For storage fields like _color, accept both 'color' and '_color'
        field_kwargs = {}
        
        for f in fields(event_class):
            if f.name == 'id':
                # Skip - we auto-assign ID
                continue
            
            # Try both the exact field name and without leading underscore
            param_name = f.name.lstrip('_')
            
            if f.name in kwargs:
                field_kwargs[f.name] = kwargs[f.name]
            elif param_name in kwargs:
                field_kwargs[f.name] = kwargs[param_name]
            # If not provided, dataclass will use its default
        
        # Create the event with auto-assigned ID
        event = event_class(id=self._next_id(), **field_kwargs)
        
        # Attach score reference if the event supports it
        if hasattr(event, 'score'):
            event.score = self
        
        # Special case: Note class has articulations that need score references
        if event_class.__name__ == 'Note' and hasattr(event, 'articulation'):
            for articulation in event.articulation:
                if hasattr(articulation, 'score'):
                    articulation.score = self
        
        # Add to the appropriate event list in the stave
        stave = self.get_stave(stave_idx)
        event_list = getattr(stave.event, event_list_name)
        event_list.append(event)
        
        return event
    
    # Set a helpful docstring
    factory_method.__doc__ = f'''
    Create and add a {event_class.__name__} to the score.
    
    Args:
        stave_idx: Index of stave to add to (default 0)
        **kwargs: Fields for {event_class.__name__} (see {event_class.__name__} dataclass)
    
    Returns:
        {event_class.__name__}: The created event instance
    
    Example:
        score.{event_list_name}(pitch=60, duration=100.0)
    '''
    
    return factory_method


def _get_field_type_str(field_obj) -> str:
    '''Convert a dataclass field type annotation to a string for stub file.'''
    return _type_annotation_to_str(field_obj.type)


def _type_annotation_to_str(field_type) -> str:
    '''Convert a type annotation to string for stub file.'''
    from typing import get_origin, get_args
    
    # First check if it's a typing generic (List, Optional, Literal, etc.)
    origin = get_origin(field_type)
    args = get_args(field_type)
    
    if origin is not None:
        # It's a generic type - handle it
        origin_name = getattr(origin, '__name__', str(origin))
        
        # Capitalize 'list' to 'List' for stub compatibility
        if origin_name == 'list':
            origin_name = 'List'
        
        # Handle Union types (Optional is Union[X, None])
        if origin_name == 'Union' or origin_name == 'UnionType':
            # Check if it's Optional (Union with None)
            if type(None) in args:
                non_none_args = [a for a in args if a is not type(None)]
                if len(non_none_args) == 1:
                    inner_type = _type_annotation_to_str(non_none_args[0])
                    return f'Optional[{inner_type}]'
            # Regular Union
            inner_types = ', '.join(_type_annotation_to_str(a) for a in args)
            return f'Union[{inner_types}]'
        
        # Handle Literal - need to preserve the actual values
        if origin_name == 'Literal':
            # Get the literal values as strings
            literal_values = ', '.join(repr(arg) for arg in args)
            return f'Literal[{literal_values}]'
        
        # Handle other generics (List, etc.)
        if args:
            inner_types = ', '.join(_type_annotation_to_str(a) for a in args)
            return f'{origin_name}[{inner_types}]'
        else:
            return origin_name
    
    # Handle simple types (int, str, float, bool)
    if hasattr(field_type, '__module__') and hasattr(field_type, '__name__'):
        if field_type.__module__ == 'builtins':
            return field_type.__name__
        # For custom classes, use just the class name
        return field_type.__name__
    
    # Fallback: convert to string and clean up
    type_str = str(field_type)
    type_str = type_str.replace('typing.', '')
    return type_str


def _generate_stub_file():
    '''
    Auto-generate SCORE.pyi stub file with type hints for IDE support.
    This file is regenerated every time the module is imported.
    '''
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
    
    # Define all event types and their list names
    event_types = [
        (Note, 'note'),
        (GraceNote, 'graceNote'),
        (Beam, 'beam'),
        (Text, 'text'),
        (Slur, 'slur'),
        (CountLine, 'countLine'),
        (Section, 'section'),
        (StartRepeat, 'startRepeat'),
        (EndRepeat, 'endRepeat'),
        (Tempo, 'tempo'),
    ]
    
    # Start building the stub file content
    stub_lines = [
        "'''",
        "Type stub file for SCORE class.",
        "AUTO-GENERATED - DO NOT EDIT MANUALLY!",
        "Generated by file/event_factory.py on module import.",
        "'''",
        "",
        "from typing import List, Literal, Optional",
        "from file.note import Note",
        "from file.graceNote import GraceNote",
        "from file.beam import Beam",
        "from file.text import Text",
        "from file.slur import Slur",
        "from file.countLine import CountLine",
        "from file.section import Section",
        "from file.startRepeat import StartRepeat",
        "from file.endRepeat import EndRepeat",
        "from file.tempo import Tempo",
        "from file.articulation import Articulation",
        "from file.metaInfo import MetaInfo",
        "from file.header import Header",
        "from file.properties import Properties",
        "from file.baseGrid import BaseGrid",
        "from file.lineBreak import LineBreak",
        "",
        "class SCORE:",
        "    '''Type hints for auto-generated event factory methods.'''",
        "",
    ]
    
    # Generate stub for each event type
    for event_class, list_name in event_types:
        # Convert camelCase to snake_case for method name
        import re
        method_name = re.sub(r'([a-z])([A-Z])', r'\1_\2', list_name).lower()
        method_name = f'new_{method_name}'
        
        # Build parameter list from dataclass fields
        params = ['self', 'stave_idx: int = 0']
        
        for f in fields(event_class):
            if f.name == 'id':
                continue  # Skip ID - auto-assigned
            
            # Use parameter name without leading underscore
            param_name = f.name.lstrip('_')
            
            # Get type annotation string
            type_str = _get_field_type_str(f)
            
            # Get default value
            if f.default is not MISSING:
                if isinstance(f.default, str):
                    default_str = f'"{f.default}"'
                elif f.default is None:
                    default_str = 'None'
                else:
                    default_str = str(f.default)
            elif f.default_factory is not MISSING:
                if 'list' in str(f.default_factory):
                    default_str = '[]'
                else:
                    default_str = 'None'
            else:
                default_str = '...'  # Required field
            
            params.append(f'{param_name}: {type_str} = {default_str}')
        
        # Add method signature
        stub_lines.append(f'    def {method_name}(')
        stub_lines.append(f'        {params[0]},')
        stub_lines.append(f'        {params[1]},')
        for param in params[2:]:
            stub_lines.append(f'        {param},')
        stub_lines.append(f'    ) -> {event_class.__name__}: ...')
        stub_lines.append('')
    
    # Write stub file
    stub_content = '\n'.join(stub_lines)
    stub_path = os.path.join(os.path.dirname(__file__), 'SCORE.pyi')
    
    try:
        with open(stub_path, 'w', encoding='utf-8') as f:
            f.write(stub_content)
    except Exception as e:
        print(f'Warning: Could not generate stub file: {e}')


def setup_event_factories(score_class):
    '''
    Attach all auto-generated event factory methods to SCORE class.
    Also generates SCORE.pyi stub file for IDE type hints.
    Call this once when the module loads.
    '''
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
    
    # Define all event types and their list names
    event_types = [
        (Note, 'note'),
        (GraceNote, 'graceNote'),
        (Beam, 'beam'),
        (Text, 'text'),
        (Slur, 'slur'),
        (CountLine, 'countLine'),
        (Section, 'section'),
        (StartRepeat, 'startRepeat'),
        (EndRepeat, 'endRepeat'),
        (Tempo, 'tempo'),
    ]
    
    # Generate and attach factory methods
    for event_class, list_name in event_types:
        # Convert camelCase to snake_case for method name
        import re
        method_name = re.sub(r'([a-z])([A-Z])', r'\1_\2', list_name).lower()
        method_name = f'new_{method_name}'
        
        factory = _generate_event_factory(event_class, list_name)
        setattr(score_class, method_name, factory)
    
    # Generate stub file for IDE type hints (development only)
    import sys
    if not getattr(sys, 'frozen', False):  # Skip when running as PyInstaller executable
        _generate_stub_file()
