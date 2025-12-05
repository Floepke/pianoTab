#!/usr/bin/env python3
'''
pianoTAB - Piano-Roll Music Notation
Main application entry point for Kivy version.
'''
import sys
import os

os.environ['KIVY_METRICS_DENSITY'] = '1.5'

# Platform-specific OpenGL backend configuration
if sys.platform == 'win32':
    # Windows: Use ANGLE (DirectX-based) for best compatibility
    os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'
    os.environ['KIVY_WINDOW'] = 'sdl2'
    # Disable problematic features on Windows
    os.environ['KIVY_GLES_LIMITS'] = '1'
elif sys.platform == 'darwin':
    # macOS: Native OpenGL works well
    os.environ['KIVY_GL_BACKEND'] = 'gl'
    os.environ['KIVY_WINDOW'] = 'sdl2'
else:
    # Linux: Native OpenGL is best
    os.environ['KIVY_GL_BACKEND'] = 'gl'
    os.environ['KIVY_WINDOW'] = 'sdl2'

# Stability settings (all platforms)
os.environ['KIVY_GL_DEBUG'] = '0'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# macOS: optionally start as a background app to avoid unhiding the Dock on launch.
# Enable by setting PTAB_BACKGROUND_START=1 (or true/yes). Must be set BEFORE importing Kivy.
try:
    if sys.platform == 'darwin':
        flag = os.getenv('PTAB_BACKGROUND_START', '').strip().lower()
        if flag in ('1', 'true', 'yes', 'on'):
            os.environ['SDL_MAC_BACKGROUND_APP'] = '1'
except Exception:
    pass

from kivy.config import Config

# Configure Kivy before importing other Kivy modules
Config.set('graphics', 'width', '1920')
Config.set('graphics', 'height', '1080')
Config.set('graphics', 'minimum_width', '800')
Config.set('graphics', 'minimum_height', '600')
Config.set('graphics', 'resizable', True)
Config.set('graphics', 'gl_version', '1')
# Config.set('graphics', 'multisamples', '2')  # Disable multisampling to avoid graphics issues

Config.set('kivy', 'keyboard_mode', '')
# Disable vsync
Config.set('graphics', 'vsync', '0')
Config.set('graphics', 'maxfps', '60')

# Configure double-tap detection to be less sensitive
# Default is 250ms - increase to 400ms to avoid accidental double-tap detection
Config.set('postproc', 'double_tap_time', '400')
# Default distance is 20 pixels - keep it reasonable
Config.set('postproc', 'double_tap_distance', '20')

# ALWAYS disable exit on escape (not just in production)
# Disable multitouch emulation (prevents red circle on right-click)
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

# Disable automatic Escape key exit - we'll handle it manually to check for unsaved changes
Config.set('kivy', 'exit_on_escape', '0')

# Configure clipboard to suppress xclip/xsel warnings
# This allows text inputs to still work while preventing error messages
# We use a custom clipboard for musical elements anyway
try:
    # Try to import clipboard providers to test availability
    import subprocess
    import shutil
    
    # Check if xclip is available
    if shutil.which('xclip'):
        # xclip is available, use it
        pass
    else:
        # No xclip, suppress warnings by disabling clipboard checks
        # TextInput will fall back to internal storage
        Config.set('kivy', 'log_level', 'warning')
except Exception:
    pass

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
from utils.settings_manager import SettingsManager
from font import load_embedded_font, cleanup_font, FONT_NAME, apply_default_font

