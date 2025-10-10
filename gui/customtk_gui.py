#!/usr/bin/env python3
"""
PianoTab CustomTkinter GUI Module - Modern dark-themed interface with resizable panels.

This module provides a modern GUI structure for PianoTab using CustomTkinter with:
- Left side panel for tools/controls (resizable)
- Right paned window with:
  - Left side: Editor area (resizable)
  - Right side: Print preview (resizable)
"""

import customtkinter as ctk
import tkinter as tk
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gui.tool_selector import ToolSelector

from utils.printview_canvas_tkinter2pymupdf import PdfCanvas

# Set CustomTkinter appearance
ctk.set_appearance_mode("dark")  # "dark" or "light"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

class ResizableFrame(ctk.CTkFrame):
    """A resizable frame that can be dragged to resize."""
    
    def __init__(self, master, min_width=100, **kwargs):
        super().__init__(master, **kwargs)
        self.min_width = min_width
        self.is_resizing = False
        
        # Create resize handle
        self.resize_handle = ctk.CTkFrame(self, width=5, corner_radius=0, fg_color="gray")
        self.resize_handle.pack(side="right", fill="y")
        
        # Bind events for resizing
        self.resize_handle.bind("<Button-1>", self.start_resize)
        self.resize_handle.bind("<B1-Motion>", self.do_resize)
        self.resize_handle.bind("<ButtonRelease-1>", self.stop_resize)
        self.resize_handle.bind("<Enter>", lambda e: self.resize_handle.configure(cursor="sb_h_double_arrow"))
        self.resize_handle.bind("<Leave>", lambda e: self.resize_handle.configure(cursor=""))
        
    def start_resize(self, event):
        self.is_resizing = True
        self.start_x = event.x_root
        self.start_width = self.winfo_width()
        
    def do_resize(self, event):
        if self.is_resizing:
            delta_x = event.x_root - self.start_x
            new_width = max(self.min_width, self.start_width + delta_x)
            self.configure(width=new_width)
            
    def stop_resize(self, event):
        self.is_resizing = False

class CustomTkMenuBar(ctk.CTkFrame):
    """Custom menu bar for CustomTkinter."""
    
    def __init__(self, master, callback=None):
        super().__init__(master)
        self.callback = callback
        self.configure(height=35, corner_radius=0)
        
        # Create menu buttons
        self.create_menus()
        
    def create_menus(self):
        """Create menu buttons."""
        # File menu
        self.file_menu = ctk.CTkOptionMenu(
            self, 
            values=["New", "Open...", "Save", "Save As...", "Export PDF", "Exit"],
            command=lambda choice: self._menu_callback("File", choice),
            width=60,
            height=28,
            corner_radius=6,
            fg_color=("gray75", "gray25"),
            button_color=("gray75", "gray25"),
            button_hover_color=("gray70", "gray30")
        )
        self.file_menu.set("File")
        self.file_menu.pack(side="left", padx=5, pady=3)
        
        # Edit menu
        self.edit_menu = ctk.CTkOptionMenu(
            self,
            values=["Undo", "Redo", "Cut", "Copy", "Paste", "Select All", "Preferences..."],
            command=lambda choice: self._menu_callback("Edit", choice),
            width=60,
            height=28,
            corner_radius=6,
            fg_color=("gray75", "gray25"),
            button_color=("gray75", "gray25"),
            button_hover_color=("gray70", "gray30")
        )
        self.edit_menu.set("Edit")
        self.edit_menu.pack(side="left", padx=5, pady=3)
        
        # View menu
        self.view_menu = ctk.CTkOptionMenu(
            self,
            values=["Zoom In", "Zoom Out", "Zoom to Fit", "Full Screen", "Show Grid", "Show Rulers"],
            command=lambda choice: self._menu_callback("View", choice),
            width=60,
            height=28,
            corner_radius=6,
            fg_color=("gray75", "gray25"),
            button_color=("gray75", "gray25"),
            button_hover_color=("gray70", "gray30")
        )
        self.view_menu.set("View")
        self.view_menu.pack(side="left", padx=5, pady=3)
        
    def _menu_callback(self, menu_name, item_name):
        """Handle menu item selection."""
        if self.callback:
            self.callback(menu_name, item_name)
        print(f"🎯 Menu action: {menu_name} -> {item_name}")

