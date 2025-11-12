"""
Selection Manager - Universal selection functionality across all tools.

Provides shift-based selection rectangle drawing, element selection,
and selection manipulation (copy, cut, paste, delete, move, transpose).
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, List, Dict, Any, Tuple
from kivy.core.window import Window
from gui.colors import ACCENT_COLOR_HEX

if TYPE_CHECKING:
    from editor.editor import Editor


class SelectionManager:
    """
    Manages element selection independently of the active tool.
    
    Activated by holding Shift key in any tool mode.
    """
    
    def __init__(self, editor: Editor):
        self.editor = editor
        
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
        
        # Clipboard
        self.clipboard: List[Dict[str, Any]] = []
        
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
        
        # If we're currently drawing a rectangle, mark that shift was released
        # but don't stop the drawing - wait for mouse release
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
        
        If Shift is held, start drawing selection rectangle.
        
        Returns:
            True if selection rectangle started (consume event), False otherwise
        """
        # Check if shift is actually held using Window modifiers (more reliable than tracking key events)
        shift_held = 'shift' in Window.modifiers
                
        if shift_held:
            # Start selection rectangle
            self.rect_start = (x, y)
            self.is_drawing_rect = True
            self.shift_was_released_during_drag = False
            
            # Clear any previous selection
            self.clear_selection()

            self.editor.canvas.delete_by_tag('cursor')
            
            return True  # Consume event - don't let tool handle it
        
        return False  # Let tool handle the click
    
    def on_drag(self, x: float, y: float, start_x: float, start_y: float) -> bool:
        """
        Called during mouse drag.
        
        If drawing selection rectangle, update it.
        
        Returns:
            True if handling selection drag (consume event), False otherwise
        """
        if self.is_drawing_rect and self.rect_start is not None:
            # Update selection rectangle
            self._draw_selection_rect(self.rect_start[0], self.rect_start[1], x, y)
            return True  # Consume event
        
        return False  # Let tool handle the drag
    
    def on_left_release(self, x: float, y: float) -> bool:
        """
        Called when left mouse button is released.
        
        If drawing selection rectangle, finalize selection.
        
        Returns:
            True if finishing selection (consume event), False otherwise
        """
        if self.is_drawing_rect and self.rect_start is not None:
            start_x, start_y = self.rect_start
            
            # Check if it's just a click (no drag) - clear selection
            distance = ((x - start_x)**2 + (y - start_y)**2) ** 0.5
            if distance < 3.0:  # 3mm threshold
                self.clear_selection()
            else:
                # Finalize selection
                self._finalize_selection(start_x, start_y, x, y)
            
            # Clean up
            self._clear_selection_rect()
            self.rect_start = None
            self.is_drawing_rect = False
            self.shift_was_released_during_drag = False
            
            return True  # Consume event
        
        return False  # Let tool handle the release
    
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
                fill=False,  # Light blue transparent
                outline=True,
                outline_color=ACCENT_COLOR_HEX,  # Blue outline (solid, fully opaque)
                outline_width_mm=0.25,  # Thicker so it's visible
                tags={'selection_rect'}
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
        self.editor.canvas.delete_by_tag('selection_rect')
    
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
            except Exception as e:
                print(f"SelectionManager: Error highlighting selection: {e}")
                import traceback
                traceback.print_exc()
    
    def _find_elements_in_rect(self, x1: float, y1: float, x2: float, y2: float) -> List[Dict[str, Any]]:
        """Find all elements within selection rectangle by checking their positions."""
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
    
    def on_key_press(self, key: str, x: float, y: float) -> bool:
        """
        Handle keyboard shortcuts for selection operations.
        
        Returns:
            True if key was handled, False otherwise
        """
        if key == 'delete' or key == 'backspace':
            if self.selected_elements:
                return self._delete_selected()
        
        elif key == 'c' or key == 'ctrl+c':
            if self.selected_elements:
                return self._copy_selected()
        
        elif key == 'x' or key == 'ctrl+x':
            if self.selected_elements:
                return self._cut_selected()
        
        elif key == 'v' or key == 'ctrl+v':
            if self.clipboard:
                return self._paste()
        
        elif key == 'escape':
            if self.selected_elements:
                self.clear_selection()
                return True
        
        elif key == 'up':
            if self.selected_elements:
                return self._move_selection_time(-self.editor.get_grid_step_ticks())
        
        elif key == 'down':
            if self.selected_elements:
                return self._move_selection_time(self.editor.get_grid_step_ticks())
        
        elif key == 'left':
            if self.selected_elements:
                return self._transpose_selection(-1)
        
        elif key == 'right':
            if self.selected_elements:
                return self._transpose_selection(1)
        
        elif key == '[' or key == 'bracketleft':
            if self.selected_elements:
                return self._assign_selection_hand('<')  # Left hand
        
        elif key == ']' or key == 'bracketright':
            if self.selected_elements:
                return self._assign_selection_hand('>')  # Right hand
        
        return False  # Let other handlers process the key
    
    # === Clipboard Operations ===
    
    def _copy_selected(self) -> bool:
        """Copy selected elements to clipboard (creates deep copy of note data)."""
        self.clipboard = []
        
        for item in self.selected_elements:
            if item['type'] == 'note':
                # Create a snapshot of the note's current state
                original = item['element']
                self.clipboard.append({
                    'type': 'note',
                    'stave_idx': item['stave_idx'],
                    # Store the actual data values, not references
                    'data': {
                        'time': original.time,
                        'pitch': original.pitch,
                        'hand': original.hand,
                        'duration': original.duration,
                        'velocity': original.velocity,
                    }
                })
        
        print(f"SelectionManager: Copied {len(self.clipboard)} elements to clipboard (snapshot)")
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
        if not self.clipboard:
            print("SelectionManager: Clipboard is empty")
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
        
        # Calculate time offset from the copied data (not current selection)
        notes_in_clipboard = [item for item in self.clipboard if item['type'] == 'note']
        
        if not notes_in_clipboard:
            print("SelectionManager: No pasteable elements in clipboard")
            return False
        
        min_time = min(item['data']['time'] for item in notes_in_clipboard)
        time_offset = paste_time - min_time
        
        print(f"SelectionManager: Pasting {len(self.clipboard)} elements at cursor position")
        
        # Clear current selection
        self.clear_selection()
        
        # Paste each element using the stored snapshot data
        for item in self.clipboard:
            if item['type'] == 'note':
                data = item['data']
                new_note = self.editor.score.new_note(
                    stave_idx=item['stave_idx'],
                    time=data['time'] + time_offset,
                    pitch=data['pitch'],  # Use original copied pitch
                    hand=data['hand'],
                    duration=data['duration'],
                    velocity=data['velocity']
                )
                # Add to selection
                self.selected_elements.append({
                    'element': new_note,
                    'type': 'note',
                    'stave_idx': item['stave_idx']
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
        """Move selected notes in time."""
        for item in self.selected_elements:
            if item['type'] == 'note':
                item['element'].time += time_offset
        
        self.editor.redraw_pianoroll()
        self._highlight_selection()
        
        if hasattr(self.editor, 'on_modified') and self.editor.on_modified:
            self.editor.on_modified()
        
        return True
    
    def _transpose_selection(self, semitone_offset: int) -> bool:
        """Transpose selected notes by semitones."""
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
