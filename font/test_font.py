#!/usr/bin/env python3
"""
Test the embedded font system.
This script creates a simple Kivy app to verify the font loads and displays correctly.
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from font import load_embedded_font, apply_default_font, FONT_NAME, cleanup_font

class FontTestApp(App):
    def build(self):
        # Load and apply font
        load_embedded_font()
        apply_default_font()
        
        # Create test UI
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        # Test default font (should use FiraCode)
        layout.add_widget(Label(
            text=f'Default Font Test\nThis should be {FONT_NAME}',
            font_size='20sp',
            halign='center'
        ))
        
        # Test explicit font_name
        layout.add_widget(Label(
            text=f'Explicit {FONT_NAME}\nWith various characters: 0O1l|',
            font_size='24sp',
            font_name=FONT_NAME,
            halign='center'
        ))
        
        # Test code-like content
        layout.add_widget(Label(
            text='Code Sample:\ndef hello():\n    print("FiraCode!")\n    return 123 != 456',
            font_size='18sp',
            halign='left',
            markup=False
        ))
        
        return layout
    
    def on_stop(self):
        cleanup_font()

if __name__ == '__main__':
    print("Starting font test app...")
    app = FontTestApp()
    app.run()
    print("Font test app closed.")
