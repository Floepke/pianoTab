"""
Grid Selector Widget for PianoTab GUI (Kivy version).

Allows selecting note length grid and subdivision for cursor snapping.
"""

from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.properties import NumericProperty, StringProperty, ObjectProperty, ListProperty
from kivy.core.window import Window
from kivy.clock import Clock
from gui.colors import DARK, DARK_LIGHTER, LIGHT, LIGHT_DARKER, ACCENT_COLOR


class SpinBox(BoxLayout):
    """
    Custom spinbox widget with +/- buttons and number display label.
    Styled to match the CustomTkinter design.
    Desktop-only (no virtual keyboard).
    """
    
    value = NumericProperty(1)
    min_value = NumericProperty(1)
    max_value = NumericProperty(99)
    
    def __init__(self, **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=None, height=36, spacing=4, **kwargs)
        
        # Decrease button
        self.dec_btn = Button(
            text='−',  # Unicode minus
            size_hint_x=None,
            width=36,
            font_size='20sp',
            bold=True,
            background_color=DARK_LIGHTER,
            background_normal='',
            color=LIGHT
        )
        self.dec_btn.bind(on_press=self.decrease)
        self.add_widget(self.dec_btn)
        
        # Value display label (not editable, prevents keyboard popup)
        self.value_label = Label(
            text='1',
            font_size='16sp',
            color=LIGHT,
            halign='center',
            valign='middle'
        )
        # Background for label
        with self.value_label.canvas.before:
            Color(*DARK)
            self.value_bg = Rectangle(pos=self.value_label.pos, size=self.value_label.size)
        self.value_label.bind(pos=self.update_label_bg, size=self.update_label_bg)
        self.value_label.bind(size=self.value_label.setter('text_size'))
        self.add_widget(self.value_label)
        
        # Increase button
        self.inc_btn = Button(
            text='+',
            size_hint_x=None,
            width=36,
            font_size='20sp',
            bold=True,
            background_color=DARK_LIGHTER,
            background_normal='',
            color=LIGHT
        )
        self.inc_btn.bind(on_press=self.increase)
        self.add_widget(self.inc_btn)
        
        # Bind for mouse wheel support
        self.bind(on_touch_down=self.on_spinbox_touch)
    
    def update_label_bg(self, *args):
        """Update background rectangle for value label."""
        self.value_bg.pos = self.value_label.pos
        self.value_bg.size = self.value_label.size
    
    def on_spinbox_touch(self, instance, touch):
        """Handle mouse wheel scrolling anywhere on spinbox."""
        if self.collide_point(*touch.pos):
            if hasattr(touch, 'button') and touch.button == 'scrollup':
                self.increase()
                return True
            elif hasattr(touch, 'button') and touch.button == 'scrolldown':
                self.decrease()
                return True
        return False
    
    def decrease(self, *args):
        """Decrease value by 1."""
        if self.value > self.min_value:
            self.value -= 1
            self.value_label.text = str(int(self.value))
    
    def increase(self, *args):
        """Increase value by 1."""
        if self.value < self.max_value:
            self.value += 1
            self.value_label.text = str(int(self.value))


