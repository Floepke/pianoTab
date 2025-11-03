#!/usr/bin/env python3
"""
Integration example: Piano Roll Editor in the main PianoTab application.
Shows how to integrate the piano roll into the existing GUI system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock

from editor.editor import PianoRollEditor
from utils.canvas import Canvas
from file.SCORE import SCORE


class IntegratedPianoRollDemo(App):
    """Demonstration of piano roll integration."""
    
    def build(self):
        # Main container
        root = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Title
        title = Label(
            text='PianoTab - Vertical Piano Roll Editor',
            size_hint_y=None,
            height=30,
            font_size=16
        )
        root.add_widget(title)
        
        # Piano roll canvas - much larger to accommodate 88 piano keys
        self.canvas = Canvas(
            width_mm=400.0,     # Wider for 88 keys + margins
            height_mm=300.0,    # Taller for multiple measures
            background_color=(0.98, 0.98, 0.98, 1.0),  # Light gray background
            border_color=(0.7, 0.7, 0.7, 1.0),
            border_width_px=1.0,
            scale_to_width=True  # Enable scrolling for tall content
        )
        
        # Load example score or create new one
        self.score = self._create_example_score()
        
        # Create piano roll editor
        self.piano_roll = PianoRollEditor(self.canvas, self.score)
        
        # Set canvas reference to piano roll editor for scroll step updates
        self.canvas.set_piano_roll_editor(self.piano_roll)
        
        # Bind canvas events
        self.canvas.bind(on_item_click=self.on_piano_roll_click)
        
        # Status label
        self.status_label = Label(
            text='Click on notes or piano keys to interact',
            size_hint_y=None,
            height=30,
            font_size=12
        )
        
        # Add to layout
        root.add_widget(self.canvas)
        root.add_widget(self.status_label)
        
        # Schedule initial render
        Clock.schedule_once(self.initial_render, 0.2)
        
        return root
    
    def _create_example_score(self) -> SCORE:
        """Create a simple example score for demonstration."""
        score = SCORE()
        
        # Create a treble stave
        score.new_stave('treble', 4)
        
        # Add a simple melody (Mary Had a Little Lamb) using key numbers instead of MIDI
        melody_notes = [
            (44, 0, 256),    # E4 (key 44)
            (42, 256, 256),  # D4 (key 42)
            (40, 512, 256),  # C4 (key 40)
            (42, 768, 256),  # D4 (key 42)
            (44, 1024, 256), # E4 (key 44)
            (44, 1280, 256), # E4 (key 44)
            (44, 1536, 512), # E4 (longer)
            (42, 2048, 256), # D4
            (42, 2304, 256), # D4
            (42, 2560, 512), # D4 (longer)
            (44, 3072, 256), # E4
            (47, 3328, 256), # G4 (key 47)
            (47, 3584, 512), # G4 (longer)
        ]
        
        for key_num, time, duration in melody_notes:
            pitch = key_num + 20  # Convert key number to MIDI pitch
            score.new_note(
                stave_idx=0,
                time=time,
                pitch=pitch,
                duration=duration,
                hand='>'
            )
        
        # Add some bass notes
        bass_notes = [
            (28, 0, 1024),    # C3 (key 28)
            (33, 1024, 1024), # F3 (key 33) 
            (28, 2048, 1024), # C3 (key 28)
            (35, 3072, 1024), # G3 (key 35)
        ]
        
        for key_num, time, duration in bass_notes:
            pitch = key_num + 20  # Convert key number to MIDI pitch
            score.new_note(
                stave_idx=0,
                time=time,
                pitch=pitch,
                duration=duration,
                hand='<'
            )
        
        return score
    
    def initial_render(self, dt):
        """Render the piano roll after the app has fully loaded."""
        try:
            self.piano_roll.render()
            self.status_label.text = f'Piano roll rendered: {len(self.score.stave[0].event.note)} notes'
        except Exception as e:
            self.status_label.text = f'Render error: {e}'
            print(f"Render error: {e}")
    
    def on_piano_roll_click(self, canvas_widget, item_id, touch, pos_mm):
        """Handle piano roll interactions."""
        try:
            # Let the piano roll handle the interaction
            handled = self.piano_roll.on_item_click(item_id, pos_mm)
            
            if handled:
                # Show feedback for successful interactions
                if self.piano_roll.selected_notes:
                    note = self.piano_roll.selected_notes[0]
                    key_number = note.pitch - 20
                    self.status_label.text = f'Selected note: Key {key_number}, Time {note.time:.0f} ticks'
                else:
                    self.status_label.text = 'Piano key clicked'
            else:
                # Handle empty area clicks
                if item_id is None:
                    key_number = self.piano_roll.x_to_key_number(pos_mm[0])
                    time_ticks = self.piano_roll.y_to_ticks(pos_mm[1])
                    
                    if (1 <= key_number <= 88 and time_ticks >= 0):
                        self.status_label.text = f'Empty area: Key {key_number}, Time {time_ticks:.0f} ticks (click to add note)'
                    else:
                        self.status_label.text = f'Clicked at position: {pos_mm}'
                        
        except Exception as e:
            self.status_label.text = f'Click error: {e}'
            print(f"Click error: {e}")


if __name__ == '__main__':
    IntegratedPianoRollDemo().run()