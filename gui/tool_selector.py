"""
Tool Selector Widget for PianoTab GUI (Kivy version).

Replicates the CustomTkinter ToolSelector: a titled label and a scrollable
list of tool buttons with a single-selection highlight and callback.
"""

from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.properties import StringProperty, ObjectProperty, ListProperty
from kivy.clock import Clock
from gui.colors import DARK, DARK_LIGHTER, LIGHT, LIGHT_DARKER


class ToolButton(Button):
    """A styled button that supports a selected state."""
    is_selected = False

    def __init__(self, text, on_select, **kwargs):
        super().__init__(
            text=text,
            size_hint_y=None,
            height=36,
            font_size='16sp',
            bold=False,
            background_normal='',
            background_color=DARK_LIGHTER,
            color=LIGHT,
            **kwargs
        )
        # Left-align text
        self.halign = 'left'
        self.valign = 'middle'
        self.bind(size=self._update_text_size)
        self._on_select = on_select
        self.bind(on_release=self._handle_press)
        self._update_style()

    def _update_text_size(self, *args):
        # Allow halign to take effect
        self.text_size = (self.width - 12, None)

    def _handle_press(self, *args):
        if self._on_select:
            self._on_select(self.text)

    def set_selected(self, selected: bool):
        self.is_selected = selected
        self._update_style()

    def _update_style(self):
        if self.is_selected:
            # Highlighted look
            self.background_color = LIGHT_DARKER
            self.color = DARK
            self.bold = True
        else:
            # Normal look
            self.background_color = DARK_LIGHTER
            self.color = LIGHT
            self.bold = False


class ToolSelector(BoxLayout):
    """
    Kivy Tool Selector with label + list of predefined tools.

    Properties:
    - current_tool: name of the selected tool
    - callback: optional callable(tool_name) invoked on selection
    """

    current_tool = StringProperty('Note')
    callback = ObjectProperty(None, allownone=True)
    tools = ListProperty([
        'Note', 'Grace-note', 'Beam', 'Line-break',
        'Count-line', 'Text', 'Slur', 'Tempo'
    ])

    def __init__(self, callback=None, **kwargs):
        # Set up as vertical BoxLayout with sizing
        kwargs['orientation'] = 'vertical'
        kwargs['padding'] = 8
        kwargs['spacing'] = 8
        kwargs['size_hint_y'] = None
        super().__init__(**kwargs)
        
        self.callback = callback

        # Background
        with self.canvas.before:
            Color(*DARK)
            self.bg = Rectangle(pos=self.pos, size=self.size)

        # Height follows content
        self.bind(minimum_height=self.setter('height'))
        self.bind(pos=self._update_graphics, size=self._update_graphics)

        self._create_widgets()

    def _update_graphics(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def _create_widgets(self):
        # Header label showing selected tool
        self.tool_label = Label(
            text=f'Tool: {self.current_tool}',
            size_hint_y=None,
            height=32,
            font_size='16sp',
            bold=True,
            color=LIGHT,
            halign='left',
            valign='middle',
            padding=(8, 0)
        )
        self.tool_label.bind(size=self.tool_label.setter('text_size'))
        self.add_widget(self.tool_label)

        # Non-scroll list container background
        self.list_container = BoxLayout(orientation='vertical', size_hint_y=None)
        with self.list_container.canvas.before:
            Color(*DARK_LIGHTER)
            self.scroll_bg = RoundedRectangle(pos=self.list_container.pos, size=self.list_container.size, radius=[6])
        self.list_container.bind(pos=self._update_scroll_bg, size=self._update_scroll_bg)

        # Vertical BoxLayout for buttons (expands height to show all)
        self.button_column = BoxLayout(orientation='vertical', size_hint_y=None, padding=(4, 6), spacing=6)
        self.button_column.bind(minimum_height=self._sync_minimum_height)

        self.list_container.add_widget(self.button_column)
        self.add_widget(self.list_container)

        # Create buttons
        self._buttons = {}
        for name in self.tools:
            btn = ToolButton(text=name, on_select=self.select_tool)
            self._buttons[name] = btn
            self.button_column.add_widget(btn)

        # Initial selection
        self._refresh_selection()

    def _update_scroll_bg(self, *args):
        self.scroll_bg.pos = self.list_container.pos
        self.scroll_bg.size = self.list_container.size

    def _sync_minimum_height(self, instance, value):
        # Height should accommodate all children
        total = 0
        for child in self.button_column.children:
            total += child.height + self.button_column.spacing
        # Add padding top/bottom
        self.button_column.height = total + 8
        # Container follows content height
        self.list_container.height = self.button_column.height + 8

    def select_tool(self, tool_name: str):
        if tool_name not in self.tools:
            return
        self.current_tool = tool_name
        self.tool_label.text = f'Tool: {tool_name}'
        self._refresh_selection()
        if self.callback:
            try:
                self.callback(tool_name)
            except Exception:
                # Silent guard; UI callback errors shouldn't break selection
                pass

    def _refresh_selection(self):
        for name, btn in self._buttons.items():
            btn.set_selected(name == self.current_tool)

    # Convenience API
    def get_tool(self):
        return self.current_tool

    def set_tool(self, tool_name: str):
        if tool_name in self.tools:
            self.select_tool(tool_name)
