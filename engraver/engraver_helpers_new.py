"""
Helper functions for the engraver, ported from Qt implementation.

Contains coordinate conversion, note processing, staff calculations, etc.
"""

import copy
from typing import List, Dict, Tuple, Any

# Constants
FRACTION = 0.01
PITCH_UNIT = 3.0  # mm
QUARTER_PIANOTICK = 256.0


def calculate_staff_width(key_min: int, key_max: int, draw_scale: float = 1.0) -> float:
    """Calculate staff width based on pitch range.
    
    Based on Qt engraver calculate_staff_width function.
    """
    if key_min == 0 and key_max == 0:
        return 0.0
    
    # Trim to force range to outer sides of staff
    key_min, key_max = min(key_min, 40), max(key_max, 44)
    
    mn_offset = {4: 0, 5: -1, 6: -2, 7: -3, 8: -4, 9: 0, 10: -1, 11: -2, 12: -3, 1: -4, 2: -5, 3: -6}
    mx_offset = {4: 4, 5: 3, 6: 2, 7: 1, 8: 0, 9: 6, 10: 5, 11: 4, 12: 3, 1: 2, 2: 1, 3: 0}
    
    key_min += mn_offset[((key_min - 1) % 12) + 1]
    key_max += mx_offset[((key_max - 1) % 12) + 1]
    key_min, key_max = max(key_min, 1), min(key_max, 88)
    
    # Calculate width
    width = 0.0
    for n in range(key_min - 1, key_max + 1):
        width += PITCH_UNIT * 2 if ((n - 1) % 12) + 1 in [4, 9] and n != key_min else PITCH_UNIT
    
    return width * draw_scale


def trim_key_to_outer_sides_staff(key_min: int, key_max: int) -> Tuple[int, int]:
    """Trim key range to outer sides of staff."""
    if not key_min and not key_max:
        return 0, 0
    
    key_min, key_max = min(key_min, 40), max(key_max, 44)
    
    mn_offset = {4: 0, 5: -1, 6: -2, 7: -3, 8: -4, 9: 0, 10: -1, 11: -2, 12: -3, 1: -4, 2: -5, 3: -6}
    mx_offset = {4: 4, 5: 3, 6: 2, 7: 1, 8: 0, 9: 6, 10: 5, 11: 4, 12: 3, 1: 2, 2: 1, 3: 0}
    
    key_min += mn_offset[((key_min - 1) % 12) + 1]
    key_max += mx_offset[((key_max - 1) % 12) + 1]
    key_min, key_max = max(key_min, 1), min(key_max, 88)
    
    return key_min, key_max


def pitch2x_view(pitch: int, staff_range: Tuple[int, int], scale: float, x_cursor: float) -> float:
    """Convert pitch to x coordinate in view."""
    key_min, key_max = staff_range
    key_min, key_max = trim_key_to_outer_sides_staff(key_min, key_max)
    
    x = x_cursor
    for n in range(1, key_min):
        remainder = ((n - 1) % 12) + 1
        x -= PITCH_UNIT * 2 * scale if remainder in [4, 9] else PITCH_UNIT * 2 * scale / 2
    
    for n in range(1, 88):
        remainder = ((n - 1) % 12) + 1
        x += PITCH_UNIT * 2 * scale if remainder in [4, 9] and n != key_min else PITCH_UNIT * 2 * scale / 2
        if n == pitch:
            break
    
    return x


def tick2y_view(time: float, line_ticks: Tuple[float, float], staff_height: float) -> float:
    """Convert time (ticks) to y coordinate in view.
    
    Args:
        time: Time in ticks
        line_ticks: (start_time, end_time) for this line
        staff_height: Height of staff in mm
    """
    if line_ticks[1] == line_ticks[0]:
        return 0.0
    
    y = staff_height * (time - line_ticks[0]) / (line_ticks[1] - line_ticks[0])
    return y


def EQUALS(a: float, b: float, threshold: float = 0.1) -> bool:
    """Check if two float values are approximately equal."""
    return abs(a - b) < threshold


def GREATER(a: float, b: float, threshold: float = 0.1) -> bool:
    """Check if a is greater than b with threshold."""
    return a > b + threshold


def continuation_dot(time: float, pitch: int, note: Dict) -> Dict:
    """Create continuation dot event."""
    return {
        'time': time,
        'pitch': pitch,
        'type': 'continuationdot',
        'staff': note.get('staff', 0),
        'hand': note.get('hand', 'r')
    }


def stop_sign(time: float, pitch: int, note: Dict) -> Dict:
    """Create stop sign event."""
    return {
        'time': time,
        'pitch': pitch,
        'type': 'notestop',
        'staff': note.get('staff', 0),
        'hand': note.get('hand', 'r')
    }


