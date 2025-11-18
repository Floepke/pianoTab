"""
Note Tool - Add, edit, and remove notes.
"""

from editor.tool.base_tool import BaseTool
from file.note import Note
from typing import Optional, Literal


class NoteTool(BaseTool):
    """Tool for adding and editing notes."""
    
    def __init__(self, editor):
        super().__init__(editor)
        self.hand_cursor = '<'  # Default to left hand
        self.edit_note = None  # Note being created/edited during drag
        self.edit_stave_idx = None  # Stave index of note being edited
    
    @property
    def name(self) -> str:
        return "Note"
    
    @property
    def cursor(self) -> str:
        return 'crosshair'
    
    def on_activate(self):
        """Called when this tool becomes active."""
        super().on_activate()
        # Reset to default hand
        self.hand_cursor = '<'
    
    def on_deactivate(self):
        """Called when switching away from this tool."""
        super().on_deactivate()

        # delete old cursor drawing
        self.editor.canvas.delete_by_tag('cursor')
    
    def on_key_press(self, key: str, x: float, y: float) -> bool:
        """Handle key press events."""
        # Map , and . keys for hand switching (they have arrow symbols on keyboard)
        if key == ',' or key == 'comma':
            self.hand_cursor = '<'  # Left hand
            # Redraw cursor at current mouse position
            pitch, time = self.get_pitch_and_time(x, y)
            cursor = Note(time=time, pitch=pitch, hand=self.hand_cursor)
            self._draw_note_cursor(cursor, type='cursor')
            return True  # We handled this key
        elif key == '.' or key == 'period':
            self.hand_cursor = '>'  # Right hand
            # Redraw cursor at current mouse position
            pitch, time = self.get_pitch_and_time(x, y)
            cursor = Note(time=time, pitch=pitch, hand=self.hand_cursor)
            self._draw_note_cursor(cursor, type='cursor')
            return True  # We handled this key
        
        return False  # We didn't handle this key
    
    def on_mouse_move(self, x: float, y: float) -> bool:
        """Handle mouse movement (hover, no buttons pressed)."""
        # Guard against startup race condition (mouse moves before file loaded)
        if not self.score:
            return False
        
        # Call parent first - handles time cursor and drag detection
        if super().on_mouse_move(x, y):
            return True  # Parent is handling drag - stop here
        
        # draw note cursor using current hand setting
        pitch, time = self.get_pitch_and_time(x, y)
        cursor = Note(time=time, pitch=pitch, duration=self.editor.grid_selector.get_grid_step(), hand=self.hand_cursor)
        
        # redraw cursor
        self._draw_note_cursor(cursor, type='cursor')
        
        return True
    
    
    def on_left_click(self, x: float, y: float) -> bool:
        """Called when left mouse button is clicked (pressed and released without dragging)."""
        
        return True
    
    def on_left_press(self, x: float, y: float, item_id: Optional[int] = None) -> bool:
        """
            Called when left mouse button is pressed down.

            Used for starting note creation or editing existing notes.
        """
        super().on_left_press(x, y)
        
        # Clear any existing selection when starting to draw/edit a note
        if hasattr(self.editor, 'selection_manager'):
            self.editor.selection_manager.clear_selection()
        
        # Guard: Prevent creating a new note if one is already being edited
        if self.edit_note is not None:
            print(f"NoteTool: Ignoring duplicate on_left_press (note {self.edit_note.id} already being edited)")
            return True
        
        # Check if we clicked on an existing note
        element, elem_type, stave_idx = self.get_element_at_position(x, y, element_types=['note'])
        
        if element and elem_type == 'note':
            # delete any existing cursor drawing
            self.editor.canvas.delete_by_tag('cursor')

            # EDIT MODE: Start editing existing note
            self.edit_note = element
            self.edit_stave_idx = stave_idx
            
            # Assign current cursor hand to the note being edited
            self.edit_note.hand = self.hand_cursor
            
            # Redraw in 'select/edit' mode for visual feedback
            self.editor._draw_single_note(stave_idx, self.edit_note, draw_mode='select/edit')
            
            print(f"NoteTool: Editing note {element.id} from stave {stave_idx}, assigned hand '{self.hand_cursor}'")
            return True
        
        # CREATE MODE: No note clicked, create new one
        pitch, time = self.get_pitch_and_time(x, y)
        
        self.edit_note = self.editor.score.new_note(
            stave_idx=0,  # TODO: determine correct stave
            time=time,
            pitch=pitch,
            hand=self.hand_cursor,
            duration=self.editor.grid_selector.get_grid_step(),
            velocity=100
        )
        self.edit_stave_idx = 0
        
        # Draw in 'select/edit' mode
        self.editor._draw_single_note(0, self.edit_note, draw_mode='select/edit')

        # delete any existing cursor drawing
        self.editor.canvas.delete_by_tag('cursor')
        
        # Mark as modified (which will trigger engraving via FileManager)
        if hasattr(self.editor, 'on_modified') and self.editor.on_modified:
            self.editor.on_modified()
        
        print(f"NoteTool: Creating new note {self.edit_note.id}")
        return True

    def on_drag(self, x: float, y: float, start_x: float, start_y: float) -> bool:
        """Called continuously while dragging WITH button pressed."""
        # Draw time cursor (parent functionality)
        super().on_drag(x, y, start_x, start_y)
        
        if self.edit_note is None:
            return False
        
        # Get mouse position
        pitch, time = self.get_pitch_and_time(x, y)

        # Specific editor mouse behavior
        self.edit_note.duration = max(self.editor.grid_selector.get_grid_step(), time - self.edit_note.time)
        if time < self.edit_note.time or y < self.editor.editor_margin: 
            # We edit the pitch in this case
            self.edit_note.pitch = pitch
        
        # Redraw in 'select/edit' mode
        self.editor._draw_single_note(self.edit_stave_idx, self.edit_note, draw_mode='select/edit')

        # Delete any existing cursor drawing
        self.editor.canvas.delete_by_tag('cursor')
        
        # Don't trigger engraver during drag - wait until drag ends
        
        return True

    def on_left_unpress(self, x: float, y: float) -> bool:
        """Called when left mouse button is released without dragging."""
        if self.edit_note is None:
            return False
        
        # Sort the note list by time to ensure continuation dots work correctly
        stave = self.editor.score.stave[self.edit_stave_idx]
        stave.event.note.sort(key=lambda n: n.time)
        
        # Delete 'select/edit' drawing and redraw as 'note'
        self.editor.canvas.delete_by_tag('select/edit')
        self.editor._draw_single_note(self.edit_stave_idx, self.edit_note, draw_mode='note')
        
        # Redraw overlapping notes to update their continuation dots
        self.editor._redraw_overlapping_notes(self.edit_stave_idx, self.edit_note)
        
        # Mark as modified (which will trigger engraving via FileManager)
        if hasattr(self.editor, 'on_modified') and self.editor.on_modified:
            self.editor.on_modified()
        
        # Clear references
        self.edit_note = None
        self.edit_stave_idx = None
        
        return True

    def on_left_release(self, x: float, y: float) -> bool:
        """Called when left mouse button is released (after drag or click)."""
        # Let parent handle the drag_end vs unpress logic
        result = super().on_left_release(x, y)
        
        # Parent will call either on_drag_end or on_left_unpress
        # Both of those handle cleanup, so we're done here
        return result
    
    def on_right_click(self, x: float, y: float) -> bool:
        """Called when right mouse button is clicked (without drag)."""
        
        print(f"NoteTool.on_right_click called at ({x:.1f}, {y:.1f})")
        
        # delete any existing cursor drawing
        self.editor.canvas.delete_by_tag('cursor')

        # Check if we clicked on an existing note
        element, elem_type, stave_idx = self.get_element_at_position(x, y, element_types=['note'])
        
        if element and elem_type == 'note':
            # Found a note to delete
            print(f"NoteTool: Deleting note {element.id} from stave {stave_idx}")
            
            # Save note's time, duration, id, and hand before deletion
            note_time = element.time
            note_duration = element.duration
            note_id = element.id
            note_hand = element.hand
            
            # Remove from SCORE
            if stave_idx is not None and stave_idx < len(self.editor.score.stave):
                stave = self.editor.score.stave[stave_idx]
                if hasattr(stave.event, 'note') and element in stave.event.note:
                    stave.event.note.remove(element)
                    
                    # Delete the visual representation
                    self.editor.canvas.delete_by_tag(str(element.id))
                    
                    # Redraw overlapping notes AFTER deleting (using saved attributes)
                    # We create a temporary object with just the needed attributes
                    class TempNote:
                        def __init__(self, time, duration, id, hand):
                            self.time = time
                            self.duration = duration
                            self.id = id
                            self.hand = hand
                    
                    temp_note = TempNote(note_time, note_duration, note_id, note_hand)
                    self.editor._redraw_overlapping_notes(stave_idx, temp_note)
                    
                    # Mark as modified (which will trigger engraving via FileManager)
                    if hasattr(self.editor, 'on_modified') and self.editor.on_modified:
                        self.editor.on_modified()
                    
                    print(f"NoteTool: Note {element.id} deleted successfully")
                    return True
            
            print(f"NoteTool: Failed to delete note {element.id}")
            return False
        
        # No note found at click position
        print(f"NoteTool: No note found at ({x}, {y})")
        return False
    
    def on_double_click(self, x: float, y: float) -> bool:
        """Called when mouse is double-clicked."""
        # TODO: Edit note properties on double-click
        print(f"NoteTool: Edit note at ({x}, {y})")
        return False
    
    def on_drag_start(self, x: float, y: float, start_x: float, start_y: float) -> bool:
        """Called when drag first starts (mouse moved beyond threshold with button down)."""
        # TODO: Initialize drag operation
        print(f"NoteTool: Start drag from ({start_x}, {start_y}) to ({x}, {y})")
        return False
    
    def on_drag_end(self, x: float, y: float) -> bool:
        """Called when drag finishes (button released after dragging)."""
        if self.edit_note is None:
            return False
        
        # Sort the note list by time to ensure continuation dots work correctly
        stave = self.editor.score.stave[self.edit_stave_idx]
        stave.event.note.sort(key=lambda n: n.time)
        
        # Delete 'select/edit' drawing and redraw as 'note'
        self.editor.canvas.delete_by_tag('select/edit')
        self.editor._draw_single_note(self.edit_stave_idx, self.edit_note, draw_mode='note')
        
        # Redraw overlapping notes to update their continuation dots
        self.editor._redraw_overlapping_notes(self.edit_stave_idx, self.edit_note)
        
        # Mark as modified (which will trigger engraving via FileManager)
        if hasattr(self.editor, 'on_modified') and self.editor.on_modified:
            self.editor.on_modified()
        
        # Clear references
        self.edit_note = None
        self.edit_stave_idx = None
        
        print(f"NoteTool: Drag ended at ({x}, {y})")
        return True
    
    def _draw_note_cursor(self, cursor: Note, type: Optional[Literal['note', 'cursor', 'selected/edit']] = 'cursor'):
        """Draw a note cursor at the given position."""
        self.editor.canvas.delete_by_tag('cursor')
        self.editor._draw_single_note(0, cursor, draw_mode=type)

    