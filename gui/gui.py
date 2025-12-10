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
        [Right: MidRightSplit (horizontal, sash 80px with contextual toolbar)]
                     [Left: CenterSplit (vertical, sash 80px for tooltips)]
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
from kivy.core.window import Window

from gui.colors import DARK, DARK_LIGHTER, LIGHT, LIGHT_DARKER
from gui.menu_bar import MenuBar
from gui.grid_selector import GridSelector
from gui.tool_selector import ToolSelector
from gui.split_view import SplitView
from gui.callbacks import create_menu_config, create_default_toolbar_config, create_contextual_toolbar_config  # toolbar configurations
from utils.canvas import Canvas
from gui.property_tree_editor import PropertyTreeEditor
from gui.keyboard_panel import KeyboardPanel
from gui.keyboard_overlay import KeyboardCursorOverlay
from gui.base_grid_editor import BaseGridEditor

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
            bar_width=0,
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
            padding=0,
            spacing=0,
            size_hint_y=None
        )
        self.layout.bind(minimum_height=self.layout.setter('height'))
        self.add_widget(self.layout)

        # Widgets:
        self.tool_selector = ToolSelector(callback=self._on_tool_selected)
        self.layout.add_widget(self.tool_selector)

        self.grid_selector = GridSelector(callback=self._on_grid_changed)
        self.layout.add_widget(self.grid_selector)
        
        # self.base_grid_editor = BaseGridEditor()
        # # Hook changes to update SCORE.baseGrid and refresh editor/canvas
        # def _on_basegrid_change(new_grids):
        #     try:
        #         app = self._get_app()
        #         score = getattr(app, 'score', None) if app else None
        #         if score is None and hasattr(self, 'file_manager') and self.file_manager:
        #             score = getattr(self.file_manager, 'score', None)
        #         if score is not None:
        #             score.baseGrid = list(new_grids)
        #             canvas = self.parent.parent.children[0].get_canvas() if hasattr(self, 'parent') else None
        #             # Prefer known editor reference
        #             canvas = self.get_root_window() and getattr(self.parent.parent, 'editor', None).get_canvas() if hasattr(self.parent.parent, 'editor') else canvas
        #             if self.parent and hasattr(self.parent.parent, 'editor'):
        #                 canvas = self.parent.parent.editor.get_canvas()
        #             if canvas is not None:
        #                 try:
        #                     canvas.canvas.ask_update()
        #                     if hasattr(canvas, 'custom_scrollbar'):
        #                         canvas.custom_scrollbar.update_layout()
        #                     ed = getattr(canvas, 'piano_roll_editor', None)
        #                     if ed and hasattr(ed, 'redraw'):
        #                         ed.redraw()
        #                 except Exception:
        #                     pass
        #     except Exception:
        #         pass
        # self.base_grid_editor.on_change = _on_basegrid_change
        # self.layout.add_widget(self.base_grid_editor)
        
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
        # Editor canvas sits above; keyboard panel overlays at bottom in same container
        self.add_widget(self.canvas_view)
        self.keyboard_panel = KeyboardPanel(size_hint_y=None, height=100)
        self.add_widget(self.keyboard_panel)
        # Overlay that draws cursor above the keyboard panel
        self.keyboard_overlay = KeyboardCursorOverlay(size_hint_y=None, height=0)
        self.add_widget(self.keyboard_overlay)

        # Attach panel to the actual piano roll editor once available
        def _attach_if_ready(_dt):
            try:
                ed = getattr(self.canvas_view, 'piano_roll_editor', None)
                if ed is not None:
                    self.keyboard_panel.attach_editor(ed)
                    # Bind panel refresh to canvas layout updates
                    self.canvas_view.bind(on_resize=lambda *args: self.keyboard_panel.refresh())
                    # Also refresh after redraws to follow scroll/zoom
                    self.canvas_view.bind(on_redraw=lambda *args: self.keyboard_panel.refresh())
                    # Attach overlay reference to editor for cursor updates
                    try:
                        ed.gui.keyboard_overlay = self.keyboard_overlay
                    except Exception:
                        pass
                    return  # stop scheduling once attached
            except Exception:
                pass
            Clock.schedule_once(_attach_if_ready, 0.2)

        Clock.schedule_once(_attach_if_ready, 0.2)

    def get_canvas(self) -> Canvas:
        return self.canvas_view

    def get_keyboard_panel(self) -> KeyboardPanel:
        return getattr(self, 'keyboard_panel', None)


