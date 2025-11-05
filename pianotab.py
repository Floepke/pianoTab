#!/usr/bin/env python3
"""
PianoTab - Music Notation Editor
Main application entry point for Kivy version.
"""
import sys
import os

os.environ["KIVY_METRICS_DENSITY"] = "1.5"
# Try to force a specific window provider to avoid issues
os.environ["KIVY_WINDOW"] = "sdl2"
# Disable vsync which can cause hanging
os.environ["KIVY_GL_BACKEND"] = "gl"
# Additional environment variables to help with stability
os.environ["KIVY_GL_DEBUG"] = "0"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivy.config import Config

# Configure Kivy before importing other Kivy modules
Config.set('graphics', 'width', '3840')
Config.set('graphics', 'height', '2160')
Config.set('graphics', 'minimum_width', '800')
Config.set('graphics', 'minimum_height', '600')
Config.set('graphics', 'resizable', True)
# Config.set('graphics', 'multisamples', '2')  # Disable multisampling to avoid graphics issues

# Platform-specific window state configuration
import platform as py_platform
if py_platform.system() == 'Linux':
    # Keep config-based maximization disabled to avoid segfault
    # Use only runtime maximization instead
    pass
else:
    # Keep windowed for macOS and Windows for better compatibility
    pass

Config.set('kivy', 'keyboard_mode', '')
# Disable vsync
Config.set('graphics', 'vsync', '0')

