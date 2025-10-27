"""
PianoTab Kivy GUI - Main GUI structure.

Recreates the tkinter GUI with:
- Left side panel
- Right split view with:
  - Left: Editor area
  - Right: Print preview
  - Wide draggable sash between them
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line
from kivy.graphics.scissor_instructions import ScissorPush, ScissorPop
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock
from gui.split_view import SplitView
from gui.grid_selector import GridSelector
from gui.tool_selector import ToolSelector
from gui.menu_bar import MenuBar
from utils.canvas import Canvas


class EditorWidget(Widget):
    """
    Simple editor widget placeholder.
    This will be replaced with your actual piano tab editor.
    Uses clipping to hide content that goes out of bounds.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Draw background with clipping
        with self.canvas.before:
            # Add scissor test to clip content
            self.scissor = ScissorPush(x=int(self.x), y=int(self.y), 
                                      width=int(self.width), height=int(self.height))
            self.bg_color = Color(0.15, 0.15, 0.2, 1)  # Dark blue-gray
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        
        # Draw some sample content
        with self.canvas:
            # Grid lines
            Color(0.25, 0.25, 0.3, 1)
            self.grid_lines = []
        
        # Close scissor test after main canvas
        with self.canvas.after:
            self.scissor_pop = ScissorPop()
        
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        
        # Add label
        self.label = Label(
            text='Editor Area\n(Piano Tab Editor)',
            color=(0.7, 0.7, 0.7, 1),
            font_size='20sp',
            halign='center'
        )
        self.add_widget(self.label)
        self.label.center = self.center
    
    def update_graphics(self, *args):
        """Update graphics when size changes."""
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
            Color(0.25, 0.25, 0.3, 1)
            # Vertical lines
            for x in range(int(self.x), int(self.x + self.width), 50):
                Line(points=[x, self.y, x, self.y + self.height], width=1, group='grid')
            # Horizontal lines
            for y in range(int(self.y), int(self.y + self.height), 50):
                Line(points=[self.x, y, self.x + self.width, y], width=1, group='grid')


class PrintPreviewWidget(Widget):
    """
    Simple print preview widget placeholder.
    This will be replaced with your actual print preview.
    Uses clipping to hide content that goes out of bounds.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Draw background with clipping
        with self.canvas.before:
            # Add scissor test to clip content
            self.scissor = ScissorPush(x=int(self.x), y=int(self.y), 
                                      width=int(self.width), height=int(self.height))
            self.bg_color = Color(0.25, 0.25, 0.25, 1)  # Medium gray
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        
        # Draw paper representation
        with self.canvas:
            Color(1, 1, 1, 1)  # White paper
            self.paper_rect = Rectangle(pos=self.pos, size=(100, 100))
        
        # Close scissor test after main canvas
        with self.canvas.after:
            self.scissor_pop = ScissorPop()
        
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        
        # Add label
        self.label = Label(
            text='Print Preview Area\n(PDF Output)',
            color=(0.9, 0.9, 0.9, 1),
            font_size='20sp',
            halign='center'
        )
        self.add_widget(self.label)
        self.label.center = self.center
    
    def update_graphics(self, *args):
        """Update graphics when size changes."""
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


class SidePanelWidget(ScrollView):
    """
    Left side panel widget - a simple scrollable vertical layout.
    Contains grid selector and tool selector.
    """
    
    def __init__(self, **kwargs):
        super().__init__(
            size_hint=(1, 1),
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=8,
            bar_color=(0.4, 0.4, 0.4, 0.8),
            bar_inactive_color=(0.3, 0.3, 0.3, 0.5),
            scroll_type=['bars', 'content'],
            **kwargs
        )
        
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
    
    def on_tool_selected(self, tool_name):
        """Handle tool selection."""
        print(f'Tool selected: {tool_name}')
    
    def on_grid_changed(self, grid_step):
        """Handle grid step change from GridSelector."""
        print(f'Grid step changed to: {grid_step} piano ticks')
        # TODO: Update editor cursor snapping behavior


class PianoTabGUI(BoxLayout):
    """
    Main GUI class for PianoTab application in Kivy.
    Recreates the tkinter structure with menu bar, left panel and split view.
    """
    
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        
        # Initialize references
        self.menu_bar = None
        self.side_panel = None
        self.editor_area = None
        self.print_preview = None
        
        self.setup_layout()
    
    def setup_layout(self):
        """Create the main layout structure with menu bar and resizable panels."""
        
        # Add menu bar at the top with dict-based configuration
        menu_config = {
            'File': {
                'New': None,
                'Open...': None,
                'Open Recent...': {
                    'recent1': None,
                    'recent2': None
                },
                'Save': None,
                'Save as...': None,
                '---': None,  # Separator
                'Exit': self.on_exit
            },
            'Edit': {
                'Undo': None,
                'Redo': None,
                '---': None,  # Separator
                'Cut': None,
                'Copy': None,
                'Paste': None
            },
            'Help': {
                'About': self.on_about
            }
        }
        self.menu_bar = MenuBar(menu_config)
        self.add_widget(self.menu_bar)
        
        # Main horizontal split: left panel | editor-preview split
        self.main_split = SplitView(
            orientation='horizontal',
            sash_width=40,
            split_ratio=0.15,
            sash_color=[0.15, 0.15, 0.18, 1],
            min_left_size=400,   # ← Side panel minimum width
            min_right_size=0   # ← Editor/preview minimum width
        )
        
        # Left side panel
        self.side_panel = SidePanelWidget()
        self.main_split.set_left(self.side_panel)
        
        # Right side: Editor-Preview split view
        self.editor_preview_split = SplitView(
            orientation='horizontal',
            sash_width=40,  # Wide sash as in tkinter version
            split_ratio=0.6,  # Editor takes 60% initially
            sash_color=[0.2, 0.2, 0.2, 1]
        )
        
        # Editor area (left side of right panel) - use our mm-based Canvas
        self.editor_area = Canvas(width_mm=210.0, height_mm=297.0,
                                    background_color=(0.15, 0.15, 0.2, 1),
                                    border_color=(0.3, 0.3, 0.35, 1),
                                    border_width_px=1.0)
        self.editor_preview_split.set_left(self.editor_area)
        
        # Print preview area (right side of right panel) - also Canvas
        self.print_preview = Canvas(width_mm=210.0, height_mm=297.0,
                                      background_color=(0.25, 0.25, 0.25, 1),
                                      border_color=(0.4, 0.4, 0.45, 1),
                                      border_width_px=1.0)
        self.editor_preview_split.set_right(self.print_preview)
        
        # Add editor-preview split to main split
        self.main_split.set_right(self.editor_preview_split)
        
        # Add main split to root layout
        self.add_widget(self.main_split)
    
    def get_editor_widget(self):
        """Get reference to the editor widget."""
        return self.editor_area
    
    def get_preview_widget(self):
        """Get reference to the preview widget."""
        return self.print_preview
    
    def get_side_panel(self):
        """Get reference to the side panel."""
        return self.side_panel

    ''' on_X event handlers '''

    def on_exit(self):
        """Handle File > Exit."""
        from kivy.app import App
        App.get_running_app().stop()

    def on_about(self):
        """Handle About menu."""
        ...


__all__ = [
    'PianoTabGUI',
    'SidePanelWidget',
    'EditorWidget',
    'PrintPreviewWidget',
]