class PrintView(BoxLayout):
    '''
    Print preview wrapper hosting a Canvas (typically keep_aspect True).
    '''
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        with self.canvas.before:
            Color(*LIGHT_DARKER)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *_: setattr(self._bg, 'pos', self.pos),
                  size=lambda *_: setattr(self._bg, 'size', self.size))

        self.canvas_view = Canvas(
            width_mm=210.0, height_mm=297.0,
            background_color=LIGHT_DARKER,
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

        # CENTER-VERTICAL: Editor (top) + Tree (bottom) via a vertical split (80px sash for tooltips)
        self.center_split = SplitView(
            orientation='vertical',
            sash_width=30,
            split_ratio=0.75,
            sash_color=DARK,
            min_left_size=80,
            min_right_size=0
        )

        self.editor = Editor()
        self.property_tree = PropertyTreeEditor()
        self.center_split.set_left(self.editor)
        self.center_split.set_right(self.property_tree)
        
        # Connect property tree to sash for tooltip display
        self.property_tree.tooltip_sash = self.center_split.sash
        # Provide the editor canvas to the property tree so it can suppress tooltips when hovering the editor
        try:
            self.property_tree.editor_widget = self.editor.get_canvas()
        except Exception:
            self.property_tree.editor_widget = None

        # Attach to OUTER BoxLayout: remove PrintView and ToolSash; keep only center split
        self.outer_layout.add_widget(self.side_panel)       # fixed width left panel
        self.outer_layout.add_widget(self.center_split)     # editor + tree view only

        # Add to GUI root
        self.add_widget(self.outer_layout)

        # No right panel; remove preview snap setup

    def _simulate_snap_drag(self, *_):
        # Removed: no mid-right split / print view
        return

    def _setup_preview_snap_ratio(self, *_):
        # Removed: no print preview panel
        return

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

    def on_restart(self):
        """Restart the application in-place."""
        try:
            from kivy.app import App
            app = App.get_running_app()
        except Exception:
            app = None
        # Prefer app's restart implementation if present
        if app and hasattr(app, 'restart_app') and callable(app.restart_app):
            try:
                app.restart_app()
                return
            except Exception:
                pass
        # Fallback: exec the current Python interpreter with same args
        try:
            import os, sys
            os.execl(sys.executable, sys.executable, *sys.argv)
        except Exception as e:
            print(f'Failed to restart: {e}')

    def on_set_midi_port(self):
        """Open a dialog to choose a MIDI output port and save to settings."""
        try:
            from kivy.uix.popup import Popup
            from kivy.uix.boxlayout import BoxLayout
            from kivy.uix.button import Button
            from kivy.uix.label import Label
            from kivy.uix.scrollview import ScrollView
            from midi.player import list_output_ports
        except Exception as e:
            print(f'Failed to open MIDI port dialog: {e}')
            return

        ports = []
        try:
            ports = list_output_ports()
        except Exception:
            ports = []

        layout = BoxLayout(orientation='vertical', spacing=8, padding=8)
        layout.add_widget(Label(text='Select MIDI Output Port', size_hint_y=None, height=28))

        sv = ScrollView(size_hint=(1, 1))
        inner = BoxLayout(orientation='vertical', size_hint_y=None, spacing=6)
        inner.bind(minimum_height=inner.setter('height'))
        sv.add_widget(inner)

        if not ports:
            inner.add_widget(Label(text='No MIDI ports found', size_hint_y=None, height=28))
        else:
            for p in ports:
                btn = Button(text=p, size_hint_y=None, height=32)
                def _on_select(instance, port_name=p):
                    try:
                        # Save to settings manager
                        app = self._get_app()
                        if app and hasattr(app, 'settings'):
                            app.settings.set('midi_port', port_name)
                            app.settings.save()
                        print(f'Selected MIDI port: {port_name}')
                    except Exception:
                        pass
                    popup.dismiss()
                btn.bind(on_release=_on_select)
                inner.add_widget(btn)

        layout.add_widget(sv)

        popup = Popup(title='Settings', content=layout, size_hint=(None, None), size=(500, 400))
        popup.open()

    def _get_app(self):
        try:
            from kivy.app import App
            return App.get_running_app()
        except Exception:
            return None

    def on_play_from_cursor(self):
        """Render a short MIDI from current cursor and send to selected port."""
        try:
            from midi.player import build_midi_file, play_file_via_port, get_selected_port
        except Exception as e:
            print(f'MIDI playback unavailable: {e}')
            return

        # Get score and the actual piano-roll editor (not the GUI wrapper)
        try:
            canvas = self.editor.get_canvas() if self.editor else None
            piano_roll_editor = getattr(canvas, 'piano_roll_editor', None) if canvas else None
            score = piano_roll_editor.score if piano_roll_editor else None
        except Exception:
            piano_roll_editor = None
            score = None

        if score is None:
            print('Play: No score available')
            return

        # Get selected port from settings
        app = self._get_app()
        settings = getattr(app, 'settings', None) if app else None
        port_name = get_selected_port(settings) if settings else None
        if not port_name:
            print('Play: No MIDI port selected. Use Settings → Set MIDI port.')
            return

        # Render and play using the actual piano-roll editor for cursor
        if piano_roll_editor is None:
            print('Play: No piano-roll editor attached to canvas')
            return
        midi_path = build_midi_file(score, piano_roll_editor)
        if not midi_path:
            print('Play: Failed to render play.mid')
            return
        ok = play_file_via_port(midi_path, port_name)
        print('Play: sent to port' if ok else 'Play: failed sending to port')

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
            if self.side_panel and hasattr(self.side_panel, 'base_grid_editor') and self.side_panel.base_grid_editor:
                try:
                    self.side_panel.base_grid_editor.set_grids(getattr(score, 'baseGrid', []))
                except Exception:
                    pass
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
    'TreeViewEditor',
]