'''
New modular GUI scaffold for pianoTAB.

- MainMenu(): wraps the existing MenuBar using the current callbacks config
- SidePanel(): fixed-width vertical panel with GridSelector + ToolSelector
- Editor(): wrapper hosting the mm-based Canvas
- PianoKeyboard(): permanent piano keyboard display that highlights stave lines
- PropertyTreeEditor(): comprehensive property tree editor for SCORE

Layout:
    Root (vertical)
        - MainMenu() at the top
        - OuterSplit (horizontal, 2 logical areas)
                [Left: SidePanel (fixed width, outer sash width = 0, not resizable)]
                [Right: MidRightSplit (horizontal, sash 80px with contextual toolbar)]
                                         [Left : Editor()]
                                         [Right: PropertyTreeEditor()]

Cross-link:
- CenterSplit (vertical) is cross-linked with MidRightSplit (horizontal)
  via ToolSash.set_linked_split so dragging either sash can delta-couple both axes.
'''

from __future__ import annotations

from typing import Optional, Callable

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.core.window import Window

from gui.colors import DARK, DARK_LIGHTER, LIGHT, LIGHT_DARKER
from gui.menu_bar import MenuBar
from gui.grid_selector import GridSelector
from gui.tool_selector import ToolSelector
from gui.split_view import SplitView
from gui.callbacks import create_menu_config, create_default_toolbar_config, create_contextual_toolbar_config  # toolbar configurations
from utils.canvas import Canvas
from gui.property_tree_editor import PropertyTreeEditor

# Fixed UI dimensions (pixels)
SIDE_PANEL_WIDTH_PX = 350



# class MainMenu(MenuBar):
#     '''
#     Wrapper around the existing MenuBar. The GUI root should pass in the current
#     menu configuration using the central callbacks configuration.
#     '''
#     def __init__(self, menu_config: Optional[dict] = None, **kwargs):
#         super().__init__(menu_config=menu_config or {}, **kwargs)


class SidePanel(ScrollView):
    '''
    Fixed-width side panel with GridSelector and ToolSelector.
    Intended width: 150 px (size_hint_x=None, width=150 on attach).
    '''
    def __init__(self, grid_callback: Optional[Callable[[float], None]] = None,
                 tool_callback: Optional[Callable[[str], None]] = None,
                 **kwargs):
        super().__init__(
            size_hint=(1, 1),
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=8,
            bar_color=DARK,
            bar_inactive_color=DARK,
            scroll_type=['bars', 'content'],
            **kwargs
        )

        self.grid_callback = grid_callback
        self.tool_callback = tool_callback

        # Background for scrollview viewport
        with self.canvas.before:
            Color(*DARK)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *_: setattr(self._bg, 'pos', self.pos),
                  size=lambda *_: setattr(self._bg, 'size', self.size))

        # Content layout
        self.layout = BoxLayout(
            orientation='vertical',
            padding=10,
            spacing=12,
            size_hint_y=None
        )
        self.layout.bind(minimum_height=self.layout.setter('height'))
        self.add_widget(self.layout)

        # Widgets
        self.grid_selector = GridSelector(callback=self._on_grid_changed)
        self.layout.add_widget(self.grid_selector)

        self.tool_selector = ToolSelector(callback=self._on_tool_selected)
        self.layout.add_widget(self.tool_selector)
        
        # Cursor management - set arrow cursor when over side panel
        Window.bind(mouse_pos=self._update_cursor_on_hover)

    def _update_cursor_on_hover(self, window, pos):
        """Set cursor to arrow when mouse is over the side panel."""
        if self.collide_point(*pos):
            Window.set_system_cursor('arrow')

    def _on_grid_changed(self, grid_step: float):
        if self.grid_callback:
            try:
                self.grid_callback(grid_step)
            except Exception:
                pass

    def _on_tool_selected(self, tool: str):
        if self.tool_callback:
            try:
                self.tool_callback(tool)
            except Exception:
                pass


class Editor(BoxLayout):
    '''
    Editor wrapper hosting the mm-based Canvas.
    '''
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        with self.canvas.before:
            Color(*DARK_LIGHTER)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *_: setattr(self._bg, 'pos', self.pos),
                  size=lambda *_: setattr(self._bg, 'size', self.size))

        self.canvas_view = Canvas(
            width_mm=210.0, height_mm=297.0,
            background_color=LIGHT_DARKER,
            border_color=DARK,
            border_width_px=1.0,
            keep_aspect=True,
            scale_to_width=True,
            enable_keyboard=True  # Enable keyboard for editor canvas
        )
        self.add_widget(self.canvas_view)

    def get_canvas(self) -> Canvas:
        return self.canvas_view