class CustomTkToolSelector(ctk.CTkFrame):
    """CustomTkinter version of ToolSelector."""
    
    def __init__(self, master, tools, callback=None):
        super().__init__(master)
        self.tools = tools
        self.callback = callback
        self.selected_tool = None
        
        # Title label
        self.title_label = ctk.CTkLabel(self, text="Tools", font=ctk.CTkFont(size=16, weight="bold"))
        self.title_label.pack(pady=(10, 5))
        
        # Current tool display
        self.current_tool_label = ctk.CTkLabel(self, text="Selected: None", font=ctk.CTkFont(size=12))
        self.current_tool_label.pack(pady=(0, 10))
        
        # Tool buttons frame
        self.tools_frame = ctk.CTkScrollableFrame(self, label_text="")
        self.tools_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Create tool buttons
        self.tool_buttons = []
        for i, (tool_name, tool_symbol) in enumerate(self.tools):
            btn = ctk.CTkButton(
                self.tools_frame,
                text=f"{tool_symbol} {tool_name}",
                command=lambda t=tool_name: self.select_tool(t),
                height=32,
                corner_radius=6,
                fg_color=("gray75", "gray25"),
                hover_color=("gray70", "gray30")
            )
            btn.pack(fill="x", pady=2)
            self.tool_buttons.append(btn)
            
        # Select first tool by default
        if self.tools:
            self.select_tool(self.tools[0][0])
    
    def select_tool(self, tool_name):
        """Select a tool and update display."""
        self.selected_tool = tool_name
        self.current_tool_label.configure(text=f"Selected: {tool_name}")
        
        # Update button colors
        for i, (name, symbol) in enumerate(self.tools):
            if name == tool_name:
                self.tool_buttons[i].configure(fg_color=("blue", "blue"))
            else:
                self.tool_buttons[i].configure(fg_color=("gray75", "gray25"))
        
        if self.callback:
            self.callback(tool_name)
    
    def get_tool(self):
        """Get currently selected tool."""
        return self.selected_tool
    
    def set_tool(self, tool_name):
        """Set tool programmatically."""
        self.select_tool(tool_name)

