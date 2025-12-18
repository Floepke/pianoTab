'''
pianoTAB Constants
==================

Shared constants for piano roll editor and sheet engraving.
These constants define the piano keyboard layout and spacing used consistently
throughout the application for both editor display and final output.
'''

# Piano keyboard layout constants
PIANO_KEY_AMOUNT: int = 88
'''Total number of piano keys (1-88).'''
from utils.tools import key_class
BE_KEYS: list[int] = key_class('be')
CF_KEYS: list[int] = key_class('cf')
ADG_KEYS: list[int] = key_class('adg')
BLACK_KEYS: list[int] = key_class('CDFGA')
WHITE_KEYS: list[int] = [k for k in range(1, PIANO_KEY_AMOUNT + 1) if k not in BLACK_KEYS]
'''Lists of key numbers for each key color group.'''

MIDI_KEY_OFFSET: int = 20
'''Offset to convert between MIDI pitch numbers (21-108) and key numbers (1-88).'''

# timing constants
PIANOTICK_QUARTER: float = 100.0
'''Number of ticks per quarter note in the pianoTAB timing system.'''

GRID_LENGTHS: dict[str, float] = {
    '1 - Whole': PIANOTICK_QUARTER * 4,      # 1024.0
    '2 - Half': PIANOTICK_QUARTER * 2,       # 512.0
    '4 - Quarter': PIANOTICK_QUARTER,        # 100.0
    '8 - Eighth': PIANOTICK_QUARTER / 2,     # 128.0
    '16 - Sixteenth': PIANOTICK_QUARTER / 4, # 64.0
    '32 - 32nd': PIANOTICK_QUARTER / 8,      # 32.0
    '64 - 64th': PIANOTICK_QUARTER / 16,     # 16.0
    '128 - 128th': PIANOTICK_QUARTER / 32,   # 8.0
}
'''Available grid lengths with their tick values.'''

DEFAULT_GRID_NAME = '8 - Eighth'
'''Initial grid selection on application startup.'''

DEFAULT_GRID_STEP_TICKS = PIANOTICK_QUARTER / 2  # 128.0 (eighth note)
'''Default grid step in ticks when grid selector is not available (fallback).'''

# Key layout calculation constants
VISUAL_SEMITONE_POSITIONS_OFFSET = 5
'''Number of semitone positions outside the editor margins (not visible).'''

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
    'gridline',
    'stavethreeline',
    'stavetwoline',
    'staveclefline',
    'barline',
    'stem_white_space',
    
    # note elements
    'stop_sign',
    'accidental',
    'notehead_white',
    'notehead_black',
    'left_dot',
    'cursor_line',      # Time cursor line
    'stem',
    'chord_connect',

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
    'selection_rect',  # Selection rectangle
    'keyboard_overlay_bg',     # Piano keyboard overlay background
    'keyboard_overlay_keys',   # Piano keyboard overlay keys
    'cursor',            # Always on top
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