class PrintView(BoxLayout):
    '''
    Print preview wrapper hosting a Canvas (typically keep_aspect True).
    '''
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        with self.canvas.before:
            Color(*DARK)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *_: setattr(self._bg, 'pos', self.pos),
                  size=lambda *_: setattr(self._bg, 'size', self.size))

        self.canvas_view = Canvas(
            width_mm=210.0, height_mm=297.0,
            background_color=(1, 1, 1, 1),
            border_color=LIGHT_DARKER,
            border_width_px=1.0,
            keep_aspect=True,
            scale_to_width=True
        )
        self.add_widget(self.canvas_view)

    def get_canvas(self) -> Canvas:
        return self.canvas_view



class GUI(BoxLayout):
    '''
    New GUI root container assembling:
      - MainMenu() on top
      - Nested SplitView structure underneath to emulate 3 panels horizontally,
        with the center panel itself split vertically.
    '''
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)

        # Top: menu bar using the central callbacks config
        try:
            menu_cfg = create_menu_config(self)
        except Exception:
            menu_cfg = {}
        self.menu_bar = MenuBar(menu_cfg)
        self.add_widget(self.menu_bar)

        # Menu/file integration (wired later by App/FileManager)
        self.file_manager = None

        # Prepare references
        self.side_panel: Optional[SidePanel] = None
        self.editor: Optional[Editor] = None
        self.property_tree: Optional[PropertyTreeEditor] = None

        # Build nested split structure
        self._build_splits()

    # ----- Layout assembly -----
    def _build_splits(self):
        # OUTER: Simple horizontal BoxLayout with fixed-width left panel
        self.outer_layout = BoxLayout(orientation='horizontal', spacing=0)

        # LEFT: SidePanel (fixed width)
        self.side_panel = SidePanel(
            grid_callback=self._on_grid_step_changed,
            tool_callback=self._on_tool_selected
        )
        self.side_panel.size_hint_x = None
        self.side_panel.width = SIDE_PANEL_WIDTH_PX

        # CENTER: Editor only (keyboard is drawn as overlay in the editor canvas)
        self.editor = Editor()

        # RIGHT: PropertyTreeEditor
        self.property_tree = PropertyTreeEditor()

        # MID-RIGHT horizontal split: [center_split | sash(80) | property_tree]
        self.mid_right_split = SplitView(
            orientation='horizontal',
            sash_width=80,
            split_ratio=0.6,
            sash_color=DARK,
            min_left_size=40,
            min_right_size=0
        )
        # Tighten snap threshold for right-panel snap-to-fit
        self.mid_right_split.snap_threshold = 80
        self.mid_right_split.set_left(self.editor)
        self.mid_right_split.set_right(self.property_tree)

        # Connect property tree to sash for tooltip display
        self.property_tree.tooltip_sash = self.mid_right_split.sash

        # Disable cross-linking to avoid accidental vertical sash changes from horizontal sash
        
        # Initialize default toolbar for vertical sash (always visible buttons with tooltips)
        try:
            # Create minimal toolbar config with tooltips (callbacks will be set later)
            default_toolbar = {
                'previous': (None, 'Previous page'),
                'next': (None, 'Next page'),
            }
            #self.mid_right_split.sash.set_configs(default_toolbar=default_toolbar)
        except Exception as e:
            print(f"Error initializing default toolbar: {e}")

        # Attach to OUTER BoxLayout
        self.outer_layout.add_widget(self.side_panel)       # fixed width left panel
        self.outer_layout.add_widget(self.mid_right_split)  # fills remaining space to the right

        # Add to GUI root
        self.add_widget(self.outer_layout)


    # ----- Compatibility API expected by App and menu callbacks -----

    # Menu delegates
    def set_file_manager(self, fm):
        self.file_manager = fm

    def on_new(self):
        if self.file_manager:
            try:
                self.file_manager.new_file()
            except Exception:
                pass

    def on_load(self):
        if self.file_manager:
            try:
                self.file_manager.open_file()
            except Exception:
                pass

    def on_save(self):
        if self.file_manager:
            try:
                self.file_manager.save_file()
            except Exception:
                pass

    def on_save_as(self):
        if self.file_manager:
            try:
                self.file_manager.save_file_as()
            except Exception:
                pass

    def on_exit(self):
        """Exit the application with unsaved changes check."""
        # Use file manager's exit_app which guards against unsaved changes
        self.file_manager.exit_app()

    def on_cut(self):
        """Cut selected elements (Ctrl+X)."""
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        
        popup = Popup(
            title='Info',
            content=Label(text='Pasting finally requires mouse cursor position.\nUse Ctrl/Cmd + X/C/V for cut/copy/paste.'),
            size_hint=(None, None),
            size=(800, 200)
        )
        popup.open()

    def on_copy(self):
        """Copy selected elements (Ctrl+C)."""
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        
        popup = Popup(
            title='Info',
            content=Label(text='Pasting finally requires mouse cursor position.\nUse Ctrl/Cmd + X/C/V for cut/copy/paste.'),
            size_hint=(None, None),
            size=(800, 200)
        )
        popup.open()

    def on_paste(self):
        """Paste elements from clipboard (Ctrl+V)."""
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        
        popup = Popup(
            title='Info',
            content=Label(text='Pasting finally requires mouse cursor position.\nUse Ctrl/Cmd + X/C/V for cut/copy/paste.'),
            size_hint=(None, None),
            size=(800, 200)
        )
        popup.open()

    def on_about(self):
        ...
    
    def on_test_score_generation(self):
        """Run the test score generation script."""
        try:
            import importlib
            import manipulate_score
            
            # Reload the module to pick up any changes during development
            importlib.reload(manipulate_score)
            
            # Get the piano roll editor from the canvas
            canvas = self.editor.get_canvas() if self.editor else None
            piano_roll_editor = getattr(canvas, 'piano_roll_editor', None) if canvas else None
            
            # Get the score from the piano roll editor
            score = piano_roll_editor.score if piano_roll_editor else None
            
            if score is None:
                print("ERROR: No score available for test generation")
                return
            
            # Run the test script
            print("\n=== Running Test Score Generation ===")
            manipulate_score.run_test(score, piano_roll_editor)
            print("=== Test Complete ===\n")
            
        except Exception as e:
            print(f"ERROR: Test score generation failed: {e}")
            import traceback
            traceback.print_exc()

    # Getters to match existing App expectations
    def get_editor_widget(self):
        try:
            return self.editor.get_canvas() if self.editor else None
        except Exception:
            return None

    def get_preview_widget(self):
        # No preview widget since PropertyTreeEditor is now in the right panel
        return None

    def get_side_panel(self):
        return self.side_panel

    def get_properties_widget(self):
        return self.property_tree

    # Properties tree wiring hooks
    def set_properties_score(self, score):
        try:
            if self.property_tree:
                self.property_tree.set_score(score)
        except Exception:
            pass

    def bind_properties_change(self, cb: Callable):
        try:
            if self.property_tree:
                self.property_tree.on_change = cb
        except Exception:
            pass

    # ----- Callbacks for SidePanel -----
    def _on_tool_selected(self, tool_name: str):
        # no-op here, but available for hooking (e.g., contextual toolbars)
        pass

    def _on_grid_step_changed(self, grid_step: float):
        # No action needed - Canvas reads grid step directly from editor.grid_selector
        pass
    
    # ----- Contextual Toolbar Management -----
    def set_contextual_toolbar(self, buttons_config: dict):
        """Update the vertical sash's contextual toolbar with tool-specific buttons.
        
        Args:
            buttons_config: Dictionary mapping icon names to (callback, tooltip) tuples.
                           Example: {'noteLeft': (callback_fn, 'Move to left hand')}
        """
        try:
            if self.mid_right_split and hasattr(self.mid_right_split, 'sash'):
                # Convert buttons_config into the format expected by ToolSash
                # ToolSash expects contextual_toolbar = {'context_key': {icon: (cb, tip)}}
                # We'll use 'active' as the context key
                contextual_config = {'active': buttons_config}
                self.mid_right_split.sash.set_configs(contextual_toolbar=contextual_config)
                self.mid_right_split.sash.set_context_key('active')
        except Exception as e:
            print(f"Error updating contextual toolbar: {e}")

__all__ = [
    'GUI',
    'MainMenu',
    'SidePanel',
    'Editor',
    'PrintView',
]