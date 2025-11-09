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
BE_GAPS = [3, 8, 15, 20, 27, 32, 39, 44, 51, 56, 63, 68, 75, 80]
'''Key positions where extra spacing (BE gaps) should be added for visual grouping.'''

# Black key positions in the 88-key layout
BLACK_KEYS = [2, 5, 7, 10, 12, 14, 17, 19, 22, 24, 26, 29, 31, 34, 36, 38, 41, 43, 46,
              48, 50, 53, 55, 58, 60, 62, 65, 67, 70, 72, 74, 77, 79, 82, 84, 86]
'''Positions of black keys in the 88-key piano layout.'''

# MIDI and timing constants
PIANOTICK_QUARTER = 256.0
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

# Default visual settings
DEFAULT_PIXELS_PER_QUARTER = 100.0
'''Default zoom level in pixels per quarter note when no score setting is available.'''

# Grid system defaults (single source of truth)
QUARTER_NOTE_TICKS = 256.0
'''Standard quarter note length in ticks (same as PIANOTICK_QUARTER).'''

# Calculate all grid lengths from quarter note for consistency
GRID_LENGTHS = [
    ('1 - Whole', QUARTER_NOTE_TICKS * 4),      # 1024.0
    ('2 - Half', QUARTER_NOTE_TICKS * 2),       # 512.0
    ('4 - Quarter', QUARTER_NOTE_TICKS),        # 256.0
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

def midi_to_key_number(midi_pitch: int) -> int:
    '''Convert MIDI pitch (21-108) to piano key number (1-88).'''
    return midi_pitch - MIDI_KEY_OFFSET

def key_number_to_midi(key_number: int) -> int:
    '''Convert piano key number (1-88) to MIDI pitch (21-108).'''
    return key_number + MIDI_KEY_OFFSET

def ticks_to_quarters(ticks: float) -> float:
    '''Convert ticks to quarter note units.'''
    return ticks / PIANOTICK_QUARTER

def quarters_to_ticks(quarters: float) -> float:
    '''Convert quarter note units to ticks.'''
    return quarters * PIANOTICK_QUARTER

def is_black_key(key_number: int) -> bool:
    '''Check if a piano key number corresponds to a black key.'''
    return key_number in BLACK_KEYS
