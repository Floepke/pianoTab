'''
Menu Bar Widget for pianoTAB (Kivy).
Provides File/Edit/View/Help menus similar to traditional desktop apps.
'''

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line
from kivy.clock import Clock
from kivy.core.window import Window
from gui.colors import DARK, DARK_LIGHTER, LIGHT


class MenuBar(BoxLayout):
    '''
    Application menu bar configured via dictionary.
    
    Configuration format:
        menu_config = {
            'File': {                      # Dict value = dropdown menu
                'New': on_new,             # Callable = menu item
                'Open': (on_open, 'Ctrl+O'),  # Tuple = (callback, tooltip)
                'Recent': {                # Nested dict = submenu (future)
                    'File1': on_file1
                },
                '---': None,               # '---' = separator
                'Exit': on_exit
            },
            'Help': on_help                # Callable at top = direct button
        }
    
    Value types:
        - dict: Creates dropdown menu
        - callable: Menu item or direct button
        - (callable, str): Menu item with tooltip
        - None: Menu item (disabled)
        - '---' key: Separator
    '''

    def __init__(self, menu_config=None, **kwargs):
        kwargs['orientation'] = 'horizontal'
        kwargs['size_hint_y'] = None
        kwargs['height'] = 32
        kwargs['spacing'] = 0
        super().__init__(**kwargs)

        # Background (no border on menu bar)
        with self.canvas.before:
            Color(*DARK)
            self.bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        # Store menu references by name
        self.menus = {}

        # Build menus from config (before adding spacer!)
        if menu_config:
            self._build_from_config(menu_config)

        # Spacer to push menus to the left (add AFTER menus)
        self.add_widget(BoxLayout())

        # Right-aligned clock (HH:MM:SS)
        self.clock_label = Label(
            text='00:00:00',
            size_hint_x=None,
            width=96,
            color=LIGHT,
            halign='right',
            valign='middle'
        )
        # Keep text aligned within label width
        # set text_size width and height so Kivy doesn't wrap the last char to a new line
        self.clock_label.bind(size=lambda lbl, s: setattr(lbl, 'text_size', (s[0] - 8, s[1])))
        self.add_widget(self.clock_label)

        # Start timer to update every second
        try:
            Clock.schedule_interval(self._update_clock, 1.0)
            self._update_clock(0)
        except Exception:
            pass
        
        # Cursor management - set arrow cursor when over menu bar
        Window.bind(mouse_pos=self._update_cursor_on_hover)
    
    def _update_cursor_on_hover(self, window, pos):
        """Set cursor to arrow when mouse is over the menu bar."""
        if self.collide_point(*pos):
            Window.set_system_cursor('arrow')

    def _build_from_config(self, config):
        '''Build menu structure from configuration dict.'''
        for menu_name, menu_value in config.items():
            if isinstance(menu_value, dict):
                # Dict = dropdown menu
                button = self._create_dropdown_button(menu_name, menu_value)
            else:
                # Callable/tuple/None = direct button
                button = self._create_direct_button(menu_name, menu_value)
            
            # Store reference
            attr_name = menu_name.lower().replace(' ', '_') + '_menu'
            self.menus[menu_name] = button
            setattr(self, attr_name, button)
            
            # Add button directly (spacer doesn't exist yet)
            self.add_widget(button)

    def _create_dropdown_button(self, text, items):
        '''Create a button with dropdown menu.'''
        button = Button(
            text=text,
            size_hint_x=None,
            width=80,
            background_normal='',
            background_color=DARK,
            color=LIGHT
        )
        
        # Calculate dropdown width based on longest menu item text
        # Use ~10 pixels per character to account for variable-width fonts
        # (wider letters like W, M, S need more space than dots or i)
        max_text_length = max((len(item_name) for item_name in items.keys() if item_name != '---'), default=10)
        dropdown_width = max(200, max_text_length * 10 + 60)  # Minimum 200px, generous padding
        
        dropdown = DropDown(auto_width=False, width=dropdown_width)
        
        # Cursor management for dropdown - set arrow cursor when dropdown is open
        def update_dropdown_cursor(window, pos):
            if dropdown.parent and dropdown.collide_point(*pos):
                Window.set_system_cursor('arrow')
        
        # Bind cursor handler when dropdown opens
        def on_dropdown_open(instance):
            Window.bind(mouse_pos=update_dropdown_cursor)
        
        # Unbind cursor handler when dropdown closes
        def on_dropdown_dismiss(instance):
            Window.unbind(mouse_pos=update_dropdown_cursor)
        
        dropdown.bind(on_open=on_dropdown_open)
        dropdown.bind(on_dismiss=on_dropdown_dismiss)
        
        # Style dropdown background with border
        with dropdown.canvas.before:
            # Background
            Color(*DARK)
            bg = Rectangle(pos=dropdown.pos, size=dropdown.size)
            # Border
            Color(*DARK_LIGHTER)
            border = Line(rectangle=(dropdown.x, dropdown.y, dropdown.width, dropdown.height), width=1)
        
        def update_dropdown_graphics(instance, value):
            bg.pos = instance.pos
            bg.size = instance.size
            border.rectangle = (instance.x, instance.y, instance.width, instance.height)
        
        dropdown.bind(pos=update_dropdown_graphics, size=update_dropdown_graphics)
        
        # Add items
        for item_name, item_value in items.items():
            if item_name == '---':
                # Separator
                self._add_separator(dropdown)
            else:
                # Regular menu item or submenu (handled in _add_menu_item)
                self._add_menu_item(dropdown, item_name, item_value)
        
        button.bind(on_release=dropdown.open)
        button.dropdown = dropdown
        return button

    def _create_direct_button(self, text, value):
        '''Create a direct button (no dropdown).'''
        button = Button(
            text=text,
            size_hint_x=None,
            width=80,
            background_normal='',
            background_color=DARK,
            color=LIGHT
        )
        
        # Extract callback and tooltip
        callback = None
        tooltip = None
        
        if isinstance(value, tuple):
            callback, tooltip = value[0], value[1] if len(value) > 1 else None
        elif callable(value):
            callback = value
        
        if callback:
            button.bind(on_release=lambda btn: callback())
        
        # TODO: Add tooltip support if needed
        
        return button

    def _add_menu_item(self, dropdown, text, value):
        '''Add a menu item to dropdown.'''
        # Check if this is a submenu (value is a dict)
        if isinstance(value, dict):
            self._add_submenu(dropdown, text, value)
            return
        
        # Extract callback and tooltip
        callback = None
        tooltip = None
        
        if isinstance(value, tuple):
            callback, tooltip = value[0], value[1] if len(value) > 1 else None
        elif callable(value):
            callback = value
        
        # Create button
        btn = Button(
            text=text,
            size_hint_y=None,
            height=36,
            background_normal='',
            background_color=DARK,
            color=LIGHT,
            halign='left',
            valign='middle',
            padding=(12, 0)  # Left padding for text
        )
        # Set text_size to enable text alignment, but make it wide enough to prevent wrapping
        btn.bind(size=lambda b, s: setattr(b, 'text_size', (s[0] - 24, s[1])))
        
        if callback:
            btn.bind(on_release=lambda b: (callback(), dropdown.dismiss()))
        else:
            # Disabled item
            btn.color = DARK_LIGHTER
        
        dropdown.add_widget(btn)

    def _add_submenu(self, parent_dropdown, text, items):
        '''Add a submenu item that opens another dropdown.'''
        # Create submenu button with arrow indicator
        btn = Button(
            text=text + ' ►',
            size_hint_y=None,
            height=36,
            background_normal='',
            background_color=DARK,
            color=LIGHT,
            halign='left',
            valign='middle'
        )
        # Don't set text_size to prevent text wrapping
        
        # Calculate submenu width based on longest item text
        # Estimate ~7 pixels per character + padding
        max_text_length = max((len(item_name) for item_name in items.keys() if item_name != '---'), default=10)
        submenu_width = max(180, max_text_length * 7 + 40)  # Minimum 180px
        
        # Create the submenu dropdown
        submenu = DropDown(auto_width=False, width=submenu_width)
        
        # Style submenu background with border
        with submenu.canvas.before:
            # Background
            Color(*DARK)
            bg = Rectangle(pos=submenu.pos, size=submenu.size)
            # Border
            Color(*DARK_LIGHTER)
            border = Line(rectangle=(submenu.x, submenu.y, submenu.width, submenu.height), width=1)
        
        def update_submenu_graphics(instance, value):
            bg.pos = instance.pos
            bg.size = instance.size
            border.rectangle = (instance.x, instance.y, instance.width, instance.height)
        
        submenu.bind(pos=update_submenu_graphics, size=update_submenu_graphics)
        submenu.bind(
            pos=lambda w, p: setattr(bg, 'pos', p),
            size=lambda w, s: setattr(bg, 'size', s)
        )
        
        # Add submenu items
        for item_name, item_value in items.items():
            if item_name == '---':
                self._add_separator(submenu)
            else:
                self._add_menu_item(submenu, item_name, item_value)
        
        # Open submenu on hover/click
        def open_submenu(button_instance):
            # Open submenu attached to the button (needed to build/size it)
            submenu.open(button_instance)

            # Reposition on the next frame using absolute window coordinates
            def _reposition(_dt):
                # Bottom-left of button in window coords
                bx, by = button_instance.to_window(*button_instance.pos)
                # Desired position: right-aligned to button, tops aligned
                new_x = bx + button_instance.width
                new_y = by + button_instance.height - submenu.height

                # Clamp to window bounds to avoid off-screen rendering
                if new_x + submenu.width > Window.width:
                    new_x = max(0, Window.width - submenu.width)
                if new_y < 0:
                    new_y = 0
                if new_y + submenu.height > Window.height:
                    new_y = max(0, Window.height - submenu.height)

                submenu.pos = (new_x, new_y)

            Clock.schedule_once(_reposition, 0)
        
        btn.bind(on_release=open_submenu)
        
        # Store submenu reference
        btn.submenu = submenu
        
        parent_dropdown.add_widget(btn)

    def _add_separator(self, dropdown):
        '''Add a separator line to dropdown.'''
        sep = Widget(size_hint_y=None, height=1)
        with sep.canvas:
            Color(*DARK_LIGHTER)
            rect = Rectangle(pos=sep.pos, size=sep.size)
        sep.bind(
            pos=lambda w, p: setattr(rect, 'pos', p),
            size=lambda w, s: setattr(rect, 'size', s)
        )
        dropdown.add_widget(sep)

    def _update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

    # ---------- Clock ----------

    def _update_clock(self, _dt):
        try:
            from datetime import datetime
            now = datetime.now().strftime('%H:%M:%S')
            if getattr(self, 'clock_label', None) is not None:
                self.clock_label.text = now
        except Exception:
            pass

