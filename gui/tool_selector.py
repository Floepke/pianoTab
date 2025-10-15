#!/usr/bin/env python3
"""
Tool Selector Widget for PianoTab GUI.

CustomTkinter-based tool selection widget with modern dark styling.
"""

import customtkinter as ctk
from logger import log


class ToolSelector(ctk.CTkFrame):
    """
    A CustomTkinter tool selector widget.
    
    Features:
    - CTkFrame with 5px padding
    - Label showing currently selected tool
    - CTkScrollableFrame with tool selection
    - Predefined tool list for piano notation
    """
    
    def __init__(self, parent, callback=None):
        """
        Initialize the ToolSelector widget.
        
        Args:
            parent: Parent widget (CustomTkinter container)
            callback: Optional callback function(tool_name)
        """
        super().__init__(parent)
        
        self.callback = callback
        self.current_tool = "Note"
        
        # Configure frame with 5px padding
        self.configure(corner_radius=6)
        
        # Define the 8 specific tools
        self.tools = [
            "Note",
            "Grace-note", 
            "Beam",
            "Line-break",
            "Count-line",
            "Text",
            "Slur",
            "Tempo"
        ]
        
        self.create_widgets()
        
    def create_widgets(self):
        """Create the widget components."""
        # Add internal padding
        self.grid_columnconfigure(0, weight=1)
        
        # Selected tool label
        self.tool_label = ctk.CTkLabel(
            self,
            text=f"Tool: {self.current_tool}",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.tool_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # Scrollable frame for tools
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self,
            height=200,
            corner_radius=6
        )
        self.scrollable_frame.grid(row=1, column=0, padx=5, pady=(0, 5), sticky="ew")
        
        # Create tool buttons
        self.tool_buttons = {}
        for i, tool in enumerate(self.tools):
            button = ctk.CTkButton(
                self.scrollable_frame,
                text=tool,
                height=32,
                command=lambda t=tool: self.select_tool(t),
                fg_color="transparent",
                hover_color=("gray75", "gray25"),
                anchor="w"
            )
            button.grid(row=i, column=0, padx=5, pady=2, sticky="ew")
            self.tool_buttons[tool] = button
            
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        
        # Highlight initial selection
        self.update_selection()
        
    def select_tool(self, tool_name):
        """Handle tool selection."""
        self.current_tool = tool_name
        self.tool_label.configure(text=f"Tool: {tool_name}")
        self.update_selection()
        
        if self.callback:
            self.callback(tool_name)
            
        log(f"🔧 Tool selected: {tool_name}")
        
    def update_selection(self):
        """Update visual selection state."""
        for tool, button in self.tool_buttons.items():
            if tool == self.current_tool:
                button.configure(
                    fg_color=("gray75", "gray25"),
                    text_color=("gray10", "gray90")
                )
            else:
                button.configure(
                    fg_color="transparent",
                    text_color=("gray10", "#DCE4EE")
                )
                
    def get_tool(self):
        """Get the currently selected tool."""
        return self.current_tool
        
    def set_tool(self, tool_name):
        """Set the selected tool programmatically."""
        if tool_name in self.tools:
            self.select_tool(tool_name)
        else:
            log(f"Warning: Tool '{tool_name}' not found")
