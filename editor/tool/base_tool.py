"""
Base class for all editor tools in pianoTAB.

Each tool handles mouse events and performs actions on the score.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Tuple
from abc import ABC, abstractmethod

from gui.colors import ACCENT_COLOR_HEX

if TYPE_CHECKING:
    from editor.editor import Editor
    from file.SCORE import SCORE

# Import engraver for automatic rendering on score changes
from engraver import get_engraver_instance


class BaseTool(ABC):
    """Abstract base class for all editor tools."""
    
    def __init__(self, editor: Editor):
        """
        Initialize the tool.
        
        Args:
            editor: The Editor instance that owns this tool
        """
        self.editor = editor
        # Don't cache score - always access via editor.score to get current value
        self.canvas = editor.canvas
        
        # Track mouse state for drag detection
        self._mouse_down_pos: Optional[Tuple[float, float]] = None
        self._is_dragging = False
        self._drag_threshold = 3  # pixels before considering it a drag
        
        # Cursor state (shared by all tools - horizontal time line)
        self._cursor_time: Optional[float] = None
    
    @property
    def score(self) -> SCORE:
        """Get the current score from the editor."""
        return self.editor.score
    
    # === Event Handlers (called by Editor) ===
    
    def on_left_click(self, x: float, y: float) -> bool:
        """
        Called when the left mouse button is released without having dragged.

        Args:
            x, y: Mouse position in canvas coordinates

        Returns:
            True if event was handled, False otherwise
        """
        return False
    
    def on_right_click(self, x: float, y: float) -> bool:
        """
        Called when the right mouse button is clicked (without drag).
        Default behavior: remove/delete element at position.

        Args:
            x, y: Mouse position in canvas coordinates

        Returns:
            True if an element was found and handled/deleted, False otherwise.
            Returning False allows the editor to clear selection on empty-space clicks.
        """
        return False
    
    def on_left_unpress(self, x: float, y: float) -> bool:
        """
        Called when the left mouse button is released without having dragged.

        Args:
            x, y: Mouse position in canvas coordinates

        Returns:
            True if event was handled, False otherwise
        """
        return False
    
    def on_right_unpress(self, x: float, y: float) -> bool:
        """
        Called when the right mouse button is released without having dragged.

        Args:
            x, y: Mouse position in canvas coordinates

        Returns:
            True if event was handled, False otherwise
        """
        return False
    
    def on_left_press(self, x: float, y: float) -> bool:
        """
        Called when the left mouse button is pressed.

        Args:
            x, y: Mouse position in canvas coordinates

        Returns:
            True if event was handled, False otherwise
        """
        self._mouse_down_pos = (x, y)
        self._is_dragging = False
        return False
    
    def on_right_release(self, x: float, y: float) -> bool:
        """
        Called when the right mouse button is released.

        Args:
            x, y: Mouse position in canvas coordinates

        Returns:
            True if event was handled, False otherwise
        """
        was_dragging = self._is_dragging
        self._mouse_down_pos = None
        self._is_dragging = False

        # If there was no drag, trigger unpress event
        result = False
        if not was_dragging:
            result = self.on_right_unpress(x, y)

        # Always call post-release hook (for drawing order updates, etc.)
        self.on_any_mouse_release(x, y, button='right', was_dragging=was_dragging)

        return result

    def on_left_release(self, x: float, y: float) -> bool:
        """
        Called when the left mouse button is released.

        Args:
            x, y: Mouse position in canvas coordinates

        Returns:
            True if event was handled, False otherwise
        """
        was_dragging = self._is_dragging
        self._mouse_down_pos = None
        self._is_dragging = False

        # If it was a drag, handle drag end first
        result = False
        if was_dragging:
            result = self.on_drag_end(x, y)
        else:
            # No drag, trigger unpress event
            result = self.on_left_unpress(x, y)

        # Always call post-release hook (for drawing order updates, etc.)
        self.on_any_mouse_release(x, y, button='left', was_dragging=was_dragging)

        return result
    
    def on_drag_start(self, x: float, y: float, start_x: float, start_y: float) -> bool:
        """
        Called when a drag operation begins (mouse moved beyond threshold while button down).

        Args:
            x, y: Current mouse position
            start_x, start_y: Position where drag started

        Returns:
            True if event was handled, False otherwise
        """
        return False
    
    def on_drag(self, x: float, y: float, start_x: float, start_y: float) -> bool:
        """
        Called during drag operation (continuous mouse movement with button down).

        Args:
            x, y: Current mouse position
            start_x, start_y: Position where drag started

        Returns:
            True if event was handled, False otherwise
        """
        return False
    
    def on_drag_end(self, x: float, y: float) -> bool:
        """
        Called when drag operation ends (button released after drag).

        Args:
            x, y: Final mouse position

        Returns:
            True if event was handled, False otherwise
        """
        return False
    
    def on_any_mouse_release(self, x: float, y: float, button: str, was_dragging: bool) -> None:
        """
        Called on every mouse button release (left or right, drag or click).

        This is useful for operations that need to happen after any mouse interaction,
        such as updating drawing order, refreshing displays, etc.

        Args:
            x, y: Mouse position in canvas coordinates
            button: Which button was released ('left' or 'right')
            was_dragging: True if this was the end of a drag, False if it was a click
        """
        # Fix drawing order after finalizing note
        self.editor.canvas._redraw_all()
    
    def on_mouse_move(self, x: float, y: float) -> bool:
        """
        Called when mouse moves (no buttons pressed, or during drag detection).
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
        Called on double-click.

        Args:
            x, y: Mouse position in canvas coordinates

        Returns:
            True if event was handled, False otherwise
        """
        return False
    
    # === Helper Methods ===
    
    def _point_to_line_distance(self, px: float, py: float, 
                                x1: float, y1: float, x2: float, y2: float) -> float:
        """
        Calculate the perpendicular distance from a point to a line segment.
        
        Args:
            px, py: Point coordinates
            x1, y1: Line segment start
            x2, y2: Line segment end
            
        Returns:
            Distance from point to line segment
        """
        # Vector from line start to end
        dx = x2 - x1
        dy = y2 - y1
        
        # If line segment is actually a point, return distance to that point
        line_length_sq = dx * dx + dy * dy
        if line_length_sq < 1e-10:
            return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
        
        # Project point onto line (parameter t)
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / line_length_sq))
        
        # Find closest point on line segment
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        # Return distance to closest point
        return ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5
    
    def is_point_near_line(self, px: float, py: float,
                          x1: float, y1: float, x2: float, y2: float,
                          line_width_mm: float) -> bool:
        """
        Check if a point is within the clickable area of a thick line.
        
        Creates a rectangle around the line based on its width and checks if the point falls inside.
        
        Args:
            px, py: Point coordinates to test
            x1, y1: Line segment start
            x2, y2: Line segment end
            line_width_mm: Width of the line in mm (creates hit area of width/2 on each side)
            
        Returns:
            True if point is within the line's hit area, False otherwise
        """
        # Calculate perpendicular distance from point to line
        distance = self._point_to_line_distance(px, py, x1, y1, x2, y2)
        
        # Hit if within half the line width (plus a small tolerance for easier clicking)
        tolerance = (line_width_mm / 2.0) + 0.5  # Add 0.5mm tolerance
        return distance <= tolerance
    
    def get_element_at_position(self, x: float, y: float, element_types=None):
        """
        Find score element at the given position using canvas item hit detection.
        Ignores cursor items and returns the first real element found.
        
        Args:
            x, y: Position in canvas coordinates (mm)
            element_types: Optional list of element types to filter by 
                        (e.g., ['note', 'beam', 'slur'])
            
        Returns:
            Tuple of (element_object, element_type, stave_idx) or (None, None, None)
            
        Example:
            note, elem_type, stave = self.get_element_at_position(x, y, ['note'])
            if note:
                print(f"Found {elem_type} with id {note.id} on stave {stave}")
        """
        # Convert mm coordinates to pixel coordinates for canvas hit detection
        x_px = x * self.editor.canvas._px_per_mm
        y_px = y * self.editor.canvas._px_per_mm
        
        # Get ALL canvas items at this position (not just topmost)
        item_ids = self.editor.canvas.get_all_items_at_position(x_px, y_px)
        
        if not item_ids:
            return (None, None, None)
        
        # Iterate through all items, skipping cursor/temporary items
        for item_id in item_ids:
            # Get tags from the canvas item
            tags = self.editor.canvas.get_tags(item_id)
            
            if not tags:
                continue
            
            # Skip cursor and temporary tags
            if any(tag in ('cursor', 'cursor_line', 'edit', 'stem', 'beam_marker') for tag in tags):
                continue
            
            # Parse tags to determine element type and ID
            # Tags format: ['element_type', 'element_id']
            element_type = None
            element_id = None
            
            for tag in tags:
                # Check if it's a numeric ID
                if tag.isdigit():
                    element_id = int(tag)
                # Check if it's an element type tag
                elif tag in ('notehead', 'midinote', 'leftdot', 'beam', 'slur', 
                            'tempo', 'text', 'barline', 'gracenote'):
                    element_type = tag
            
            # If we didn't find a valid element in this item, continue to next
            if element_id is None or element_type is None:
                continue
            
            # Normalize element type
            normalized_type = self._normalize_element_type(element_type)
            
            # Filter by element types if specified
            if element_types is not None and normalized_type not in element_types:
                continue
            
            # Use SCORE.find_by_id() to get the element
            element = self.editor.score.find_by_id(element_id)
            
            if element is None:
                continue
            
            # Find which stave contains this element
            stave_idx = self._find_stave_for_element(element)
            
            # Found a valid element - return it
            return (element, normalized_type, stave_idx)
        
        # No valid element found at this position
        return (None, None, None)

    def _normalize_element_type(self, canvas_tag: str) -> str:
        """Convert canvas tag to normalized element type name."""
        tag_to_type = {
            'notehead': 'note',
            'leftdot': 'note',
            'midinote': 'note',
            'stem': 'note',
            'beam': 'beam',
            'slur': 'slur',
            'tempo': 'tempo',
            'text': 'text',
            'barline': 'barline',
            'gracenote': 'gracenote',
        }
        return tag_to_type[canvas_tag] if canvas_tag in tag_to_type else canvas_tag

    def _find_stave_for_element(self, element) -> Optional[int]:
        """Find which stave contains the given element."""
        for stave_idx, stave in enumerate(self.editor.score.stave):
            if not hasattr(stave, 'event'):
                continue
            
            # Check all event types
            for event_type in ['note', 'graceNote', 'beam', 'slur', 'tempo', 'text', 
                            'countLine', 'startRepeat', 'endRepeat', 'section']:
                if hasattr(stave.event, event_type):
                    event_list = getattr(stave.event, event_type)
                    if element in event_list:
                        return stave_idx
        
        return None
    
    def refresh_canvas(self):
        """Request a canvas redraw."""
        if hasattr(self.canvas, 'request_redraw'):
            self.canvas.request_redraw()
        elif hasattr(self.editor, 'refresh'):
            self.editor.refresh()
    
    def trigger_engrave(self):
        """
        Trigger engraving of the current score for ALL canvases.
        
        Call this method after ANY modification to the SCORE model to
        queue a layout calculation and rendering task.
        
        The engraver automatically handles:
        - Running layout calculations in a background thread
        - Discarding old render tasks when new changes arrive
        - Drawing results on the canvas on the main thread
        
        Triggers engraving for:
        - Editor canvas (main editing view)
        - Print preview canvas (if available via editor.gui)
        """
        try:
            # Safety check - don't engrave if score is None
            if self.score is None:
                print("BaseTool: Cannot trigger engrave - score is None")
                return
                
            engraver = get_engraver_instance()
            
            # ONLY trigger for print preview canvas (not the editor canvas!)
            # The editor has its own drawing system (piano roll)
            if hasattr(self.editor, 'gui') and self.editor.gui:
                preview_canvas = self.editor.gui.get_preview_widget()
                if preview_canvas:
                    engraver.do_engrave(
                        score=self.score,
                        canvas=preview_canvas,
                        callback=self._on_preview_engrave_complete
                    )
        except Exception as e:
            print(f"BaseTool: Failed to trigger engrave: {e}")
    
    def _on_engrave_complete(self, success: bool, error: Optional[str]):
        """
        Callback invoked when editor canvas engraving completes.
        
        Args:
            success: True if engraving succeeded
            error: Error message if success is False, None otherwise
        """
        if success:
            print("BaseTool: Editor engraving completed successfully")
        else:
            print(f"BaseTool: Editor engraving failed: {error}")
    
    def _on_preview_engrave_complete(self, success: bool, error: Optional[str]):
        """
        Callback invoked when print preview canvas engraving completes.
        
        Args:
            success: True if engraving succeeded
            error: Error message if success is False, None otherwise
        """
        if success:
            print("BaseTool: Preview engraving completed successfully")
        else:
            print(f"BaseTool: Preview engraving failed: {error}")
    
    # === Lifecycle Methods ===
    
    def on_activate(self):
        """Called when this tool becomes active."""
        pass
    
    def get_contextual_buttons(self) -> dict:
        """Return contextual toolbar button configuration for this tool.
        
        Returns:
            Dictionary mapping icon names to (callback, tooltip) tuples.
            Example: {'noteLeft': (self._move_left, 'Move note to left hand')}
        """
        return {}
    
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
            self._draw_dash_cursor()
        except Exception as e:
            print(f'CURSOR: update failed: {e}')
    
    def _clear_time_cursor(self):
        """Remove the time cursor from the canvas."""
        self._cursor_time = None
        # Delete all cursor lines by tag
        self.canvas.delete_by_tag('cursor_line')
    
    def _draw_dash_cursor(self):
        """Draw or update the horizontal dashed cursor line at the current time.
        
        Draws two separate lines:
        1. From left edge to left side of piano staves
        2. From right side of piano staves to right edge
        This creates a gap where the piano keys are displayed.
        """
        # Remove existing cursor lines by tag
        self.canvas.delete_by_tag('cursor_line')

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
        
        # Draw left line (if there's space)
        if left_x2 > left_x1:
            self.canvas.add_line(
                x1_mm=left_x1,
                y1_mm=y_mm,
                x2_mm=left_x2,
                y2_mm=y_mm,
                color=ACCENT_COLOR_HEX,
                width_mm=0.25,
                dash=True,
                dash_pattern_mm=(2.0, 2.0),
                tags=['cursor_line']
            )
        
        # Draw right line (if there's space)
        if right_x2 > right_x1:
            self.canvas.add_line(
                x1_mm=right_x1,
                y1_mm=y_mm,
                x2_mm=right_x2,
                y2_mm=y_mm,
                color=ACCENT_COLOR_HEX,
                width_mm=0.25,
                dash=True,
                dash_pattern_mm=(2.0, 2.0),
                tags=['cursor_line']
            )

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
    
    def on_key_press(self, key: str, x: float, y: float) -> bool:
        """Called when a key is pressed.

        Args:
            key: The key that was pressed
            x: Current mouse x position in mm
            y: Current mouse y position in mm

        Returns:
            True if the tool handled the key press, False otherwise
        """
        return False
    
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
