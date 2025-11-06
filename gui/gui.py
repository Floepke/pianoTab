'''
New modular GUI scaffold for pianoTAB.

- MainMenu(): wraps the existing MenuBar using the current callbacks config
- SidePanel(): fixed-width vertical panel with GridSelector + ToolSelector
- Editor(): wrapper hosting the mm-based Canvas
- PrintView(): wrapper hosting a Canvas configured for preview
- TreeViewEditor(): temporary stub below the Editor (to be replaced later)

Layout:
  Root (vertical)
    - MainMenu() at the top
    - OuterSplit (horizontal, 3 logical areas via nesting)
        [Left: SidePanel (fixed width, outer sash width = 0, not resizable)]
        [Right: MidRightSplit (horizontal, sash 40px)]
                     [Left: CenterSplit (vertical, sash 40px)]
                                [Top   : Editor()]
                                [Bottom: TreeViewEditor()]
                     [Right: PrintView()]

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

from gui.colors import DARK, DARK_LIGHTER, LIGHT, LIGHT_DARKER
from gui.menu_bar import MenuBar
from gui.grid_selector import GridSelector
from gui.tool_selector import ToolSelector
from gui.split_view import SplitView
from gui.callbacks import create_menu_config  # reuse existing menu configuration
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
            background_color=(1, 1, 1, 1),
            border_color=DARK,
            border_width_px=1.0,
            keep_aspect=True,
            scale_to_width=True
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


class TreeViewEditor(BoxLayout):
    '''
    Temporary stub for the property tree editor area (bottom panel).
    Replace later with a real PropertyTreeEditor implementation.
    '''
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        with self.canvas.before:
            Color(*DARK_LIGHTER)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *_: setattr(self._bg, 'pos', self.pos),
                  size=lambda *_: setattr(self._bg, 'size', self.size))

        lbl = Label(
            text='Tree View Editor (stub)\nReplace with PropertyTreeEditor later',
            size_hint=(1, 1),
            color=LIGHT,
            font_size='16sp',
            halign='center',
            valign='middle'
        )
        lbl.bind(size=lbl.setter('text_size'))
        self.add_widget(lbl)


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
        self.print_view: Optional[PrintView] = None

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

        # CENTER-VERTICAL: Editor (top) + Tree (bottom) via a vertical split (40px sash)
        self.center_split = SplitView(
            orientation='vertical',
            sash_width=40,
            split_ratio=0.75,
            sash_color=DARK,
            min_left_size=80,
            min_right_size=0
        )

        self.editor = Editor()
        self.property_tree = PropertyTreeEditor()
        self.center_split.set_left(self.editor)
        self.center_split.set_right(self.property_tree)

        # RIGHT: PrintView
        self.print_view = PrintView()

        # MID-RIGHT horizontal split: [center_split | sash(40) | print_view]
        self.mid_right_split = SplitView(
            orientation='horizontal',
            sash_width=40,
            split_ratio=0.6,
            sash_color=DARK,
            min_left_size=40,
            min_right_size=0
        )
        # Tighten snap threshold for right-panel snap-to-fit
        self.mid_right_split.snap_threshold = 80
        self.mid_right_split.set_left(self.center_split)
        self.mid_right_split.set_right(self.print_view)

        # Cross-link the 40px sashes for combined X/Y deltas while dragging
        try:
            self.mid_right_split.sash.set_linked_split(self.center_split)
            self.center_split.sash.set_linked_split(self.mid_right_split)
        except Exception:
            pass

        # Attach to OUTER BoxLayout
        self.outer_layout.add_widget(self.side_panel)       # fixed width left panel
        self.outer_layout.add_widget(self.mid_right_split)  # fills remaining space to the right

        # Add to GUI root
        self.add_widget(self.outer_layout)

        # Setup right-panel snap-to-fit for A4 aspect on the mid-right split and keep updated
        Clock.schedule_once(self._setup_preview_snap_ratio, 0)
        self.mid_right_split.bind(size=lambda *_: self._setup_preview_snap_ratio())

    def _setup_preview_snap_ratio(self, *_):
        '''
        Calculate and set the snap ratio on the mid-right split so the right panel
        (print preview) snaps to the exact width where an A4 page fits fully:
          right_width == right_height / (height_mm / width_mm).
        Uses a snap threshold of 40 px on the vertical sash.
        '''
        sp = getattr(self, 'mid_right_split', None)
        if not sp:
            return
        # Wait until sizes are ready
        if sp.width <= 0 or sp.height <= 0:
            Clock.schedule_once(self._setup_preview_snap_ratio, 0)
            return

        # Determine A4 aspect ratio from the print view canvas
        try:
            cv = self.print_view.get_canvas() if self.print_view else None
        except Exception:
            cv = None
        page_w_mm = getattr(cv, 'width_mm', 210.0) if cv else 210.0
        page_h_mm = getattr(cv, 'height_mm', 297.0) if cv else 297.0
        aspect_ratio = (page_h_mm / page_w_mm) if page_w_mm else (297.0 / 210.0)

        # Ensure the desired snap threshold and compute snap ratio
        try:
            sp.snap_threshold = 80
        except Exception:
            pass
        sp.set_snap_ratio_from_aspect(aspect_ratio)

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
        try:
            from kivy.app import App
            App.get_running_app().stop()
        except Exception:
            pass

    def on_about(self):
        ...

    # Getters to match existing App expectations
    def get_editor_widget(self):
        try:
            return self.editor.get_canvas() if self.editor else None
        except Exception:
            return None

    def get_preview_widget(self):
        try:
            return self.print_view.get_canvas() if self.print_view else None
        except Exception:
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
        try:
            if self.editor and isinstance(self.editor, Editor):
                cv = self.editor.get_canvas()
                if cv:
                    cv.set_grid_step(grid_step)
        except Exception:
            pass


__all__ = [
    'GUI',
    'MainMenu',
    'SidePanel',
    'Editor',
    'PrintView',
    'TreeViewEditor',
]