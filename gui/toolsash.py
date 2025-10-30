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
import math

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
from gui.callbacks import create_menu_config, create_button_config
from gui.colors import DARK, DARK_LIGHTER, LIGHT_DARKER, LIGHT
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
            Color(*DARK)
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
            bar_color=DARK_LIGHTER,
            bar_inactive_color=DARK,
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
        
        # Bind button callbacks to this instance
        self._setup_button_callbacks()
        
        self.setup_layout()
    
    def _setup_button_callbacks(self):
        """Bind toolbar button callbacks to this GUI instance."""
        from gui.callbacks import BUTTON_CONFIG
        
        # Update the global BUTTON_CONFIG with instance methods
        BUTTON_CONFIG["note2left"] = self.on_note_to_left
        BUTTON_CONFIG["note2right"] = self.on_note_to_right
        BUTTON_CONFIG["note"] = self.on_add_note
    
    def setup_layout(self):
        """Create the main layout structure with menu bar and resizable panels."""
        
        # Add menu bar at the top using centralized configuration
        menu_config = create_menu_config(self)
        self.menu_bar = MenuBar(menu_config)
        self.add_widget(self.menu_bar)
        
        # Main horizontal layout: fixed-width left panel | editor-preview split
        self.main_layout = BoxLayout(orientation='horizontal', spacing=0)
        
        # Left side panel with fixed width
        self.side_panel = SidePanelWidget(size_hint_x=None, width=400)
        self.main_layout.add_widget(self.side_panel)
        
        # Right side: Editor-Preview split view
        self.editor_preview_split = SplitView(
            orientation='horizontal',
            sash_width=80,  # Wide sash for toolbar buttons
            split_ratio=0.6,  # Editor takes 60% initially
            sash_color=DARK
        )
        
        # Editor area (left side of right panel) - use our mm-based Canvas
        self.editor_area = Canvas(width_mm=210.0, height_mm=297.0,
                                    background_color=(1, 1, 1, 1),
                                    border_color=DARK,
                                    border_width_px=1.0)
        self.editor_preview_split.set_left(self.editor_area)
        
        # Print preview area (right side of right panel) - also Canvas
        self.print_preview = Canvas(width_mm=210.0, height_mm=297.0,
                                      background_color=(1, 1, 1, 1),
                                      border_color=DARK_LIGHTER,
                                      border_width_px=1.0)
        self.editor_preview_split.set_right(self.print_preview)
        
        # Add editor-preview split to main layout
        self.main_layout.add_widget(self.editor_preview_split)
        
        # Add main layout to root layout
        self.add_widget(self.main_layout)

        # After layout is added and sized, calculate the snap ratio for perfect paper fit
        # This allows the user to snap to this position when dragging the sash
        Clock.schedule_once(self._setup_snap_ratio, 0)

        # File management is owned by App; GUI receives a setter later.
        self.file_manager = None
    
    def get_editor_widget(self):
        """Get reference to the editor widget."""
        return self.editor_area
    
    def get_preview_widget(self):
        """Get reference to the preview widget."""
        return self.print_preview
    
    def get_side_panel(self):
        """Get reference to the side panel."""
        return self.side_panel

    def _setup_snap_ratio(self, _dt):
        """Calculate and set the snap ratio for the editor-preview split.
        
        This allows the sash to snap to the perfect position where the paper
        dimensions (width_mm/height_mm ratio) fit exactly in the right panel.
        """
        sp = self.editor_preview_split
        if not sp:
            return
        
        # Wait until sizes are ready
        if sp.width <= 0 or sp.height <= 0:
            Clock.schedule_once(self._setup_snap_ratio, 0)
            return
        
        # Get paper aspect ratio from the Canvas
        page_w_mm = getattr(self.print_preview, 'width_mm', 210.0)
        page_h_mm = getattr(self.print_preview, 'height_mm', 297.0)
        aspect_ratio = page_h_mm / page_w_mm if page_w_mm else math.sqrt(2.0)
        
        # Set snap ratio on the split view
        sp.set_snap_ratio_from_aspect(aspect_ratio)
        
        # Also bind to size changes to recalculate snap ratio
        sp.bind(size=lambda *args: sp.set_snap_ratio_from_aspect(aspect_ratio))

    def _fit_preview_page_on_start(self, _dt):
        """Adjust the editor-preview sash so the A4 page in the preview fits fully.

        The preview Canvas uses scale_to_width, so content_height = preview_width * (page_h/page_w).
        To fit exactly, set preview_width ≈ (preview_height - ε) / (page_h/page_w).
        Then back-compute split_ratio so right panel width equals this preview width.
        
        NOTE: This method is currently disabled. The snap-to-fit behavior allows users
        to manually snap to this position by dragging the sash.
        """
        sp = self.editor_preview_split
        if not sp:
            return
        total_w = sp.width
        total_h = sp.height
        # If sizes aren't ready yet, try again next frame
        if total_w <= 0 or total_h <= 0:
            Clock.schedule_once(self._fit_preview_page_on_start, 0)
            return

        # Page aspect based on the Canvas logical size (A4: 210x297 mm)
        page_w_mm = getattr(self.print_preview, 'width_mm', 210.0)
        page_h_mm = getattr(self.print_preview, 'height_mm', 297.0)
        ratio = page_h_mm / page_w_mm if page_w_mm else math.sqrt(2.0)

        sash = sp.sash_width
        # Choose width so that int(round(width*ratio)) equals total_h as closely as possible
        required_right = max(0.0, (total_h) / ratio)

        # Respect SplitView minimums
        min_left = getattr(sp, 'min_left_size', 150)
        min_right = getattr(sp, 'min_right_size', 150)

        # Max right width we can allocate while honoring min_left (accounting for full sash width)
        max_right = max(0.0, total_w - min_left - sash)
        desired_right = min(required_right, max_right)

        # Compute split ratio so right_width = desired_right
        # right_width = total_w * (1 - r) - sash/2  =>  r = 1 - (desired_right + sash/2)/total_w
        if total_w > 0:
            r = 1.0 - (desired_right + sash / 2.0) / total_w
        else:
            r = sp.split_ratio

        # Enforce min right width if configured
        min_right_ratio_cap = 1.0 - (min_right + sash / 2.0) / total_w if total_w > 0 else r
        r = min(r, min_right_ratio_cap)

        # Ensure min left width
        min_left_ratio_floor = (min_left + sash / 2.0) / total_w if total_w > 0 else r
        r = max(r, min_left_ratio_floor)

        # Final clamp 0..1 and apply
        sp.split_ratio = max(0.0, min(1.0, r))
        sp.update_layout()

        # One-shot pixel-perfect correction: recompute using the actual preview height
        # to mitigate rounding differences (aim for round(width*ratio) == height)
        try:
            pw = float(self.print_preview.width)
            ph = float(self.print_preview.height)
            desired_right_rounded = max(0.0, round(ph / ratio))
            desired_right_rounded = min(desired_right_rounded, max_right)
            if abs(pw - desired_right_rounded) >= 1.0 and total_w > 0:
                r2 = 1.0 - (desired_right_rounded + sash / 2.0) / total_w
                r2 = min(r2, min_right_ratio_cap)
                r2 = max(r2, min_left_ratio_floor)
                sp.split_ratio = max(0.0, min(1.0, r2))
                sp.update_layout()
        except Exception:
            pass
        # Mark as done so we don't re-run on further size events
        self._did_fit_preview = True

    ''' on_X event handlers '''

    def on_exit(self):
        """Handle File > Exit."""
        if self.file_manager:
            self.file_manager.exit_app()
        else:
            from kivy.app import App
            App.get_running_app().stop()

    def on_about(self):
        """Handle About menu."""
        ...

    # ----- File menu delegates (wired in menu_config) -----
    def set_file_manager(self, fm):
        self.file_manager = fm

    def on_new(self):
        if self.file_manager:
            self.file_manager.new_file()

    def on_load(self):
        if self.file_manager:
            self.file_manager.open_file()

    def on_save(self):
        if self.file_manager:
            self.file_manager.save_file()

    def on_save_as(self):
        if self.file_manager:
            self.file_manager.save_file_as()

    # ----- Toolbar button delegates (wired in callbacks.py) -----
    
    def on_note_to_left(self):
        """Move selected note(s) to left hand."""
        print("Move note to left hand")
        # TODO: Implement note hand assignment logic
    
    def on_note_to_right(self):
        """Move selected note(s) to right hand."""
        print("Move note to right hand")
        # TODO: Implement note hand assignment logic
    
    def on_add_note(self):
        """Add a new note at current position."""
        print("Add note")
        # TODO: Implement note creation logic


__all__ = [
    'PianoTabGUI',
    'SidePanelWidget',
    'EditorWidget',
    'PrintPreviewWidget',
]
