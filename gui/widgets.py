'''
    - Left side panel
    - Editor Widget
    - PrintPreview Widget
'''

import sys
import os
import math

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line
from kivy.graphics.scissor_instructions import ScissorPush, ScissorPop
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from gui.grid_selector import GridSelector
from gui.tool_selector import ToolSelector
from gui.colors import DARK, DARK_LIGHTER, LIGHT_DARKER, LIGHT


class EditorWidget(Widget):
    '''
    Simple editor widget placeholder.
    This will be replaced with your actual piano tab editor.
    Uses clipping to hide content that goes out of bounds.
    '''
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Draw background with clipping
        with self.canvas.before:
            # Add scissor test to clip content
            self.scissor = ScissorPush(x=int(self.x), y=int(self.y), 
                                      width=int(self.width), height=int(self.height))
            self.bg_color = Color(*DARK_LIGHTER)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        
        # Draw some sample content
        with self.canvas:
            # Grid lines
            Color(*DARK)
            self.grid_lines = []
        
        # Close scissor test after main canvas
        with self.canvas.after:
            self.scissor_pop = ScissorPop()
        
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        
        # Add label
        self.label = Label(
            text='Editor Area\n(Piano Tab Editor)',
            color=LIGHT_DARKER,
            font_size='20sp',
            halign='center'
        )
        self.add_widget(self.label)
        self.label.center = self.center
    
    def update_graphics(self, *args):
        '''Update graphics when size changes.'''
        # Update scissor clipping region
        self.scissor.x = int(self.x)
        self.scissor.y = int(self.y)
        self.scissor.width = int(self.width)
        self.scissor.height = int(self.height)
        
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.label.center = self.center
        
        # Draw grid
        self.canvas.remove_group('grid')
        with self.canvas:
            Color(*DARK)
            # Vertical lines
            for x in range(int(self.x), int(self.x + self.width), 50):
                Line(points=[x, self.y, x, self.y + self.height], width=1, group='grid')
            # Horizontal lines
            for y in range(int(self.y), int(self.y + self.height), 50):
                Line(points=[self.x, y, self.x + self.width, y], width=1, group='grid')


class PrintPreviewWidget(Widget):
    '''
    Simple print preview widget placeholder.
    This will be replaced with your actual print preview.
    Uses clipping to hide content that goes out of bounds.
    '''
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Draw background with clipping
        with self.canvas.before:
            # Add scissor test to clip content
            self.scissor = ScissorPush(x=int(self.x), y=int(self.y), 
                                      width=int(self.width), height=int(self.height))
            self.bg_color = Color(*DARK)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        
        # Draw paper representation
        with self.canvas:
            Color(*LIGHT)  # White paper
            self.paper_rect = Rectangle(pos=self.pos, size=(100, 100))
        
        # Close scissor test after main canvas
        with self.canvas.after:
            self.scissor_pop = ScissorPop()
        
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        
        # Cursor management
        Window.bind(mouse_pos=self._update_cursor_on_hover)
        
        # Add label
        self.label = Label(
            text='Print Preview Area\n(PDF Output)',
            color=LIGHT,
            font_size='20sp',
            halign='center'
        )
        self.add_widget(self.label)
        self.label.center = self.center
    
    def update_graphics(self, *args):
        '''Update graphics when size changes.'''
        # Update scissor clipping region
        self.scissor.x = int(self.x)
        self.scissor.y = int(self.y)
        self.scissor.width = int(self.width)
        self.scissor.height = int(self.height)
        
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.label.center = self.center
        
        # Draw paper in center (A4 ratio: 1:1.414)
        paper_width = min(self.width * 0.8, self.height * 0.8 / 1.414)
        paper_height = paper_width * 1.414
        paper_x = self.x + (self.width - paper_width) / 2
        paper_y = self.y + (self.height - paper_height) / 2
        
        self.paper_rect.pos = (paper_x, paper_y)
        self.paper_rect.size = (paper_width, paper_height)
    
    def _update_cursor_on_hover(self, window, pos):
        '''Update cursor to arrow when hovering over print preview widget.'''
        if self.collide_point(*pos):
            Window.set_system_cursor('arrow')


class SidePanelWidget(ScrollView):
    '''
    Left side panel widget - a simple scrollable vertical layout.
    Contains grid selector and tool selector.
    '''
    
    def __init__(self, grid_callback=None, tool_callback=None, **kwargs):
        print("SidePanelWidget.__init__ called!")
        super().__init__(
            size_hint=(1, 1),
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=8,
            bar_color=DARK_LIGHTER,
            bar_inactive_color=DARK,
            scroll_type=['bars', 'content'],
            **kwargs
        )
        print("SidePanelWidget: After super().__init__")
        
        self.grid_callback = grid_callback
        self.tool_callback = tool_callback
        
        # Simple vertical layout
        self.layout = BoxLayout(
            orientation='vertical',
            padding=10,
            spacing=12,
            size_hint_y=None
        )
        self.layout.bind(minimum_height=self.layout.setter('height'))
        self.add_widget(self.layout)
        
        # Add Grid Selector first (appears at top)
        self.grid_selector = GridSelector(callback=self.on_grid_changed)
        self.layout.add_widget(self.grid_selector)
        
        # Add Tool Selector below
        self.tool_selector = ToolSelector(callback=self.on_tool_selected)
        self.layout.add_widget(self.tool_selector)
        
        # Cursor management - set arrow cursor when over side panel
        Window.bind(mouse_pos=self._update_cursor_on_hover)
        print(f"SidePanelWidget: Bound cursor handler to Window.mouse_pos")
    
    def _update_cursor_on_hover(self, window, pos):
        """
        Set cursor to arrow when mouse is over the side panel.
        
        Called automatically when mouse position changes.
        """
        print(f"SidePanel _update_cursor_on_hover called with pos={pos}")
        # Check if mouse is within this widget's bounds
        # Note: collide_point uses window coordinates
        if self.collide_point(*pos):
            # Debug: print when we detect hover
            print(f"SidePanel hover detected at {pos}, bounds: x={self.x}, y={self.y}, w={self.width}, h={self.height}")
            Window.set_system_cursor('arrow')
    
    def on_tool_selected(self, tool_name):
        '''Handle tool selection and notify main GUI.'''
        if self.tool_callback:
            try:
                self.tool_callback(tool_name)
            except Exception:
                # Silent guard for UI callback
                pass
        print(f'Tool selected: {tool_name}')
    
    def on_grid_changed(self, grid_step):
        '''Handle grid step change from GridSelector.'''
        print(f'Grid step changed to: {grid_step} piano ticks')
        
        # Call the main GUI callback if available
        if self.grid_callback:
            self.grid_callback(grid_step)


__all__ = [
    'SidePanelWidget',
    'EditorWidget',
    'PrintPreviewWidget',
]