class GridButton(Button):
    """Custom styled button for grid selection."""
    
    is_selected = False
    
    def __init__(self, widget_height=96, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = widget_height
        self.background_normal = ''
        self.background_down = ''
        self.halign = 'left'
        self.valign = 'middle'
        self.font_size = '16sp'
        self.bold = False
        self.update_style()
        # Bind size to update text_size for left alignment
        self.bind(size=self._update_text_size)
    
    def _update_text_size(self, *args):
        # Allow halign to take effect
        self.text_size = (self.width - 12, None)
    
    def update_style(self):
        """Update button appearance based on selection state."""
        if self.is_selected:
            self.background_color = ACCENT_COLOR
            self.color = LIGHT
            self.bold = True
        else:
            self.background_color = DARK_LIGHTER
            self.color = LIGHT
            self.bold = False
    
    def set_selected(self, selected):
        """Set selection state."""
        self.is_selected = selected
        self.update_style()


class GridSelector(BoxLayout):
    """
    Grid selector widget for timing/rhythm grid in Kivy.
    
    Features:
    - Label showing calculated grid step in piano ticks
    - List with note length selection buttons
    - Custom SpinBox for subdivision (1-99)
    - Real-time calculation display
    - Callback when grid changes
    """
    
    quarter_note_ticks = NumericProperty(256.0)
    current_grid_step = NumericProperty(256.0)
    callback = ObjectProperty(None, allownone=True)
    
    def __init__(self, callback=None, **kwargs):
        # Set up as vertical BoxLayout with sizing
        kwargs['orientation'] = 'vertical'
        kwargs['padding'] = 8
        kwargs['spacing'] = 8
        kwargs['size_hint_y'] = None
        super().__init__(**kwargs)
        
        self.widget_height = 96  # Standard widget height for consistency
        
        self.callback = callback
        self.current_grid_name = '4 - Quarter'
        self.subdivision = 1
        
        # Define grid lengths with their pianotick values
        self.grid_lengths = [
            ('1 - Whole', 1024.0),
            ('2 - Half', 512.0),
            ('4 - Quarter', 256.0),
            ('8 - Eighth', 128.0),
            ('16 - Sixteenth', 64.0),
            ('32 - 32nd', 32.0),
            ('64 - 64th', 16.0),
            ('128 - 128th', 8.0)
        ]
        
        # Background
        with self.canvas.before:
            Color(*DARK)
            self.bg = Rectangle(pos=self.pos, size=self.size)
        
        # Let widget height follow content height (for panel scrolling)
        self.bind(minimum_height=self.setter('height'))
        
        # Bind to size/pos changes for background
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        
        self.create_widgets()
        self.update_grid_step_label()

    def _get_grid_lengths(self):
        """calculates the right grid lengths based on the file models pianoTick value."""
        pianotick = ...
        return self.grid_lengths
    
    def update_graphics(self, *args):
        """Update all graphics when size/pos changes."""
        self.bg.pos = self.pos
        self.bg.size = self.size
    
    def create_widgets(self):
        """Create all UI components."""
        
        # Grid step display label
        self.grid_label = Label(
            text='Grid Step: 256.0',
            size_hint_y=None,
            height=self.widget_height,
            font_size='16sp',
            bold=True,
            color=LIGHT,
            halign='left',
            valign='middle',
            padding=(8, 0)
        )
        self.grid_label.bind(size=self.grid_label.setter('text_size'))
        self.add_widget(self.grid_label)
        
        # Non-scroll list of grid length buttons
        gridlist_container = BoxLayout(orientation='vertical', size_hint_y=None, padding=(0, 0), spacing=4)
        
        # Background for grid list
        with gridlist_container.canvas.before:
            Color(*DARK_LIGHTER)
            self.scroll_bg = RoundedRectangle(
                pos=gridlist_container.pos,
                size=gridlist_container.size,
                radius=[6]
            )
        gridlist_container.bind(pos=self.update_scroll_bg, size=self.update_scroll_bg)
        
        # Inner layout for buttons (no internal scrolling)
        self.button_layout = BoxLayout(
            orientation='vertical',
            spacing=6,
            size_hint_y=None,
            padding=[4, 6]
        )
        self.button_layout.bind(minimum_height=self.button_layout.setter('height'))
        
        # Create grid buttons
        self.grid_buttons = {}
        for grid_name, ticks in self.grid_lengths:
            btn = GridButton(text=grid_name, widget_height=self.widget_height)
            btn.bind(on_press=lambda instance, name=grid_name: self.select_grid(name))
            self.button_layout.add_widget(btn)
            self.grid_buttons[grid_name] = btn
        
        gridlist_container.add_widget(self.button_layout)
        # Make container follow content height
        self.button_layout.bind(height=lambda inst, val: setattr(gridlist_container, 'height', val + 12))
        self.add_widget(gridlist_container)
        
        # Subdivision section - use BoxLayout
        # Height = widget_height + spinbox_height + spacing + (padding*2)
        # 96 + 36 + 6 + 16 = 154
        subdiv_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=self.widget_height + 36 + 6 + 16,
            spacing=6,
            padding=8
        )
        
        # Background
        with subdiv_container.canvas.before:
            Color(*DARK_LIGHTER)
            self.subdiv_bg = RoundedRectangle(
                pos=subdiv_container.pos,
                size=subdiv_container.size,
                radius=[6]
            )
        subdiv_container.bind(pos=self.update_subdiv_bg, size=self.update_subdiv_bg)
        
        # Label
        subdiv_label = Label(
            text='÷',
            size_hint_y=None,
            height=self.widget_height,
            font_size='48sp',
            color=LIGHT,
            halign='center',
            valign='middle'
        )
        subdiv_label.bind(size=subdiv_label.setter('text_size'))
        subdiv_container.add_widget(subdiv_label)
        
        # SpinBox
        self.spinbox = SpinBox(min_value=1, max_value=99)
        self.spinbox.bind(value=self.on_subdivision_change)
        subdiv_container.add_widget(self.spinbox)
        
        self.add_widget(subdiv_container)
        
        # Update initial selection
        self.update_selection()
    
    def update_scroll_bg(self, instance, value):
        """Update scroll background."""
        self.scroll_bg.pos = instance.pos
        self.scroll_bg.size = instance.size
    
    def update_subdiv_bg(self, instance, value):
        """Update subdivision background."""
        self.subdiv_bg.pos = instance.pos
        self.subdiv_bg.size = instance.size
    
    def select_grid(self, grid_name):
        """Handle grid length selection."""
        self.current_grid_name = grid_name
        self.update_selection()
        self.update_grid_step_label()
        
        if self.callback:
            self.callback(self.current_grid_step)
    
    def update_selection(self):
        """Update visual selection state of buttons."""
        for name, button in self.grid_buttons.items():
            button.set_selected(name == self.current_grid_name)
    
    def on_subdivision_change(self, instance, value):
        """Handle subdivision value change."""
        self.subdivision = int(value)
        self.update_grid_step_label()
        
        if self.callback:
            self.callback(self.current_grid_step)
    
    def update_grid_step_label(self):
        """Update the grid step label with calculated value."""
        self.current_grid_step = self.get_grid_step()
        
        # Format as float with appropriate precision
        grid_text = f'{self.current_grid_step:.6f}'.rstrip('0').rstrip('.')
        if '.' not in grid_text:
            grid_text += '.0'
        
        self.grid_label.text = f'Grid Step: {grid_text}'
    
    def get_grid_step(self):
        """Calculate and return current grid step value in piano ticks."""
        # Find the tick value for current grid
        grid_ticks = 256.0  # Default to quarter note
        for grid_name, ticks in self.grid_lengths:
            if grid_name == self.current_grid_name:
                grid_ticks = ticks
                break
        
        # Calculate grid step (piano ticks divided by subdivision)
        grid_step = grid_ticks / self.subdivision
        return grid_step
    
    def get_current_grid(self):
        """Get the currently selected grid length name."""
        return self.current_grid_name
    
    def get_subdivision(self):
        """Get the current subdivision value."""
        return self.subdivision
    
    def set_subdivision(self, value):
        """Set the subdivision value programmatically."""
        try:
            value = int(value)
            if 1 <= value <= 99:
                self.spinbox.value = value
                self.spinbox.value_label.text = str(value)
            else:
                print(f'Warning: Subdivision value {value} out of range (1-99)')
        except (ValueError, TypeError):
            print(f'Warning: Invalid subdivision value: {value}')


# Export
__all__ = ['GridSelector', 'SpinBox', 'GridButton']
