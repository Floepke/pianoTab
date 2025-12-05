'''
pianoTAB Constants
==================

Shared constants for piano roll editor and sheet engraving.
These constants define the piano keyboard layout and spacing used consistently
throughout the application for both editor display and final output.
'''

# Piano keyboard layout constants
PHYSICAL_SEMITONE_POSITIONS = 103
'''Total number of physical semitone positions in the piano layout.'''

# BE gaps - positions where extra visual spacing is added between key groups
BE_GAPS = [3, 8, 15, 20, 27, 32, 39, 44, 51, 56, 63, 68, 75, 80, 87]
'''Key positions where extra spacing (BE gaps) should be added for visual grouping.'''

# Black key positions in the 88-key layout
BLACK_KEYS = [2, 5, 7, 10, 12, 14, 17, 19, 22, 24, 26, 29, 31, 34, 36, 38, 41, 43, 46,
              48, 50, 53, 55, 58, 60, 62, 65, 67, 70, 72, 74, 77, 79, 82, 84, 86]
'''Positions of black keys in the 88-key piano layout.'''

# MIDI and timing constants
PIANOTICK_QUARTER = 100.0
'''Number of ticks per quarter note in the pianoTAB timing system.'''

MIDI_KEY_OFFSET = 20
'''Offset to convert between MIDI pitch numbers (21-108) and key numbers (1-88).'''

# Piano key range
PIANO_KEY_COUNT = 88
'''Total number of piano keys (1-88).'''

MIDI_PITCH_MIN = 21
'''Minimum MIDI pitch number (key 1).'''

MIDI_PITCH_MAX = 108
'''Maximum MIDI pitch number (key 88).'''

# Grid system defaults (single source of truth)
QUARTER_NOTE_TICKS = 100.0
'''Standard quarter note length in ticks (same as PIANOTICK_QUARTER).'''

# Calculate all grid lengths from quarter note for consistency
GRID_LENGTHS = [
    ('1 - Whole', QUARTER_NOTE_TICKS * 4),      # 1024.0
    ('2 - Half', QUARTER_NOTE_TICKS * 2),       # 512.0
    ('4 - Quarter', QUARTER_NOTE_TICKS),        # 100.0
    ('8 - Eighth', QUARTER_NOTE_TICKS / 2),     # 128.0
    ('16 - Sixteenth', QUARTER_NOTE_TICKS / 4), # 64.0
    ('32 - 32nd', QUARTER_NOTE_TICKS / 8),      # 32.0
    ('64 - 64th', QUARTER_NOTE_TICKS / 16),     # 16.0
    ('128 - 128th', QUARTER_NOTE_TICKS / 32),   # 8.0
]
'''Available grid lengths with their tick values.'''

DEFAULT_GRID_NAME = '8 - Eighth'
'''Initial grid selection on application startup.'''

DEFAULT_GRID_STEP_TICKS = QUARTER_NOTE_TICKS / 2  # 128.0 (eighth note)
'''Default grid step in ticks when grid selector is not available (fallback).'''

# Key layout calculation constants
VISUAL_SEMITONE_POSITIONS_OFFSET = 5
'''Number of semitone positions outside the editor margins (not visible).'''

def get_visual_semitone_positions():
    '''Get the number of visible semitone positions in the editor.'''
    return PHYSICAL_SEMITONE_POSITIONS - VISUAL_SEMITONE_POSITIONS_OFFSET

'''
    Canvas Drawing Layer Order
    ===========================

    Defines the z-order (stacking order) of visual elements in the piano roll editor canvas.
    Elements are drawn from bottom to top in the order listed, with lower indices appearing
    behind higher indices.

    The DRAWING_LAYERS list establishes the rendering sequence where:
    - Layer 0 (midinote) forms the background
    - Middle layers (1-22) contain musical notation elements
    - Layer 23 (edit) shows user selections and edit highlights
    - Layer 24 (cursor) is always drawn on top

    TAG_TO_LAYER provides O(1) lookup from layer tag names to their numerical z-index,
    useful for setting canvas element stacking with the tag_raise() method.
'''
DRAWING_LAYERS = [
    # midi_note in background of the notation.
    'cursor_grid',
    'midi_note', 
    
    # stave elements
    'chord_guide',
    'note_guide',
    'gridline',        
    'barline',
    'stem_white_space',
    'stavethreeline',  
    'stavetwoline',    
    'staveclefline',   
    
    # note elements
    'stop_sign',
    'notehead_white',
    'notehead_black',      
    'left_dot',
    'stem',
    'accidental',

    # grace_note          
    'grace_note',

    # beam elements      
    'beam',
    'beam_stem',

    # other notation elements
    'measure_number',

    'slur',
    'text',
    'tempo',
        'line_break',
        'count_line',
    
    # UI elements (top layers)
    'cursor_line',      # Time cursor line
    'selection_rect',  # Selection rectangle
]

# Create a lookup dict for quick tag->layer mapping
TAG_TO_LAYER = {tag: idx for idx, tag in enumerate(DRAWING_LAYERS)}

OPERATOR_TRESHOLD = 1.0
'''
    I use this treshold to concider two float numbers as equal even though they differ slightly. 
    It seems quite big but smaller numbers then 8 means smaller then 128th note (8=128th note)
    length which is unusual/unpractical to use in music notation. 128th note is the smallest 
    note length in this app.
'''
