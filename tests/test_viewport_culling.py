#!/usr/bin/env python3
'''
Test script to verify viewport culling performance in Canvas widget.
Creates a long vertical piano roll with many measures and monitors redraw performance.
'''

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
import time


class ViewportCullingTest(BoxLayout):
    '''Test widget with a Canvas and performance stats.'''
    
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        
        # Import Canvas here to avoid circular imports
        from utils.canvas import Canvas
        
        # Stats label at top
        self.stats_label = Label(
            text='Initializing...',
            size_hint_y=None,
            height=40,
            font_size='14sp'
        )
        self.add_widget(self.stats_label)
        
        # Canvas with long content
        self.canvas_widget = Canvas(
            width_mm=210.0,
            height_mm=5000.0,  # Very long canvas (5 meters!)
            background_color=(1, 1, 1, 1),
            border_color=(0.5, 0.5, 0.5, 1),
            border_width_px=1.0,
            keep_aspect=True,
            scale_to_width=True
        )
        self.add_widget(self.canvas_widget)
        
        # Control buttons at bottom
        button_box = BoxLayout(size_hint_y=None, height=50, spacing=10, padding=10)
        
        add_10_btn = Button(text='Add 10 Measures')
        add_10_btn.bind(on_press=lambda x: self.add_measures(10))
        button_box.add_widget(add_10_btn)
        
        add_128_btn = Button(text='Add 128 Measures')
        add_128_btn.bind(on_press=lambda x: self.add_measures(128))
        button_box.add_widget(add_128_btn)
        
        clear_btn = Button(text='Clear All')
        clear_btn.bind(on_press=lambda x: self.clear_measures())
        button_box.add_widget(clear_btn)
        
        self.add_widget(button_box)
        
        # Track measure count and performance
        self.measure_count = 0
        self.last_redraw_time = 0
        
        # Schedule periodic stats update
        Clock.schedule_interval(self.update_stats, 0.5)
        
        # Add some initial measures
        Clock.schedule_once(lambda dt: self.add_measures(20), 0.5)
    
    def add_measures(self, count):
        '''Add piano roll measures to the canvas.'''
        start_time = time.time()
        
        measure_height_mm = 30.0  # 30mm per measure
        staff_lines = 5
        
        for i in range(count):
            y_offset_mm = self.measure_count * measure_height_mm
            
            # Draw 5 staff lines per measure
            for line_num in range(staff_lines):
                line_y = y_offset_mm + 5 + line_num * 5
                self.canvas_widget.add_line(
                    0, line_y,
                    210, line_y,
                    stroke_color='#CCCCCC',
                    stroke_width_mm=0.2,
                    tags=['staff']
                )
            
            # Add measure number
            self.canvas_widget.add_text(
                5, y_offset_mm + 2,
                text=f'M{self.measure_count + 1}',
                font_pt=8,
                color='#666666',
                tags=['measure_num']
            )
            
            # Add some note rectangles (simulate notes)
            for note_x in range(20, 200, 40):
                note_y = y_offset_mm + 10 + (i % 10) * 2
                self.canvas_widget.add_rectangle(
                    note_x, note_y,
                    note_x + 15, note_y + 4,
                    fill=True,
                    fill_color='#000000',
                    tags=['note']
                )
            
            self.measure_count += 1
        
        add_time = time.time() - start_time
        
        # Trigger a redraw and measure it
        start_redraw = time.time()
        self.canvas_widget._redraw_all()
        self.last_redraw_time = time.time() - start_redraw
        
        print(f'Added {count} measures in {add_time:.3f}s, redraw took {self.last_redraw_time:.3f}s')
        self.update_stats()
    
    def clear_measures(self):
        '''Clear all measures from canvas.'''
        self.canvas_widget.delete('all')
        self.measure_count = 0
        self.last_redraw_time = 0
        self.update_stats()
    
    def update_stats(self, *args):
        '''Update performance statistics display.'''
        total_items = len(self.canvas_widget._items)
        
        # Get visible range
        if hasattr(self.canvas_widget, '_get_visible_y_range_mm'):
            y_min, y_max = self.canvas_widget._get_visible_y_range_mm()
            visible_range_mm = y_max - y_min
        else:
            y_min, y_max = 0, 0
            visible_range_mm = 0
        
        scroll_mm = self.canvas_widget._scroll_px / max(0.1, self.canvas_widget._px_per_mm)
        
        self.stats_label.text = (
            f'Measures: {self.measure_count} | '
            f'Total Items: {total_items} | '
            f'Last Redraw: {self.last_redraw_time*1000:.1f}ms | '
            f'Scroll: {scroll_mm:.1f}mm | '
            f'Visible: {y_min:.1f}-{y_max:.1f}mm ({visible_range_mm:.1f}mm)'
        )


class TestApp(App):
    def build(self):
        return ViewportCullingTest()


if __name__ == '__main__':
    TestApp().run()
