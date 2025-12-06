"""
Base class for all editor tools in pianoTAB.

Each tool handles mouse events and performs actions on the score.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Tuple
from abc import ABC, abstractmethod

from gui.colors import ACCENT_HEX, DARK_HEX
from utils.CONSTANTS import BLACK_KEYS

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
        # Keep time cursor updating during drag
        try:
            self._update_time_cursor(y)
        except Exception:
            pass

        # Update keyboard cursor overlay to match note cursor position
        try:
            gui = getattr(self.editor, 'gui', None)
            overlay = getattr(gui, 'keyboard_overlay', None) if gui else None
            cv = getattr(self.editor, 'canvas', None)
            if overlay and cv:
                # Prefer edit_note pitch if available (note stays at chosen pitch during edit)
                pitch = None
                if hasattr(self, 'edit_note') and getattr(self, 'edit_note', None) is not None:
                    try:
                        pitch = int(getattr(self, 'edit_note').pitch)
                    except Exception:
                        pitch = None
                if pitch is None and hasattr(self.editor, 'x_to_pitch'):
                    try:
                        pitch = int(self.editor.x_to_pitch(x))
                    except Exception:
                        pitch = None
                if pitch is not None:
                    # Store for consistency with other paths
                    self.editor.cursor_pitch = pitch
                    x_mm = self.editor.pitch_to_x(pitch)
                    px_per_mm = float(getattr(cv, '_px_per_mm', 0.0) or 0.0)
                    semitone_w_mm = float(getattr(self.editor, 'semitone_width', 3.0))
                    key_w_px = (semitone_w_mm * px_per_mm if px_per_mm > 0 else 12.0)
                    diameter_px = key_w_px
                    key_h_px = int(80 * (2.0 / 3.0))
                    bottom_margin_px = 80 - key_h_px
                    x_px, _ = cv._mm_to_px_point(x_mm, 0.0)
                    try:
                        from utils.CONSTANTS import BLACK_KEYS
                        is_black = int(pitch) in BLACK_KEYS
                    except Exception:
                        is_black = False
                    base_y = gui.editor.keyboard_panel.y if hasattr(gui, 'editor') else 0
                    y_px = base_y + (bottom_margin_px if is_black else 0)
                    x_circle = float(x_px) - (diameter_px / 2.0)
                    overlay.set_cursor_circle(x_circle, y_px + 5, diameter_px)
        except Exception:
            pass

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
        # Restore overlay if present
        try:
            if hasattr(self.editor, 'keyboard_overlay') and self.editor.keyboard_overlay:
                self.editor.keyboard_overlay.redraw()
        except Exception:
            pass
    
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

        # Forward to keyboard panel for highlight update
        try:
            gui = getattr(self.editor, 'gui', None)
            kp = getattr(gui, 'keyboard_panel', None) if gui else None
            # Update time cursor on move
            try:
                self._update_time_cursor(y)
            except Exception:
                pass

            # Trigger keyboard cursor overlay update (drawn above keyboard panel)
            try:
                gui = getattr(self.editor, 'gui', None)
                # Update editor's cursor_pitch from current x for keyboard highlight
                if hasattr(self.editor, 'x_to_pitch'):
                    try:
                        self.editor.cursor_pitch = int(self.editor.x_to_pitch(x))
                    except Exception:
                        pass
                # If overlay exists, compute position and update circle
                overlay = getattr(gui, 'keyboard_overlay', None) if gui else None
                cv = getattr(self.editor, 'canvas', None)
                if overlay and cv:
                    try:
                        pitch = getattr(self.editor, 'cursor_pitch', None)
                        if pitch is not None:
                            x_mm = self.editor.pitch_to_x(pitch)
                            px_per_mm = float(getattr(cv, '_px_per_mm', 0.0) or 0.0)
                            semitone_w_mm = float(getattr(self.editor, 'semitone_width', 3.0))
                            key_w_px = (semitone_w_mm * px_per_mm if px_per_mm > 0 else 12.0)
                            # Circle diameter relative to key width
                            diameter_px = key_w_px
                            key_h_px = int(80 * (2.0 / 3.0))
                            bottom_margin_px = 80 - key_h_px
                            x_px, _ = cv._mm_to_px_point(x_mm, 0.0)
                            # Position circle at bottom of black key if black, else bottom of keyboard panel
                            try:
                                from utils.CONSTANTS import BLACK_KEYS
                                is_black = int(pitch) in BLACK_KEYS
                            except Exception:
                                is_black = False
                            base_y = gui.editor.keyboard_panel.y if hasattr(gui, 'editor') else 0
                            y_px = base_y + (bottom_margin_px if is_black else 0)
                            # Center circle horizontally on key
                            x_circle = float(x_px) - (diameter_px / 2.0)
                            overlay.set_cursor_circle(x_circle, y_px + 15, diameter_px)
                    except Exception:
                        pass
            except Exception:
                pass
                kp._update_cursor(x, y)  # or kp._update_cursor() if it reads editor state
        except Exception as e:
            print(f'KB_PANEL: _update_cursor failed: {e}')

        # Drag detection (unchanged)
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
        tolerance = (line_width_mm / 2.0) + 1  # Add 1mm tolerance
        return distance <= tolerance
    
    def get_element_at_position(self, x: float, y: float, element_types=None):
        """
        Find score element at the given position using detection rectangles.
        
        Args:
            x, y: Position in canvas coordinates (mm)
            element_types: Optional list of element types to filter by 
                        (e.g., ['note', 'beam', 'slur', 'line_break'])
            
        Returns:
            Tuple of (element_object, element_type, stave_idx) or (None, None, None)
            
        Example:
            note, elem_type, stave = self.get_element_at_position(x, y, ['note'])
            if note:
                print(f"Found {elem_type} with id {note.id} on stave {stave}")
        """
        if not self.editor.score:
            return (None, None, None)

        note_flag = False
        note_list = []
        
        # Check all registered detection rectangles
        for element_id, (x1, y1, x2, y2) in self.editor.detection_rects.items():
            # Normalize rectangle coordinates (in case x2 < x1 or y2 < y1)
            min_x, max_x = min(x1, x2), max(x1, x2)
            min_y, max_y = min(y1, y2), max(y1, y2)
            
            # Check if point is inside rectangle
            if min_x <= x <= max_x and min_y <= y <= max_y:
                # Find the element by ID
                element = self.editor.score.find_by_id(element_id)
                
                if element is None:
                    continue
                
                # Determine element type from the element itself
                element_type = self._get_element_type(element)
                
                # Filter by element types if specified
                if element_types is not None and element_type not in element_types:
                    continue
                
                # Find which stave contains this element
                stave_idx = self._find_stave_for_element(element)

                if element_type == 'note':
                    note_flag = True
                    note_list.append( (element, element_type, stave_idx) )
                
                # # Found a valid element - return it
                # return (element, element_type, stave_idx)

        if note_flag and len(note_list) > 1:
            # if there are multiple notes under the mouse xy we need to select the right one
            for n in note_list:
                element, element_type, stave_idx = n
                
                # 
                if element.pitch in BLACK_KEYS:
                    center_pitch = self.editor.pitch_to_x(element.pitch)
                    if abs(x - center_pitch) < self.editor.semitone_width / 2:  # 3mm tolerance for black keys
                        return (element, element_type, stave_idx)
        else:
            return (None, None, None)
        
        # No valid element found at this position
        return (None, None, None)

    def get_element_at_position(self, x: float, y: float, element_types=None):
        """
        Find score element at the given position using detection rectangles.
        
        When multiple elements overlap, selects the one whose center is closest
        to the mouse cursor position.
        
        Args:
            x, y: Position in canvas coordinates (mm)
            element_types: Optional list of element types to filter by 
                        (e.g., ['note', 'beam', 'slur', 'line_break'])
            
        Returns:
            Tuple of (element_object, element_type, stave_idx) or (None, None, None)
            
        Example:
            note, elem_type, stave = self.get_element_at_position(x, y, ['note'])
            if note:
                print(f"Found {elem_type} with id {note.id} on stave {stave}")
        """
        if not self.editor.score:
            return (None, None, None)

        candidates = []
        
        # Check all registered detection rectangles
        for element_id, (x1, y1, x2, y2) in self.editor.detection_rects.items():
            # Normalize rectangle coordinates (in case x2 < x1 or y2 < y1)
            min_x, max_x = min(x1, x2), max(x1, x2)
            min_y, max_y = min(y1, y2), max(y1, y2)
            
            # Check if point is inside rectangle
            if min_x <= x <= max_x and min_y <= y <= max_y:
                # Find the element by ID
                element = self.editor.score.find_by_id(element_id)
                
                if element is None:
                    continue
                
                # Determine element type from the element itself
                element_type = self._get_element_type(element)
                
                # Filter by element types if specified
                if element_types is not None and element_type not in element_types:
                    continue
                
                # Find which stave contains this element
                stave_idx = self._find_stave_for_element(element)
                
                # Calculate center of the rectangle
                center_x = (min_x + max_x) / 2.0
                center_y = (min_y + max_y) / 2.0
                
                # Calculate distance from mouse to center
                distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                
                # Add to candidates with distance
                candidates.append((element, element_type, stave_idx, distance))
        
        # If no candidates found, return None
        if not candidates:
            return (None, None, None)
        
        # If only one candidate, return it
        if len(candidates) == 1:
            element, element_type, stave_idx, _ = candidates[0]
            return (element, element_type, stave_idx)
        
        # Multiple candidates - select the one with the smallest distance to center
        closest = min(candidates, key=lambda c: c[3])  # Sort by distance (4th element)
        element, element_type, stave_idx, _ = closest
        
        return (element, element_type, stave_idx)
    
    def _get_element_type(self, element) -> str:
        """Determine the type of an element from its class."""
        class_name = element.__class__.__name__
        
        # Map class names to element types
        type_map = {
            'Note': 'note',
            'GraceNote': 'grace_note',
            'Beam': 'beam',
            'Slur': 'slur',
            'Tempo': 'tempo',
            'Text': 'text',
            'LineBreak': 'line_break',
            'CountLine': 'count_line',
            'StartRepeat': 'start_repeat',
            'EndRepeat': 'end_repeat',
            'Section': 'section',
        }
        
        return type_map.get(class_name, class_name.lower())

    def _normalize_element_type(self, canvas_tag: str) -> str:
        """
            Convert canvas tag to normalized element type name.
            Normalizes legacy and variant tags to canonical names used by tools.
        """
        tag_to_type = {
            # Note variants
            'notehead': 'note',
            'notehead_black': 'note',
            'notehead_white': 'note',
            'left_dot': 'note',
            'midi_note': 'note',
            'stem': 'note',
            # Beam / slur / others
            'beam': 'beam',
            'slur': 'slur',
            'tempo': 'tempo',
            'text': 'text',
            'barline': 'barline',
            'line_break': 'line_break',
            'grace_note': 'grace_note',
            'gracenote_head_black': 'grace_note',
            'gracenote_head_white': 'grace_note',
        }
        return tag_to_type.get(canvas_tag, canvas_tag)

    def _find_stave_for_element(self, element) -> Optional[int]:
        """Find which stave contains the given element."""
        # Check score-level elements first (lineBreak, section, etc.)
        score = self.editor.score
        for score_level_type in ['lineBreak', 'section']:
            if hasattr(score, score_level_type):
                event_list = getattr(score, score_level_type)
                if element in event_list:
                    return None  # Score-level elements have no stave_idx
        
        # Check stave-level elements
        for stave_idx, stave in enumerate(self.editor.score.stave):
            if not hasattr(stave, 'event'):
                continue
            
            # Check all event types
            # Support both legacy and current grace note field naming; actual field is 'graceNote'
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
            ed = getattr(self, 'editor', None)
            if ed is None:
                return

            # Ensure conversion functions exist
            if not hasattr(ed, 'y_to_time') or not callable(ed.y_to_time):
                return

            raw_y = float(y_mm)
            raw_ticks = float(ed.y_to_time(raw_y))

            # Read grid step robustly
            step = None
            if hasattr(ed, 'get_grid_step_ticks') and callable(ed.get_grid_step_ticks):
                try:
                    step = float(ed.get_grid_step_ticks())
                except Exception:
                    step = None
            if step is None or step <= 0:
                step = 1.0  # sensible fallback

            # Snap down to grid
            snapped = math.floor(raw_ticks / step) * step

            # Clamp within score bounds (fallbacks if unavailable)
            total = None
            if hasattr(ed, '_get_score_length_in_ticks') and callable(ed._get_score_length_in_ticks):
                try:
                    total = float(ed._get_score_length_in_ticks())
                except Exception:
                    total = None
            if total is None:
                # Try derive from score if available
                total = float(getattr(getattr(ed, 'score', None), 'metaInfo', None).totalLengthTicks) if (
                    hasattr(getattr(ed, 'score', None), 'metaInfo') and
                    hasattr(getattr(ed.score, 'metaInfo'), 'totalLengthTicks')
                ) else float(max(0.0, snapped))

            snapped = max(0.0, min(total, snapped))

            # Update cursor position and draw time cursor
            self._cursor_time = snapped
            self._draw_time_cursor()
        except Exception as e:
            print(f'CURSOR: update failed: {e}')
    
    def _clear_time_cursor(self):
        """Remove the time cursor from the canvas."""
        self._cursor_time = None
        # Delete all cursor lines by tag
        self.canvas.delete_by_tag('cursor_line')
    
    def _draw_time_cursor(self):
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
                color=DARK_HEX,
                width_mm=self.editor.score.properties.globalBasegrid.barlineWidthMm,
                dash=False,
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
                color=DARK_HEX,
                width_mm=self.editor.score.properties.globalBasegrid.barlineWidthMm,
                dash=False,
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
