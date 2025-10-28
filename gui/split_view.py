"""
Custom SplitView widget for Kivy with draggable wide sash.
Similar to tkinter's PanedWindow but with customizable sash width.
"""

from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.properties import NumericProperty, ObjectProperty, ListProperty
from kivy.core.window import Window
from gui.colors import DARK


class Sash(Widget):
    """Draggable sash for splitting views."""
    
    def __init__(self, split_view, **kwargs):
        super().__init__(**kwargs)
        self.split_view = split_view
        self.dragging = False
        
        # Draw sash background (use canvas, not canvas.before to avoid duplication)
        with self.canvas:
            self.bg_color = Color(*DARK)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        
        self.bind(pos=self.update_rect, size=self.update_rect)
    
    def update_rect(self, *args):
        """Update sash rectangle."""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
    
    def on_touch_down(self, touch):
        """Handle mouse down on sash."""
        if self.collide_point(*touch.pos):
            self.dragging = True
            touch.grab(self)
            # Change cursor to resize
            if self.split_view.orientation == 'horizontal':
                Window.set_system_cursor('size_we')
            else:
                Window.set_system_cursor('size_ns')
            return True
        return super().on_touch_down(touch)
    
    def on_touch_move(self, touch):
        """Handle mouse drag on sash."""
        if touch.grab_current is self and self.dragging:
            self.split_view.update_split(touch.pos)
            return True
        return super().on_touch_move(touch)
    
    def on_touch_up(self, touch):
        """Handle mouse up."""
        if touch.grab_current is self:
            self.dragging = False
            touch.ungrab(self)
            Window.set_system_cursor('arrow')
            return True
        return super().on_touch_up(touch)


class SplitView(Widget):
    """
    A split view widget with draggable sash.
    Similar to tkinter's PanedWindow but with Kivy styling.
    """
    
    sash_width = NumericProperty(20)  # Width of the draggable sash
    split_ratio = NumericProperty(0.5)  # Initial split ratio (0.0 to 1.0)
    left_widget = ObjectProperty(None, allownone=True)
    right_widget = ObjectProperty(None, allownone=True)
    sash_color = ListProperty(DARK)  # Use color system default
    orientation = 'horizontal'  # 'horizontal' or 'vertical'
    
    # Add minimum size properties
    min_left_size = NumericProperty(150)  # Minimum pixels for left panel
    min_right_size = NumericProperty(150)  # Minimum pixels for right panel
    
    def __init__(self, orientation='horizontal', **kwargs):
        super().__init__(**kwargs)
        self.orientation = orientation
        
        # Container for left/top widget
        self.left_container = Widget()
        self.add_widget(self.left_container)
        
        # Sash
        self.sash = Sash(self, size_hint=(None, 1) if orientation == 'horizontal' else (1, None))
        if orientation == 'horizontal':
            self.sash.width = self.sash_width
        else:
            self.sash.height = self.sash_width
        self.add_widget(self.sash)
        
        # Container for right/bottom widget
        self.right_container = Widget()
        self.add_widget(self.right_container)
        
        # Bind to size changes
        self.bind(size=self.update_layout, pos=self.update_layout)
        self.bind(sash_width=self.on_sash_width_change)
        self.bind(sash_color=self.update_sash_color)
    
    def on_sash_width_change(self, instance, value):
        """Update sash size when sash_width changes."""
        if self.orientation == 'horizontal':
            self.sash.width = value
        else:
            self.sash.height = value
        self.update_layout()
    
    def update_sash_color(self, *args):
        """Update sash background color."""
        self.sash.bg_color.rgba = self.sash_color
    
    def set_left(self, widget):
        """Set the left/top widget."""
        if self.left_widget:
            self.left_container.remove_widget(self.left_widget)
        
        self.left_widget = widget
        if widget:
            self.left_container.add_widget(widget)
            self.update_layout()
    
    def set_right(self, widget):
        """Set the right/bottom widget."""
        if self.right_widget:
            self.right_container.remove_widget(self.right_widget)
        
        self.right_widget = widget
        if widget:
            self.right_container.add_widget(widget)
            self.update_layout()
    
    def update_layout(self, *args):
        """Update the layout based on split ratio."""
        if self.orientation == 'horizontal':
            # Horizontal split
            total_width = self.width
            left_width = total_width * self.split_ratio - self.sash_width / 2
            right_width = total_width * (1 - self.split_ratio) - self.sash_width / 2
            
            # Position and size left container
            self.left_container.pos = self.pos
            self.left_container.size = (max(0, left_width), self.height)
            
            # Position and size sash
            self.sash.pos = (self.x + left_width, self.y)
            self.sash.size = (self.sash_width, self.height)
            
            # Position and size right container
            self.right_container.pos = (self.x + left_width + self.sash_width, self.y)
            self.right_container.size = (max(0, right_width), self.height)
            
            # Update child widgets
            if self.left_widget:
                self.left_widget.pos = self.left_container.pos
                self.left_widget.size = self.left_container.size
            
            if self.right_widget:
                self.right_widget.pos = self.right_container.pos
                self.right_widget.size = self.right_container.size
        else:
            # Vertical split
            total_height = self.height
            top_height = total_height * self.split_ratio - self.sash_width / 2
            bottom_height = total_height * (1 - self.split_ratio) - self.sash_width / 2
            
            # Position and size top container
            self.left_container.pos = (self.x, self.y + bottom_height + self.sash_width)
            self.left_container.size = (self.width, max(0, top_height))
            
            # Position and size sash
            self.sash.pos = (self.x, self.y + bottom_height)
            self.sash.size = (self.width, self.sash_width)
            
            # Position and size bottom container
            self.right_container.pos = self.pos
            self.right_container.size = (self.width, max(0, bottom_height))
            
            # Update child widgets
            if self.left_widget:
                self.left_widget.pos = self.left_container.pos
                self.left_widget.size = self.left_container.size
            
            if self.right_widget:
                self.right_widget.pos = self.right_container.pos
                self.right_widget.size = self.right_container.size
    
    def update_split(self, touch_pos):
        """Update split ratio based on touch position."""
        if self.orientation == 'horizontal':
            # Calculate new ratio based on x position
            relative_x = touch_pos[0] - self.x
            new_ratio = relative_x / self.width
            
            # Clamp to respect minimum sizes
            min_ratio = self.min_left_size / self.width
            max_ratio = 1.0 - (self.min_right_size / self.width)
            new_ratio = max(min_ratio, min(max_ratio, new_ratio))
        else:
            # Calculate new ratio based on y position
            relative_y = touch_pos[1] - self.y
            new_ratio = 1.0 - (relative_y / self.height)
            
            # Clamp to respect minimum sizes
            min_ratio = self.min_right_size / self.height
            max_ratio = 1.0 - (self.min_left_size / self.height)
            new_ratio = max(min_ratio, min(max_ratio, new_ratio))
        
        self.split_ratio = new_ratio
        self.update_layout()
