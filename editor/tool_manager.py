"""
Tool Manager - handles tool registration and dispatching events to active tool.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Type, Optional
import importlib

if TYPE_CHECKING:
    from editor.editor import Editor
    from editor.tool.base_tool import BaseTool


class ToolManager:
    """Manages editor tools and dispatches events to the active tool."""
    
    def __init__(self, editor: Editor):
        self.editor = editor
        self._tools: Dict[str, BaseTool] = {}
        self._active_tool: Optional[BaseTool] = None
        
        # Auto-register all tools
        self._register_tools()
    
    def _register_tools(self):
        """Automatically import and register all tool classes."""
        # Map tool module names to their class names
        tool_definitions = {
            'note_tool': 'NoteTool',
            'gracenote_tool': 'GraceNoteTool',
            'beam_tool': 'BeamTool',
            'linebreak_tool': 'LineBreakTool',
            'countline_tool': 'CountLineTool',
            'text_tool': 'TextTool',
            'slur_tool': 'SlurTool',
            'tempo_tool': 'TempoTool',
        }
        
        for tool_module_name, class_name in tool_definitions.items():
            try:
                # Import the module
                module = importlib.import_module(f'editor.tool.{tool_module_name}')
                
                # Get the tool class
                tool_class: Type[BaseTool] = getattr(module, class_name)
                
                # Instantiate and register
                tool_instance = tool_class(self.editor)
                self._tools[tool_instance.name] = tool_instance
                
            except (ImportError, AttributeError) as e:
                print(f"Warning: Could not load tool '{tool_module_name}': {e}")
    
    def set_active_tool(self, tool_name: str) -> bool:
        """
        Activate a tool by name.
        
        Args:
            tool_name: Name of the tool (must match tool.name property)
            
        Returns:
            True if tool was activated, False if not found
        """
        if tool_name not in self._tools:
            print(f"Warning: Tool '{tool_name}' not found")
            return False
        
        # Deactivate current tool
        if self._active_tool:
            self._active_tool.on_deactivate()
        
        # Activate new tool
        self._active_tool = self._tools[tool_name]
        self._active_tool.on_activate()
        
        # Update cursor if needed
        from kivy.core.window import Window
        Window.set_system_cursor(self._active_tool.cursor)
        
        return True
    
    def get_active_tool(self) -> Optional[BaseTool]:
        """Get the currently active tool."""
        return self._active_tool
    
    # === Event Dispatching ===
    
    def dispatch_left_click(self, x: float, y: float) -> bool:
        """Dispatch left click to active tool."""
        if self._active_tool:
            return self._active_tool.on_left_click(x, y)
        return False
    
    def dispatch_right_click(self, x: float, y: float) -> bool:
        """Dispatch right click to active tool."""
        if self._active_tool:
            return self._active_tool.on_right_click(x, y)
        return False
    
    def dispatch_left_press(self, x: float, y: float) -> bool:
        """Dispatch left button press to active tool."""
        if self._active_tool:
            return self._active_tool.on_left_press(x, y)
        return False
    
    def dispatch_left_release(self, x: float, y: float) -> bool:
        """Dispatch left button release to active tool."""
        if self._active_tool:
            return self._active_tool.on_left_release(x, y)
        return False
    
    def dispatch_mouse_move(self, x: float, y: float) -> bool:
        """Dispatch mouse move to active tool."""
        if self._active_tool:
            return self._active_tool.on_mouse_move(x, y)
        return False
    
    def dispatch_double_click(self, x: float, y: float) -> bool:
        """Dispatch double click to active tool."""
        if self._active_tool:
            return self._active_tool.on_double_click(x, y)
        return False
