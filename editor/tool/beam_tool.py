"""
Beam Tool - Add, edit, and remove beams.
"""

from editor.tool.base_tool import BaseTool
from file.beam import Beam
from typing import Optional, Tuple


class BeamTool(BaseTool):
    """Tool for adding and editing beam custom grouping."""
    
    def __init__(self, editor):
        super().__init__(editor)
        self.edit_beam = None  # Beam being created/edited during drag
        self.edit_stave_idx = None  # Stave index of beam being edited
    
    @property
    def name(self) -> str:
        return "Beam"
    
    @property
    def cursor(self) -> str:
        return 'crosshair'
    
    def _get_beam_at_position(self, x: float, y: float) -> Tuple[Optional[Beam], Optional[int]]:
        """
        Find a beam element at the given position using line hit detection.
        
        Args:
            x, y: Position in canvas coordinates (mm)
            
        Returns:
            Tuple of (beam_object, stave_idx) or (None, None)
        """
        if not self.score:
            return (None, None)
        
        # Get the currently rendered stave
        stave_idx = self.score.fileSettings.get_rendered_stave_index(
            num_staves=len(self.score.stave)
        )
        
        stave = self.score.stave[stave_idx]
        if not hasattr(stave.event, 'beam'):
            return (None, None)
        
        # Check each beam to see if click is on it
        for beam in stave.event.beam:
            # Calculate beam line coordinates
            y_start = self.editor.time_to_y(beam.time)
            y_end = self.editor.time_to_y(beam.time + beam.duration)
            
            if beam.hand == '<':
                x1 = 9
                x2 = 10
            else:
                x1 = self.editor.editor_margin * 2 + self.editor.stave_width - 9
                x2 = self.editor.editor_margin * 2 + self.editor.stave_width - 10
            
            # Check main vertical beam line (1mm width)
            if self.is_point_near_line(x, y, x1, y_start, x2, y_end, line_width_mm=1.0):
                return (beam, stave_idx)
            
            # Check horizontal guide lines (0.25mm width)
            guide_x2 = self.editor.editor_margin + self.editor.stave_width if beam.hand == '>' else self.editor.editor_margin
            
            # Top guide line
            if self.is_point_near_line(x, y, x1, y_start, guide_x2, y_start, line_width_mm=0.25):
                return (beam, stave_idx)
            
            # Bottom guide line
            if self.is_point_near_line(x, y, x1, y_end, guide_x2, y_end, line_width_mm=0.25):
                return (beam, stave_idx)
        
        return (None, None)
    
    def get_element_at_position(self, x: float, y: float, element_types=None):
        """Override to use beam-specific line hit detection."""
        # If looking for beams, use our custom beam detection
        if element_types is not None and element_types == ['beam']:
            beam, stave_idx = self._get_beam_at_position(x, y)
            if beam:
                return (beam, 'beam', stave_idx)
            return (None, None, None)
        
        # Otherwise use parent's detection
        return super().get_element_at_position(x, y, element_types)
    
    def on_activate(self):
        """Called when this tool becomes active."""
        super().on_activate()
    
    def on_deactivate(self):
        """Called when switching away from this tool."""
        super().on_deactivate()
        # Delete old cursor drawing
        self.editor.canvas.delete_by_tag('cursor')
        self.editor.canvas.delete_by_tag('beam_marker')
    
    def on_mouse_move(self, x: float, y: float) -> bool:
        """Handle mouse movement (hover, no buttons pressed)."""
        # Call parent's drag detection first
        if super().on_mouse_move(x, y):
            return True  # Parent is handling drag - stop here
        
        # Guard against startup race condition (mouse moves before file loaded)
        if not self.score:
            return False
        
        # Get pitch and time from mouse position
        pitch, time = self.get_pitch_and_time(x, y)
        duration = 0
        
        # Determine hand based on pitch (< 40 is left, >= 40 is right)
        if pitch < 40:
            hand = '<'
        else:
            hand = '>'
        
        # Clamp time to valid range
        score_length = self.editor.get_score_length_in_ticks()
        if time + duration > score_length:
            time = score_length - duration
        if time < 0:
            time = 0
        
        # Create cursor beam
        cursor = Beam(time=time, duration=duration, hand=hand)
        
        # Draw cursor
        self._draw_cursor(cursor, type='cursor')
        
        return True
    
    def on_left_press(self, x: float, y: float, item_id: Optional[int] = None) -> bool:
        """
        Called when left mouse button is pressed down.
        
        Used for starting beam creation or editing existing beams.
        """
        super().on_left_press(x, y)
        
        # Clear any existing selection when starting to draw/edit a beam
        if hasattr(self.editor, 'selection_manager'):
            self.editor.selection_manager.clear_selection()
        
        # Guard: Prevent creating a new beam if one is already being edited
        if self.edit_beam is not None:
            print(f"BeamTool: Ignoring duplicate on_left_press (beam {self.edit_beam.id} already being edited)")
            return True
        
        # Check if we clicked on an existing beam
        element, elem_type, stave_idx = self.get_element_at_position(x, y, element_types=['beam'])
        
        if element and elem_type == 'beam':
            # EDIT MODE: Start editing existing beam
            self.edit_beam = element
            self.edit_stave_idx = stave_idx
            
            # Redraw in 'edit' mode for visual feedback
            self.editor._draw_single_beam_marker(stave_idx, self.edit_beam, draw_mode='edit')
            
            print(f"BeamTool: Editing beam {element.id} from stave {stave_idx}")
            return True
        
        # CREATE MODE: No beam clicked, create new one
        pitch, time = self.get_pitch_and_time(x, y)
        
        # Determine hand based on pitch
        if pitch < 40:
            hand = '<'
        else:
            hand = '>'
        
        # Boundary check: Clamp time to valid range
        score_length = self.editor.get_score_length_in_ticks()
        duration = 0
        
        # Clamp time to valid range (0 to score_length - duration)
        if time + duration > score_length:
            time = score_length - duration
        if time < 0:
            time = 0
        
        # Get the currently rendered stave index from fileSettings
        stave_idx = self.editor.score.fileSettings.get_rendered_stave_index(
            num_staves=len(self.editor.score.stave)
        )
        
        self.edit_beam = self.editor.score.new_beam(
            stave_idx=stave_idx,
            time=time,
            duration=duration,
            hand=hand
        )
        self.edit_stave_idx = stave_idx
        
        # Draw in 'edit' mode
        self.editor._draw_single_beam_marker(stave_idx, self.edit_beam, draw_mode='edit')
        
        # Mark as modified
        if hasattr(self.editor, 'on_modified') and self.editor.on_modified:
            self.editor.on_modified()
        
        print(f"BeamTool: Creating new beam {self.edit_beam.id}")
        return True
    
    def on_left_click(self, x: float, y: float) -> bool:
        """Called when left mouse button is clicked (pressed and released without dragging)."""
        return True
    
    def on_left_unpress(self, x: float, y: float) -> bool:
        """Called when left mouse button is released without having dragged."""
        if self.edit_beam is None:
            return False
        
        # Sort the beam list by time
        stave = self.editor.score.stave[self.edit_stave_idx]
        stave.event.beam.sort(key=lambda b: b.time)
        
        # Delete 'edit' drawing and redraw as 'beam'
        self.editor.canvas.delete_by_tag('edit')
        self.editor.canvas.delete_by_tag('beam_marker')
        self.editor._draw_single_beam_marker(self.edit_stave_idx, self.edit_beam, draw_mode='beam')
        
        # Mark as modified
        if hasattr(self.editor, 'on_modified') and self.editor.on_modified:
            self.editor.on_modified()
        
        # Clear references
        self.edit_beam = None
        self.edit_stave_idx = None
        
        return True
    
    def on_left_release(self, x: float, y: float) -> bool:
        """Called when left mouse button is released (after drag or click)."""
        # Let parent handle the drag_end vs unpress logic
        result = super().on_left_release(x, y)
        return result
    
    def on_right_click(self, x: float, y: float) -> bool:
        """Called when right mouse button is clicked (without drag)."""
        print(f"BeamTool.on_right_click called at ({x:.1f}, {y:.1f})")
        
        # Delete any existing cursor drawing
        self.editor.canvas.delete_by_tag('cursor')

        # Check if we clicked on an existing beam
        element, elem_type, stave_idx = self.get_element_at_position(x, y, element_types=['beam'])
        
        if element and elem_type == 'beam':
            # Found a beam to delete
            print(f"BeamTool: Deleting beam {element.id} from stave {stave_idx}")
            
            # Remove from SCORE
            if stave_idx is not None and stave_idx < len(self.editor.score.stave):
                stave = self.editor.score.stave[stave_idx]
                if hasattr(stave.event, 'beam') and element in stave.event.beam:
                    stave.event.beam.remove(element)
                    
                    # Delete the visual representation
                    self.editor.canvas.delete_by_tag(str(element.id))
                    
                    # Mark as modified
                    if hasattr(self.editor, 'on_modified') and self.editor.on_modified:
                        self.editor.on_modified()
                    
                    print(f"BeamTool: Beam {element.id} deleted successfully")
                    return True
            
            print(f"BeamTool: Failed to delete beam {element.id}")
            return False
        
        # No beam found at click position
        print(f"BeamTool: No beam found at ({x}, {y})")
        return False
    
    def on_double_click(self, x: float, y: float) -> bool:
        """Called when mouse is double-clicked."""
        # TODO: Edit beam properties on double-click
        return False
    
    def on_drag_start(self, x: float, y: float, start_x: float, start_y: float) -> bool:
        """Called when drag first starts (mouse moved beyond threshold with button down)."""
        return False
    
    def on_drag(self, x: float, y: float, start_x: float, start_y: float) -> bool:
        """Called continuously while dragging WITH button pressed."""
        # Draw time cursor (parent functionality)
        super().on_drag(x, y, start_x, start_y)
        
        if self.edit_beam is None:
            return False
        
        # Get mouse position
        pitch, time = self.get_pitch_and_time(x, y)
        
        # Boundary check: Prevent dragging beam outside valid time range
        score_length = self.editor.get_score_length_in_ticks()
        
        # Calculate proposed duration (dragging down extends the beam)
        proposed_duration = max(0, time - self.edit_beam.time)
        
        # Only update duration if dragging down (extending the beam)
        if time >= self.edit_beam.time:
            proposed_end_time = self.edit_beam.time + proposed_duration
            
            # Only update duration if it stays within bounds
            if proposed_end_time <= score_length:
                self.edit_beam.duration = proposed_duration
            else:
                # Cap duration at score boundary
                max_duration = score_length - self.edit_beam.time
                if max_duration > 0:
                    self.edit_beam.duration = max_duration
        
        # Redraw in 'edit' mode
        self.editor._draw_single_beam_marker(self.edit_stave_idx, self.edit_beam, draw_mode='edit')

        # Delete any existing cursor drawing
        self.editor.canvas.delete_by_tag('cursor')
        
        return True
    
    def on_drag_end(self, x: float, y: float) -> bool:
        """Called when drag finishes (button released after dragging)."""
        if self.edit_beam is None:
            return False
        
        # Sort the beam list by time
        stave = self.editor.score.stave[self.edit_stave_idx]
        stave.event.beam.sort(key=lambda b: b.time)
        
        # Delete 'edit' drawing and redraw as 'beam'
        self.editor.canvas.delete_by_tag('edit')
        self.editor.canvas.delete_by_tag('beam_marker')
        self.editor._draw_single_beam_marker(self.edit_stave_idx, self.edit_beam, draw_mode='beam')
        
        # Mark as modified
        if hasattr(self.editor, 'on_modified') and self.editor.on_modified:
            self.editor.on_modified()
        
        # Clear references
        self.edit_beam = None
        self.edit_stave_idx = None
        
        print(f"BeamTool: Drag ended at ({x}, {y})")
        return True
    
    def _draw_cursor(self, cursor: Beam, type: str = 'cursor') -> None:
        """Draw the beam cursor on the canvas.

        Args:
            cursor: The Beam object representing the cursor.
            type: Type of cursor ('cursor' or 'preview').
        """
        self.editor._draw_single_beam_marker(0, cursor, draw_mode=type)