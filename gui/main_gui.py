#!/usr/bin/env python3
'''
PianoTab GUI Module - Clean interface with resizable panels.

This module provides the main GUI structure for PianoTab with:
- Left side panel (ToolSelector)
- Right paned window with:
  - Left side: Editor area (PdfCanvas without scrollbars)
  - Right side: Print preview (PdfCanvas without scrollbars)
'''

import tkinter as tk
import customtkinter as ctk
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.menu import MenuBar
from utils.printview_canvas_tkinter2pymupdf import PdfCanvas
from gui.tool_selector import ToolSelector
from gui.grid_selector import GridSelector
from gui.toolbar import Toolbar

# Set CustomTkinter appearance
ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('blue')

# GUI Scaling Configuration  
GUI_SCALE = 1.0  # Adjust this for your monitor: 0.8 = smaller, 1.2 = larger
ctk.set_widget_scaling(GUI_SCALE)
ctk.set_window_scaling(GUI_SCALE)

class PianoTabGUI:
    '''Main GUI class for PianoTab application using CustomTkinter with resizable panels.'''
    
    def __init__(self, master=None):
        '''Initialize the GUI structure.'''
        if master is None:
            self.root = ctk.CTk()
            self.is_root_owner = True
        else:
            self.root = master
            self.is_root_owner = False
            
        # Initialize references to main areas
        self.side_panel = None
        self.editor_area = None
        self.print_preview = None
            
        self.setup_window()
        self.create_layout()
        
    def setup_window(self):
        '''Configure the main window.'''
        self.root.title('PianoTab - Music Notation Editor')
        self.root.geometry('1400x800')
        self.root.minsize(800, 600)
        
    def create_layout(self):
        '''Create the main layout structure with resizable panels.'''
        # Create native menu bar (automatically attaches to window)
        MenuBar(self.root, self.on_menu_action)
        
        # Main container frame
        self.main_container = ctk.CTkFrame(self.root, corner_radius=10)
        self.main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Use tkinter PanedWindow inside CustomTkinter frame for resizable panels
        # Wide sash to include padding space as draggable area
        self.main_paned = tk.PanedWindow(self.main_container, orient=tk.HORIZONTAL, 
                                        sashwidth=25, sashrelief='flat',
                                        bg=self.main_container.cget('fg_color')[1],
                                        sashpad=0, borderwidth=0, sashcursor='arrow')
        self.main_paned.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Left side panel
        self.side_panel_frame = ctk.CTkFrame(self.main_paned, width=300, corner_radius=8)

        # Add the ToolSelector
        self.tool_selector = ToolSelector(self.side_panel_frame, self.on_tool_selected)
        self.tool_selector.pack(fill='x', padx=5, pady=(5, 0))
        
        # Add the GridSelector
        self.grid_selector = GridSelector(self.side_panel_frame, self.on_grid_changed)
        self.grid_selector.pack(fill='x', padx=5, pady=(5, 5))

        self.left_side_panel()
        self.main_paned.add(self.side_panel_frame, minsize=200, padx=5, pady=5)
        
        # Right side - horizontal paned window (editor | print preview)
        self.editor_preview_paned = tk.PanedWindow(self.main_paned, orient=tk.HORIZONTAL,
                                                  sashwidth=25, sashrelief='flat',
                                                  bg=self.main_container.cget('fg_color')[1],
                                                  sashpad=0, borderwidth=0, sashcursor='arrow')
        
        # Editor area (left side of right panel) - no padding to maximize sash area
        self.editor_frame = ctk.CTkFrame(self.editor_preview_paned, corner_radius=8)
        self.create_editor_area()
        self.editor_preview_paned.add(self.editor_frame, minsize=400, padx=0, pady=0)
        
        # Print preview area (right side of right panel) - no padding to maximize sash area
        self.preview_frame = ctk.CTkFrame(self.editor_preview_paned, corner_radius=8)
        self.create_print_preview()
        self.editor_preview_paned.add(self.preview_frame, minsize=300, padx=0, pady=0)
        
        self.main_paned.add(self.editor_preview_paned, minsize=700, padx=0, pady=0)
        
    def left_side_panel(self):
        '''Create the left side panel (empty).'''
        # Store reference for external access
        self.side_panel = self.side_panel_frame
    
    def on_tool_selected(self, tool_name):
        '''Callback function when a tool is selected.'''
        print(f'Tool selected: {tool_name}')
    
    def on_grid_changed(self, grid_step):
        '''Callback function when grid step is changed.'''
        print(f'Grid step changed to: {grid_step}')
    
    def on_menu_action(self, menu_name, item_name):
        '''Callback function when a menu item is selected.'''
        print(f'Menu action: {menu_name} -> {item_name}')
        
        # Handle common menu actions
        if item_name == 'Exit':
            self.destroy()
        elif item_name == 'New':
            print('Creating new document...')
        elif item_name == 'Open...':
            print('Opening file dialog...')
        elif item_name == 'Save':
            print('Saving document...')
        elif item_name == 'Preferences...':
            print('Opening preferences...')
        # Add more menu handling as needed
        
    def create_editor_area(self):
        '''Create the main editor area (PdfCanvas without scrollbars) with vertical toolbar.'''
        
        # Create main editor container with horizontal layout
        editor_container = ctk.CTkFrame(self.editor_frame)
        editor_container.pack(fill='both', expand=True, padx=0, pady=0)
        
        # # Create vertical toolbar (right side of editor) - FIRST to ensure it gets space
        # self.toolbar = Toolbar(editor_container, self.on_toolbar_action)
        # self.toolbar.pack(side='right', fill='y', padx=(2, 0), pady=0)
        
        # # Ensure toolbar has minimum width and doesn't get hidden
        # self.toolbar.configure(width=60, height=400)  # Set both width and height
        # self.toolbar.pack_propagate(False)
        
        # Create canvas frame (left side) - AFTER toolbar to fill remaining space
        canvas_frame = ctk.CTkFrame(editor_container)
        canvas_frame.pack(side='left', fill='both', expand=True, padx=(0, 2), pady=0)
        
        # Create editor canvas without scrollbars
        self.editor_canvas = PdfCanvas(canvas_frame, page_width=595, page_height=842, pdf_mode=False) # a4 size in points
        
        # Pack canvas without scrollbars
        self.editor_canvas.pack(fill='both', expand=True, padx=0, pady=0)
        
        # Store reference for external access
        self.editor_area = self.editor_canvas
        
    def create_print_preview(self):
        '''Create the print preview area (PdfCanvas without scrollbars).'''
        
        # Create preview canvas container (tkinter frame for PdfCanvas compatibility) - zero padding
        canvas_frame = ctk.CTkFrame(self.preview_frame)
        canvas_frame.pack(fill='both', expand=True, padx=0, pady=0)
        
        # Create preview canvas without scrollbars
        self.preview_canvas = PdfCanvas(canvas_frame, page_width=595, page_height=842) # a4 size in points
        
        # Pack canvas without scrollbars
        self.preview_canvas.pack(fill='both', expand=True, padx=0, pady=0)
        
        # Store reference for external access
        self.print_preview = self.preview_canvas
        
    def get_editor_canvas(self):
        '''Get reference to the editor canvas for external use.'''
        return self.editor_area
        
    def get_preview_canvas(self):
        '''Get reference to the preview canvas for external use.'''
        return self.print_preview
        
    def get_side_panel(self):
        '''Get reference to the side panel for external use.'''
        return self.side_panel
        
    def run(self):
        '''Run the GUI (only if this module owns the root window).'''
        if self.is_root_owner:
            self.root.mainloop()
            
    def destroy(self):
        '''Clean up the GUI.'''
        if self.is_root_owner:
            self.root.destroy()

# For standalone testing
if __name__ == '__main__':
    app = PianoTabGUI()
    app.run()