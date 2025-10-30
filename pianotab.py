#!/usr/bin/env python3
"""
PianoTab - Music Notation Editor
Main application entry point for Kivy version.
"""
import sys
import os

os.environ["KIVY_METRICS_DENSITY"] = "1.5"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivy.config import Config

# Configure Kivy before importing other Kivy modules
Config.set('graphics', 'width', '1400')
Config.set('graphics', 'height', '800')
Config.set('graphics', 'minimum_width', '100')
Config.set('graphics', 'minimum_height', '100')
Config.set('graphics', 'resizable', True)
Config.set('graphics', 'multisamples', '2')
Config.set('graphics', 'window_state', 'maximized')
Config.set('kivy', 'keyboard_mode', '')

from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.utils import platform
from gui.toolsash import PianoTabGUI
from gui.colors import DARK
from editor.editor import Editor
from file.SCORE import SCORE
from utils.file_manager import FileManager
from utils.settings import SettingsManager

class PianoTab(App):
    """Main PianoTab application."""
    
    title = 'PianoTab - Music Notation Editor'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize UI and controllers here (no data models in App)
        self.editor = None
        self.gui = None
        self.file_manager = None
        # App-wide settings available from anywhere via App.get_running_app().settings
        self.settings: SettingsManager = SettingsManager()
        self.settings.load()
    
    def build(self):
        """Build and return the root widget - UI construction only."""
        # Window setup
        Window.clearcolor = DARK
        # On macOS, try to enter real native fullscreen (green button behavior)
        # after the window is created and visible. Other platforms use
        # window_state='maximized' (configured above).
        if platform == 'macosx':
            # Try twice with small delays to catch the moment after first draw.
            Clock.schedule_once(lambda _dt: self._try_enter_native_fullscreen_macos(attempt=1), 0.25)
            Clock.schedule_once(lambda _dt: self._try_enter_native_fullscreen_macos(attempt=2), 1.0)
        
        # Create and return GUI (UI only)
        self.gui = PianoTabGUI()
        return self.gui
    
    def on_start(self):
        """Called after build() - Initialize business logic here."""
        Logger.info('PianoTab: Application started')
        
        # Initialize Editor (which owns the SCORE)
        self.editor = Editor(self.gui.get_editor_widget())
        
        # Example test notes
        self.editor.score.new_note(pitch=60, duration=256.0, time=0.0, stave_idx=0)
        self.editor.score.new_note(pitch=62, duration=256.0, time=0.0, stave_idx=0)
        self.editor.score.new_note(pitch=40, duration=256.0, time=0.0, stave_idx=0)
        
        # Setup any additional connections/bindings
        self._setup_bindings()
        
        # File management: create and wire into GUI
        self.file_manager = FileManager(app=self, gui=self.gui, editor=self.editor)
        # Mark dirty on edits
        self.editor.on_modified = self.file_manager.mark_dirty
        # Let GUI delegate its menu actions to the manager
        if hasattr(self.gui, 'set_file_manager'):
            self.gui.set_file_manager(self.file_manager)
    
    def _setup_bindings(self):
        """Setup event bindings between components."""
        # Example: bind keyboard shortcuts, menu actions, etc.
        pass

    def _try_enter_native_fullscreen_macos(self, attempt: int = 1):
        """Best-effort native fullscreen on macOS using AppKit when available.

        - First, try PyObjC to call NSWindow.toggleFullScreen_ for true native
          macOS fullscreen (separate Space, menu bar auto-hide behavior).
        - If PyObjC isn't available, fall back to Kivy's fullscreen/maximize.
        - Attempt this a couple of times as the main window may not be ready
          immediately after build().
        """
        # Only run on macOS
        if platform != 'macosx':
            return

        def _is_nswindow_fullscreen(ns_window) -> bool:
            try:
                # NSWindowStyleMaskFullScreen = 1 << 14
                NSWindowStyleMaskFullScreen = 1 << 14
                return bool(ns_window.styleMask() & NSWindowStyleMaskFullScreen)
            except Exception:
                return False

        # Try using PyObjC (preferred for true native fullscreen)
        try:
            from objc import lookUpClass  # type: ignore
            NSApplication = lookUpClass('NSApplication')
            app = NSApplication.sharedApplication()
            ns_window = app.mainWindow() or app.keyWindow()
            if ns_window is not None:
                if not _is_nswindow_fullscreen(ns_window):
                    ns_window.toggleFullScreen_(None)
                # If still not fullscreen, we'll try once more later (via schedule)
                return
        except Exception:
            # PyObjC not installed or AppKit not available; fall back below
            pass

        # Fallback: try Kivy's toggle_fullscreen, then maximize
        try:
            # Kivy's toggle_fullscreen is borderless fullscreen; not native but better than nothing
            Window.toggle_fullscreen()
            return
        except Exception:
            pass
        try:
            Window.maximize()
        except Exception:
            Logger.debug('PianoTab: Fullscreen/maximize not supported on this platform')
    
    def on_stop(self):
        """Cleanup when app is closing."""
        Logger.info('PianoTab: Application stopping')
        
        # Perform any necessary cleanup here
        try:
            # Persist settings just in case
            if hasattr(self, "settings") and self.settings is not None:
                self.settings.save()
        except Exception:
            pass

def main():
    """Main entry point."""
    Logger.info('PianoTab: Starting PianoTab Music Notation Editor')
    app = PianoTab()
    try:
        app.run()
    except KeyboardInterrupt:
        Logger.info('PianoTab: Application interrupted by user')
    except Exception as e:
        Logger.error(f'PianoTab: Unexpected error: {e}')
        import traceback
        traceback.print_exc()
        return 1
    Logger.info('PianoTab: Application closed')
    return 0

if __name__ == '__main__':
    sys.exit(main())