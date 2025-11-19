"""
Selection Manager - Universal selection functionality across all tools.

Provides shift-based selection rectangle drawing, element selection,
and selection manipulation (copy, cut, paste, delete, move, transpose).
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, List, Dict, Any, Tuple
from kivy.core.window import Window
from kivy.clock import Clock
from gui.colors import ACCENT_COLOR_HEX
from utils import clipboard  # Musical element clipboard
from utils.keyboard import matches_shortcut  # Cross-platform key matching
from utils.CONSTANTS import OPERATOR_TRESHOLD
from utils.operator import OperatorThreshold

if TYPE_CHECKING:
    from editor.editor import Editor


class SelectionManager:
    """
    Manages element selection independently of the active tool.
    
    Activated by holding Shift key in any tool mode.
    """
    
    def __init__(self, editor: Editor):
        self.editor = editor
        
        # Threshold-based comparison operator for time values
        self._time_op = OperatorThreshold(threshold=OPERATOR_TRESHOLD)
        
        # Selection state
        self.selected_elements: List[Dict[str, Any]] = []
        # Each item: {'element': obj, 'type': str, 'stave_idx': int}
        
        # Selection rectangle tracking
        self.is_drawing_rect: bool = False
        self.rect_start: Optional[Tuple[float, float]] = None
        self.rect_id: Optional[int] = None
        
        # Shift key state
        self.shift_pressed: bool = False
        self.shift_was_released_during_drag: bool = False
        
        # Independent mouse button tracking to work around Kivy/SDL2 bugs
        # We track button state ourselves and ignore spurious touch events
        self._left_button_is_down: bool = False
        self._right_button_is_down: bool = False
        
        # Track last drag position to detect spurious releases
        self._last_drag_pos: Optional[Tuple[float, float]] = None
        self._last_drag_time: float = 0.0
        
        # Mouse position tracking for paste
        self._last_mouse_x: float = 0.0
        self._last_mouse_y: float = 0.0
    
    # === Shift Key Handling ===
    
    def on_shift_press(self) -> bool:
        """Called when Shift key is pressed."""
        self.shift_pressed = True
        return False  # Don't consume event, let tools handle too
    
    def on_shift_release(self) -> bool:
        """Called when Shift key is released."""
        self.shift_pressed = False
        
        # If we're drawing, just mark that shift was released
        # Don't finalize yet - wait for mouse release
        if self.is_drawing_rect:
            self.shift_was_released_during_drag = True
        
        return False  # Don't consume event
    
    # === Mouse Event Handling ===
    
    def on_mouse_move(self, x: float, y: float) -> bool:
        """Track mouse position for paste and other operations."""
        self._last_mouse_x = x
        self._last_mouse_y = y
        return False  # Don't consume
    
    def on_left_press(self, x: float, y: float) -> bool:
        """
        Called when left mouse button is pressed.
        
        Returns:
            False - left button doesn't trigger selection rectangle anymore
        """
        # Track that left button is now down (independent tracking)
        print(f"DEBUG SelectionManager: on_left_press() setting _left_button_is_down = True")
        self._left_button_is_down = True
        self._last_drag_pos = (x, y)
        
        return False  # Let tool handle the click
    
    def on_right_press(self, x: float, y: float) -> bool:
        """
        Called when right mouse button is pressed.
        
        Tracks position for drag detection.
        
        Returns:
            False - actual selection starts on drag
        """
        print(f"DEBUG SelectionManager: on_right_press() setting _right_button_is_down = True")
        self._right_button_is_down = True
        self._last_drag_pos = (x, y)
        
        return False  # Don't consume - wait for drag
    
    def on_right_drag(self, x: float, y: float) -> bool:
        """
        Called during right mouse button drag.
        
        Start selection rectangle on first drag movement (10px threshold).
        
        Returns:
            True if handling selection rectangle
        """
        print(f"DEBUG SelectionManager: on_right_drag() _right_button_is_down={self._right_button_is_down}, is_drawing_rect={self.is_drawing_rect}")
        
        if not self._right_button_is_down:
            return False
        
        # Start selection rectangle on first drag (if not already drawing)
        if not self.is_drawing_rect:
            if self._last_drag_pos:
                # Check if we've moved at least 10 pixels from the start position
                start_x, start_y = self._last_drag_pos
                
                # Convert mm to pixels for accurate threshold
                canvas = self.editor.canvas
                start_px = canvas._mm_to_px_point(start_x, start_y)
                current_px = canvas._mm_to_px_point(x, y)
                
                dx = current_px[0] - start_px[0]
                dy = current_px[1] - start_px[1]
                distance_px = (dx**2 + dy**2) ** 0.5
                
                # Only start selection rectangle if moved more than 10 pixels
                if distance_px > 10:
                    self.rect_start = self._last_drag_pos
                    self.is_drawing_rect = True
                    self.shift_was_released_during_drag = False
                    
                    # Clear any previous selection
                    self.clear_selection()
                    self.editor.canvas.delete_by_tag('cursor')
                    
                    print(f"DEBUG SelectionManager: Right-drag selection rect started at {self.rect_start} (moved {distance_px:.1f}px)")
                else:
                    # Not enough movement yet, don't start rectangle
                    return False
        
        # Update selection rectangle
        if self.is_drawing_rect and self.rect_start is not None:
            self._draw_selection_rect(self.rect_start[0], self.rect_start[1], x, y)
            return True
        
        return False
    
    def on_left_drag(self, x: float, y: float) -> bool:
        """
        Called during left mouse button drag.
        
        Selection rectangle is now triggered by right mouse button only.
        
        Returns:
            False - selection rectangle not handled by left drag
        """
        print(f"DEBUG SelectionManager: on_left_drag() _left_button_is_down={self._left_button_is_down}, is_drawing_rect={self.is_drawing_rect}")
        
        # Track the last drag position and time
        from time import time
        self._last_drag_pos = (x, y)
        self._last_drag_time = time()
        
        # Left drag no longer handles selection rectangle
        return False
    
    def on_left_release(self, x: float, y: float) -> bool:
        """
        Called when left mouse button is released.
        
        Returns:
            False - left button doesn't finalize selection rectangle anymore
        """
        print(f"DEBUG SelectionManager: on_left_release() at ({x:.1f}, {y:.1f}), _left_button_is_down={self._left_button_is_down}")
        
        self._left_button_is_down = False
        self._last_drag_pos = None
        
        return False  # Let tool handle the release
    
    def on_right_release(self, x: float, y: float) -> bool:
        """
        Called when right mouse button is released.
        
        If drawing selection rectangle, finalize selection.
        
        Returns:
            True if finishing selection (consume event), False otherwise
        """
        print(f"DEBUG SelectionManager: on_right_release() at ({x:.1f}, {y:.1f}), _right_button_is_down={self._right_button_is_down}, is_drawing_rect={self.is_drawing_rect}")
        
        # Ignore release if button wasn't down
        if not self._right_button_is_down:
            print("DEBUG: Ignoring release (button not down)")
            return False
        
        # Process the release
        print(f"DEBUG: Processing right release, was_drawing={self.is_drawing_rect}")
        self._right_button_is_down = False
        was_drawing = self.is_drawing_rect
        self._last_drag_pos = None
        
        if was_drawing and self.rect_start is not None:
            start_x, start_y = self.rect_start
            
            # Finalize selection
            self._finalize_selection(start_x, start_y, x, y)
            
            # Clean up
            self._clear_selection_rect()
            self.rect_start = None
            self.is_drawing_rect = False
            self.shift_was_released_during_drag = False
            
            return True  # Consume event
        
        # No selection rectangle was drawn - let tool handle the click
        print("DEBUG: No selection rectangle, returning False to let tool handle click")
        return False  # Let tool handle the release (for click without drag)
    
    def on_scroll(self, x: float, y: float, scroll_x: float, scroll_y: float) -> bool:
        """
        Called during mouse scroll (if scroll is enabled).
        
        During selection rectangle drawing, scroll is disabled at canvas level,
        so this shouldn't be called. If it is called, just ignore it.
        
        Returns:
            False to allow normal scroll handling
        """
        # Nothing to do - scrolling is disabled during selection
        return False
    
    # === Selection Rectangle Drawing ===
    
    def _draw_selection_rect(self, x1: float, y1: float, x2: float, y2: float):
        """Draw or update the selection rectangle."""
        try:
            # Remove old rectangle
            if self.rect_id is not None:
                self.editor.canvas.delete(self.rect_id)
                        
            # Draw new rectangle (solid outline, no dash support for rectangles)
            self.rect_id = self.editor.canvas.add_rectangle(
                x1_mm=x1,
                y1_mm=y1,
                x2_mm=x2,
                y2_mm=y2,
                fill=True,
                fill_color=ACCENT_COLOR_HEX + "40",  # Light blue transparent
                outline=True,
                outline_color=ACCENT_COLOR_HEX,  # Blue outline (solid, fully opaque)
                outline_width_mm=0.25,  # Thicker so it's visible
                tags={'selectionrect'}
            )
            
        except Exception as e:
            print(f"SelectionManager: Failed to draw selection rectangle: {e}")
            import traceback
            traceback.print_exc()
    
    def _clear_selection_rect(self):
        """Remove the selection rectangle from canvas."""
        if self.rect_id is not None:
            self.editor.canvas.delete(self.rect_id)
            self.rect_id = None
        self.editor.canvas.delete_by_tag('selectionrect')
    
    # === Element Finding ===
    
    def _finalize_selection(self, x1: float, y1: float, x2: float, y2: float):
        """Find all elements within rectangle and select them."""
        try:
            self.selected_elements = self._find_elements_in_rect(x1, y1, x2, y2)
        except Exception as e:
            print(f"SelectionManager: Error finding elements: {e}")
            import traceback
            traceback.print_exc()
            self.selected_elements = []
                
        # Highlight selected elements
        if self.selected_elements:
            try:
                self._highlight_selection()
                
                # If in note mode and exactly one note selected, scroll property tree to it
                if (hasattr(self.editor, 'tool_manager') and 
                    self.editor.tool_manager.get_active_tool() == 'Note' and
                    len(self.selected_elements) == 1 and
                    self.selected_elements[0]['type'] == 'note'):
                    
                    # Get the note and stave index
                    note = self.selected_elements[0]['element']
                    stave_idx = self.selected_elements[0]['stave_idx']
                    
                    # Notify property tree to scroll to this note
                    if hasattr(self.editor, 'gui') and self.editor.gui:
                        property_tree = self.editor.gui.get_property_tree()
                        if property_tree and hasattr(property_tree, 'on_note_selected'):
                            property_tree.on_note_selected(stave_idx, note)
            except Exception as e:
                print(f"SelectionManager: Error highlighting selection: {e}")
                import traceback
                traceback.print_exc()
    
    def _find_elements_in_rect(self, x1: float, y1: float, x2: float, y2: float) -> List[Dict[str, Any]]:
        """Find all elements within selection rectangle by checking their positions.
        
        Only searches the currently rendered stave (from fileSettings.editorRenderedStave).
        """
        selected = []
        
        # Normalize rectangle
        left = min(x1, x2)
        right = max(x1, x2)
        top = min(y1, y2)
        bottom = max(y1, y2)
        
        print(f"  Selection rect: x=[{left:.1f}, {right:.1f}], y=[{top:.1f}, {bottom:.1f}]")
        
        # Get the currently rendered stave index
        stave_idx = self.editor.score.fileSettings.get_rendered_stave_index(
            num_staves=len(self.editor.score.stave)
        ) if (self.editor.score and hasattr(self.editor.score, 'fileSettings')) else 0
        
        # Only check the currently rendered stave
        stave = self.editor.score.stave[stave_idx]
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
        
        print(f"  Found {len(selected)} elements")
        return selected
    
    # === Selection Highlighting ===
    
    def _highlight_selection(self):
        """Draw visual highlight around selected elements."""
        try:
            # Clear old highlights
            self.editor.canvas.delete_by_tag('selection_highlight')
            
            for item in self.selected_elements:
                if item['type'] == 'note':
                    # Redraw note in 'selected' mode (uses accent color)
                    self.editor._draw_single_note(
                        item['stave_idx'], 
                        item['element'], 
                        draw_mode='selected'
                    )
        except Exception as e:
            print(f"SelectionManager: Error highlighting: {e}")
    
    def clear_selection(self):
        """Clear the current selection."""
        # Restore selected notes to normal drawing mode
        for item in self.selected_elements:
            if item['type'] == 'note':
                element = item['element']
                stave_idx = item['stave_idx']
                # Delete selected drawing
                self.editor.canvas.delete_by_tag(str(element.id))
                # Redraw in normal mode
                self.editor._draw_single_note(stave_idx, element, draw_mode='note')
        
        self.selected_elements = []
        self.editor.canvas.delete_by_tag('selection_highlight')
    
    # === Keyboard Shortcuts ===
    
    def on_key_press(self, key: str, x: float, y: float, modifiers: list = None) -> bool:
        """
        Handle keyboard shortcuts for selection operations.
        
        On macOS, both Ctrl and Cmd (meta) work for shortcuts with 'ctrl+' prefix.
        
        Args:
            key: The key that was pressed
            x: Current mouse x position in mm
            y: Current mouse y position in mm
            modifiers: List of modifier keys pressed (e.g., ['ctrl'], ['meta'])
        
        Returns:
            True if key was handled, False otherwise
        """
        if modifiers is None:
            modifiers = []
        
        # Check if a TextInput or other text widget has focus
        # If so, don't intercept C/X/V keys - let them handle text operations
        focused_widget = Window.focus
        
        # If a text input widget has focus, only handle non-text shortcuts
        if focused_widget is not None:
            from kivy.uix.textinput import TextInput
            if isinstance(focused_widget, TextInput):
                # Allow text widget to handle C/X/V for text operations
                # But we can still handle other shortcuts like Delete, Escape, arrows
                if matches_shortcut(key, modifiers, 'c', 'ctrl+c', 'x', 'ctrl+x', 'v', 'ctrl+v'):
                    return False  # Let TextInput handle it
        
        # Musical clipboard shortcuts (only when editor has focus)
        # matches_shortcut automatically handles macOS cmd/ctrl equivalence
        if matches_shortcut(key, modifiers, 'delete', 'backspace'):
            if self.selected_elements:
                return self._delete_selected()
        
        elif matches_shortcut(key, modifiers, 'c', 'ctrl+c'):
            if self.selected_elements:
                return self._copy_selected()
        
        elif matches_shortcut(key, modifiers, 'x', 'ctrl+x'):
            if self.selected_elements:
                return self._cut_selected()
        
        elif matches_shortcut(key, modifiers, 'v', 'ctrl+v'):
            if clipboard.has_data():
                return self._paste()
        
        elif matches_shortcut(key, modifiers, 'escape'):
            if self.selected_elements:
                self.clear_selection()
                return True
        
        elif matches_shortcut(key, modifiers, 'up'):
            if self.selected_elements:
                return self._move_selection_time(-self.editor.get_grid_step_ticks())
        
        elif matches_shortcut(key, modifiers, 'down'):
            if self.selected_elements:
                return self._move_selection_time(self.editor.get_grid_step_ticks())
        
        elif matches_shortcut(key, modifiers, 'left'):
            if self.selected_elements:
                return self._transpose_selection(-1)
        
        elif matches_shortcut(key, modifiers, 'right'):
            if self.selected_elements:
                return self._transpose_selection(1)
        
        elif matches_shortcut(key, modifiers, '[', 'bracketleft'):
            if self.selected_elements:
                return self._assign_selection_hand('<')  # Left hand
        
        elif matches_shortcut(key, modifiers, ']', 'bracketright'):
            if self.selected_elements:
                return self._assign_selection_hand('>')  # Right hand
        
        return False  # Let other handlers process the key
    
    # === Clipboard Operations ===
    
    def _copy_selected(self) -> bool:
        """Copy selected elements to clipboard (creates deep copy of note data)."""
        if not self.selected_elements:
            print("SelectionManager: No elements selected to copy")
            return False
        
        # Prepare clipboard data
        notes_data = []
        for item in self.selected_elements:
            if item['type'] == 'note':
                # Create a snapshot of the note's current state
                original = item['element']
                notes_data.append({
                    'stave_idx': item['stave_idx'],
                    'time': original.time,
                    'pitch': original.pitch,
                    'hand': original.hand,
                    'duration': original.duration,
                    'velocity': original.velocity,
                })
        
        # Store in musical clipboard (not text clipboard)
        clipboard.copy({
            'type': 'notes',
            'notes': notes_data
        })
        
        print(f"SelectionManager: Copied {len(notes_data)} notes to clipboard")
        return True
    
    def _cut_selected(self) -> bool:
        """Cut selected elements (copy + delete)."""
        if self._copy_selected():
            return self._delete_selected()
        return False
    
    def _delete_selected(self) -> bool:
        """Delete all selected elements."""
        
        for item in self.selected_elements:
            if item['type'] == 'note':
                stave = self.editor.score.stave[item['stave_idx']]
                if item['element'] in stave.event.note:
                    stave.event.note.remove(item['element'])
        
        self.clear_selection()
        
        if hasattr(self.editor, 'on_modified') and self.editor.on_modified:
            self.editor.on_modified()
        
        self.editor.redraw_pianoroll()
        return True
    
    def _paste(self) -> bool:
        """Paste elements from clipboard at current cursor position."""
        # Get data from musical clipboard
        clipboard_data = clipboard.paste()
        
        if not clipboard_data or clipboard_data.get('type') != 'notes':
            print("SelectionManager: Clipboard is empty or doesn't contain notes")
            return False
        
        notes_data = clipboard_data.get('notes', [])
        if not notes_data:
            print("SelectionManager: No notes in clipboard")
            return False
        
        # Get paste time from current mouse cursor position
        from editor.tool.base_tool import BaseTool
        # Create temporary tool instance just to use get_pitch_and_time
        temp_tool = type('TempTool', (BaseTool,), {
            'name': property(lambda self: 'Temp'),
            'cursor': property(lambda self: 'arrow'),
            'on_activate': lambda self: None,
            'on_deactivate': lambda self: None
        })(self.editor)
        
        _, paste_time = temp_tool.get_pitch_and_time(self._last_mouse_x, self._last_mouse_y)
        
        # Calculate time offset from the copied data
        min_time = min(note['time'] for note in notes_data)
        time_offset = paste_time - min_time
        
        print(f"SelectionManager: Pasting {len(notes_data)} notes at cursor position")
        
        # Clear current selection
        self.clear_selection()
        
        # Paste each note using the stored snapshot data
        for note_data in notes_data:
            new_note = self.editor.score.new_note(
                stave_idx=note_data['stave_idx'],
                time=note_data['time'] + time_offset,
                pitch=note_data['pitch'],
                hand=note_data['hand'],
                duration=note_data['duration'],
                velocity=note_data['velocity']
            )
            # Add to selection
            self.selected_elements.append({
                'element': new_note,
                'type': 'note',
                'stave_idx': note_data['stave_idx']
            })
        
        # Highlight pasted elements
        if self.selected_elements:
            self._highlight_selection()
        
        if hasattr(self.editor, 'on_modified') and self.editor.on_modified:
            self.editor.on_modified()
        
        self.editor.redraw_pianoroll()
        return True
    
    # === Selection Movement ===
    
    def _move_selection_time(self, time_offset: float) -> bool:
        """Move selected notes in time.
        
        Prevents moving notes before time 0 or beyond the score length.
        """
        if not self.selected_elements:
            return False
        
        # Find the earliest note start time and latest note end time in selection
        min_time = float('inf')
        max_time_end = float('-inf')
        
        for item in self.selected_elements:
            if item['type'] == 'note':
                note = item['element']
                min_time = min(min_time, note.time)
                max_time_end = max(max_time_end, note.time + note.duration)
        
        # If no notes found, nothing to do
        if min_time == float('inf'):
            return False
        
        # Calculate new boundaries after the move
        new_min_time = min_time + time_offset
        new_max_time_end = max_time_end + time_offset
        
        # Check if moving backward would go below zero (not equal to zero - that's valid)
        if time_offset < 0 and self._time_op.less(new_min_time, 0):
            print(f"SelectionManager: Cannot move selection - would go before time 0")
            return False
        
        # Check if moving forward would exceed score length
        if time_offset > 0:
            # Get total score length from all baseGrids
            score_length = self.editor.get_score_length_in_ticks()
            if self._time_op.greater(new_max_time_end, score_length):
                print(f"SelectionManager: Cannot move selection - would exceed score length ({score_length} ticks)")
                return False
        
        # All checks passed, perform the move
        for item in self.selected_elements:
            if item['type'] == 'note':
                item['element'].time += time_offset
        
        self.editor.redraw_pianoroll()
        self._highlight_selection()
        
        if hasattr(self.editor, 'on_modified') and self.editor.on_modified:
            self.editor.on_modified()
        
        return True
    
    def _transpose_selection(self, semitone_offset: int) -> bool:
        """Transpose selected notes by semitones.
        
        Prevents transposing notes outside the valid pitch range (1-88).
        """
        if not self.selected_elements:
            return False
        
        # First check if any note would go out of range
        for item in self.selected_elements:
            if item['type'] == 'note':
                new_pitch = item['element'].pitch + semitone_offset
                if new_pitch < 1:
                    print(f"SelectionManager: Cannot transpose - would go below pitch 1")
                    return False
                elif new_pitch > 88:
                    print(f"SelectionManager: Cannot transpose - would go above pitch 88")
                    return False
        
        # All checks passed, perform the transposition
        for item in self.selected_elements:
            if item['type'] == 'note':
                item['element'].pitch += semitone_offset
        
        self.editor.redraw_pianoroll()
        self._highlight_selection()
        
        if hasattr(self.editor, 'on_modified') and self.editor.on_modified:
            self.editor.on_modified()
        
        return True
    
    def _assign_selection_hand(self, hand: str) -> bool:
        """Assign hand to all selected notes.
        
        Args:
            hand: '<' for left hand, '>' for right hand
        """
        if not self.selected_elements:
            return False
        
        for item in self.selected_elements:
            if item['type'] == 'note':
                item['element'].hand = hand
        
        print(f"SelectionManager: Assigned {len(self.selected_elements)} notes to hand '{hand}'")
        
        self.editor.redraw_pianoroll()
        self._highlight_selection()
        
        if hasattr(self.editor, 'on_modified') and self.editor.on_modified:
            self.editor.on_modified()
        
        return True
