"""
Tempo Tool - Add, edit, and remove tempo markings.
"""

from editor.tool.base_tool import BaseTool
from typing import Optional, Tuple, Callable


class TempoTool(BaseTool):
    """Tool for adding and editing tempo markings."""
    
    @property
    def name(self) -> str:
        return "Tempo"
    
    @property
    def cursor(self) -> str:
        return 'crosshair'
    
    def on_activate(self):
        """Called when this tool becomes active."""
        super().on_activate()
        # TODO: Initialize tool-specific state
        pass
    
    def on_deactivate(self):
        """Called when switching away from this tool."""
        super().on_deactivate()
        # TODO: Clean up tool-specific state
        pass
    
    def on_mouse_move(self, x: float, y: float) -> bool:
        """Handle mouse movement (hover, no buttons pressed)."""
        # Call parent's drag detection first
        if super().on_mouse_move(x, y):
            return True  # Parent is handling drag - stop here
        
        # TODO: Show hover preview (only when not dragging)
        return False
    
    def on_left_press(self, x: float, y: float) -> bool:
        """
        Called when left mouse button is pressed down.
        
        Used for starting tempo creation or editing existing tempo markings.
        """
        super().on_left_press(x, y)
        # For tempo, we handle everything on click (no drag editing)
        return False

    def _get_tempo_at_position(self, x: float, y: float) -> Tuple[Optional[object], Optional[int]]:
        """Custom hit test for tempo markers based on where they are drawn.

        Returns (tempo, stave_idx) if a tempo marker rectangle contains (x, y), else (None, None).
        """
        if not self.score:
            return (None, None)

        # Use the currently rendered stave index
        stave_idx = self.editor.score.fileSettings.get_rendered_stave_index(
            num_staves=len(self.editor.score.stave)
        ) if (self.editor.score and hasattr(self.editor.score, 'fileSettings')) else 0

        if stave_idx is None or stave_idx < 0 or stave_idx >= len(self.editor.score.stave):
            return (None, None)

        stave = self.editor.score.stave[stave_idx]
        if not hasattr(stave.event, 'tempo'):
            return (None, None)

        # Recreate the same hitbox used in drawing
        x1_base = float(self.editor.editor_margin) + float(self.editor.stave_width) + 5.0
        x2_base = float(self.editor.editor_margin) + float(self.editor.stave_width) + 10.0

        # Expand hitbox for easier clicking
        x1_pad = x1_base - 4.0
        x2_pad = x2_base + 12.0

        for tempo in stave.event.tempo:
            y_line = self.editor.time_to_y(tempo.time)
            y1 = y_line
            y2 = y_line + 10.0

            min_x, max_x = (x1_pad, x2_pad) if x1_pad <= x2_pad else (x2_pad, x1_pad)
            min_y, max_y = (y1, y2) if y1 <= y2 else (y2, y1)

            if (min_x <= x <= max_x) and (min_y <= y <= max_y):
                return (tempo, stave_idx)

        return (None, None)

    def get_element_at_position(self, x: float, y: float, element_types=None):
        """Override to use tempo-specific rectangle detection for tempos.

        Falls back to BaseTool for other element types.
        """
        if element_types is not None and element_types == ['tempo']:
            tempo, stave_idx = self._get_tempo_at_position(x, y)
            if tempo is not None:
                return (tempo, 'tempo', stave_idx)
            return (None, None, None)

        return super().get_element_at_position(x, y, element_types)
    
    def on_left_click(self, x: float, y: float) -> bool:
        """Called when left mouse button is clicked (pressed and released without dragging).

        Behavior:
        - Click on an existing tempo marker: prompt for BPM and update it.
        - Click on empty space: prompt for BPM and add a new tempo marker at the clicked (snapped) time.
        """
        # Clear any existing cursor drawing
        self.editor.canvas.delete_by_tag('cursor')

        # Determine snapped time from Y
        time = self.get_snapped_time_from_y(y)

        # Clamp time to valid range
        score_length = self.editor._get_score_length_in_ticks()
        if time < 0:
            time = 0.0
        if time > score_length:
            time = float(score_length)

        # Check if we clicked on an existing tempo
        element, elem_type, stave_idx = self.get_element_at_position(x, y, element_types=['tempo'])

        if element and elem_type == 'tempo':
            # Edit existing tempo BPM via prompt (do not change time here)
            def _apply_bpm(new_bpm: int):
                try:
                    element.bpm = int(new_bpm)
                except Exception:
                    return
                # Keep tempos sorted by time for consistency
                if stave_idx is not None and 0 <= stave_idx < len(self.editor.score.stave):
                    try:
                        self.editor.score.stave[stave_idx].event.tempo.sort(key=lambda t: t.time)
                    except Exception:
                        pass
                self.editor.redraw_pianoroll()
                if hasattr(self.editor, 'on_modified') and self.editor.on_modified:
                    self.editor.on_modified()
                print(f"TempoTool: Set tempo {element.id} BPM to {element.bpm}")

            self._open_bpm_prompt(initial_bpm=getattr(element, 'bpm', 120), on_submit=_apply_bpm)
            return True

        # No tempo clicked: create a new one at this time
        # Choose stave: use currently rendered stave index
        stave_idx = self.editor.score.fileSettings.get_rendered_stave_index(
            num_staves=len(self.editor.score.stave)
        ) if (self.editor.score and hasattr(self.editor.score, 'fileSettings')) else 0

        # Create new tempo at snapped time after prompting for BPM
        def _create_bpm(new_bpm: int):
            try:
                bpm_val = int(new_bpm)
            except Exception:
                bpm_val = 120
            new_tempo = self.editor.score.new_tempo(
                stave_idx=stave_idx,
                time=float(time),
                bpm=bpm_val,
            )
            try:
                self.editor.score.stave[stave_idx].event.tempo.sort(key=lambda t: t.time)
            except Exception:
                pass
            self.editor.redraw_pianoroll()
            if hasattr(self.editor, 'on_modified') and self.editor.on_modified:
                self.editor.on_modified()
            print(f"TempoTool: Added tempo {new_tempo.id} at t={time} bpm={new_tempo.bpm}")

        self._open_bpm_prompt(initial_bpm=120, on_submit=_create_bpm)
        return True
    
    def on_left_unpress(self, x: float, y: float) -> bool:
        """Called when left mouse button is released without having dragged."""
        # TODO: Finalize tempo creation on click (no drag)
        return False
    
    def on_left_release(self, x: float, y: float) -> bool:
        """Called when left mouse button is released (after drag or click)."""
        # Let parent handle the drag_end vs unpress logic
        result = super().on_left_release(x, y)
        return result
    
    def on_right_click(self, x: float, y: float) -> bool:
        """Called when right mouse button is clicked (without drag)."""
        # Delete any existing cursor drawing
        self.editor.canvas.delete_by_tag('cursor')

        # Check if we clicked on an existing tempo
        element, elem_type, stave_idx = self.get_element_at_position(x, y, element_types=['tempo'])

        if element and elem_type == 'tempo':
            # Remove from SCORE
            if stave_idx is not None and 0 <= stave_idx < len(self.editor.score.stave):
                stave = self.editor.score.stave[stave_idx]
                if hasattr(stave.event, 'tempo') and element in stave.event.tempo:
                    stave.event.tempo.remove(element)

                    # Delete the visual representation
                    self.editor.canvas.delete_by_tag(str(element.id))

                    # Mark as modified and redraw
                    if hasattr(self.editor, 'on_modified') and self.editor.on_modified:
                        self.editor.on_modified()
                    self.editor.redraw_pianoroll()

                    print(f"TempoTool: Deleted tempo {element.id}")
                    return True

            print(f"TempoTool: Failed to delete tempo {getattr(element, 'id', 'unknown')}")
            return False

        # No tempo found at click position
        print(f"TempoTool: No tempo found at ({x}, {y})")
        return False
    
    def on_double_click(self, x: float, y: float) -> bool:
        """Called when mouse is double-clicked."""
        # TODO: Edit existing tempo on double-click (open tempo editing dialog)
        print(f"TempoTool: Edit tempo at ({x}, {y})")
        return True
    
    def on_drag_start(self, x: float, y: float, start_x: float, start_y: float) -> bool:
        """Called when drag first starts (mouse moved beyond threshold with button down)."""
        # TODO: Initialize drag operation
        return False
    
    def on_drag(self, x: float, y: float, start_x: float, start_y: float) -> bool:
        """Called continuously while dragging WITH button pressed."""
        # TODO: Update drag preview
        return False
    
    def on_drag_end(self, x: float, y: float) -> bool:
        """Called when drag finishes (button released after dragging)."""
        # TODO: Finalize drag operation
        return False

    # ---------- Simple BPM prompt ----------
    def _open_bpm_prompt(self, initial_bpm: int, on_submit: Callable[[int], None]):
        """Open a simple modal prompt to enter an integer BPM.

        Args:
            initial_bpm: Suggested starting value in the input field.
            on_submit: Callback receiving the validated BPM int when OK is pressed.
        """
        try:
            from kivy.uix.modalview import ModalView
            from kivy.uix.boxlayout import BoxLayout
            from kivy.uix.label import Label
            from kivy.uix.textinput import TextInput
            from kivy.uix.button import Button
            from kivy.metrics import dp

            popup = ModalView(size_hint=(None, None), size=(dp(360), dp(180)), auto_dismiss=False)
            root = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))

            title = Label(text='Set Tempo (BPM)', size_hint_y=None, height=dp(28))
            input_field = TextInput(text=str(int(initial_bpm)), multiline=False, input_filter='int',
                                    size_hint_y=None, height=dp(36))

            btn_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(44), spacing=dp(8))
            btn_cancel = Button(text='Cancel')
            btn_ok = Button(text='OK')

            def close_popup(*_):
                try:
                    popup.dismiss()
                except Exception:
                    pass

            def submit_and_close(*_):
                txt = (input_field.text or '').strip()
                try:
                    val = int(txt)
                except Exception:
                    val = initial_bpm
                # clamp to a sensible range
                if val < 20:
                    val = 20
                if val > 300:
                    val = 300
                try:
                    on_submit(val)
                finally:
                    close_popup()

            btn_cancel.bind(on_release=close_popup)
            btn_ok.bind(on_release=submit_and_close)

            btn_row.add_widget(btn_cancel)
            btn_row.add_widget(btn_ok)
            root.add_widget(title)
            root.add_widget(input_field)
            root.add_widget(btn_row)
            popup.add_widget(root)
            popup.open()
        except Exception as e:
            # Fallback: console log if UI fails
            print(f"TempoTool: Failed to open BPM prompt: {e}")
