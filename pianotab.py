#!/usr/bin/env python3

"""
    PianoTab Main Application

    pianoTab is a music notation editor focused on piano sheet music in an unconventional way.
    in short it is a piano-roll editor suitable for printing on paper. It's condensed form of staves
    makes it readable and compact.
"""

import tkinter as tk
import customtkinter as ctk
from logger import log

# TODO: Make this scaling settings available in app settings
ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('blue')
WIDGET_SCALE = 2.5  # Adjust as needed (try 1.0, 1.25, 1.5, 2.0)
WINDOW_SCALE = 2.5  # Adjust as needed
ctk.set_widget_scaling(WIDGET_SCALE)
ctk.set_window_scaling(WINDOW_SCALE)

print(f"CustomTkinter scaling set to: Widget={WIDGET_SCALE}, Window={WINDOW_SCALE}")

import platform
import os
from gui.main_gui import PianoTabGUI
from editor.editor import Editor
from file.SCORE import SCORE

class PianoTabApplication:
    """Main application class that integrates GUI with business logic."""
    
    def __init__(self):
        # Create main window
        self.root = ctk.CTk()
        
        # macOS focus fix - bring window to front and focus
        if platform.system() == "Darwin":  # macOS
            self.fix_macos_focus()
        
        # Initialize GUI with scaling factor
        self.gui = PianoTabGUI(self.root, widget_scale=WIDGET_SCALE)
        self.root.update_idletasks()  # Force tkinter to update widget dimensions

        # Initialize new SCORE
        self.score = SCORE()

        # Initialize editor
        self.editor = Editor(self.gui.editor_canvas, self.score, self.gui.grid_selector)

        # Bind mouse release to update drawing on panedwindow sash
        self.gui.editor_preview_paned.bind('<ButtonRelease-1>', lambda e: self.editor.drawer.update())
        self.root.bind('<Escape>', lambda e: self.quit())
        
        # Application state
        self.current_file = None
        self.is_modified = False
        
    def fix_macos_focus(self):
        """Fix window focus issues on macOS."""
        # Bring window to front
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.focus_force()
        
        # Schedule to remove topmost after window is shown
        self.root.after(100, lambda: self.root.attributes('-topmost', False))
        
        # Alternative method using AppleScript (more reliable)
        try:
            import subprocess
            # Get the current application name
            app_name = "Python"  # or "PianoTab" if you set it
            script = f'''
                tell application "System Events"
                    set frontmost of process "{app_name}" to true
                end tell
            '''
            subprocess.run(["osascript", "-e", script], check=False)
        except Exception:
            # Fallback if AppleScript fails
            pass
        
    def run(self):
        """Start the application."""
        print("🎹 PianoTab Application Starting...")
        self.root.mainloop()

    def quit(self):
        """Quit the application."""
        print("👋 PianoTab Application Exiting...")
        self.root.quit()
        self.root.destroy()

# Entry point
if __name__ == "__main__":
    app = PianoTabApplication()
    app.run()