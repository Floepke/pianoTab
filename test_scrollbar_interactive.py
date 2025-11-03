#!/usr/bin/env python3
"""
Comprehensive scrollbar test with user interaction instructions.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from utils.canvas import Canvas


class ScrollbarInteractiveTest(App):
    def build(self):
        main_layout = BoxLayout(orientation='vertical', padding=5, spacing=5)
        
        # Instructions
        instructions = Label(
            text='Custom Scrollbar Test Instructions:\n' +
                 '• Mouse wheel to scroll up/down\n' +
                 '• Click and drag the gray scrollbar thumb\n' +
                 '• Click on scrollbar track to jump\n' +
                 '• Hover over thumb to see color change\n' +
                 '• Scrollbar should be 40px wide (2x sash width)',
            size_hint=(1, None), height=100, halign='left', valign='top'
        )
        main_layout.add_widget(instructions)
        
        # Control buttons
        controls = BoxLayout(size_hint=(1, None), height=40, spacing=10)
        
        toggle_mode_btn = Button(text='Toggle Scale Mode', size_hint=(None, 1), width=150)
        toggle_mode_btn.bind(on_release=self.toggle_scale_mode)
        controls.add_widget(toggle_mode_btn)
        
        reset_scroll_btn = Button(text='Reset Scroll', size_hint=(None, 1), width=120)
        reset_scroll_btn.bind(on_release=self.reset_scroll)
        controls.add_widget(reset_scroll_btn)
        
        status_label = Label(text='Scale-to-width: ON, Scrollbar: VISIBLE', halign='left')
        controls.add_widget(status_label)
        self.status_label = status_label
        
        main_layout.add_widget(controls)
        
        # Create tall canvas
        self.canvas = Canvas(
            width_mm=180.0,
            height_mm=800.0,  # Very tall content
            scale_to_width=True,
            background_color=(1, 1, 1, 1),
            border_color=(0, 0, 0, 1),
            border_width_px=2
        )
        
        # Add rich test content
        self.create_test_content()
        
        main_layout.add_widget(self.canvas)
        return main_layout
    
    def create_test_content(self):
        """Create comprehensive test content to verify scrolling."""
        
        # Grid lines every 25mm for position reference
        for y in range(0, 800, 25):
            color = "#e0e0e0" if y % 100 != 0 else "#cccccc"
            self.canvas.add_line(0, y, 180, y, stroke_color=color, stroke_width_mm=0.3)
            
        # Position markers every 100mm
        for y in range(0, 800, 100):
            self.canvas.add_text(f"{y}mm", 5, y+3, font_size_pt=10, color="#888888")
            self.canvas.add_rectangle(170, y, 180, y+15, fill=True, fill_color="#dddddd")
        
        # Colorful test sections
        sections = [
            {"y": 50, "color": "#ff6b6b", "title": "Red Section"},
            {"y": 150, "color": "#4ecdc4", "title": "Teal Section"},
            {"y": 250, "color": "#45b7d1", "title": "Blue Section"},
            {"y": 350, "color": "#96ceb4", "title": "Green Section"},
            {"y": 450, "color": "#ffeaa7", "title": "Yellow Section"},
            {"y": 550, "color": "#dda0dd", "title": "Purple Section"},
            {"y": 650, "color": "#98d8c8", "title": "Mint Section"},
            {"y": 750, "color": "#fab1a0", "title": "Orange Section"}
        ]
        
        for section in sections:
            y = section["y"]
            color = section["color"]
            title = section["title"]
            
            # Main colored rectangle
            self.canvas.add_rectangle(20, y, 160, y+80, 
                                    fill=True, fill_color=color,
                                    outline=True, outline_color="#333333", 
                                    outline_width_mm=0.5)
            
            # Title text
            self.canvas.add_text(title, 90, y+45, font_size_pt=16, 
                               color="#ffffff", anchor="center")
            
            # Small detail rectangles
            for i in range(3):
                detail_x = 30 + i * 40
                self.canvas.add_rectangle(detail_x, y+10, detail_x+25, y+25,
                                        fill=True, fill_color="#ffffff",
                                        outline=True, outline_color="#000000")
                self.canvas.add_text(f"{i+1}", detail_x+12.5, y+17.5, 
                                   font_size_pt=12, color="#000000", anchor="center")
        
        # Bottom marker
        self.canvas.add_rectangle(10, 780, 170, 795, 
                                fill=True, fill_color="#333333")
        self.canvas.add_text("END OF CONTENT", 90, 787.5, font_size_pt=14, 
                           color="#ffffff", anchor="center")
        
        print(f"✓ Created test content: {self.canvas.width_mm}mm x {self.canvas.height_mm}mm")
        print(f"  Scrollbar should be visible and functional")
    
    def toggle_scale_mode(self, button):
        """Toggle between scale-to-width and keep-aspect modes."""
        self.canvas.set_scale_to_width(not self.canvas.scale_to_width)
        mode = "ON" if self.canvas.scale_to_width else "OFF"
        scrollbar = "VISIBLE" if self.canvas.scale_to_width else "HIDDEN"
        self.status_label.text = f'Scale-to-width: {mode}, Scrollbar: {scrollbar}'
        print(f"Switched to scale-to-width: {mode}")
    
    def reset_scroll(self, button):
        """Reset scroll position to top."""
        self.canvas._scroll_px = 0.0
        self.canvas._redraw_all()
        self.canvas._update_border()
        if hasattr(self.canvas, 'custom_scrollbar'):
            self.canvas.custom_scrollbar.update_layout()
        print("Reset scroll to top")


if __name__ == '__main__':
    print("Starting Interactive Scrollbar Test...")
    print("Look for a gray scrollbar on the right side (40px wide)")
    ScrollbarInteractiveTest().run()