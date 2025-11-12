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
from kivy.metrics import dp
from gui.colors import DARK, DARK_LIGHTER, LIGHT, LIGHT_DARKER, ACCENT_COLOR


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

        # Background
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
            color=LIGHT,
            halign='right',
            valign='middle'
        )
        
        # Prevent wrapping and use Kivy's built-in texture_size for exact width
        self.clock_label.texture_update()
        self.clock_label.width = self.clock_label.texture_size[0] + dp(16)
        
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
            background_normal='',
            background_color=DARK,
            color=LIGHT
        )
        
        # Add hover effect to menu bar button
        self._add_hover_effect(button, DARK, LIGHT)
        
        # Use Kivy's texture_size for exact button width
        button.texture_update()
        button.width = button.texture_size[0] + dp(24)
        
        # Create dropdown and collect all buttons to measure max width
        dropdown = DropDown(auto_width=False)
        
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
        dropdown.bind(on_open=on_dropdown_open)
        dropdown.bind(on_dismiss=on_dropdown_dismiss)
        
        # Style dropdown background
        with dropdown.canvas.before:
            # Background
            Color(*DARK)
            bg = Rectangle(pos=dropdown.pos, size=dropdown.size)
        
        def update_dropdown_graphics(instance, value):
            bg.pos = instance.pos
            bg.size = instance.size
        
        dropdown.bind(pos=update_dropdown_graphics, size=update_dropdown_graphics)
        
        # Add items and track buttons to measure max width
        menu_buttons = []
        for item_name, item_value in items.items():
            if item_name.startswith('---'):
                # Separator (supports '---', '---1', '---2', etc.)
                self._add_separator(dropdown)
            else:
                # Regular menu item or submenu (handled in _add_menu_item)
                btn = self._add_menu_item(dropdown, item_name, item_value)
                if btn:
                    menu_buttons.append(btn)
        
        # Calculate dropdown width from longest menu item using Kivy's texture_size
        max_width = 200  # Minimum width
        for btn in menu_buttons:
            btn.texture_update()
            text_width = btn.texture_size[0]
            if text_width > max_width:
                max_width = text_width
        
        # Set dropdown width to fit longest item + padding (12px left + 12px right)
        dropdown.width = max_width
        
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
        
        # Add hover effect to direct button
        self._add_hover_effect(button, DARK, LIGHT)
        
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

    def _add_hover_effect(self, btn, normal_bg, normal_fg):
        '''Add hover effect to button that inverts background and text colors.'''
        # Store original colors
        btn._normal_bg = normal_bg
        btn._normal_fg = normal_fg
        
        def on_mouse_pos(window, pos):
            '''Check if mouse is over button and update colors.'''
            if btn.get_root_window():  # Only if button is still attached
                if btn.collide_point(*btn.to_widget(*pos)):
                    # Mouse over - invert colors
                    btn.background_color = normal_fg
                    btn.color = normal_bg
                else:
                    # Mouse not over - restore normal colors
                    btn.background_color = normal_bg
                    btn.color = normal_fg
        
        # Bind to window mouse position
        Window.bind(mouse_pos=on_mouse_pos)
        
        # Clean up when button is removed
        def on_parent(instance, value):
            if value is None:  # Button removed from parent
                Window.unbind(mouse_pos=on_mouse_pos)
        
        btn.bind(parent=on_parent)

    def _add_menu_item(self, dropdown, text, value):
        '''Add a menu item to dropdown. Returns the button for width measurement.'''
        # Check if this is a submenu (value is a dict)
        if isinstance(value, dict):
            return self._add_submenu(dropdown, text, value)
        
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
        
        # Set text_size to match button width so halign='left' works
        # This binding ensures text_size updates when button is resized by dropdown
        btn.bind(size=lambda b, s: setattr(b, 'text_size', (s[0], s[1])))
        
        if callback:
            btn.bind(on_release=lambda b: (callback(), dropdown.dismiss()))
            # Add hover effect for enabled items (invert colors on hover)
            self._add_hover_effect(btn, DARK, LIGHT)
        else:
            # Disabled item
            btn.color = DARK_LIGHTER
        
        dropdown.add_widget(btn)
        return btn

    def _add_submenu(self, parent_dropdown, text, items):
        '''Add a submenu item that opens another dropdown. Returns the button for width measurement.'''
        # Create submenu button with arrow indicator
        btn = Button(
            text=text + ' ►',
            size_hint_y=None,
            height=36,
            background_normal='',
            background_color=DARK,
            color=LIGHT,
            halign='left',
            valign='middle',
            padding=(12, 0)
        )
        
        # Set text_size to match button width so halign='left' works
        btn.bind(size=lambda b, s: setattr(b, 'text_size', (s[0], s[1])))
        
        # Add hover effect
        self._add_hover_effect(btn, DARK, LIGHT)
        
        # Create the submenu dropdown
        # Create the submenu dropdown
        submenu = DropDown(auto_width=False)
        
        # Style submenu background
        with submenu.canvas.before:
            # Background
            Color(*DARK)
            bg = Rectangle(pos=submenu.pos, size=submenu.size)
        
        def update_submenu_graphics(instance, value):
            bg.pos = instance.pos
            bg.size = instance.size
        
        submenu.bind(pos=update_submenu_graphics, size=update_submenu_graphics)
        
        # Add submenu items and measure max width
        submenu_buttons = []
        for item_name, item_value in items.items():
            if item_name.startswith('---'):
                # Separator (supports '---', '---1', '---2', etc.)
                self._add_separator(submenu)
            else:
                sub_btn = self._add_menu_item(submenu, item_name, item_value)
                if sub_btn:
                    submenu_buttons.append(sub_btn)
        
        # Calculate submenu width from longest item using Kivy's texture_size
        max_width = 180  # Minimum width
        for sub_btn in submenu_buttons:
            sub_btn.texture_update()
            text_width = sub_btn.texture_size[0]
            if text_width > max_width:
                max_width = text_width
        
        # Set submenu width to fit longest item + padding (12px left + 12px right)
        submenu.width = max_width
        
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
        return btn

    def _add_separator(self, dropdown):
        '''Add a centered separator line to dropdown.'''
        # Container widget for vertical spacing
        sep_container = Widget(size_hint_y=None, height=8)
        
        # We need to bind to the dropdown's width to calculate the line width
        # Line width = 80% of dropdown width, centered with 10% margin on each side
        with sep_container.canvas:
            Color(*LIGHT_DARKER)
            line = Rectangle()
        
        def update_separator(instance, value):
            '''Update separator position and size based on dropdown width.'''
            # Get dropdown width
            if hasattr(dropdown, 'width'):
                line_width = dropdown.width * 0.8
                # Calculate x position relative to sep_container's parent (dropdown)
                # The separator container is positioned at sep_container.x, 
                # and we want to offset 10% from the left edge of the dropdown
                x_offset = dropdown.width * 0.1
                # Center vertically in the container (height=8, line thickness=2)
                y_offset = 3
                
                # Position relative to the separator container itself, not dropdown
                line.pos = (sep_container.x + x_offset, sep_container.y + y_offset)
                line.size = (line_width, 2)  # Width=80% of dropdown, height=2px
        
        # Bind to both dropdown and container changes
        sep_container.bind(pos=update_separator, size=update_separator)
        dropdown.bind(pos=update_separator, size=update_separator, width=update_separator)
        
        dropdown.add_widget(sep_container)

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

