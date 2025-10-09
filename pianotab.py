#!/usr/bin/env python3
"""
Example integration of GUI module with main PianoTab application.

This shows how to integrate the GUI module while keeping separation of concerns.
"""

import tkinter as tk
from gui.main_gui import PianoTabGUI

class PianoTabApplication:
    """Main application class that integrates GUI with business logic."""
    
    def __init__(self):
        # Create main window
        self.root = tk.Tk()
        
        # Initialize GUI
        self.gui = PianoTabGUI(self.root)
        
        # Connect GUI to application logic
        self.setup_event_handlers()
        
        # Application state
        self.current_file = None
        self.is_modified = False
        
    def setup_event_handlers(self):
        """Connect GUI events to application logic."""
        # Get canvas references
        self.editor_canvas = self.gui.get_editor_canvas()
        self.preview_canvas = self.gui.get_preview_canvas()
        
        # Example: Add mouse click handler to editor
        self.editor_canvas.bind("<Button-1>", self.on_editor_click)
        self.editor_canvas.bind("<B1-Motion>", self.on_editor_drag)
        
        # Example: Add keyboard shortcuts
        self.root.bind("<Control-s>", self.save_file)
        self.root.bind("<Control-o>", self.open_file)
        self.root.bind("<Control-n>", self.new_file)
        
        print("📋 Event handlers connected:")
        print("   - Mouse clicks on editor canvas")
        print("   - Keyboard shortcuts: Ctrl+S, Ctrl+O, Ctrl+N")
        
    def on_editor_click(self, event):
        """Handle mouse clicks in the editor."""
        x, y = self.editor_canvas.canvasx(event.x), self.editor_canvas.canvasy(event.y)
        print(f"🖱️  Editor click at ({x:.0f}, {y:.0f})")
        
        # Example: Add a note at click position
        note_id = self.editor_canvas.create_oval(x-5, y-5, x+5, y+5, 
                                                fill="blue", outline="darkblue")
        
        # Update preview (simplified example)
        self.update_preview()
        
    def on_editor_drag(self, event):
        """Handle mouse drag in the editor."""
        x, y = self.editor_canvas.canvasx(event.x), self.editor_canvas.canvasy(event.y)
        # Example: Could implement note dragging here
        
    def update_preview(self):
        """Update the print preview based on editor content."""
        # This is where you'd sync editor content to preview
        # For now, just add a simple indicator
        self.preview_canvas.create_text(200, 500, text=f"Last update: {tk.StringVar().get()}", 
                                       font=("Arial", 8), fill="green", tags="update_indicator")
        self.preview_canvas.delete("update_indicator")  # Remove old indicators
        
    def save_file(self, event=None):
        """Save the current file."""
        print("💾 Save file requested")
        # Implement your save logic here
        return "break"  # Prevent default behavior
        
    def open_file(self, event=None):
        """Open a file."""
        print("📂 Open file requested")
        # Implement your open logic here
        return "break"
        
    def new_file(self, event=None):
        """Create a new file."""
        print("📄 New file requested")
        # Clear editor and preview
        self.editor_canvas.delete("all")
        self.preview_canvas.delete("all")
        self.gui.draw_demo_staff()
        self.gui.draw_preview_page()
        return "break"
        
    def run(self):
        """Start the application."""
        print("🎹 PianoTab Application Starting...")
        print("🎨 GUI Module Loaded Successfully!")
        print("\n📖 Try these interactions:")
        print("   - Click in the editor area to add notes")
        print("   - Use Ctrl+S, Ctrl+O, Ctrl+N shortcuts")
        print("   - Resize the panels by dragging the dividers")
        
        self.root.mainloop()

# Entry point
if __name__ == "__main__":
    app = PianoTabApplication()
    app.run()