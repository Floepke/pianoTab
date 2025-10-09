#!/usr/bin/env python3
"""
Tool Selector Widget for PianoTab GUI.

Provides a reusable tool selection widget with LabelFrame container,
listbox for tool display, and callback support for tool changes.
"""

import tkinter as tk
from tkinter import ttk


class ToolSelector:
    """
    A reusable tool selector widget with LabelFrame container.
    
    This widget provides:
    - LabelFrame container with title
    - Listbox with tools (name + symbol)
    - Selection callback support
    - Programmatic tool selection
    """
    
    def __init__(self, parent, tools, callback=None, title="Tool Selection"):
        """
        Initialize the ToolSelector widget.
        
        Args:
            parent: Parent widget (tkinter container)
            tools: List of tuples [(tool_name, symbol), ...]
            callback: Optional callback function(tool_name)
            title: Title for the LabelFrame
        """
        self.parent = parent
        self.tools = tools
        self.callback = callback
        self.current_tool_index = 0
        
        # Create the main container
        self.container = None
        self.tools_label = None
        self.tool_listbox = None
        
        # Build the widget
        self.create_widget(title)
        
        # Initialize selection
        if self.tools:
            self.set_tool(0)
    
    def create_widget(self, title):
        """Create the widget components."""
        # Main container (LabelFrame)
        self.container = ttk.LabelFrame(self.parent, text=title, padding="8")
        
        # Tool selection label
        self.tools_label = tk.Label(self.container, text="Selected Tool: None",
                                   font=("Arial", 10, "bold"))
        self.tools_label.pack(anchor="w", pady=(0, 8))
        
        # Tools listbox
        self.tool_listbox = tk.Listbox(self.container, height=8, selectmode="single",
                                      font=("Arial", 9))
        self.tool_listbox.pack(fill="both", expand=True, pady=(0, 5))
        
        # Bind selection event
        self.tool_listbox.bind('<<ListboxSelect>>', self._on_tool_select)
        
        # Populate with tools
        self.populate_tools()
    
    def pack(self, **kwargs):
        """Pack the container widget."""
        self.container.pack(**kwargs)
        
    def grid(self, **kwargs):
        """Grid the container widget."""
        self.container.grid(**kwargs)
        
    def place(self, **kwargs):
        """Place the container widget."""
        self.container.place(**kwargs)
    
    def populate_tools(self):
        """Populate the listbox with available tools."""
        self.tool_listbox.delete(0, tk.END)
        
        for tool_name, symbol in self.tools:
            display_text = f"{symbol} {tool_name}"
            self.tool_listbox.insert(tk.END, display_text)
    
    def _on_tool_select(self, event):
        """Handle tool selection from listbox."""
        selection = self.tool_listbox.curselection()
        if selection:
            tool_index = selection[0]
            self.current_tool_index = tool_index
            self._update_label()
            
            # Call callback if provided
            if self.callback:
                tool_name, symbol = self.tools[tool_index]
                self.callback(tool_name)
                
            print(f"🔧 Tool selected: {self.tools[tool_index][0]} (index {tool_index})")
    
    def _update_label(self):
        """Update the tools label with current selection."""
        if 0 <= self.current_tool_index < len(self.tools):
            tool_name, symbol = self.tools[self.current_tool_index]
            self.tools_label.config(text=f"Selected Tool: {tool_name}")
    
    def get_tool(self):
        """
        Get the currently selected tool.
        
        Returns:
            tuple: (tool_index, tool_name, symbol)
        """
        if 0 <= self.current_tool_index < len(self.tools):
            tool_name, symbol = self.tools[self.current_tool_index]
            return (self.current_tool_index, tool_name, symbol)
        return (0, self.tools[0][0], self.tools[0][1])
    
    def set_tool(self, tool_identifier):
        """
        Set the selected tool programmatically.
        
        Args:
            tool_identifier (int or str): Index of tool to select, or tool name
        """
        tool_index = tool_identifier
        
        # If it's a string, find the index
        if isinstance(tool_identifier, str):
            tool_index = None
            for i, (name, symbol) in enumerate(self.tools):
                if name == tool_identifier:
                    tool_index = i
                    break
            
            if tool_index is None:
                print(f"Warning: Tool '{tool_identifier}' not found")
                return
        
        if 0 <= tool_index < len(self.tools):
            self.current_tool_index = tool_index
            
            # Update listbox selection
            self.tool_listbox.selection_clear(0, tk.END)
            self.tool_listbox.selection_set(tool_index)
            self.tool_listbox.see(tool_index)  # Ensure visible
            
            # Update label
            self._update_label()
            
            print(f"🎯 Tool set programmatically: {self.tools[tool_index][0]} (index {tool_index})")


# Demo/Test function
def demo_tool_selector():
    """Demonstrate the ToolSelector widget."""
    
    def on_tool_selected(tool_name):
        print(f"Callback: Tool changed to {tool_name}")
    
    # Create test window
    root = tk.Tk()
    root.title("ToolSelector Demo")
    root.geometry("400x600")
    
    # Test tools
    test_tools = [
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
    
    # Create ToolSelector
    tool_selector = ToolSelector(root, test_tools, on_tool_selected, "Music Tools")
    tool_selector.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Test buttons
    button_frame = tk.Frame(root)
    button_frame.pack(fill="x", padx=10, pady=5)
    
    def test_get():
        current = tool_selector.get_tool()
        print(f"Current tool: {current}")
    
    def test_set_note():
        tool_selector.set_tool("Note")
    
    def test_set_index():
        tool_selector.set_tool(3)  # Should be "Beam"
    
    tk.Button(button_frame, text="Get Current Tool", command=test_get).pack(side="left", padx=2)
    tk.Button(button_frame, text="Set to Note", command=test_set_note).pack(side="left", padx=2)
    tk.Button(button_frame, text="Set to Index 3", command=test_set_index).pack(side="left", padx=2)
    
    root.mainloop()


if __name__ == "__main__":
    # Run demo if executed directly
    demo_tool_selector()