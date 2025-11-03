#!/usr/bin/env python3
"""
Test script for the vertical piano roll editor.
Creates a simple Kivy app to demonstrate the piano roll functionality.
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock

from editor.editor import PianoRollEditor
from utils.canvas import Canvas
from file.SCORE import SCORE


class PianoRollTestApp(App):
    def build(self):
        # Main layout
        root = BoxLayout(orientation='vertical', spacing=5, padding=5)
        
        # Create canvas for piano roll
        self.canvas = Canvas(
            width_mm=200.0,
            height_mm=150.0,
            background_color=(0.95, 0.95, 0.95, 1.0),
            size_hint=(1, 0.9)
        )
        
        # Create score with some test notes
        self.score = SCORE()
        self.score.new_stave('treble', 4)  # Create a treble stave
        
        # Add some test notes (C major scale)
        c_major_pitches = [60, 62, 64, 65, 67, 69, 71, 72]  # C4 to C5
        for i, pitch in enumerate(c_major_pitches):
            self.score.new_note(
                stave_idx=0,
                time=i * 256.0,  # One beat apart
                pitch=pitch,
                duration=256.0,  # Quarter note duration
                hand='>'
            )
        
        # Add some harmony notes
        harmony_pitches = [48, 52, 55, 60]  # Lower octave chord
        for i, pitch in enumerate(harmony_pitches):
            self.score.new_note(
                stave_idx=0,
                time=i * 512.0,  # Two beats apart
                pitch=pitch,
                duration=512.0,  # Half note duration
                hand='<'
            )
        
        # Create piano roll editor
        self.piano_roll = PianoRollEditor(self.canvas, self.score)
        
        # Set canvas reference to piano roll editor for scroll step updates
        self.canvas.set_piano_roll_editor(self.piano_roll)
        
        # Bind canvas click events
        self.canvas.bind(on_item_click=self.on_canvas_click)
        
        # Control buttons
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=5)
        
        zoom_in_btn = Button(text='Zoom In', size_hint_x=0.2)
        zoom_in_btn.bind(on_press=lambda x: self.piano_roll.zoom_in())
        
        zoom_out_btn = Button(text='Zoom Out', size_hint_x=0.2)
        zoom_out_btn.bind(on_press=lambda x: self.piano_roll.zoom_out())
        
        render_btn = Button(text='Re-render', size_hint_x=0.2)
        render_btn.bind(on_press=lambda x: self.piano_roll.render())
        
        clear_btn = Button(text='Clear Selection', size_hint_x=0.2)
        clear_btn.bind(on_press=lambda x: setattr(self.piano_roll, 'selected_notes', []))
        
        delete_btn = Button(text='Delete Selected', size_hint_x=0.2)
        delete_btn.bind(on_press=lambda x: self.piano_roll.delete_selected_notes())
        
        button_layout.add_widget(zoom_in_btn)
        button_layout.add_widget(zoom_out_btn)
        button_layout.add_widget(render_btn)
        button_layout.add_widget(clear_btn)
        button_layout.add_widget(delete_btn)
        
        # Add widgets to root
        root.add_widget(self.canvas)
        root.add_widget(button_layout)
        
        # Initial render
        Clock.schedule_once(lambda dt: self.piano_roll.render(), 0.1)
        
        return root
    
    def on_canvas_click(self, canvas_widget, item_id, touch, pos_mm):
        """Handle canvas clicks."""
        print(f"Canvas click: item_id={item_id}, pos={pos_mm}")
        
        # Let the piano roll handle the click
        handled = self.piano_roll.on_item_click(item_id, pos_mm)
        
        if not handled and item_id is None:
            # Empty area clicked - could add note here
            pitch = self.piano_roll.get_pitch_at_x(pos_mm[0])
            time = self.piano_roll.get_time_at_y(pos_mm[1])
            
            if pitch >= self.piano_roll.min_pitch and pitch <= self.piano_roll.max_pitch:
                print(f"Empty area clicked: would add note at pitch={pitch}, time={time:.2f}")
                # Uncomment to actually add notes:
                # self.piano_roll.add_note_at_position(pitch, time)


if __name__ == '__main__':
    PianoRollTestApp().run()