class PianoTabCustomGUI:
    """Main GUI class for PianoTab application using CustomTkinter with resizable panels."""
    
    def __init__(self, master=None):
        """Initialize the GUI structure."""
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
        self.menu_bar = None
            
        self.setup_window()
        self.create_layout()
        
    def setup_window(self):
        """Configure the main window."""
        self.root.title("PianoTab - Music Notation Editor")
        self.root.geometry("1400x800")
        self.root.minsize(800, 600)
        
    def create_layout(self):
        """Create the main layout structure with resizable panels."""
        # Create menu bar at the top
        self.menu_bar = CustomTkMenuBar(self.root, self.on_menu_action)
        self.menu_bar.pack(fill="x", side="top", padx=10, pady=(10, 5))
        
        # Main container frame
        self.main_container = ctk.CTkFrame(self.root, corner_radius=10)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        
        # Use tkinter PanedWindow inside CustomTkinter frame for resizable panels
        self.main_paned = tk.PanedWindow(self.main_container, orient=tk.HORIZONTAL, 
                                        sashwidth=15, sashrelief="flat",
                                        bg=self.main_container.cget("fg_color")[1])
        self.main_paned.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Left side panel (resizable)
        self.side_panel_frame = ctk.CTkFrame(self.main_paned, width=300, corner_radius=8)
        self.left_side_panel()
        self.main_paned.add(self.side_panel_frame, minsize=200)
        
        # Right side - horizontal paned window (editor | print preview)
        self.editor_preview_paned = tk.PanedWindow(self.main_paned, orient=tk.HORIZONTAL,
                                                  sashwidth=15, sashrelief="flat",
                                                  bg=self.main_container.cget("fg_color")[1])
        
        # Editor area (left side of right panel)
        self.editor_frame = ctk.CTkFrame(self.editor_preview_paned, corner_radius=8)
        self.create_editor_area()
        self.editor_preview_paned.add(self.editor_frame, minsize=400)
        
        # Print preview area (right side of right panel)
        self.preview_frame = ctk.CTkFrame(self.editor_preview_paned, corner_radius=8)
        self.create_print_preview()
        self.editor_preview_paned.add(self.preview_frame, minsize=300)
        
        self.main_paned.add(self.editor_preview_paned, minsize=700)
        
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
        
        # Create CustomTk ToolSelector
        self.tool_selector = CustomTkToolSelector(self.side_panel_frame, tool_list, self.on_tool_selected)
        self.tool_selector.pack(fill='both', expand=True, padx=10, pady=10)

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
        # Title
        title_label = ctk.CTkLabel(self.editor_frame, text="Editor", font=ctk.CTkFont(size=16, weight="bold"))
        title_label.pack(pady=(10, 5))
        
        # Editor canvas container (using regular tkinter canvas inside CTkFrame)
        editor_container = ctk.CTkFrame(self.editor_frame, corner_radius=6)
        editor_container.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        
        # Create canvas with scrollbars (tkinter canvas for drawing compatibility)
        canvas_frame = tk.Frame(editor_container, bg=editor_container.cget("fg_color")[1])
        canvas_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.editor_canvas = tk.Canvas(canvas_frame, bg="white", 
                                      scrollregion=(0, 0, 3000, 2000),
                                      highlightthickness=1,
                                      highlightbackground="gray")
        
        # Scrollbars
        h_scroll = tk.Scrollbar(canvas_frame, orient="horizontal", 
                               command=self.editor_canvas.xview)
        v_scroll = tk.Scrollbar(canvas_frame, orient="vertical", 
                               command=self.editor_canvas.yview)
        
        self.editor_canvas.configure(xscrollcommand=h_scroll.set, 
                                    yscrollcommand=v_scroll.set)
        
        # Grid layout
        self.editor_canvas.grid(row=0, column=0, sticky="nsew")
        h_scroll.grid(row=1, column=0, sticky="ew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Store reference for external access
        self.editor_area = self.editor_canvas
        
    def create_print_preview(self):
        """Create the print preview area."""
        # Title
        title_label = ctk.CTkLabel(self.preview_frame, text="Print Preview", font=ctk.CTkFont(size=16, weight="bold"))
        title_label.pack(pady=(10, 5))
        
        # Preview canvas container
        preview_container = ctk.CTkFrame(self.preview_frame, corner_radius=6)
        preview_container.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        
        # Create preview canvas container (tkinter frame for PdfCanvas compatibility)
        canvas_frame = tk.Frame(preview_container, bg=preview_container.cget("fg_color")[1])
        canvas_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create preview canvas with scrollbars
        self.preview_canvas = PdfCanvas(canvas_frame, page_width=595, page_height=842) # a4 size in points
        
        # Scrollbars for preview
        h_scroll_prev = tk.Scrollbar(canvas_frame, orient="horizontal", 
                                    command=self.preview_canvas.xview)
        v_scroll_prev = tk.Scrollbar(canvas_frame, orient="vertical", 
                                    command=self.preview_canvas.yview)
        
        self.preview_canvas.configure(xscrollcommand=h_scroll_prev.set, 
                                     yscrollcommand=v_scroll_prev.set)
        
        # Grid layout
        self.preview_canvas.grid(row=0, column=0, sticky="nsew")
        h_scroll_prev.grid(row=1, column=0, sticky="ew")
        v_scroll_prev.grid(row=0, column=1, sticky="ns")
        
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
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

# Demo function with test content
def demo_customtk_gui():
    """Demo the CustomTkinter GUI with resizable panels and test content."""
    app = PianoTabCustomGUI()
    
    # Add some test content to the editor
    editor = app.get_editor_canvas()
    editor.create_text(50, 50, text="✏️ Editor Area - Draw music notation here", anchor="nw", font=("Arial", 14))
    editor.create_rectangle(50, 80, 300, 200, outline="blue", width=2)
    editor.create_text(175, 140, text="Resizable Canvas", font=("Arial", 12))
    editor.create_oval(350, 80, 500, 200, outline="green", width=2)
    editor.create_text(425, 140, text="Test Drawing", font=("Arial", 12))
    
    # Add some test content to the preview
    preview = app.get_preview_canvas()
    if hasattr(preview, 'new_page'):
        preview.disable_pdf_mode()  # For fast preview
        preview.add_text(100, 100, "📄 Print Preview Area", size=16, anchor='nw')
        preview.add_rectangle(100, 130, 200, 100, color="#0000FF", fill=False)
        preview.add_text(150, 180, "PDF Preview", size=12, anchor='center')
    
    print("🎨 CustomTkinter GUI with Resizable Panels Demo!")
    print("📌 Features:")
    print("   ✅ Modern dark theme with CustomTkinter")
    print("   ✅ RESIZABLE PANELS using tkinter PanedWindow")
    print("   ✅ Custom menu bar with dropdown options") 
    print("   ✅ Scrollable tool selector with visual feedback")
    print("   ✅ Professional rounded corners and styling")
    print("   🎯 Drag the panel borders to resize!")
    
    app.run()

# For standalone testing
if __name__ == "__main__":
    demo_customtk_gui()