class pianoTAB(App):
    '''Main pianoTAB application.'''
    
    title = 'pianoTAB - Piano-Roll Music Notation'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize UI and controllers here (no data models in App)
        self.editor = None
        self.gui = None
        self.file_manager = None
        self._close_allowed = False  # Flag to control when app can actually close
        # App-wide settings available from anywhere via App.get_running_app().settings
        self.settings: SettingsManager = SettingsManager()
        self.settings.load()
    
    def build(self):
        '''Build and return the root widget - UI construction only.'''
        # Load embedded font before creating any widgets
        try:
            load_embedded_font()
            apply_default_font()
            Logger.info(f'pianoTAB: Using embedded font: {FONT_NAME}')
        except Exception as e:
            Logger.warning(f'pianoTAB: Could not load embedded font: {e}')
        
        # Window setup
        Window.clearcolor = DARK
        
        # Create GUI
        self.gui = GUI()
        
        return self.gui
    
    def on_start(self):
        '''Called after build() - Initialize business logic here.'''
        Logger.info('pianoTAB: Application started')
        
        # Platform-specific window maximization for Linux
        from kivy.utils import platform
        if platform == 'linux':
            try:
                # Use immediate maximization
                Clock.schedule_once(self._safe_maximize_linux, 0)
                Logger.info('pianoTAB: Scheduled window maximization for Linux')
            except Exception as e:
                Logger.warning(f'pianoTAB: Could not schedule window maximization: {e}')
        
        # Initialize Editor (which owns the SCORE model)
        self.editor = Editor(self.gui.get_editor_widget(), gui=self.gui)
        
        # Connect editor to grid_selector for cursor snapping
        self.editor.grid_selector = self.gui.side_panel.grid_selector
        
        # Connect score to grid_selector for quarterNoteUnit access
        print(f'pianoTAB: Before assignment - grid_selector.score = {self.gui.side_panel.grid_selector.score}')
        self.gui.side_panel.grid_selector.score = self.editor.score
        print(f'pianoTAB: After assignment - grid_selector.score = {self.gui.side_panel.grid_selector.score}')
        print(f'pianoTAB: Assigned score to grid_selector, quarterNoteUnit={self.editor.score.fileSettings.quarterNoteUnit if self.editor.score else "N/A"}')
        
        # Bind grid_selector changes to redraw piano roll
        self.gui.side_panel.grid_selector.bind(
            current_grid_step=lambda instance, value: self.editor.redraw_pianoroll()
        )
        
        # Connect tool_selector to editor's tool_manager
        self.gui.side_panel.tool_selector.callback = lambda tool_name: self.editor.tool_manager.set_active_tool(tool_name)
        
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

        # Wire PropertyTreeEditor change callback (bind ONCE)
        try:
            if hasattr(self.gui, 'bind_properties_change'):
                self.gui.bind_properties_change(self._on_properties_changed)
        except Exception as e:
            Logger.warning(f'pianoTAB: Could not bind properties change: {e}')

        # Create initial score once canvas is ready (event-driven)
        def _initialize_score():
            # Load test file on startup
            test_file = '/home/flop/pianoTab/test.piano'
            
            if os.path.exists(test_file):
                self.file_manager.load_file_manually(test_file)
                Logger.info(f'pianoTAB: Loaded file: {test_file}')
            else:
                Logger.info(f'pianoTAB: File not found: {test_file}, creating new file')
                self.file_manager.new_file()

            # redraw_pianoroll because the editor initially draws it's pixels per quarter wrong.
            Clock.schedule_once(lambda dt: self.editor.redraw_pianoroll(), 0)

        try:
            self.editor.canvas.on_ready(_initialize_score)
        except Exception as e:
            Logger.warning(f'pianoTAB: Could not register ready callback: {e}')

        # Optional: bring window to front after background start (macOS)
        try:
            if sys.platform == 'darwin':
                bring = os.getenv('PTAB_BRING_TO_FRONT', '').strip().lower()
                if bring in ('1', 'true', 'yes', 'on'):
                    Clock.schedule_once(lambda _dt: Window.raise_window(), 0.1)
        except Exception:
            pass

    def _setup_bindings(self):
        '''Setup event bindings between components.'''
        # Bind global keyboard shortcuts for zooming
        try:
            Window.bind(on_key_down=self._on_key_down)
        except Exception:
            pass
        
        # Bind window close request to handle unsaved changes
        try:
            Window.bind(on_request_close=self.on_request_close)
        except Exception:
            pass

    def _on_properties_changed(self, score):
        '''Invoked by PropertyTreeEditor after edits.
        
        Marks file as dirty, which triggers engraving for print preview via FileManager.
        Also triggers editor piano roll redraw to reflect property changes.
        '''
        try:
            # Mark file as dirty (which will trigger engraving via FileManager.mark_dirty)
            if self.file_manager is not None:
                self.file_manager.mark_dirty()
            
            # Refresh grid selector in case quarterNoteUnit changed
            if hasattr(self.gui, 'side_panel') and hasattr(self.gui.side_panel, 'grid_selector'):
                self.gui.side_panel.grid_selector.refresh_from_score()
                self.editor.redraw_pianoroll()
            
            # Redraw editor piano roll to reflect changes
            if self.editor is not None:
                self.editor.redraw_pianoroll()
        except Exception as e:
            Logger.warning(f'pianoTAB: Failed to handle property change: {e}')

    def _on_key_down(self, window, key, scancode, codepoint, modifiers):
        '''Handle global key presses for zooming.

        Binds the following keys:
        - '=' or '+' -> zoom in
        - '-' or '_' -> zoom out
        '''
        try:
            # Normalize codepoint; fall back to ASCII from key if needed
            ch = codepoint or ''
            # Some layouts may not provide codepoint; ignore in that case
            if not ch:
                return False
            if ch in ('=', '+'):
                if self.editor is not None:
                    self.editor.zoom_in(factor=1.01)
                    return True
            elif ch in ('-', '_'):
                if self.editor is not None:
                    self.editor.zoom_out(factor=1.01)
                    return True
        except Exception:
            pass
        return False

    def _test_scroll_sequence(self, dt):
        '''Test: scroll to time 0 now, then to 1024.0 two seconds later.'''
        try:
            if self.editor is not None:
                Logger.info('pianoTAB: TEST - Scrolling to time 0.0')
                self.editor.scroll_to_time(0.0)
            Clock.schedule_once(self._scroll_to_second_barline, 2.0)
        except Exception as e:
            Logger.warning(f'pianoTAB: TEST - Failed initial scroll to 0.0: {e}')

    def _scroll_to_second_barline(self, dt):
        try:
            if self.editor is not None:
                Logger.info('pianoTAB: TEST - Scrolling to time 1024.0 (second barline)')
                self.editor.scroll_to_time(1024.0)
        except Exception as e:
            Logger.warning(f'pianoTAB: TEST - Failed scroll to 1024.0: {e}')

    def _safe_maximize_linux(self, dt):
        '''Safely maximize window on Linux with error handling.'''
        try:
            from kivy.utils import platform
            if platform == 'linux':
                # Check if the window is ready and properly initialized
                if Window and hasattr(Window, 'maximize'):
                    Window.maximize()
                    Logger.info('pianoTAB: Window maximized successfully on Linux')
                else:
                    Logger.warning('pianoTAB: Window maximize method not available')
        except Exception as e:
            Logger.warning(f'pianoTAB: Safe maximize failed: {e}')
            # Fallback: try to resize to a large size
            try:
                # Set to a large window size as fallback
                Window.size = (1600, 1000)
                Logger.info('pianoTAB: Window resized to large size (fallback)')
            except Exception as fallback_error:
                Logger.warning(f'pianoTAB: Fallback resize also failed: {fallback_error}')

    def _try_enter_native_fullscreen_macos(self, attempt: int = 1):
        '''Best-effort native fullscreen on macOS using AppKit when available.

        - First, try PyObjC to call NSWindow.toggleFullScreen_ for true native
          macOS fullscreen (separate Space, menu bar auto-hide behavior).
        - If PyObjC isn't available, fall back to Kivy's fullscreen/maximize.
        - Attempt this a couple of times as the main window may not be ready
          immediately after build().
        '''
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
            Logger.debug('pianoTAB: Fullscreen/maximize not supported on this platform')
    
    def on_request_close(self, window, *args, **kwargs):
        '''Handle window close request (including window manager close button).
        
        Returns False to prevent immediate close, allowing save dialog to show.
        The file_manager will call self.stop() after handling unsaved changes.
        '''
        # If close was already approved (by file_manager calling stop()), allow it
        if self._close_allowed:
            Logger.info('pianoTAB: Close approved, allowing window to close')
            return False  # Return False means "allow close"
        
        Logger.info('pianoTAB: Window close requested, checking for unsaved changes')
        # Use file manager's exit routine which guards unsaved changes
        if self.file_manager:
            # This will show the dialog and eventually call self.stop() if user confirms
            self.file_manager.exit_app()
            # Return True to prevent immediate close - dialog will handle it
            Logger.info('pianoTAB: Blocking close to show save dialog')
            return True  # Return True means "prevent close"
        else:
            # No file manager, allow close
            Logger.info('pianoTAB: No file manager, allowing close')
            self._close_allowed = True
            return False  # Allow close
    
    def stop(self, *args, **kwargs):
        '''Override stop to set the close_allowed flag and close the window.'''
        Logger.info('pianoTAB: stop() called, allowing close')
        self._close_allowed = True
        # Close the window which will trigger on_request_close again, but this time it will be allowed
        Window.close()
        return super().stop(*args, **kwargs)
    
    def on_stop(self):
        '''Cleanup when app is closing.'''
        Logger.info('pianoTAB: Application stopping')
        
        # Perform any necessary cleanup here
        try:
            # Persist settings just in case
            if hasattr(self, 'settings') and self.settings is not None:
                self.settings.save()
        except Exception:
            pass
        
        # Clean up temporary font files
        try:
            cleanup_font()
            Logger.info('pianoTAB: Cleaned up temporary font files')
        except Exception as e:
            Logger.warning(f'pianoTAB: Could not clean up font files: {e}')

def main():
    '''Main entry point.'''
    Logger.info('pianoTAB: Starting pianoTAB Music Notation Editor')
    app = pianoTAB()
    try:
        app.run()
    except KeyboardInterrupt:
        Logger.info('pianoTAB: Application interrupted by user')
    except Exception as e:
        Logger.error(f'pianoTAB: Unexpected error: {e}')
        import traceback
        traceback.print_exc()
        return 1
    Logger.info('pianoTAB: Application closed')
    return 0

if __name__ == '__main__':
    sys.exit(main())