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
        
        # Track mouse state for drag detection
        self._mouse_down_pos: Optional[Tuple[float, float]] = None
        self._is_dragging = False
        self._drag_threshold = 3  # pixels before considering it a drag
        
        # Cursor state (shared by all tools - horizontal time line)
        self._cursor_time: Optional[float] = None
    
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
        # Update and draw the horizontal time cursor
        self._update_time_cursor(y)
        
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
        # Clear the time cursor
        self._clear_time_cursor()

    # === Time Cursor Methods (shared by all tools) ===
    
    def _update_time_cursor(self, y_mm: float):
        """
        Update and draw the horizontal time cursor at the mouse Y position.
        Snaps to grid and clamps to score bounds.
        
        Args:
            y_mm: Mouse Y position in millimeters
        """
        import math
        try:
            # Convert Y to ticks with grid snapping
            raw_ticks = self.editor.y_to_time(float(y_mm))
            step = max(1e-6, self.editor.get_grid_step_ticks())
            snapped = math.floor(raw_ticks / step) * step
            
            # Clamp within score bounds
            snapped = max(0.0, snapped)
            total = float(self.editor.get_score_length_in_ticks())
            snapped = min(total, snapped)
            
            # Update cursor position
            self._cursor_time = snapped
            self._draw_cursor()
        except Exception as e:
            print(f'CURSOR: update failed: {e}')
    
    def _clear_time_cursor(self):
        """Remove the time cursor from the canvas."""
        self._cursor_time = None
        # Delete all cursor lines by tag
        self.canvas.delete_by_tag('cursorLine')
    
    def _draw_cursor(self):
        """Draw or update the horizontal dashed cursor line at the current time.
        
        Draws two separate lines:
        1. From left edge to left side of piano staves
        2. From right side of piano staves to right edge
        This creates a gap where the piano keys are displayed.
        """
        # Remove existing cursor lines by tag
        self.canvas.delete_by_tag('cursorLine')

        if self._cursor_time is None:
            return
        
        # Compute Y in mm from cursor time
        y_mm = self.editor.time_to_y(self._cursor_time)
        
        # Get stave boundaries from editor
        stave_left = float(getattr(self.editor, 'stave_left', 0.0))
        stave_right = float(getattr(self.editor, 'stave_right', 0.0))
        editor_width = float(self.editor.editor_width)
        
        # Left line: from 0 to stave_left
        left_x1 = 0.0
        left_x2 = stave_left
        
        # Right line: from stave_right to editor_width
        right_x1 = stave_right
        right_x2 = editor_width
        
        if left_x2 <= left_x1 and right_x2 <= right_x1:
            return
        
        try:
            # Draw left line (if there's space)
            if left_x2 > left_x1:
                self.canvas.add_line(
                    x1_mm=left_x1,
                    y1_mm=y_mm,
                    x2_mm=left_x2,
                    y2_mm=y_mm,
                    color='#000000',
                    width_mm=0.25,
                    dash=True,
                    dash_pattern_mm=(2.0, 2.0),
                    tags=['cursorLine']
                )
            
            # Draw right line (if there's space)
            if right_x2 > right_x1:
                self.canvas.add_line(
                    x1_mm=right_x1,
                    y1_mm=y_mm,
                    x2_mm=right_x2,
                    y2_mm=y_mm,
                    color='#000000',
                    width_mm=0.25,
                    dash=True,
                    dash_pattern_mm=(2.0, 2.0),
                    tags=['cursorLine']
                )
        except Exception as e:
            print(f'CURSOR: draw failed: {e}')

    # === Helper Methods for Musical Coordinate Conversion ===

    def x_to_pitch(self, x_mm: float) -> int:
        """
        Convert X coordinate (mm) to piano pitch number (1-88).
        
        Args:
            x_mm: X position in millimeters
            
        Returns:
            Pitch number from 1 (A0) to 88 (C8), or None if out of range
        """
        pitch = self.editor.x_to_pitch(x_mm)
        
        # Clamp to valid piano range (1-88)
        if pitch < 1:
            return 1
        elif pitch > 88:
            return 88
        
        return pitch

    def get_time_from_y(self, y_mm: float) -> float:
        """
        Convert Y coordinate (mm) to time in ticks.
        
        Args:
            y_mm: Y position in millimeters
            
        Returns:
            Time in ticks (using score's time unit)
        """
        ticks = self.editor.y_to_time(y_mm)
        
        # Clamp to valid range (non-negative)
        if ticks < 0:
            return 0.0
        
        return ticks

    def get_snapped_time_from_y(self, y_mm: float) -> float:
        """
        Convert Y coordinate (mm) to time in ticks, snapped to grid.
        Snaps down (floor) to the grid line you just passed, not the nearest one.
        
        Args:
            y_mm: Y position in millimeters
            
        Returns:
            Time in ticks, snapped to the current grid step (floor)
        """
        import math
        ticks = self.get_time_from_y(y_mm)
        grid_step = self.editor.get_grid_step_ticks()
        
        if grid_step > 0:
            # Snap down to the grid line (floor) - captures as soon as you enter the grid cell
            snapped_ticks = math.floor(ticks / grid_step) * grid_step
            return snapped_ticks
        
        return ticks

    def get_pitch_and_time(self, x_mm: float, y_mm: float, snap_to_grid: bool = True):
        """
        Convert mouse position to musical coordinates.
        
        Args:
            x_mm: X position in millimeters
            y_mm: Y position in millimeters
            snap_to_grid: Whether to snap time to grid (default: True)
            
        Returns:
            Tuple of (pitch: int, time_ticks: float)
        """
        pitch = self.x_to_pitch(x_mm)
        
        if snap_to_grid:
            time_ticks = self.get_snapped_time_from_y(y_mm)
        else:
            time_ticks = self.get_time_from_y(y_mm)
        
        return (pitch, time_ticks)

    def get_x_from_pitch(self, pitch: int) -> float:
        """
        Convert pitch number to X coordinate (mm).
        
        Args:
            pitch: Piano pitch number (1-88)
            
        Returns:
            X position in millimeters
        """
        return self.editor.pitch_to_x(pitch)

    def get_y_from_time(self, time_ticks: float) -> float:
        """
        Convert time in ticks to Y coordinate (mm).
        
        Args:
            time_ticks: Time in ticks
            
        Returns:
            Y position in millimeters
        """
        return self.editor.time_to_y(time_ticks)
    
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
