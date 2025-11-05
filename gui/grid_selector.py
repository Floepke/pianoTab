'''
Grid Selector Widget for pianoTAB GUI (Kivy version).

Allows selecting note length grid and subdivision for cursor snapping.
'''

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.properties import NumericProperty, ObjectProperty
from gui.colors import DARK, DARK_LIGHTER, LIGHT, LIGHT_DARKER, ACCENT_COLOR


class SpinBox(BoxLayout):
    '''
    Custom spinbox widget with +/- buttons and number display label.
    Styled to match the CustomTkinter design.
    Desktop-only (no virtual keyboard).
    '''
    
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
            background_down='',
            color=LIGHT
        )
        self.dec_btn.bind(on_press=self.decrease)
        # Highlight on press
        self._bind_press_highlight(self.dec_btn)
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
            background_down='',
            color=LIGHT
        )
        self.inc_btn.bind(on_press=self.increase)
        # Highlight on press
        self._bind_press_highlight(self.inc_btn)
        self.add_widget(self.inc_btn)
        
        # Bind for mouse wheel support
        self.bind(on_touch_down=self.on_spinbox_touch)

    def _bind_press_highlight(self, btn, normal_color=DARK_LIGHTER, pressed_color=ACCENT_COLOR):
        '''Bind button to show pressed highlight color and restore on release.'''
        def _on_state(instance, state):
            if state == 'down':
                instance.background_color = pressed_color
            else:
                instance.background_color = normal_color
        btn.bind(state=_on_state)
    
    def update_label_bg(self, *args):
        '''Update background rectangle for value label.'''
        self.value_bg.pos = self.value_label.pos
        self.value_bg.size = self.value_label.size
    
    def on_spinbox_touch(self, instance, touch):
        '''Handle mouse wheel scrolling anywhere on spinbox.'''
        if self.collide_point(*touch.pos):
            if hasattr(touch, 'button') and touch.button == 'scrollup':
                self.increase()
                return True
            elif hasattr(touch, 'button') and touch.button == 'scrolldown':
                self.decrease()
                return True
        return False
    
    def decrease(self, *args):
        '''Decrease value by 1.'''
        if self.value > self.min_value:
            self.value -= 1
            self.value_label.text = str(int(self.value))
    
    def increase(self, *args):
        '''Increase value by 1.'''
        if self.value < self.max_value:
            self.value += 1
            self.value_label.text = str(int(self.value))


class ClickableLabel(ButtonBehavior, Label):
    '''Label that can receive click/tap events (via ButtonBehavior).'''
    pass


class GridButton(Button):
    '''Custom styled button for grid selection.'''
    
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
        # Pressed highlight
        self.bind(state=self._on_state_change)
    
    def _update_text_size(self, *args):
        # Allow halign to take effect
        self.text_size = (self.width - 12, None)
    
    def update_style(self):
        '''Update button appearance based on selection state.'''
        if self.is_selected:
            self.background_color = ACCENT_COLOR
            self.color = LIGHT
            self.bold = True
        else:
            self.background_color = DARK_LIGHTER
            self.color = LIGHT
            self.bold = False
    
    def set_selected(self, selected):
        '''Set selection state.'''
        self.is_selected = selected
        self.update_style()

    def _on_state_change(self, instance, value):
        # Temporarily show press highlight; restore style on release
        if value == 'down':
            self._saved_bg = getattr(self, '_saved_bg', self.background_color)
            self.background_color = ACCENT_COLOR
        else:
            # Restore to selected/non-selected style
            self.update_style()


class SubdivContainer(BoxLayout):
    '''Container that intercepts mouse wheel to adjust subdivision when hovered.'''
    def __init__(self, owner, **kwargs):
        super().__init__(**kwargs)
        self._owner = owner

    def on_touch_down(self, touch):
        btn = getattr(touch, 'button', None)
        if btn in ('scrollup', 'scrolldown') and self.collide_point(*touch.pos):
            if btn == 'scrollup':
                self._owner.increase_subdivision()
            elif btn == 'scrolldown':
                self._owner.decrease_subdivision()
            return True
        return super().on_touch_down(touch)


