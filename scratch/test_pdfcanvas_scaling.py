#!/usr/bin/env python3
'''
Test PdfCanvas scaling behavior with a rectangle and margins.

This test creates a rectangle with 25px margins on all four sides
and tests how the scaling affects the rectangle positioning and size
when the canvas is resized.
'''

import tkinter as tk
import sys
import os

# Add parent directory to path to import PdfCanvas
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.canvas_tkinter2pymupdf import PdfCanvas

class PdfCanvasScalingTest:
    '''Test class for PdfCanvas scaling behavior.'''
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('PdfCanvas Scaling Test')
        self.root.geometry('800x600')
        
        # Create control frame
        self.control_frame = tk.Frame(self.root)
        self.control_frame.pack(side='top', fill='x', padx=10, pady=5)
        
        # Add resize buttons
        tk.Button(self.control_frame, text='Small (400x300)', 
                 command=lambda: self.resize_window(400, 300)).pack(side='left', padx=5)
        tk.Button(self.control_frame, text='Medium (600x450)', 
                 command=lambda: self.resize_window(600, 450)).pack(side='left', padx=5)
        tk.Button(self.control_frame, text='Large (1000x750)', 
                 command=lambda: self.resize_window(1000, 750)).pack(side='left', padx=5)
        
        # Add info label
        self.info_label = tk.Label(self.control_frame, text='Canvas size: 0x0, Scale: 1.0', 
                                  font=('Arial', 10))
        self.info_label.pack(side='right', padx=5)
        
        # Create canvas frame
        self.canvas_frame = tk.Frame(self.root, bg='lightgray')
        self.canvas_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create PdfCanvas (A4 size: 595x842 points)
        self.canvas = PdfCanvas(self.canvas_frame, page_width=595, page_height=842)
        self.canvas.pack(fill='both', expand=True)
        
        # Draw test rectangle with 25px margins
        self.draw_test_rectangle()
        
        # Bind resize event to update info
        self.canvas.bind('<Configure>', self.on_canvas_resize)
        
    def draw_test_rectangle(self):
        '''Draw a test rectangle with 25px margins on all sides.'''
        # Clear canvas first
        self.canvas.delete('all')
        
        # Canvas dimensions (logical A4 size)
        canvas_width = 595
        canvas_height = 842
        
        # Margin size
        margin = 25
        
        # Calculate rectangle coordinates
        x1 = margin
        y1 = margin
        x2 = canvas_width - margin
        y2 = canvas_height - margin
        
        # Draw the test rectangle using PdfCanvas custom method
        self.canvas.add_rectangle(x1, y1, x2, y2, 
                                 outline_width=2,  # Red outline
                                 fill=True,     # Light red fill
                                 color='#FF0000')  # Red color
        
        # Draw corner markers to verify margins
        marker_size = 10
        marker_color = '#0000FF'  # Blue
        
        # Top-left corner
        self.canvas.add_rectangle(margin - marker_size//2, margin - marker_size//2,
                                 margin + marker_size//2, margin + marker_size//2,
                                 color=marker_color)
        
        # Top-right corner  
        self.canvas.add_rectangle(x2 - marker_size//2, margin - marker_size//2,
                                 x2 + marker_size//2, margin + marker_size//2,
                                 color=marker_color)
        
        # Bottom-left corner
        self.canvas.add_rectangle(margin - marker_size//2, y2 - marker_size//2,
                                 margin + marker_size//2, y2 + marker_size//2,
                                 color=marker_color)
        
        # Bottom-right corner
        self.canvas.add_rectangle(x2 - marker_size//2, y2 - marker_size//2,
                                 x2 + marker_size//2, y2 + marker_size//2,
                                 color=marker_color)
        
        # Add text labels
        self.canvas.add_text(canvas_width//2, 15, 'PdfCanvas Scaling Test', 
                           size=16, anchor='center', color='#000000')
        self.canvas.add_text(canvas_width//2, canvas_height - 15, 
                           f'Rectangle: {x1},{y1} to {x2},{y2} (margin: {margin}px)', 
                           size=12, anchor='center', color='#666666')
        
        # Add measurement lines
        self.draw_measurement_lines(margin, canvas_width, canvas_height)
        
    def draw_measurement_lines(self, margin, width, height):
        '''Draw measurement lines to show margins.'''
        line_color = '#00AA00'  # Green
        
        # Top margin line
        self.canvas.add_line(0, margin, width, margin, color=line_color, width=1)
        self.canvas.add_text(5, margin - 5, f'{margin}px', size=10, color=line_color)
        
        # Bottom margin line
        bottom_y = height - margin
        self.canvas.add_line(0, bottom_y, width, bottom_y, color=line_color, width=1)
        self.canvas.add_text(5, bottom_y + 15, f'{margin}px', size=10, color=line_color)
        
        # Left margin line
        self.canvas.add_line(margin, 0, margin, height, color=line_color, width=1)
        self.canvas.add_text(margin + 5, 15, f'{margin}px', size=10, color=line_color)
        
        # Right margin line
        right_x = width - margin
        self.canvas.add_line(right_x, 0, right_x, height, color=line_color, width=1)
        self.canvas.add_text(right_x - 40, 15, f'{margin}px', size=10, color=line_color)
        
    def resize_window(self, width, height):
        '''Resize the window to test scaling.'''
        self.root.geometry(f'{width}x{height}')
        
    def on_canvas_resize(self, event):
        '''Update info when canvas resizes.'''
        # Get actual canvas size
        actual_width = self.canvas.winfo_width()
        actual_height = self.canvas.winfo_height()
        
        # Calculate scale (PdfCanvas should handle this internally)
        logical_width = 595
        logical_height = 842
        
        scale_x = actual_width / logical_width if logical_width > 0 else 1.0
        scale_y = actual_height / logical_height if logical_height > 0 else 1.0
        scale = min(scale_x, scale_y)  # Uniform scaling
        
        # Update info label
        self.info_label.config(text=f'Canvas size: {actual_width}x{actual_height}, Scale: {scale:.2f}')
        
    def run(self):
        '''Run the test application.'''
        print('PdfCanvas Scaling Test')
        print('=====================')
        print('- Red rectangle should maintain 25px margins on all sides')
        print('- Blue corner markers should stay at exact margin positions')
        print('- Green measurement lines show margin boundaries')
        print('- Use resize buttons to test scaling behavior')
        print('- Rectangle should scale uniformly while maintaining proportions')
        
        self.root.mainloop()

if __name__ == '__main__':
    test = PdfCanvasScalingTest()
    test.run()