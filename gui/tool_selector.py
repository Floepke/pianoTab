'''
Tool Selector Widget for pianoTAB GUI (Kivy version).

Replicates the CustomTkinter ToolSelector: a titled label and a scrollable
list of tool buttons with a single-selection highlight and callback.
'''

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.properties import StringProperty, ObjectProperty, ListProperty
from gui.colors_hue import DARK, DARK_LIGHTER, LIGHT, ACCENT_COLOR
from icons.icon import load_icon


class ToolButton(BoxLayout):
    '''A styled button with icon and text that supports a selected state.'''
    is_selected = False

    def __init__(self, text, icon_name=None, on_select=None, **kwargs):
        super().__init__(
            orientation='horizontal',
            size_hint_y=None,
            height=96,
            spacing=8,
            padding=[8, 0, 8, 0],
            **kwargs
        )
        
        self.text = text
        self._on_select = on_select
        
        # Background color
        with self.canvas.before:
            self.bg_color = Color(*DARK_LIGHTER)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        # Icon (if provided)
        self.icon_widget = None
        if icon_name:
            icon_texture = load_icon(icon_name)
            if icon_texture:
                self.icon_widget = Image(
                    texture=icon_texture.texture,
                    size_hint=(None, None),
                    size=(96, 96),
                    fit_mode='contain'
                )
                self.add_widget(self.icon_widget)
        
        # Text label
        self.label = Label(
            text=text,
            font_size='16sp',
            bold=False,
            color=LIGHT,
            halign='left',
            valign='middle',
            text_size=(None, None)
        )
        self.label.bind(size=self._update_text_size)
        self.add_widget(self.label)
        
        # Handle clicks
        self.bind(on_touch_down=self._on_touch_down)
        
        self._update_style()
    
    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
    
    def _update_text_size(self, *args):
        self.label.text_size = (self.label.width, None)
    
    def _on_touch_down(self, instance, touch):
        if self.collide_point(*touch.pos):
            if self._on_select:
                self._on_select(self.text)
            return True
        return False

    def set_selected(self, selected: bool):
        self.is_selected = selected
        self._update_style()

    def _update_style(self):
        if self.is_selected:
            # Highlighted look with accent color
            self.bg_color.rgba = ACCENT_COLOR
            self.label.color = LIGHT
            self.label.bold = True
        else:
            # Normal look
            self.bg_color.rgba = DARK_LIGHTER
            self.label.color = LIGHT
            self.label.bold = False


class ToolSelector(BoxLayout):
    '''
    Kivy Tool Selector with label + list of predefined tools.

    Properties:
    - current_tool: name of the selected tool
    - callback: optional callable(tool_name) invoked on selection
    '''

    current_tool = StringProperty('Note')
    callback = ObjectProperty(None, allownone=True)
    tools = ListProperty([
        'Note', 'Grace-note', 'Beam', 'Line-break',
        'Count-line', 'Text', 'Slur', 'Tempo'
    ])
    # Map tool names to icon names (without .png extension)
    tool_icons = {
        'Note': 'note',
        'Grace-note': 'gracenote',
        'Beam': 'beam',
        'Line-break': 'linebreak',
        'Count-line': 'countline',
        'Text': 'text',
        'Slur': 'slur',
        'Tempo': 'tempo'
    }

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
            icon_name = self.tool_icons.get(name)  # Get icon name or None
            btn = ToolButton(text=name, icon_name=icon_name, on_select=self.select_tool)
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
