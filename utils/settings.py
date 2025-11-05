'''
Application settings management for pianoTAB.

Responsibilities:
- Resolve a cross-platform user config path: ~/.pianoTAB/settings.json
- Ensure the folder/file exist with sane defaults
- Load/save JSON safely (preserve unknown keys, tolerate comments off)
- Provide simple get/set helpers and helpers for recent files

Access patterns:
- Primary: via the Kivy App instance: App.get_running_app().settings
- Fallback (non-App contexts): current_settings() returns a module-level singleton
'''

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import threading

try:
    # Prefer Kivy logger when available
    from kivy.logger import Logger  # type: ignore
except Exception:  # pragma: no cover - falls back for non-kivy contexts
    import logging as Logger  # type: ignore


DEFAULTS: Dict[str, Any] = {
    'last_opened_file': '',
    'auto_save': True,
    # Use a clean key name in file; accept legacy verbose key when loading
    'auto_save_interval_in_seconds': 30,  # 0 = instant autosave; >0 = interval in seconds
    'recent_files': [],
    'midi_port': '',
}


def _config_dir() -> Path:
    '''Return the per-user config directory: ~/.pianoTAB'''
    return Path.home() / '.pianoTAB'


def _config_path() -> Path:
    '''Return the full path to settings.json under the config dir.'''
    return _config_dir() / 'settings.json'


@dataclass
class SettingsManager:
    '''JSON-backed settings store with simple helpers.

    Thread-safe for simple get/set/save operations.
    '''

    path: Path = field(default_factory=_config_path)
    _data: Dict[str, Any] = field(default_factory=dict)
    _lock: threading.RLock = field(default_factory=threading.RLock, init=False)

    def ensure_exists(self) -> None:
        '''Ensure the folder and file exist; create with defaults if missing.'''
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if not self.path.exists():
                self._data = DEFAULTS.copy()
                self._safe_write(self._data)

    def load(self) -> None:
        '''Load settings from disk; create with defaults if missing or invalid.'''
        with self._lock:
            try:
                self.ensure_exists()
                raw = self.path.read_text(encoding='utf-8')
                data = json.loads(raw) if raw.strip() else {}
            except Exception as e:
                Logger.warning(f'Settings: failed to read settings.json, recreating defaults: {e}')
                data = {}

            # Backward/legacy compatibility for verbose key name
            legacy_key = 'auto_save_interval_in_seconds(zero for instant auto save or more for interval in seconds)'
            if legacy_key in data and 'auto_save_interval_in_seconds' not in data:
                data['auto_save_interval_in_seconds'] = data.get(legacy_key)

            # Merge with defaults (defaults as base; overlay with file values)
            merged = DEFAULTS.copy()
            merged.update({k: v for k, v in data.items() if v is not None})
            # Normalize types for a few keys
            merged['recent_files'] = list(dict.fromkeys([str(p) for p in merged.get('recent_files', [])]))
            try:
                merged['auto_save_interval_in_seconds'] = int(merged.get('auto_save_interval_in_seconds', 30))
            except Exception:
                merged['auto_save_interval_in_seconds'] = 30

            self._data = merged
            # If we migrated keys, persist
            if legacy_key in data:
                self._safe_write(self._data)

    def save(self) -> None:
        '''Persist current settings to disk.'''
        with self._lock:
            self._safe_write(self._data)

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._data.get(key, default)

    def set(self, key: str, value: Any, *, save: bool = True) -> None:
        with self._lock:
            self._data[key] = value
            if save:
                self._safe_write(self._data)

    # Convenience helpers -------------------------------------------------
    def add_recent_file(self, path: str, *, max_items: int = 15, save: bool = True) -> None:
        with self._lock:
            recents: List[str] = list(self._data.get('recent_files', []))
            path = str(Path(path))
            if path in recents:
                recents.remove(path)
            recents.insert(0, path)
            if max_items > 0:
                recents = recents[:max_items]
            self._data['recent_files'] = recents
            self._data['last_opened_file'] = path
            if save:
                self._safe_write(self._data)

    def clear_recent_files(self, *, save: bool = True) -> None:
        self.set('recent_files', [], save=save)

    # Internal ------------------------------------------------------------
    def _safe_write(self, data: Dict[str, Any]) -> None:
        try:
            # Write atomically via a temp file
            tmp = self.path.with_suffix(self.path.suffix + '.tmp')
            tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            tmp.replace(self.path)
        except Exception as e:
            Logger.warning(f'Settings: failed to write settings.json: {e}')


# Module-level fallback instance for non-App contexts -----------------------
_singleton: Optional[SettingsManager] = None


def current_settings() -> SettingsManager:
    '''Return the active SettingsManager.

    - If running under Kivy, returns App.get_running_app().settings when available.
    - Otherwise, returns (and lazily initializes) a module-level singleton.
    '''
    try:
        from kivy.app import App  # type: ignore
        app = App.get_running_app()
        if app is not None and hasattr(app, 'settings'):
            return app.settings  # type: ignore[attr-defined]
    except Exception:
        pass

    global _singleton
    if _singleton is None:
        _singleton = SettingsManager()
        _singleton.load()
    return _singleton