class GridSelector(BoxLayout):
    '''
    Grid selector widget for timing/rhythm grid in Kivy.
    
    Features:
    - Label showing calculated grid step in piano ticks
    - List with note length selection buttons
    - Custom SpinBox for subdivision (1-99)
    - Real-time calculation display
    - Callback when grid changes
    '''
    
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
        
        self.widget_height = 48  # Button height - half of standard 96px
        
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
        '''calculates the right grid lengths based on the file models pianoTick value.'''
        pianotick = ...
        return self.grid_lengths
    
    def update_graphics(self, *args):
        '''Update all graphics when size/pos changes.'''
        self.bg.pos = self.pos
        self.bg.size = self.size
    
    def create_widgets(self):
        '''Create all UI components.'''
        
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
        
        # Subdivision section - bottom DARK_LIGHTER rounded box with centered labels (÷ and number)
        # Layout: [ - button | centered (÷  value) | + button ]
        # Buttons are vertically centered relative to the box; labels centered in the box.
        subdiv_container = SubdivContainer(self,
            orientation='horizontal',
            size_hint_y=None,
            height=96,
            spacing=8,
            padding=(23, 8)
        )
        # Keep a reference for scroll-wheel handling
        self.subdiv_container = subdiv_container
        
        # Background
        with subdiv_container.canvas.before:
            Color(*DARK_LIGHTER)
            self.subdiv_bg = RoundedRectangle(
                pos=subdiv_container.pos,
                size=subdiv_container.size,
                radius=[6]
            )
        subdiv_container.bind(pos=self.update_subdiv_bg, size=self.update_subdiv_bg)
        
        # Left side: '−' button centered vertically
        from kivy.uix.widget import Widget as _W
        left_vbox = BoxLayout(orientation='vertical', size_hint_x=None, width=56)
        left_vbox.add_widget(_W(size_hint_y=1))
        dec_btn = Button(
            text='−',
            size_hint=(None, None),
            width=56,
            height=56,  # was 58; match + button
            font_size='24sp',
            bold=True,
            background_color=DARK,
            background_normal='',
            background_down='',
            color=LIGHT
        )
        dec_btn.bind(on_press=lambda *_: self.decrease_subdivision())
        # Highlight on press tied to accent color
        dec_btn.bind(state=lambda inst, s: setattr(inst, 'background_color', ACCENT_COLOR if s == 'down' else DARK))
        left_vbox.add_widget(dec_btn)
        left_vbox.add_widget(_W(size_hint_y=1))
        subdiv_container.add_widget(left_vbox)

        # Center: both labels centered (÷ and value)
        center_box = BoxLayout(orientation='horizontal', size_hint_x=1, spacing=12)
        # Spacer to center content
        left_spacer = _W(size_hint_x=1)
        right_spacer = _W(size_hint_x=1)

        # Unified clickable label: '÷   <number>'
        self.subdiv_combo_label = ClickableLabel(
            text=f'÷   {int(self.subdivision)}',
            size_hint=(None, None),
            height=56,
            font_size='24sp',
            color=LIGHT,
            halign='center',
            valign='middle'
        )
        # Background for the unified label (no rounded corners for review)
        with self.subdiv_combo_label.canvas.before:
            self._subdiv_combo_bg_color = Color(*DARK_LIGHTER)
            self._subdiv_combo_bg = Rectangle(pos=self.subdiv_combo_label.pos, size=self.subdiv_combo_label.size)
        # Keep background synced to label
        self.subdiv_combo_label.bind(pos=self._update_subdiv_combo_bg, size=self._update_subdiv_combo_bg)
        # Fit label width to its texture + padding; avoid tight loops
        def _fit_combo_label(inst, val):
            target = val[0] + 24
            if abs(inst.width - target) > 0.5:
                inst.width = target
        self.subdiv_combo_label.bind(texture_size=_fit_combo_label)
        # Reset subdivision on click and show pressed highlight
        self.subdiv_combo_label.bind(on_release=lambda *_: self.reset_subdivision())
        # Press highlight: slightly darker on press, match container on release
        #self.subdiv_combo_label.bind(state=lambda inst, s: setattr(self._subdiv_combo_bg_color, 'rgba', LIGHT_DARKER if s == 'down' else DARK_LIGHTER))

        center_box.add_widget(left_spacer)
        center_box.add_widget(self.subdiv_combo_label)
        center_box.add_widget(right_spacer)
        # Wrap center_box in a vertical box to center it vertically
        center_vbox = BoxLayout(orientation='vertical', size_hint_x=1)
        center_vbox.add_widget(_W(size_hint_y=1))
        center_box.size_hint_y = None
        center_box.height = 56
        center_vbox.add_widget(center_box)
        center_vbox.add_widget(_W(size_hint_y=1))
        subdiv_container.add_widget(center_vbox)

        # Right side: '+' button centered vertically
        right_vbox = BoxLayout(orientation='vertical', size_hint_x=None, width=56)
        right_vbox.add_widget(_W(size_hint_y=1))
        inc_btn = Button(
            text='+',
            size_hint=(None, None),
            width=56,
            height=56,
            font_size='24sp',
            bold=True,
            background_color=DARK,
            background_normal='',
            background_down='',
            color=LIGHT
        )
        inc_btn.bind(on_press=lambda *_: self.increase_subdivision())
        # Highlight on press tied to accent color
        inc_btn.bind(state=lambda inst, s: setattr(inst, 'background_color', ACCENT_COLOR if s == 'down' else DARK))
        right_vbox.add_widget(inc_btn)
        right_vbox.add_widget(_W(size_hint_y=1))
        subdiv_container.add_widget(right_vbox)
        
        self.add_widget(subdiv_container)
        
        # Update initial selection
        self.update_selection()
    
    def update_scroll_bg(self, instance, value):
        '''Update scroll background.'''
        self.scroll_bg.pos = instance.pos
        self.scroll_bg.size = instance.size
    
    def update_subdiv_bg(self, instance, value):
        '''Update subdivision background.'''
        self.subdiv_bg.pos = instance.pos
        self.subdiv_bg.size = instance.size
    
    def select_grid(self, grid_name):
        '''Handle grid length selection.'''
        self.current_grid_name = grid_name
        self.update_selection()
        self.update_grid_step_label()
        
        if self.callback:
            self.callback(self.current_grid_step)
    
    def update_selection(self):
        '''Update visual selection state of buttons.'''
        for name, button in self.grid_buttons.items():
            button.set_selected(name == self.current_grid_name)
    
    def on_subdivision_change(self):
        '''Reflect subdivision change into UI and fire callback.'''
        # Update unified label text
        if hasattr(self, 'subdiv_combo_label'):
            self.subdiv_combo_label.text = f'÷   {int(self.subdivision)}'
        self.update_grid_step_label()
        if self.callback:
            self.callback(self.current_grid_step)

    def increase_subdivision(self):
        if self.subdivision < 99:
            self.subdivision += 1
            self.on_subdivision_change()

    def decrease_subdivision(self):
        if self.subdivision > 1:
            self.subdivision -= 1
            self.on_subdivision_change()

    def reset_subdivision(self):
        '''Reset subdivision to 1 and update UI/callback.'''
        if self.subdivision != 1:
            self.subdivision = 1
            self.on_subdivision_change()
    
    def update_grid_step_label(self):
        '''Update the grid step label with calculated value.'''
        self.current_grid_step = self.get_grid_step()
        
        # Format as float with appropriate precision
        grid_text = f'{self.current_grid_step:.6f}'.rstrip('0').rstrip('.')
        if '.' not in grid_text:
            grid_text += '.0'
        
        self.grid_label.text = f'Grid Step: {grid_text}'
    
    def get_grid_step(self):
        '''Calculate and return current grid step value in piano ticks.'''
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
        '''Get the currently selected grid length name.'''
        return self.current_grid_name
    
    def get_subdivision(self):
        '''Get the current subdivision value.'''
        return self.subdivision
    
    def set_subdivision(self, value):
        '''Set the subdivision value programmatically.'''
        try:
            ival = int(value)
            if 1 <= ival <= 99:
                self.subdivision = ival
                self.on_subdivision_change()
            else:
                print(f'Warning: Subdivision value {value} out of range (1-99)')
        except (ValueError, TypeError):
            print(f'Warning: Invalid subdivision value: {value}')

    def _update_subdiv_combo_bg(self, *args):
        if hasattr(self, '_subdiv_combo_bg') and hasattr(self, 'subdiv_combo_label'):
            self._subdiv_combo_bg.pos = self.subdiv_combo_label.pos
            self._subdiv_combo_bg.size = self.subdiv_combo_label.size

    # Intercept mouse wheel when hovering subdivision area to edit subdivision instead of scrolling parent
    def on_touch_down(self, touch):
        try:
            btn = getattr(touch, 'button', None)
        except Exception:
            btn = None
        if btn in ('scrollup', 'scrolldown') and hasattr(self, 'subdiv_container') and self.subdiv_container:
            if self.subdiv_container.collide_point(*touch.pos):
                if btn == 'scrollup':
                    self.increase_subdivision()
                elif btn == 'scrolldown':
                    self.decrease_subdivision()
                # Stop propagation so the outer ScrollView doesn't scroll
                return True
        # Otherwise, use default behavior
        return super().on_touch_down(touch)


# Export
__all__ = ['GridSelector', 'SpinBox', 'GridButton']
