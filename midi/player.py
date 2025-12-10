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

from editor.editor import Editor
from utils.CONSTANTS import MIDI_KEY_OFFSET, PIANOTICK_QUARTER
from utils.operator import Operator

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
        self._port = None  # type: ignore

    def is_playing(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def stop(self):
        # Signal stop and attempt a soft panic (all notes off) without touching the thread's port
        self._stop.set()
        active = self._active_port
        if active:
            try:
                _init_mido_backend()
                # Open a short-lived output handle to send All Notes Off; avoid closing thread's port here
                with mido.open_output(active) as p:
                    for ch in range(16):
                        # Safety: sustain off, all sound off, all notes off
                        p.send(mido.Message('control_change', channel=ch, control=64, value=0, time=0))
                        # CC 120: All Sound Off, CC 123: All Notes Off (not all synths honor these)
                        p.send(mido.Message('control_change', channel=ch, control=120, value=0, time=0))
                        p.send(mido.Message('control_change', channel=ch, control=123, value=0, time=0))
                        # Explicitly send note_off for every note number to avoid hangs
                        for note in range(128):
                            p.send(mido.Message('note_off', channel=ch, note=note, velocity=0, time=0))
                        time.sleep(0.001)
                        for note in range(128):
                            p.send(mido.Message('note_off', channel=ch, note=note, velocity=0, time=0))
            except Exception:
                # Ignore panic failures; thread will close its own port on exit
                pass

        # Join running thread so we never run two players at once
        t = self._thread
        if t is not None and t.is_alive():
            try:
                t.join(timeout=0.5)
            except Exception:
                pass
        self._thread = None
        self._active_port = None

    def start_file(self, midi_path: str, port_name: str):
        # Ensure any existing playback is fully stopped first
        self.stop()
        self._stop.clear()
        self._active_port = port_name

        def _run():
            _init_mido_backend()
            try:
                mf = mido.MidiFile(midi_path)
                with mido.open_output(port_name) as port:
                    self._port = port
                    for msg in mf:
                        if self._stop.is_set():
                            break
                        # mido yields delta time in seconds
                        if msg.time > 0:
                            # Interruptible sleep for immediate stop responsiveness
                            end = time.monotonic() + float(msg.time)
                            while not self._stop.is_set():
                                remaining = end - time.monotonic()
                                if remaining <= 0:
                                    break
                                time.sleep(min(0.01, remaining))
                        # Skip meta (and optionally sysex) for realtime ports
                        if msg.is_meta or msg.type in ('sysex',):
                            continue
                        port.send(msg)
            except Exception as e:
                print(f"MIDIplayer: Error during MIDI playback: {e}")
            finally:
                # Ensure port reference cleared so stop() won't double-close
                self._port = None

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


def build_midi_file(score, editor: Editor) -> Optional[str]:
    """Render a short MIDI file from the score starting at start_time_ticks (score units, 100.0 == quarter)."""
    ensure_app_data_dir()
    if mido is None:
        print("mido not available; cannot build MIDI file")
        return None

    # Ticks per quarter note in the MIDI file
    tpq = int(getattr(score.fileSettings, 'quarterNoteUnit', 480))

    # Score time base: 100.0 units == 1 quarter note
    units_per_quarter = PIANOTICK_QUARTER  # 100.0

    def to_ticks(t: float) -> int:
        return int(round(float(t) * tpq / units_per_quarter))

    mid = mido.MidiFile(ticks_per_beat=tpq)
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # Tempo from score (default 120 BPM)
    bpm = float(getattr(getattr(score, 'fileSettings', object()), 'tempoBPM', 120.0))
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm), time=0))

    # Collect notes (simple: first stave)
    stave = score.stave[0] if getattr(score, 'stave', None) else None
    notes = getattr(getattr(stave, 'event', None), 'note', []) if stave else []
    
    # get mouse cursor position
    print('MIDI: building from cursor position')
    mouse_cursor = float(editor.mouse_time_cursor)
    print('Building MIDI from cursor position')

    # Note chasing:
    # - include notes starting at/after cursor unchanged
    # - include notes that started before but are still sounding at cursor, trimmed to start at cursor
    note_items = []
    for n in notes:
        start_units = float(n.time)
        dur_units = float(getattr(n, 'duration', units_per_quarter * 0.5))
        if dur_units <= 0:
            continue
        end_units = start_units + dur_units

        if Operator().less_or_equal(end_units, mouse_cursor):
            # fully before cursor; skip
            continue

        if Operator().less(start_units, mouse_cursor) and Operator().less(mouse_cursor, end_units):
            adj_start = mouse_cursor
            adj_dur = end_units - mouse_cursor
        else:
            adj_start = start_units
            adj_dur = dur_units

        pitch = max(0, min(127, int(getattr(n, 'pitch', 60)) + MIDI_KEY_OFFSET))
        velocity = max(1, min(127, int(getattr(n, 'velocity', 90))))
        note_items.append((adj_start, adj_dur, pitch, velocity))

    # Sort by adjusted start time
    note_items.sort(key=lambda item: item[0])

    # Build timeline events with ABSOLUTE times in TICKS
    events = []
    for adj_start, adj_dur, pitch, velocity in note_items:
        start_tick = to_ticks(adj_start)
        end_tick = start_tick + max(0, to_ticks(adj_dur))
        events.append((start_tick, 1, 'note_on', pitch, velocity))
        events.append((end_tick,   0, 'note_off', pitch, 64))  # release velocity

    # Sort by absolute tick time then by order, then emit deltas
    events.sort(key=lambda e: (e[0], e[1]))
    last_tick = to_ticks(mouse_cursor)
    for abs_tick, _order, typ, pitch, vel in events:
        delta = max(0, abs_tick - last_tick)
        track.append(mido.Message(typ, note=pitch, velocity=vel, time=delta))
        last_tick = abs_tick

    # End of track at last_tick (no extra wait)
    track.append(mido.MetaMessage('end_of_track', time=0))

    mid.save(PLAY_MID_PATH)
    return PLAY_MID_PATH


def play_file_via_port(midi_path: str, port_name: str) -> bool:
    if mido is None:
        return False
    _init_mido_backend()
    try:
        _PLAYBACK.start_file(midi_path, port_name)
        return True
    except Exception:
        print("MIDIplayer: Failed to start MIDI playback")
        return False


def stop_playback() -> None:
    _PLAYBACK.stop()

def is_playing() -> bool:
    return _PLAYBACK.is_playing()

