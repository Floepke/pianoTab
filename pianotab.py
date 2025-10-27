#!/usr/bin/env python3
"""
PianoTab - Music Notation Editor
Main application entry point for Kivy version.

This is the main launcher for the PianoTab application.
It initializes and runs the Kivy GUI.
"""
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivy.config import Config

# Configure Kivy before importing other Kivy modules
# Set window size and position
Config.set('graphics', 'width', '1400')
Config.set('graphics', 'height', '800')
Config.set('graphics', 'minimum_width', '100')
Config.set('graphics', 'minimum_height', '100')
Config.set('graphics', 'resizable', True)

# Set multisampling for smoother graphics
Config.set('graphics', 'multisamples', '2')

# Enable window maximized on startup (platform-specific)
Config.set('graphics', 'window_state', 'maximized')

# Disable virtual keyboard for desktop app
Config.set('kivy', 'keyboard_mode', '')

from kivy.app import App
from kivy.core.window import Window
from kivy.logger import Logger
from kivy.metrics import Metrics
from gui.main_gui import PianoTabGUI
from editor.editor import Editor

# set global scaling from kivy
Metrics.density = 6  # 3x scaling
Metrics.fontscale = .25  # 0.5x font scaling

class PianoTab(App):
    """Main PianoTab application entry point and structure overview."""

    title = 'PianoTab - Music Notation Editor'

    def build(self):
        # Window and theme
        Window.clearcolor = (0.10, 0.10, 0.12, 1)
        try:
            # Maximize on supported platforms
            Window.maximize()
        except Exception:
            pass

        # Build GUI structure (left side panel + split view with editor/preview)
        self.gui = PianoTabGUI()

        # Create Editor controller and attach to the editor canvas
        self.editor = Editor(self.gui.get_editor_widget())
        self.editor.load_empty()

        return self.gui

    def on_start(self):
        Logger.info('PianoTab: Application started')


def main():
    """Main entry point for PianoTab application."""
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
