"""
Base class for all editor tools in pianoTAB.

Each tool handles mouse events and performs actions on the score.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Tuple
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from editor.editor import Editor
    from file.SCORE import SCORE


class BaseTool(ABC):
    """Abstract base class for all editor tools."""
    
    def __init__(self, editor: Editor):
        """
        Initialize the tool.
        
        Args:
            editor: The Editor instance that owns this tool
        """
        self.editor = editor
        self.score: SCORE = editor.score
        self.canvas = editor.canvas
        
        # Track mouse state
        self._mouse_down_pos: Optional[Tuple[float, float]] = None
        self._is_dragging = False
        self._drag_threshold = 5  # pixels before considering it a drag
    
    # === Event Handlers (called by Editor) ===
    
    def on_left_click(self, x: float, y: float) -> bool:
        """
        Handle left mouse button click (no drag).
        
        Args:
            x, y: Mouse position in canvas coordinates
            
        Returns:
            True if event was handled, False otherwise
        """
        return False
    
    def on_right_click(self, x: float, y: float) -> bool:
        """
        Handle right mouse button click (no drag).
        Default behavior: remove/delete element at position.
        
        Args:
            x, y: Mouse position in canvas coordinates
            
        Returns:
            True if event was handled, False otherwise
        """
        return False
    
    def on_left_press(self, x: float, y: float) -> bool:
        """
        Handle left mouse button press (before drag).
        
        Args:
            x, y: Mouse position in canvas coordinates
            
        Returns:
            True if event was handled, False otherwise
        """
        self._mouse_down_pos = (x, y)
        self._is_dragging = False
        return False
    
    def on_left_release(self, x: float, y: float) -> bool:
        """
        Handle left mouse button release.
        
        Args:
            x, y: Mouse position in canvas coordinates
            
        Returns:
            True if event was handled, False otherwise
        """
        was_dragging = self._is_dragging
        self._mouse_down_pos = None
        self._is_dragging = False
        
        # If it was a drag, handle drag end
        if was_dragging:
            return self.on_drag_end(x, y)
        return False
    
    def on_drag_start(self, x: float, y: float, start_x: float, start_y: float) -> bool:
        """
        Handle start of drag operation.
        
        Args:
            x, y: Current mouse position
            start_x, start_y: Position where drag started
            
        Returns:
            True if event was handled, False otherwise
        """
        return False
    
    def on_drag(self, x: float, y: float, start_x: float, start_y: float) -> bool:
        """
        Handle mouse drag (continuous movement with button down).
        
        Args:
            x, y: Current mouse position
            start_x, start_y: Position where drag started
            
        Returns:
            True if event was handled, False otherwise
        """
        return False
    
    def on_drag_end(self, x: float, y: float) -> bool:
        """
        Handle end of drag operation.
        
        Args:
            x, y: Final mouse position
            
        Returns:
            True if event was handled, False otherwise
        """
        return False
    
    def on_mouse_move(self, x: float, y: float) -> bool:
        """
        Handle mouse movement (no buttons pressed).
        Useful for hover effects, cursor changes, etc.
        
        Args:
            x, y: Mouse position in canvas coordinates
            
        Returns:
            True if event was handled, False otherwise
        """
        # Check if we should start a drag
        if self._mouse_down_pos is not None:
            start_x, start_y = self._mouse_down_pos
            distance = ((x - start_x)**2 + (y - start_y)**2) ** 0.5
            
            if distance > self._drag_threshold and not self._is_dragging:
                self._is_dragging = True
                return self.on_drag_start(x, y, start_x, start_y)
            elif self._is_dragging:
                return self.on_drag(x, y, start_x, start_y)
        
        return False
    
    def on_double_click(self, x: float, y: float) -> bool:
        """
        Handle double-click event.
        
        Args:
            x, y: Mouse position in canvas coordinates
            
        Returns:
            True if event was handled, False otherwise
        """
        return False
    
    # === Helper Methods ===
    
    def get_element_at_position(self, x: float, y: float, element_types=None):
        """
        Find score element at the given position.
        
        Args:
            x, y: Position in canvas coordinates
            element_types: Optional list of element types to search for
            
        Returns:
            Element at position or None
        """
        # TODO: Implement hit detection
        # This would query the score for elements near (x, y)
        pass
    
    def refresh_canvas(self):
        """Request a canvas redraw."""
        if hasattr(self.canvas, 'request_redraw'):
            self.canvas.request_redraw()
        elif hasattr(self.editor, 'refresh'):
            self.editor.refresh()
    
    # === Lifecycle Methods ===
    
    def on_activate(self):
        """Called when this tool becomes active."""
        pass
    
    def on_deactivate(self):
        """Called when switching away from this tool."""
        # Clean up any temporary visual feedback
        self._mouse_down_pos = None
        self._is_dragging = False
    
    # === Abstract Methods (optional to override) ===
    
    @property
    @abstractmethod
    def name(self) -> str:
        """The tool's display name (must match ToolSelector)."""
        pass
    
    @property
    def cursor(self) -> str:
        """
        Cursor type for this tool.
        Returns: 'arrow', 'crosshair', 'hand', 'ibeam', etc.
        """
        return 'arrow'
