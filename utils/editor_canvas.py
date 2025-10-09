#!/usr/bin/env python3
"""
EditorCanvas - A tkinter Canvas with automatic coordinate scaling.

This canvas maintains a logical coordinate system (e.g., 1024x768) while
automatically scaling all drawing to fit the actual widget size.
Similar to Qt's QGraphicsView/QGraphicsScene architecture.
"""

import tkinter as tk
import math

class EditorCanvas(tk.Canvas):
    """
    A Canvas that maintains logical coordinates while auto-scaling to widget size.
    
    Features:
    - Logical coordinate system (e.g., 1024x768) independent of widget size
    - Automatic scaling of all drawing operations
    - Mouse coordinates automatically converted to logical coordinates
    - Maintains aspect ratio or allows stretching
    - No need to redraw when widget resizes - tkinter handles scaling automatically
    """
    
    def __init__(self, parent, logical_width=1024, logical_height=768, 
                 maintain_aspect_ratio=True, **kwargs):
        """
        Initialize the EditorCanvas.
        
        Args:
            parent: Parent widget
            logical_width (int): Virtual/logical width in your coordinate system
            logical_height (int): Virtual/logical height in your coordinate system
            maintain_aspect_ratio (bool): Whether to maintain aspect ratio when scaling
            **kwargs: Additional Canvas arguments
        """
        super().__init__(parent, **kwargs)
        
        # Logical coordinate system
        self.logical_width = logical_width
        self.logical_height = logical_height
        self.maintain_aspect_ratio = maintain_aspect_ratio
        
        # Scaling factors (will be calculated on resize)
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        # Set initial scroll region to logical coordinates
        self.configure(scrollregion=(0, 0, logical_width, logical_height))
        
        # Bind resize event
        self.bind('<Configure>', self._on_resize)
        
        # Track if we're in the middle of a resize to avoid recursion
        self._resizing = False
        
        print(f"✨ EditorCanvas created with logical size {logical_width}x{logical_height}")
        
    def _on_resize(self, event):
        """Handle canvas resize - recalculate scaling."""
        if self._resizing or event.widget != self:
            return
            
        self._resizing = True
        
        try:
            # Get actual canvas size
            canvas_width = event.width
            canvas_height = event.height
            
            if canvas_width <= 1 or canvas_height <= 1:
                return
                
            if self.maintain_aspect_ratio:
                # Calculate scale factor that maintains aspect ratio
                scale_x = canvas_width / self.logical_width
                scale_y = canvas_height / self.logical_height
                scale = min(scale_x, scale_y)  # Use smaller scale to fit everything
                
                self.scale_x = scale
                self.scale_y = scale
                
                # Center the content
                scaled_width = self.logical_width * scale
                scaled_height = self.logical_height * scale
                self.offset_x = (canvas_width - scaled_width) / 2
                self.offset_y = (canvas_height - scaled_height) / 2
                
            else:
                # Scale to fill entire canvas (may distort)
                self.scale_x = canvas_width / self.logical_width
                self.scale_y = canvas_height / self.logical_height
                self.offset_x = 0
                self.offset_y = 0
            
            # Apply scaling transformation
            self._apply_scaling()
            
            print(f"🔄 Canvas resized to {canvas_width}x{canvas_height}, "
                  f"scale: {self.scale_x:.3f}x{self.scale_y:.3f}")
                  
        finally:
            self._resizing = False
    
    def _apply_scaling(self):
        """Apply the scaling transformation to the canvas."""
        # Reset any previous transformations
        self.delete("transform_marker")
        
        # Apply scale and translate transformation
        # tkinter uses matrix transformations: scale then translate
        self.scale("all", 0, 0, self.scale_x, self.scale_y)
        if self.offset_x != 0 or self.offset_y != 0:
            self.move("all", self.offset_x, self.offset_y)
    
    def set_logical_size(self, width, height):
        """
        Change the logical coordinate system size.
        
        Args:
            width (int): New logical width
            height (int): New logical height
        """
        self.logical_width = width
        self.logical_height = height
        self.configure(scrollregion=(0, 0, width, height))
        
        # Trigger resize recalculation
        self.event_generate('<Configure>')
        
        print(f"📏 Logical size changed to {width}x{height}")
        return self
    
    def set_logical_height(self, height):
        """
        Change only the logical height (perfect for piano roll editors).
        Keeps width constant while extending/shrinking height based on content.
        
        Args:
            height (int): New logical height
        """
        self.logical_height = height
        self.configure(scrollregion=(0, 0, self.logical_width, height))
        
        # Trigger resize recalculation to update scaling
        self.event_generate('<Configure>')
        
        print(f"📏 Logical height changed to {height} (width stays {self.logical_width})")
        return self
    
    def extend_logical_height(self, additional_height):
        """
        Extend the logical height by a certain amount.
        Useful for adding more content to a piano roll.
        
        Args:
            additional_height (int): Height to add to current logical height
        """
        new_height = self.logical_height + additional_height
        return self.set_logical_height(new_height)
    
    def fit_content_height(self, content_height, padding=50):
        """
        Set logical height to fit specific content with optional padding.
        
        Args:
            content_height (int): Height needed for content
            padding (int): Extra padding at bottom
        """
        return self.set_logical_height(content_height + padding)
    
    def logical_to_canvas(self, x, y):
        """
        Convert logical coordinates to actual canvas coordinates.
        
        Args:
            x, y: Logical coordinates
            
        Returns:
            tuple: (canvas_x, canvas_y)
        """
        canvas_x = x * self.scale_x + self.offset_x
        canvas_y = y * self.scale_y + self.offset_y
        return canvas_x, canvas_y
    
    def canvas_to_logical(self, canvas_x, canvas_y):
        """
        Convert canvas coordinates to logical coordinates.
        
        Args:
            canvas_x, canvas_y: Canvas coordinates (e.g., from mouse events)
            
        Returns:
            tuple: (logical_x, logical_y)
        """
        logical_x = (canvas_x - self.offset_x) / self.scale_x if self.scale_x != 0 else 0
        logical_y = (canvas_y - self.offset_y) / self.scale_y if self.scale_y != 0 else 0
        return logical_x, logical_y
    
    def get_logical_bounds(self):
        """
        Get the logical coordinate bounds.
        
        Returns:
            tuple: (x1, y1, x2, y2) in logical coordinates
        """
        return (0, 0, self.logical_width, self.logical_height)
    
    def get_scale_info(self):
        """
        Get current scaling information.
        
        Returns:
            dict: Scaling information
        """
        return {
            'logical_size': (self.logical_width, self.logical_height),
            'canvas_size': (self.winfo_width(), self.winfo_height()),
            'scale': (self.scale_x, self.scale_y),
            'offset': (self.offset_x, self.offset_y),
            'maintain_aspect_ratio': self.maintain_aspect_ratio
        }
    
    # Override drawing methods to work with logical coordinates
    def create_line_logical(self, x1, y1, x2, y2, **kwargs):
        """Create a line using logical coordinates."""
        return self.create_line(x1, y1, x2, y2, **kwargs)
    
    def create_rectangle_logical(self, x1, y1, x2, y2, **kwargs):
        """Create a rectangle using logical coordinates."""
        return self.create_rectangle(x1, y1, x2, y2, **kwargs)
    
    def create_oval_logical(self, x1, y1, x2, y2, **kwargs):
        """Create an oval using logical coordinates."""
        return self.create_oval(x1, y1, x2, y2, **kwargs)
    
    def create_text_logical(self, x, y, **kwargs):
        """Create text using logical coordinates."""
        return self.create_text(x, y, **kwargs)
    
    def create_polygon_logical(self, *coords, **kwargs):
        """Create a polygon using logical coordinates."""
        return self.create_polygon(*coords, **kwargs)
    
    # Convenience method for drawing a grid in logical coordinates
    def draw_logical_grid(self, grid_size=100, color="lightgray"):
        """
        Draw a grid using logical coordinates to visualize the coordinate system.
        
        Args:
            grid_size (int): Grid spacing in logical units
            color (str): Grid line color
        """
        # Vertical lines
        for x in range(0, self.logical_width + 1, grid_size):
            self.create_line_logical(x, 0, x, self.logical_height, 
                                   fill=color, width=1, tags="grid")
        
        # Horizontal lines  
        for y in range(0, self.logical_height + 1, grid_size):
            self.create_line_logical(0, y, self.logical_width, y, 
                                   fill=color, width=1, tags="grid")
        
        # Add coordinate labels
        for x in range(0, self.logical_width + 1, grid_size * 2):
            self.create_text_logical(x + 10, 15, text=str(x), 
                                   fill=color, font=("Arial", 8), tags="grid")
        
        for y in range(grid_size, self.logical_height + 1, grid_size * 2):
            self.create_text_logical(15, y, text=str(y), 
                                   fill=color, font=("Arial", 8), tags="grid")
    
    def clear_grid(self):
        """Remove the grid."""
        self.delete("grid")
    
    # Piano Roll specific methods
    def setup_piano_roll(self, track_width=1024, pixels_per_beat=100, total_beats=32):
        """
        Setup canvas for vertical piano roll editing.
        
        Args:
            track_width (int): Fixed width for the piano roll
            pixels_per_beat (int): Height per beat/measure
            total_beats (int): Initial number of beats
        """
        self.piano_roll_width = track_width
        self.pixels_per_beat = pixels_per_beat
        self.total_beats = total_beats
        
        initial_height = pixels_per_beat * total_beats
        self.set_logical_size(track_width, initial_height)
        
        print(f"🎹 Piano roll setup: {track_width}x{initial_height} "
              f"({pixels_per_beat}px/beat, {total_beats} beats)")
        return self
    
    def add_beats(self, beats):
        """
        Add more beats to the piano roll (extends height).
        
        Args:
            beats (int): Number of beats to add
        """
        self.total_beats += beats
        new_height = self.pixels_per_beat * self.total_beats
        self.set_logical_height(new_height)
        
        print(f"🎵 Added {beats} beats, total: {self.total_beats} beats")
        return self
    
    def set_midi_length(self, length_in_beats):
        """
        Set piano roll height based on MIDI length.
        
        Args:
            length_in_beats (float): Length of MIDI in beats
        """
        self.total_beats = length_in_beats
        new_height = int(self.pixels_per_beat * length_in_beats)
        self.set_logical_height(new_height)
        
        print(f"🎼 MIDI length set to {length_in_beats} beats = {new_height}px height")
        return self
    
    def get_beat_position(self, beat):
        """
        Get Y coordinate for a specific beat position.
        
        Args:
            beat (float): Beat number
            
        Returns:
            int: Y coordinate in logical coordinates
        """
        return int(beat * self.pixels_per_beat)
    
    def get_beat_from_y(self, y):
        """
        Get beat number from Y coordinate.
        
        Args:
            y (int): Y coordinate in logical coordinates
            
        Returns:
            float: Beat number
        """
        return y / self.pixels_per_beat if self.pixels_per_beat > 0 else 0

