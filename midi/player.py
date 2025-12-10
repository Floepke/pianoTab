"""
Simple MIDI player utilities for pianoTAB.
- Lists available MIDI output ports
- Saves/reads selected port from SettingsManager
- Renders a temporary MIDI file to .pianoTAB/play.mid starting at a given cursor time
- Sends the file to the selected MIDI port for playback (basic implementation)
"""

import os
from typing import List, Optional
import threading
import time

try:
    import mido
except Exception:
    mido = None

# Ensure a real-time backend is selected (python-rtmidi) when available
def _init_mido_backend():
    global mido
    if mido is None:
        return
    try:
        current = getattr(mido, 'backend', None)
        if not current or 'rtmidi' not in str(current).lower():
            # Prefer RtMidi backend if installed
            mido.set_backend('mido.backends.rtmidi')
    except Exception:
        # Silently ignore; mido will fall back to default/backend-less operations
        pass

APP_DATA_DIR = os.path.join(os.path.expanduser('~'), '.pianoTAB')
PLAY_MID_PATH = os.path.join(APP_DATA_DIR, 'play.mid')


class _PlaybackController:
    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._active_port: Optional[str] = None

    def is_playing(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def stop(self):
        self._stop.set()
        # Let thread exit naturally
        self._thread = None
        self._active_port = None

    def start_file(self, midi_path: str, port_name: str):
        self.stop()
        self._stop.clear()
        self._active_port = port_name

        def _run():
            _init_mido_backend()
            try:
                with mido.open_output(port_name) as port:
                    for msg in mido.MidiFile(midi_path):
                        if self._stop.is_set():
                            break
                        # Sleep for the message time in seconds; mido provides .time in seconds when iterating
                        time.sleep(msg.time)
                        port.send(msg)
            except Exception:
                pass

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()


_PLAYBACK = _PlaybackController()


def ensure_app_data_dir() -> str:
    os.makedirs(APP_DATA_DIR, exist_ok=True)
    return APP_DATA_DIR


def list_output_ports() -> List[str]:
    if mido is None:
        return []
    _init_mido_backend()
    try:
        ports = mido.get_output_names() or []
        return ports
    except Exception:
        return []


def get_selected_port(settings_manager) -> Optional[str]:
    try:
        return settings_manager.get('midi_port')
    except Exception:
        return None


def set_selected_port(settings_manager, port_name: str) -> None:
    try:
        settings_manager.set('midi_port', port_name)
        settings_manager.save()
    except Exception:
        pass


def build_midi_file(score, start_time_ticks: float) -> Optional[str]:
    """Render a short MIDI file from the score starting at start_time_ticks.
    This is a minimal placeholder: it collects notes starting at/after start_time_ticks
    for a brief duration and writes a single-track MIDI file.
    """
    ensure_app_data_dir()
    if mido is None:
        print("mido not available; cannot build MIDI file")
        return None
    try:
        mid = mido.MidiFile(ticks_per_beat=int(getattr(score.fileSettings, 'quarterNoteUnit', 480)))
        track = mido.MidiTrack()
        mid.tracks.append(track)
        # Simple: collect notes from first stave
        stave = score.stave[0] if getattr(score, 'stave', None) else None
        notes = getattr(getattr(stave, 'event', None), 'note', []) if stave else []
        # Filter notes at/after start
        notes = [n for n in notes if float(n.time) >= float(start_time_ticks)]
        # Sort by time
        notes.sort(key=lambda n: float(n.time))
        # Limit duration window (e.g., 2 measures worth)
        window = float(getattr(score.metaInfo, 'totalLengthTicks', 100000)) * 0.05 if getattr(score, 'metaInfo', None) else 960.0
        end_time = float(start_time_ticks) + window
        for n in notes:
            if float(n.time) > end_time:
                break
            # Write note on/off using delta times
            start = int(float(n.time) - float(start_time_ticks))
            duration = int(float(getattr(n, 'duration', 120)))
            pitch = int(getattr(n, 'pitch', 60))
            velocity = int(getattr(n, 'velocity', 90))
            track.append(mido.Message('note_on', note=pitch, velocity=velocity, time=max(0, start)))
            track.append(mido.Message('note_off', note=pitch, velocity=0, time=max(0, duration)))
        mid.save(PLAY_MID_PATH)
        return PLAY_MID_PATH
    except Exception:
        return None


def play_file_via_port(midi_path: str, port_name: str) -> bool:
    if mido is None:
        return False
    _init_mido_backend()
    try:
        _PLAYBACK.start_file(midi_path, port_name)
        return True
    except Exception:
        return False


def stop_playback() -> None:
    _PLAYBACK.stop()

def is_playing() -> bool:
    return _PLAYBACK.is_playing()


def get_cursor_time_from_editor(piano_roll_editor) -> float:
    """Extract current cursor time (ticks) from the active tool or view offset."""
    try:
        tm = getattr(piano_roll_editor, 'tool_manager', None)
        active = getattr(tm, 'active_tool', None) if tm else None
        cursor_time = getattr(active, '_cursor_time', None) if active else None
    except Exception:
        cursor_time = None
    if cursor_time is not None:
        return float(cursor_time)
    # Fallback: top of current view using scroll_time_offset (quarters → ticks)
    try:
        qnu = float(getattr(getattr(piano_roll_editor, 'score', None).fileSettings, 'quarterNoteUnit', 480))
        quarters = float(getattr(piano_roll_editor, 'scroll_time_offset', 0.0))
        return quarters * qnu
    except Exception:
        return 0.0


def play_from_cursor(editor_widget, settings_manager) -> bool:
    """Render a short MIDI from the editor's current cursor and play to selected port.
    editor_widget: the GUI Editor wrapper (provides get_canvas()) or the Canvas
    settings_manager: SettingsManager instance to read selected port
    Returns True on successful start of playback.
    """
    # Get piano roll editor and score from canvas
    try:
        canvas_getter = getattr(editor_widget, 'get_canvas', None)
        canvas = canvas_getter() if callable(canvas_getter) else editor_widget
        piano_roll_editor = getattr(canvas, 'piano_roll_editor', None)
        score = piano_roll_editor.score if piano_roll_editor else None
    except Exception:
        score = None
        piano_roll_editor = None
    if score is None or piano_roll_editor is None:
        return False
    # Selected port
    port_name = get_selected_port(settings_manager) if settings_manager else None
    if not port_name:
        return False
    # Cursor time
    start_ticks = get_cursor_time_from_editor(piano_roll_editor)
    midi_path = build_midi_file(score, float(start_ticks))
    if not midi_path:
        return False
    return play_file_via_port(midi_path, port_name)