def note_processor(note: Dict, barline_times: List[float]) -> List[Dict]:
    """Process a note: split on barlines if needed.
    
    Based on Qt engraver note_processor function.
    Returns list of note/notesplit events plus continuation dots.
    """
    output = []
    
    note_start = note['time']
    note_end = note['time'] + note['duration']
    
    # Check if there's a barline between note_start and note_end
    bl_times = []
    for bl in barline_times:
        if note_start < bl < note_end:
            bl_times.append(bl)
            output.append(continuation_dot(bl, note['pitch'], note))
    
    # If no barline in between, add as-is
    if not bl_times:
        note_copy = dict(note)
        note_copy['type'] = 'note'
        output.append(note_copy)
        return output
    
    # Split note on barlines
    first = True
    for bl in bl_times:
        new = dict(note)
        new['duration'] = bl - note_start
        new['time'] = note_start
        new['type'] = 'note' if first else 'notesplit'
        output.append(new)
        note_start = bl
        first = False
    
    # Add last split note
    new = dict(note)
    new['duration'] = note_end - note_start
    new['time'] = note_start
    new['type'] = 'notesplit'
    output.append(new)
    
    return output


def continuation_dot_stopsign_and_connectstem_processor(note_events: List[Dict], DOC: List[Dict]) -> List[Dict]:
    """Process notes to add continuation dots, stop signs, and connect stems.
    
    Based on Qt engraver continuation_dot_stopsign_and_connectstem_processor.
    """
    # Create note_on_off list like MIDI
    note_on_off = []
    for note in sorted(note_events, key=lambda y: y['time']):
        evt = copy.deepcopy(note)
        evt['endtime'] = evt['time'] + evt['duration']
        evt['original_type'] = evt.get('type', 'note')
        note_on_off.append(copy.deepcopy(evt))
        
        # Add noteoff
        evt_off = copy.deepcopy(evt)
        evt_off['type'] = 'noteoff'
        note_on_off.append(evt_off)
    
    # Sort by time
    note_on_off = sorted(
        note_on_off,
        key=lambda y: (
            round(y['time']) if y['type'] != 'noteoff' else round(y['endtime']),
            round(y['endtime'])
        )
    )
    
    # Add notestop and continuationdot events
    active_notes = []
    for idx, note in enumerate(note_on_off):
        if note['type'] != 'noteoff':
            active_notes.append(note)
            
            # Continuation dots for note start
            for n in active_notes:
                if n.get('id') != note.get('id'):
                    if (not EQUALS(n['time'], note['time']) and
                        note.get('staff') == n.get('staff') and
                        note.get('hand') == n.get('hand')):
                        DOC.append(continuation_dot(note['time'], n['pitch'], note))
        
        elif note['type'] == 'noteoff':
            # Remove from active notes
            for n in list(active_notes):
                if (n.get('duration') == note.get('duration') and
                    n.get('pitch') == note.get('pitch') and
                    n.get('staff') == note.get('staff') and
                    n.get('hand') == note.get('hand')):
                    active_notes.remove(n)
                    break
            
            # Continuation dots for note end
            for n in active_notes:
                if n.get('id') != note.get('id'):
                    if (not EQUALS(n['endtime'], note['endtime']) and
                        note.get('staff') == n.get('staff') and
                        note.get('hand') == n.get('hand')):
                        DOC.append(continuation_dot(note['endtime'], n['pitch'], note))
        
        if note['type'] == 'noteoff':
            continue
        
        # Stop sign
        stop_flag = False
        for n in note_on_off[idx + 1:]:
            if (n['type'] != 'noteoff' and
                EQUALS(n['time'], note['time'] + note['duration']) and
                n.get('staff') == note.get('staff') and
                n.get('hand') == note.get('hand')):
                break
            if (n['type'] != 'noteoff' and
                GREATER(n['time'], note['time'] + note['duration']) and
                n.get('staff') == note.get('staff') and
                n.get('hand') == note.get('hand')):
                stop_flag = True
                break
            if n == note_on_off[-1]:
                stop_flag = True
        
        if stop_flag:
            DOC.append(stop_sign(note['time'] + note['duration'] - FRACTION, note['pitch'], note))
        
        # Connect stem
        for n in note_on_off[idx + 1:]:
            if (EQUALS(n['time'], note['time']) and
                n.get('staff') == note.get('staff') and
                n.get('hand') == note.get('hand')):
                DOC.append({
                    'type': 'connectstem',
                    'time': note['time'],
                    'pitch': note['pitch'],
                    'time2': note['time'],
                    'pitch2': n['pitch'],
                    'staff': note.get('staff', 0)
                })
            if n['time'] > note['time']:
                break
    
    return DOC
