#!/usr/bin/env python3
"""
Test script for the custom scrollbar in Canvas widget.
Creates a tall canvas that should trigger the scrollbar.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from utils.canvas import Canvas


class ScrollbarTestApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Add title
        title = Label(text='Custom Scrollbar Test\nThis canvas should show a scrollbar when content is taller than viewport',
                     size_hint=(1, None), height=60, halign='center')
        layout.add_widget(title)
        
        # Create a Canvas with tall content to trigger scrollbar
        canvas = Canvas(
            width_mm=150.0,
            height_mm=600.0,  # Much taller than typical viewport
            scale_to_width=True,  # Enable scrollbar mode
            background_color=(1, 1, 1, 1),
            border_color=(0, 0, 0, 1)
        )
        
        # Add some test content to make scrolling visible
        self.add_test_content(canvas)
        
        layout.add_widget(canvas)
        return layout
    
    def add_test_content(self, canvas):
        """Add test content to the canvas to demonstrate scrolling."""
        
        # Add vertical lines every 50mm to show scroll position
        for y in range(0, 600, 50):
            canvas.add_line(0, y, 150, y, stroke_color="#cccccc", stroke_width_mm=0.5)
            canvas.add_text(f"{y}mm", 5, y+5, font_size_pt=12, color="#666666")
        
        # Add some colored rectangles
        colors = ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff", "#00ffff"]
        for i, color in enumerate(colors):
            y = i * 80 + 20
            canvas.add_rectangle(10, y, 140, y+60, fill=True, fill_color=color, 
                               outline=True, outline_color="#000000")
            canvas.add_text(f"Rectangle {i+1}", 75, y+30, font_size_pt=14, 
                           color="#ffffff", anchor="center")
        
        print("✓ Test content added to canvas")
        print(f"  Canvas size: {canvas.width_mm}mm x {canvas.height_mm}mm")
        print("  Expected scrollbar: YES (content height > viewport)")


if __name__ == '__main__':
    print("Testing Custom Scrollbar...")
    ScrollbarTestApp().run()