#!/usr/bin/env python3
"""
PianoTab GUI Module - Modular interface with side panels and dual-pane editor/preview.

This module provides the main GUI structure for PianoTab with:
- Left side panel for tools/controls
- Right paned window with:
  - Left side: Editor area
  - Right side: Print preview (horizontal split)
"""

import tkinter as tk
from tkinter import ttk
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gui.tool_selector import ToolSelector
from gui.menu import MenuBar

from utils.printview_canvas_tkinter2pymupdf import PdfCanvas

class PianoTabGUI:
    """Main GUI class for PianoTab application."""
    
    def __init__(self, master=None):
        """Initialize the GUI structure."""
        if master is None:
            self.root = tk.Tk()
            self.is_root_owner = True
        else:
            self.root = master
            self.is_root_owner = False
            
        # Initialize references to main areas
        self.side_panel = None
        self.editor_area = None
        self.print_preview = None
        self.menu_bar = None
            
        self.setup_window()
        self.create_layout()
        
    def setup_window(self):
        """Configure the main window."""
        self.root.title("PianoTab - Music Notation Editor")
        self.root.geometry("1400x800")
        self.root.minsize(800, 600)
        
    def create_layout(self):
        """Create the main layout structure."""
        # Ensure proper menu configuration for the root window
        self.root.option_add('*tearOff', False)
        
        # Create menu bar at the top
        self.menu_bar = MenuBar(self.root, self.on_menu_action)
        self.menu_bar.pack(fill="x", side="top")
        
        # Main horizontal paned window (side panel | editor+preview)
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        
        # Left side panel
        self.side_panel_frame = ttk.LabelFrame(self.main_paned, text="Tools & Controls", padding="8")
        self.left_side_panel()
        self.main_paned.add(self.side_panel_frame, weight=1)
        
        # Right side - horizontal paned window (editor | print preview)
        self.editor_preview_paned = ttk.PanedWindow(self.main_paned, orient=tk.HORIZONTAL)
        
        # Editor area (left side of right panel)
        self.editor_frame = ttk.LabelFrame(self.editor_preview_paned, text="Editor", padding="5")
        self.create_editor_area()
        self.editor_preview_paned.add(self.editor_frame, weight=3)
        
        # Print preview area (right side of right panel)
        self.preview_frame = ttk.LabelFrame(self.editor_preview_paned, text="Print Preview", padding="5")
        self.create_print_preview()
        self.editor_preview_paned.add(self.preview_frame, weight=2)
        
        self.main_paned.add(self.editor_preview_paned, weight=4)
        
    def left_side_panel(self):
        """Create the left side panel with tools and controls."""
        # Add ToolSelector widget
        tool_list = [
            ("Select Tool", "⚙"),
            ("Note", "♪"),
            ("Rest", "𝄽"),
            ("Beam", "♫"),
            ("Slur", "⌒"),
            ("Chord", "♬"),
            ("Grace Note", "♪*"),
            ("Measure Line", "|"),
            ("Text", "A"),
            ("Tempo", "♩="),
            ("Dynamics", "f"),
            ("Edit", "✏")
        ]
        
        # Create ToolSelector with callback function
        self.tool_selector = ToolSelector(self.side_panel_frame, tool_list, self.on_tool_selected)
        self.tool_selector.pack(fill='both', expand=True, padx=5, pady=5)

        # Separator
        ttk.Separator(self.side_panel_frame, orient="horizontal").pack(fill="x", pady=15)
        
        # Store references for external access
        self.side_panel = self.side_panel_frame
    
    def on_tool_selected(self, tool_name):
        """Callback function when a tool is selected."""
        print(f"Tool selected: {tool_name}")
        # Here you can add logic to handle tool changes
        # For example, changing cursor, enabling/disabling features, etc.
    
    def on_menu_action(self, menu_name, item_name):
        """Callback function when a menu item is selected."""
        print(f"Menu action: {menu_name} -> {item_name}")
        
        # Handle common menu actions
        if item_name == "Exit":
            self.destroy()
        elif item_name == "New":
            print("Creating new document...")
        elif item_name == "Open...":
            print("Opening file dialog...")
        elif item_name == "Save":
            print("Saving document...")
        elif item_name == "Preferences...":
            print("Opening preferences...")
        # Add more menu handling as needed
        
    def create_editor_area(self):
        """Create the main editor area with canvas and scrollbars."""
        # Editor canvas container
        editor_container = tk.Frame(self.editor_frame)
        editor_container.pack(fill="both", expand=True)
        
        # Create canvas with scrollbars
        self.editor_canvas = tk.Canvas(editor_container, bg="white", 
                                      scrollregion=(0, 0, 3000, 2000),
                                      highlightthickness=1,
                                      highlightbackground="gray")
        
        # Scrollbars
        h_scroll = tk.Scrollbar(editor_container, orient="horizontal", 
                               command=self.editor_canvas.xview)
        v_scroll = tk.Scrollbar(editor_container, orient="vertical", 
                               command=self.editor_canvas.yview)
        
        self.editor_canvas.configure(xscrollcommand=h_scroll.set, 
                                    yscrollcommand=v_scroll.set)
        
        # Grid layout
        self.editor_canvas.grid(row=0, column=0, sticky="nsew")
        h_scroll.grid(row=1, column=0, sticky="ew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        
        editor_container.grid_rowconfigure(0, weight=1)
        editor_container.grid_columnconfigure(0, weight=1)
        
        # Store reference for external access
        self.editor_area = self.editor_canvas
        
    def create_print_preview(self):
        """Create the print preview area."""
        # Preview canvas container
        preview_container = tk.Frame(self.preview_frame)
        preview_container.pack(fill="both", expand=True)
        
        # Create preview canvas with scrollbars
        self.preview_canvas = PdfCanvas(preview_container, page_width=595, page_height=842) # a4 size in points
        
        # Scrollbars for preview
        h_scroll_prev = tk.Scrollbar(preview_container, orient="horizontal", 
                                    command=self.preview_canvas.xview)
        v_scroll_prev = tk.Scrollbar(preview_container, orient="vertical", 
                                    command=self.preview_canvas.yview)
        
        self.preview_canvas.configure(xscrollcommand=h_scroll_prev.set, 
                                     yscrollcommand=v_scroll_prev.set)
        
        # Grid layout
        self.preview_canvas.grid(row=0, column=0, sticky="nsew")
        h_scroll_prev.grid(row=1, column=0, sticky="ew")
        v_scroll_prev.grid(row=0, column=1, sticky="ns")
        
        preview_container.grid_rowconfigure(0, weight=1)
        preview_container.grid_columnconfigure(0, weight=1)
        
        # Store reference for external access
        self.print_preview = self.preview_canvas
        
    def get_editor_canvas(self):
        """Get reference to the editor canvas for external use."""
        return self.editor_area
        
    def get_preview_canvas(self):
        """Get reference to the preview canvas for external use."""
        return self.print_preview
        
    def get_side_panel(self):
        """Get reference to the side panel for external use."""
        return self.side_panel
    
    def get_menu_bar(self):
        """Get reference to the menu bar for external use."""
        return self.menu_bar
    
    def get_selected_tool(self):
        """Get the currently selected tool."""
        if hasattr(self, 'tool_selector'):
            return self.tool_selector.get_tool()
        return None
    
    def set_selected_tool(self, tool_name):
        """Set the selected tool programmatically."""
        if hasattr(self, 'tool_selector'):
            self.tool_selector.set_tool(tool_name)
        
    def run(self):
        """Run the GUI (only if this module owns the root window)."""
        if self.is_root_owner:
            self.root.mainloop()
            
    def destroy(self):
        """Clean up the GUI."""
        if self.is_root_owner:
            self.root.destroy()

# For standalone testing
if __name__ == "__main__":
    app = PianoTabGUI()
    app.run()