from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.utils import platform
from gui.gui import GUI
from gui.colors import DARK
from editor.editor import Editor
from file.SCORE import SCORE
from utils.file_manager import FileManager
from utils.settings import SettingsManager
from utils.embedded_font import cleanup_embedded_fonts

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
        
        # Create and return GUI (UI only)
        self.gui = GUI()
        return self.gui
    
    def on_start(self):
        """Called after build() - Initialize business logic here."""
        Logger.info('PianoTab: Application started')
        
        # Platform-specific window maximization for Linux
        from kivy.utils import platform
        if platform == 'linux':
            try:
                # Use a safer delayed maximization approach for Linux
                Clock.schedule_once(self._safe_maximize_linux, 1.0)
                Logger.info('PianoTab: Scheduled safe window maximization for Linux')
            except Exception as e:
                Logger.warning(f'PianoTab: Could not schedule window maximization: {e}')
        
        # Initialize Editor (which owns the SCORE)
        self.editor = Editor(self.gui.get_editor_widget())
        
        # Set canvas reference to piano roll editor for scroll snap functionality
        self.gui.get_editor_widget().set_piano_roll_editor(self.editor)
        
        # Setup any additional connections/bindings
        self._setup_bindings()
        
        # File management: create and wire into GUI
        self.file_manager = FileManager(app=self, gui=self.gui, editor=self.editor)
        
        # Mark dirty on edits
        self.editor.on_modified = self.file_manager.mark_dirty
        
        # Let GUI delegate its menu actions to the manager
        if hasattr(self.gui, 'set_file_manager'):
            self.gui.set_file_manager(self.file_manager)

        # Wire PropertyTreeEditor to current SCORE and bind change callback
        try:
            if hasattr(self.gui, 'bind_properties_change'):
                self.gui.bind_properties_change(self._on_properties_changed)
            if hasattr(self.gui, 'set_properties_score') and self.editor is not None:
                # Immediate bind
                self.gui.set_properties_score(self.editor.score)
                # Also schedule on next frame to guarantee GUI is fully laid out
                Clock.schedule_once(lambda dt: self.gui.set_properties_score(self.editor.score), 0)
        except Exception:
            pass

        # Run a zoom refresh once the GUI/canvas is laid out so SCORE ppq applies with real scale.
        try:
            Clock.schedule_once(self._zoom_refresh_after_gui_ready, 0)
        except Exception as e:
            Logger.warning(f'PianoTab: Could not schedule zoom refresh: {e}')

        # Test: set scroll to time 0, then after 2 seconds to 1024.0 (second barline)
        try:
            Clock.schedule_once(self._test_scroll_sequence, 0.8)
            Logger.info('PianoTab: Scheduled test scroll sequence (0.0 then 1024.0)')
        except Exception as e:
            Logger.warning(f'PianoTab: Could not schedule test scroll sequence: {e}')

    def _zoom_refresh_after_gui_ready(self, dt, attempts: int = 0):
        """Ensure editor.zoom_refresh runs after canvas is sized and scaled.

        Retries briefly if layout isn't ready yet.
        """
        try:
            cv = self.gui.get_editor_widget() if self.gui else None
            if not cv or cv.width <= 0 or cv.height <= 0 or getattr(cv, '_px_per_mm', 0) <= 0:
                if attempts < 20:
                    Clock.schedule_once(lambda _dt: self._zoom_refresh_after_gui_ready(_dt, attempts + 1), 0.05)
                else:
                    Logger.warning('PianoTab: zoom_refresh skipped (canvas not ready after retries)')
                return
            if self.editor is not None:
                self.editor.zoom_refresh()
                Logger.info('PianoTab: Performed zoom_refresh after GUI ready')
        except Exception as e:
            Logger.warning(f'PianoTab: zoom_refresh after GUI failed: {e}')
    
    def _setup_bindings(self):
        """Setup event bindings between components."""
        # Bind global keyboard shortcuts for zooming
        try:
            Window.bind(on_key_down=self._on_key_down)
        except Exception:
            pass

    def _on_properties_changed(self, score):
        """
        Invoked by PropertyTreeEditor after edits.
        Refresh the editor view to reflect updated SCORE properties and mark as dirty.
        """
        try:
            if self.editor is not None:
                self.editor.refresh_display()
            if self.file_manager is not None:
                self.file_manager.mark_dirty()
        except Exception:
            pass

    def _on_key_down(self, window, key, scancode, codepoint, modifiers):
        """Handle global key presses for zooming.

        Binds the following keys:
        - '=' or '+' -> zoom in
        - '-' or '_' -> zoom out
        """
        try:
            # Normalize codepoint; fall back to ASCII from key if needed
            ch = codepoint or ''
            # Some layouts may not provide codepoint; ignore in that case
            if not ch:
                return False
            if ch in ('=', '+'):
                if self.editor is not None:
                    self.editor.zoom_in(1.2)
                    return True
            elif ch in ('-', '_'):
                if self.editor is not None:
                    self.editor.zoom_out(1.2)
                    return True
        except Exception:
            pass
        return False

    def _test_scroll_sequence(self, dt):
        """Test: scroll to time 0 now, then to 1024.0 two seconds later."""
        try:
            if self.editor is not None:
                Logger.info('PianoTab: TEST - Scrolling to time 0.0')
                self.editor.scroll_to_time(0.0)
            Clock.schedule_once(self._scroll_to_second_barline, 2.0)
        except Exception as e:
            Logger.warning(f'PianoTab: TEST - Failed initial scroll to 0.0: {e}')

    def _scroll_to_second_barline(self, dt):
        try:
            if self.editor is not None:
                Logger.info('PianoTab: TEST - Scrolling to time 1024.0 (second barline)')
                self.editor.scroll_to_time(1024.0)
        except Exception as e:
            Logger.warning(f'PianoTab: TEST - Failed scroll to 1024.0: {e}')

    def _safe_maximize_linux(self, dt):
        """Safely maximize window on Linux with error handling."""
        try:
            from kivy.utils import platform
            if platform == 'linux':
                # Check if the window is ready and properly initialized
                if Window and hasattr(Window, 'maximize'):
                    Window.maximize()
                    Logger.info('PianoTab: Window maximized successfully on Linux')
                else:
                    Logger.warning('PianoTab: Window maximize method not available')
        except Exception as e:
            Logger.warning(f'PianoTab: Safe maximize failed: {e}')
            # Fallback: try to resize to a large size
            try:
                # Set to a large window size as fallback
                Window.size = (1600, 1000)
                Logger.info('PianoTab: Window resized to large size (fallback)')
            except Exception as fallback_error:
                Logger.warning(f'PianoTab: Fallback resize also failed: {fallback_error}')

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
        
        # Clean up temporary font files
        try:
            cleanup_embedded_fonts()
            Logger.info('PianoTab: Cleaned up temporary font files')
        except Exception as e:
            Logger.warning(f'PianoTab: Could not clean up font files: {e}')

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