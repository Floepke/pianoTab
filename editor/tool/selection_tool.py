"""
Selection Tool - Select, copy, cut, paste, and delete multiple elements.

States:
- IDLE: No selection, hovering
- DRAWING_RECT: User is dragging to draw selection rectangle
- SELECTED: Elements are selected (can cut/copy/paste/delete)
"""

from editor.tool.base_tool import BaseTool
from typing import Optional, List, Dict, Any, Tuple


class SelectionTool(BaseTool):
    """Tool for selecting and manipulating multiple score elements."""
    
    def __init__(self, editor):
        super().__init__(editor)
        
        # Selection state
        self.selected_elements: List[Dict[str, Any]] = []
        # Each item: {'element': obj, 'type': str, 'stave_idx': int}
        
        # Selection rectangle tracking
        self.selection_rect_start: Optional[Tuple[float, float]] = None
        self.selection_rect_id: Optional[int] = None
        
        # Clipboard
        self.clipboard: List[Dict[str, Any]] = []
        
        # Mouse cursor position for paste operations
        self._last_mouse_x: float = 0.0
        self._last_mouse_y: float = 0.0
    
    @property
    def name(self) -> str:
        return "Selection"
    
    @property
    def cursor(self) -> str:
        return 'arrow'  # Standard arrow cursor for selection
    
    def on_activate(self):
        """Called when this tool becomes active."""
        super().on_activate()
        self.clear_selection()
    
    def on_deactivate(self):
        """Called when switching away from this tool."""
        super().on_deactivate()
        self.clear_selection()
        self._clear_selection_rect()
    
    # === Selection Rectangle Drawing ===
    
    def on_left_press(self, x: float, y: float) -> bool:
        """Start drawing selection rectangle."""
        super().on_left_press(x, y)
        
        # Store starting position
        self.selection_rect_start = (x, y)
        
        # Clear any previous selection
        self.clear_selection()
        
        print(f"SelectionTool: Starting selection at ({x:.1f}, {y:.1f})")
        return True
    
    def on_drag_start(self, x: float, y: float, start_x: float, start_y: float) -> bool:
        """Begin drawing the selection rectangle."""
        print(f"SelectionTool: Drag started from ({start_x:.1f}, {start_y:.1f})")
        self._draw_selection_rect(start_x, start_y, x, y)
        return True
    
    def on_drag(self, x: float, y: float, start_x: float, start_y: float) -> bool:
        """Update selection rectangle as user drags."""
        self._draw_selection_rect(start_x, start_y, x, y)
        return True
    
    def on_drag_end(self, x: float, y: float) -> bool:
        """Finalize selection - find all elements in rectangle."""
        if self.selection_rect_start is None:
            print("SelectionTool: on_drag_end called but no selection_rect_start")
            return False
        
        start_x, start_y = self.selection_rect_start
        
        print(f"SelectionTool: Finalizing selection from ({start_x:.1f}, {start_y:.1f}) to ({x:.1f}, {y:.1f})")
        
        # Find all elements within the rectangle
        try:
            self.selected_elements = self._find_elements_in_rect(start_x, start_y, x, y)
        except Exception as e:
            print(f"SelectionTool: Error finding elements: {e}")
            import traceback
            traceback.print_exc()
            self.selected_elements = []
        
        print(f"SelectionTool: Selected {len(self.selected_elements)} elements")
        
        # Remove the selection rectangle
        self._clear_selection_rect()
        self.selection_rect_start = None
        
        # Highlight selected elements
        if self.selected_elements:
            try:
                self._highlight_selection()
            except Exception as e:
                print(f"SelectionTool: Error highlighting selection: {e}")
                import traceback
                traceback.print_exc()
        
        return True
    
    def on_left_release(self, x: float, y: float) -> bool:
        """Handle release without drag - single click."""
        result = super().on_left_release(x, y)
        
        # If we didn't drag, treat as a click to deselect
        if not result and self.selection_rect_start is not None:
            # It was a click, not a drag - clear selection
            self.clear_selection()
            self.selection_rect_start = None
        
        return result
    
    def _draw_selection_rect(self, x1: float, y1: float, x2: float, y2: float):
        """Draw or update the selection rectangle."""
        try:
            # Remove old rectangle
            if self.selection_rect_id is not None:
                self.canvas.delete(self.selection_rect_id)
            
            # Draw new rectangle using correct Canvas API (x1_mm, y1_mm, x2_mm, y2_mm)
            # No need to normalize - Canvas handles any corner pair
            self.selection_rect_id = self.canvas.add_rectangle(
                x1_mm=x1,
                y1_mm=y1,
                x2_mm=x2,
                y2_mm=y2,
                fill=True,
                fill_color='#3380FF33',  # Light blue transparent fill
                outline=True,
                outline_color='#3380FFCC',  # Blue outline
                outline_width_mm=0.2,
                tags={'selection_rect'}
            )
        except Exception as e:
            print(f"SelectionTool: Failed to draw selection rectangle: {e}")
            # Continue anyway - selection will still work
    
    def _clear_selection_rect(self):
        """Remove the selection rectangle from canvas."""
        if self.selection_rect_id is not None:
            self.canvas.delete(self.selection_rect_id)
            self.selection_rect_id = None
        
        # Also remove by tag just in case
        self.canvas.delete_by_tag('selection_rect')
    
    # === Element Finding (Direct Position Check) ===
    
    def _find_elements_in_rect(self, x1: float, y1: float, x2: float, y2: float) -> List[Dict[str, Any]]:
        """
        Find all elements within selection rectangle by checking their positions directly.
        
        For notes: Uses the notehead position (pitch_to_x, time_to_y) as the detection point.
        This allows precise selection without including the midi note rectangle.
        
        Args:
            x1, y1: First corner of rectangle
            x2, y2: Opposite corner of rectangle
            
        Returns:
            List of selected elements with metadata
        """
        selected = []
        
        # Normalize rectangle
        left = min(x1, x2)
        right = max(x1, x2)
        top = min(y1, y2)
        bottom = max(y1, y2)
        
        print(f"  Selection rect: x=[{left:.1f}, {right:.1f}], y=[{top:.1f}, {bottom:.1f}]")
        
        # Check each stave
        for stave_idx, stave in enumerate(self.editor.score.stave):
            # Check notes - use notehead position only
            for note in stave.event.note:
                # Get notehead position in mm coordinates
                note_x = self.editor.pitch_to_x(note.pitch)
                note_y = self.editor.time_to_y(note.time)
                
                # Check if notehead is within selection rectangle
                if left <= note_x <= right and top <= note_y <= bottom:
                    selected.append({
                        'element': note,
                        'type': 'note',
                        'stave_idx': stave_idx,
                    })
                    print(f"  Found note at ({note_x:.1f}, {note_y:.1f})")
            
            # TODO: Add other element types if needed (beams, slurs, etc.)
            # For now, only notes are supported
        
        print(f"  Found {len(selected)} elements")
        return selected
    
    # === Selection Highlighting ===
    
    def _highlight_selection(self):
        """Draw visual highlight around selected elements."""
        # Remove old highlights
        self.canvas.delete_by_tag('selection_highlight')
        
        for item in self.selected_elements:
            element = item['element']
            elem_type = item['type']
            stave_idx = item['stave_idx']
            
            # For notes, redraw them in 'selected' mode
            if elem_type == 'note':
                # Delete the normal drawing
                self.canvas.delete_by_tag(str(element.id))
                # Redraw in selected mode
                self.editor._draw_single_note(stave_idx, element, draw_mode='selected')
            else:
                # For other element types, draw a highlight box
                bbox = self._get_element_bbox(element, elem_type, stave_idx)
                
                if bbox is not None:
                    x1, y1, x2, y2 = bbox
                    
                    # Draw highlight rectangle around element
                    self.canvas.add_rectangle(
                        x1_mm=x1 - 1.0,  # Add padding
                        y1_mm=y1 - 1.0,
                        x2_mm=x2 + 1.0,
                        y2_mm=y2 + 1.0,
                        fill=True,
                        fill_color='#3380FF26',  # Light blue transparent
                        outline=True,
                        outline_color='#3380FFE6',  # Blue outline
                        outline_width_mm=0.3,
                        tags={'selection_highlight'}
                    )
    
    def _get_element_bbox(self, element: Any, elem_type: str, stave_idx: int) -> Optional[Tuple[float, float, float, float]]:
        """
        Get bounding box of an element in canvas coordinates.
        
        Returns:
            (x1, y1, x2, y2) in mm, or None if unable to determine
        """
        # Use canvas item lookup to get bounding box
        # Elements are typically drawn with their id as a tag
        element_id = getattr(element, 'id', None)
        
        if element_id is None:
            return None
        
        # Get all canvas items with this element's id tag
        items = self.canvas.find_by_tag(str(element_id))
        
        if not items:
            return None
        
        # Calculate bounding box from all items with this tag
        # For now, return a simple estimate based on element type
        # TODO: Could walk through canvas._items to get actual bounds
        
        # Simple fallback: use element position and approximate size
        if elem_type == 'note':
            # Notes have time and pitch
            if hasattr(element, 'time') and hasattr(element, 'pitch'):
                x = element.pitch  # Pitch maps to x coordinate
                y = element.time    # Time maps to y coordinate
                # Approximate note size
                return (x - 2, y - 2, x + 2, y + 2)
        
        return None
    
    # === Selection Management ===
    
    def clear_selection(self):
        """Clear the current selection."""
        # Restore selected notes to normal drawing mode
        for item in self.selected_elements:
            if item['type'] == 'note':
                element = item['element']
                stave_idx = item['stave_idx']
                # Delete selected drawing
                self.canvas.delete_by_tag(str(element.id))
                # Redraw in normal mode
                self.editor._draw_single_note(stave_idx, element, draw_mode='note')
        
        self.selected_elements = []
        self.canvas.delete_by_tag('selection_highlight')
        print("SelectionTool: Selection cleared")
    
    # === Keyboard Shortcuts ===
    
    def on_key_press(self, key: str, x: float, y: float) -> bool:
        """Handle keyboard shortcuts for selection operations."""
        
        if key == 'delete' or key == 'backspace':
            # Delete selected elements
            return self._delete_selected()
        
        elif key == 'c' or key == 'ctrl+c':
            # Copy
            return self._copy_selected()
        
        elif key == 'x' or key == 'ctrl+x':
            # Cut
            return self._cut_selected()
        
        elif key == 'v' or key == 'ctrl+v':
            # Paste at cursor position
            return self._paste()
        
        elif key == 'escape':
            # Clear selection (only handle if we have a selection)
            if self.selected_elements:
                self.clear_selection()
                return True
            return False  # Let other handlers process escape
        
        elif key == 'up':
            # Move selection up by grid step
            return self._move_selection_time(-self.editor.get_grid_step_ticks())
        
        elif key == 'down':
            # Move selection down by grid step
            return self._move_selection_time(self.editor.get_grid_step_ticks())
        
        elif key == 'left':
            # Transpose selection down by 1 semitone
            return self._transpose_selection(-1)
        
        elif key == 'right':
            # Transpose selection up by 1 semitone
            return self._transpose_selection(1)
        
        return False
    
    # === Clipboard Operations (Placeholder) ===
    
    def _delete_selected(self) -> bool:
        """Delete all selected elements."""
        if not self.selected_elements:
            print("SelectionTool: No elements to delete")
            return False
        
        print(f"SelectionTool: Deleting {len(self.selected_elements)} elements")
        
        for item in self.selected_elements:
            element = item['element']
            elem_type = item['type']
            stave_idx = item['stave_idx']
            
            # Delete from score based on type
            self._delete_element(element, elem_type, stave_idx)
        
        # Clear selection
        self.clear_selection()
        
        # Mark as modified
        if hasattr(self.editor, 'on_modified') and self.editor.on_modified:
            self.editor.on_modified()
        
        # Redraw canvas
        self.editor.redraw_pianoroll()
        
        return True
    
    def _delete_element(self, element: Any, elem_type: str, stave_idx: int):
        """Delete a single element from the score."""
        if stave_idx >= len(self.editor.score.stave):
            return
        
        stave = self.editor.score.stave[stave_idx]
        
        # Delete based on element type
        if elem_type == 'note' and hasattr(stave.event, 'note'):
            if element in stave.event.note:
                stave.event.note.remove(element)
                print(f"  Deleted note {getattr(element, 'id', '?')}")
        
        elif elem_type == 'beam' and hasattr(stave.event, 'beam'):
            if element in stave.event.beam:
                stave.event.beam.remove(element)
                print(f"  Deleted beam {getattr(element, 'id', '?')}")
        
        elif elem_type == 'slur' and hasattr(stave.event, 'slur'):
            if element in stave.event.slur:
                stave.event.slur.remove(element)
                print(f"  Deleted slur {getattr(element, 'id', '?')}")
        
        elif elem_type == 'gracenote' and hasattr(stave.event, 'graceNote'):
            if element in stave.event.graceNote:
                stave.event.graceNote.remove(element)
                print(f"  Deleted grace note {getattr(element, 'id', '?')}")
        
        elif elem_type == 'text' and hasattr(stave.event, 'text'):
            if element in stave.event.text:
                stave.event.text.remove(element)
                print(f"  Deleted text {getattr(element, 'id', '?')}")
        
        elif elem_type == 'tempo' and hasattr(stave.event, 'tempo'):
            if element in stave.event.tempo:
                stave.event.tempo.remove(element)
                print(f"  Deleted tempo {getattr(element, 'id', '?')}")
        
        elif elem_type == 'countline' and hasattr(stave.event, 'countLine'):
            if element in stave.event.countLine:
                stave.event.countLine.remove(element)
                print(f"  Deleted count line {getattr(element, 'id', '?')}")
        
        elif elem_type == 'linebreak' and hasattr(stave.event, 'lineBreak'):
            if element in stave.event.lineBreak:
                stave.event.lineBreak.remove(element)
                print(f"  Deleted line break {getattr(element, 'id', '?')}")
    
    def _copy_selected(self) -> bool:
        """Copy selected elements to clipboard."""
        if not self.selected_elements:
            print("SelectionTool: No elements to copy")
            return False
        
        # Store a copy of the selection metadata
        # We store the element references and metadata - actual copying happens during paste
        self.clipboard = [
            {
                'element': item['element'],  # Keep reference to original
                'type': item['type'],
                'stave_idx': item['stave_idx']
            }
            for item in self.selected_elements
        ]
        
        print(f"SelectionTool: Copied {len(self.clipboard)} elements to clipboard")
        return True
    
    def _cut_selected(self) -> bool:
        """Cut selected elements (copy + delete)."""
        if self._copy_selected():
            return self._delete_selected()
        return False
    
    def _paste(self) -> bool:
        """Paste elements from clipboard at current cursor position."""
        if not self.clipboard:
            print("SelectionTool: Clipboard is empty")
            return False
        
        print(f"SelectionTool: Pasting {len(self.clipboard)} elements at cursor position")
        
        # Get paste time from current mouse cursor position
        # We only need the time, pitch stays the same
        _, paste_time = self.get_pitch_and_time(self._last_mouse_x, self._last_mouse_y)
        
        print(f"  Cursor time: {paste_time:.2f}")
        
        # Calculate time offset from original clipboard position
        # Find the minimum time in clipboard to use as reference (first note)
        notes_in_clipboard = [item for item in self.clipboard 
                            if hasattr(item['element'], 'time')]
        
        if not notes_in_clipboard:
            print("SelectionTool: No pasteable elements in clipboard (only notes supported currently)")
            return False
        
        min_time = min(item['element'].time for item in notes_in_clipboard)
        
        time_offset = paste_time - min_time
        pitch_offset = 0  # Keep original pitch values
        
        print(f"  Paste offset: time={time_offset:.2f}, pitch={pitch_offset}")
        
        # Clear current selection
        self.clear_selection()
        
        # Paste each element with offset
        pasted_count = 0
        for item in self.clipboard:
            element = item['element']
            elem_type = item['type']
            stave_idx = item['stave_idx']
            
            # Only paste notes for now (TODO: support other element types)
            if elem_type == 'note':
                pasted_element = self._paste_note(element, stave_idx, time_offset, pitch_offset)
                if pasted_element:
                    # Add to selection so user can see what was pasted
                    self.selected_elements.append({
                        'element': pasted_element,
                        'type': elem_type,
                        'stave_idx': stave_idx
                    })
                    pasted_count += 1
        
        print(f"SelectionTool: Pasted {pasted_count} elements")
        
        # Highlight the pasted elements
        if self.selected_elements:
            self._highlight_selection()
        
        # Mark as modified
        if hasattr(self.editor, 'on_modified') and self.editor.on_modified:
            self.editor.on_modified()
        
        # Refresh to show the changes
        self.editor.redraw_pianoroll()
        
        return pasted_count > 0
    
    def _paste_note(self, original_note: Any, stave_idx: int, time_offset: float, pitch_offset: int) -> Optional[Any]:
        """
        Paste a single note with offset.
        
        Returns:
            The newly created note, or None if paste failed
        """
        if stave_idx >= len(self.editor.score.stave):
            return None
        
        # Create new note with offset position
        # Note: score.new_note() automatically assigns a unique ID
        new_note = self.editor.score.new_note(
            stave_idx=stave_idx,
            time=original_note.time + time_offset,
            pitch=original_note.pitch + pitch_offset,
            hand=getattr(original_note, 'hand', '<'),
            duration=getattr(original_note, 'duration', 1.0),
            velocity=getattr(original_note, 'velocity', 80)
        )
        
        # Draw the new note
        self.editor._draw_single_note(stave_idx, new_note, draw_mode='note')
        
        print(f"  Pasted note: id={new_note.id}, pitch={new_note.pitch}, time={new_note.time:.2f} (original id={original_note.id})")
        
        return new_note
    
    # === Selection Movement ===
    
    def _move_selection_time(self, time_offset: float) -> bool:
        """
        Move selected notes in time by the specified offset.
        
        Args:
            time_offset: Time offset in ticks (positive = later, negative = earlier)
            
        Returns:
            True if selection was moved, False if no selection
        """
        if not self.selected_elements:
            print("SelectionTool: No elements to move")
            return False
        
        print(f"SelectionTool: Moving {len(self.selected_elements)} elements by time offset {time_offset:.2f}")
        
        # Move each selected element
        moved_count = 0
        for item in self.selected_elements:
            if item['type'] == 'note':
                note = item['element']
                # Update note time
                note.time += time_offset
                moved_count += 1
        
        if moved_count > 0:
            # Redraw to show the changes
            #self.clear_selection()  # Clear visual highlights
            self.editor.redraw_pianoroll()
            
            # Re-highlight at new positions
            self._highlight_selection()
            
            # Mark as modified
            if hasattr(self.editor, 'on_modified') and self.editor.on_modified:
                self.editor.on_modified()
            
            print(f"SelectionTool: Moved {moved_count} notes")
            return True
        
        return False
    
    def _transpose_selection(self, semitone_offset: int) -> bool:
        """
        Transpose selected notes by the specified number of semitones.
        
        Args:
            semitone_offset: Number of semitones to transpose (positive = up, negative = down)
            
        Returns:
            True if selection was transposed, False if no selection
        """
        if not self.selected_elements:
            print("SelectionTool: No elements to transpose")
            return False
        
        print(f"SelectionTool: Transposing {len(self.selected_elements)} elements by {semitone_offset} semitones")
        
        # Transpose each selected element
        transposed_count = 0
        for item in self.selected_elements:
            if item['type'] == 'note':
                note = item['element']
                # Update note pitch
                note.pitch += semitone_offset
                transposed_count += 1
        
        if transposed_count > 0:
            # Redraw to show the changes
            #self.clear_selection()  # Clear visual highlights
            self.editor.redraw_pianoroll()
            
            # Re-highlight at new positions
            self._highlight_selection()
            
            # Mark as modified
            if hasattr(self.editor, 'on_modified') and self.editor.on_modified:
                self.editor.on_modified()
            
            print(f"SelectionTool: Transposed {transposed_count} notes")
            return True
        
        return False
    
    # === Mouse Events (Hover) ===
    
    def on_mouse_move(self, x: float, y: float) -> bool:
        """Handle mouse movement (hover effects)."""
        # Track cursor position for paste operations
        self._last_mouse_x = x
        self._last_mouse_y = y
        
        # Call parent for drag detection
        if super().on_mouse_move(x, y):
            return True
        
        # No special hover behavior for now
        return False
