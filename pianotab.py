#!/usr/bin/env python3
"""
PianoTab - Music Notation Editor
Main application entry point for Kivy version.
"""
import sys
import os

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
from kivy.logger import Logger
from kivy.metrics import Metrics
from gui.main_gui import PianoTabGUI
from gui.colors import DARK
from editor.editor import Editor
from file.SCORE import SCORE

Metrics.density = 6
Metrics.fontscale = .25

class PianoTab(App):
    """Main PianoTab application."""
    
    title = 'PianoTab - Music Notation Editor'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize data models and controllers here
        self.score = None
        self.editor = None
        self.gui = None
    
    def build(self):
        """Build and return the root widget - UI construction only."""
        # Window setup
        Window.clearcolor = DARK
        try:
            Window.maximize()
        except Exception:
            pass
        
        # Create and return GUI (UI only)
        self.gui = PianoTabGUI()
        return self.gui
    
    def on_start(self):
        """Called after build() - Initialize business logic here."""
        Logger.info('PianoTab: Application started')
        
        # Initialize data model
        self.score = SCORE()
        
        # Create test data
        self.score.new_note(pitch=60, duration=256.0, time=0.0, stave_idx=0)
        self.score.new_note(pitch=62, duration=256.0, time=0.0, stave_idx=0)
        self.score.new_note(pitch=64, duration=256.0, time=0.0, stave_idx=0)
        
        # Initialize controllers
        self.editor = Editor(self.gui.get_editor_widget(), self.score)
        
        # Setup any additional connections/bindings
        self._setup_bindings()
    
    def _setup_bindings(self):
        """Setup event bindings between components."""
        # Example: bind keyboard shortcuts, menu actions, etc.
        pass
    
    def on_stop(self):
        """Cleanup when app is closing."""
        Logger.info('PianoTab: Application stopping')
        
        # Perform any necessary cleanup here
        ...

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