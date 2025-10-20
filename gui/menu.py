#!/usr/bin/env python3
'''
Custom Menu Bar Widget for PianoTab GUI using CustomTkinter.

Provides a custom menu bar using CustomTkinter styled buttons with popup menus
in borderless windows. The menu looks consistent across all platforms.
'''

import tkinter as tk
import customtkinter as ctk
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import log


class MenuDropdown:
    '''A popup menu window that appears below a menu button.'''
    
    def __init__(self, parent_window, items, callback, menu_name, scale_factor=1.0):
        self.parent_window = parent_window
        self.items = items
        self.callback = callback
        self.menu_name = menu_name
        self.scale_factor = scale_factor
        self.window = None
        self.buttons = []
        
    def _measure_actual_heights(self, main_frame):
        '''Measure the actual heights of buttons and separators after they're created.'''
        # Create a test button to measure its actual height
        test_button = ctk.CTkButton(
            main_frame,
            text="Test Button",
            height=32,
            corner_radius=4,
            anchor='w',
            hover_color=("gray80", "gray20"),
            fg_color="transparent",
            text_color=("black", "white")
        )
        test_button.pack(fill='x', padx=6, pady=2)
        test_button.update_idletasks()
        
        # Get actual button height including padding
        actual_button_height = test_button.winfo_reqheight()
        
        # Create a test separator to measure its height
        test_separator = ctk.CTkFrame(main_frame, height=1, fg_color=("gray60", "gray40"))
        test_separator.pack(fill='x', padx=8, pady=4)
        test_separator.pack_propagate(False)
        test_separator.update_idletasks()
        
        # Get actual separator height including padding
        actual_separator_height = test_separator.winfo_reqheight()
        
        # Clean up test widgets
        test_button.destroy()
        test_separator.destroy()
        
        log(f'📐 Measured heights: button={actual_button_height}px, separator={actual_separator_height}px')
        
        return actual_button_height, actual_separator_height
        
    def show(self, x, y):
        '''Show the dropdown menu at the specified screen coordinates.'''
        if self.window:
            self.hide()
            
        # Create borderless toplevel window
        self.window = ctk.CTkToplevel(self.parent_window)
        self.window.withdraw()  # Hide initially
        
        # Configure window to be borderless and always on top
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        
        # Let CustomTkinter handle scaling naturally - don't override it
        
        # Create main frame with border effect
        main_frame = ctk.CTkFrame(self.window, corner_radius=0, border_width=0)
        main_frame.pack(fill='both', expand=True, padx=0, pady=0)
        
        # Measure actual widget heights first
        actual_button_height, actual_separator_height = self._measure_actual_heights(main_frame)
        
        # Add menu items
        self.buttons = []
        for item in self.items:
            if item == '---':
                # Add separator - create a visible separator frame
                separator_frame = ctk.CTkFrame(main_frame, height=1, fg_color=("gray60", "gray40"))
                separator_frame.pack(fill='x', padx=8, pady=4)
                # Make sure the separator frame doesn't disappear
                separator_frame.pack_propagate(False)
            else:
                # Determine item details
                if isinstance(item, tuple) and len(item) == 2:
                    item_name, item_callback = item
                    if item_callback is None:
                        command = lambda i=item_name: self._on_item_click(i)
                    else:
                        command = lambda i=item_name, c=item_callback: self._on_item_click_custom(i, c)
                else:
                    item_name = item
                    command = lambda i=item_name: self._on_item_click(i)
                
                # Create menu item button
                btn = ctk.CTkButton(
                    main_frame,
                    text=item_name,
                    height=32,  # Increased height
                    corner_radius=4,
                    anchor='w',
                    hover_color=("gray80", "gray20"),
                    fg_color="transparent",
                    text_color=("black", "white"),
                    command=command
                )
                btn.pack(fill='x', padx=6, pady=2)  # Increased padding
                self.buttons.append(btn)
        
        # Calculate window size more accurately
        self.window.update_idletasks()
        
        # Calculate width based on actual text rendering
        min_width = 150
        max_item_width = min_width
        
        # Create a temporary label to measure text accurately
        temp_label = ctk.CTkLabel(self.window, text="Sample")
        temp_label.pack()
        temp_label.update_idletasks()
        
        for item in self.items:
            if item != '---':
                # Get item name
                if isinstance(item, tuple) and len(item) == 2:
                    item_name = item[0]
                else:
                    item_name = item
                
                # Measure text width using temporary label
                temp_label.configure(text=item_name)
                temp_label.update_idletasks()
                text_width = temp_label.winfo_reqwidth() + 40  # Add padding
                max_item_width = max(max_item_width, text_width)
        
        # Clean up temporary label
        temp_label.destroy()
        
        # Ensure minimum and maximum bounds
        window_width = max(min_width, min(max_item_width, 350))  # Increased max width
        
        # Calculate height using actual measured heights
        total_items = len(self.items)
        item_count = len([item for item in self.items if item != '---'])
        separator_count = len([item for item in self.items if item == '---'])
        
        # Use measured heights plus small frame padding
        frame_padding = 8  # Top and bottom padding of main frame
        window_height = (item_count * actual_button_height + 
                        separator_count * actual_separator_height + 
                        frame_padding)
        
        # Ensure minimum height
        min_height = 60  # Reduced minimum height
        window_height = max(window_height, min_height)
        
        # Debug output for sizing
        log(f'📏 Menu sizing: {item_count} buttons x {actual_button_height}px + {separator_count} separators x {actual_separator_height}px + {frame_padding}px padding = {window_height}px total height, width={window_width}px')
        
        # Position window
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # Adjust position if menu would go off screen
        if x + window_width > screen_width:
            x = screen_width - window_width - 10
        if y + window_height > screen_height:
            y = y - window_height - 40  # Show above button instead
            
        self.window.geometry(f'{window_width}x{window_height}+{x}+{y}')
        
        # Show window
        self.window.deiconify()
        
        # Bind clicks outside menu to close it
        self.window.bind('<FocusOut>', lambda e: self._delayed_hide())
        self.window.focus_set()
        
        # Bind escape key to close
        self.window.bind('<Escape>', lambda e: self.hide())
        
        # Start monitoring for outside clicks
        self._monitor_outside_clicks()
        
    def _delayed_hide(self):
        '''Hide menu after a short delay to prevent flickering.'''
        self.window.after(100, lambda: self.hide() if self.window else None)
        
    def _monitor_outside_clicks(self):
        '''Monitor for mouse clicks outside the menu.'''
        def check_click():
            if self.window:
                try:
                    # Get mouse position
                    x, y = self.window.winfo_pointerxy()
                    
                    # Check if mouse is outside menu window
                    mx = self.window.winfo_rootx()
                    my = self.window.winfo_rooty()
                    mw = self.window.winfo_width()
                    mh = self.window.winfo_height()
                    
                    if not (mx <= x <= mx + mw and my <= y <= my + mh):
                        # Check if any mouse button is pressed
                        self.window.after(50, check_click)
                    else:
                        self.window.after(50, check_click)
                except:
                    pass  # Window might be destroyed
        
        self.window.after(50, check_click)
        
    def hide(self):
        '''Hide the dropdown menu.'''
        if self.window:
            self.window.destroy()
            self.window = None
            self.buttons = []
            
    def _on_item_click(self, item_name):
        '''Handle menu item click with default callback.'''
        self.hide()
        if self.callback:
            self.callback(self.menu_name, item_name)
        else:
            log(f'🎯 Menu action: {self.menu_name} -> {item_name}')
            
    def _on_item_click_custom(self, item_name, custom_callback):
        '''Handle menu item click with custom callback.'''
        self.hide()
        if custom_callback:
            custom_callback()
        else:
            # Fallback to default callback if custom callback is None
            if self.callback:
                self.callback(self.menu_name, item_name)
            else:
                log(f'🎯 Menu action: {self.menu_name} -> {item_name}')


class MenuBar:
    '''
    A custom menu bar widget using CustomTkinter styled buttons with popup menus.
    '''
    
    def __init__(self, parent, callback=None, scale_factor=1.0):
        '''
        Initialize the MenuBar widget.
        
        Args:
            parent: Parent widget (customtkinter window)
            callback: Optional callback function(menu_name, item_name)
            scale_factor: Scaling factor for menu fonts (1.0 = normal, 1.5 = 50% larger)
        '''
        self.parent = parent
        self.callback = callback
        self.scale_factor = scale_factor
        
        # Store menu data and references
        self.menus = {}
        self.menu_buttons = {}
        self.current_dropdown = None
        self.menubar_frame = None
        
        # Create the menu bar
        self.create_widget()
        
        # Setup default menus
        self.setup_menu()
    
    def create_widget(self):
        '''Create the custom menu bar widget.'''
        # Create menu bar frame
        self.menubar_frame = ctk.CTkFrame(self.parent, height=40, corner_radius=0)
        self.menubar_frame.pack(fill='x', side='top', padx=0, pady=0)
        self.menubar_frame.pack_propagate(False)  # Maintain fixed height
        
        # Bind clicks outside any menu button to close dropdowns
        self.parent.bind('<Button-1>', self._on_outside_click, add='+')
        
        # Start global click monitoring
        self._setup_global_click_monitoring()
        
    def _setup_global_click_monitoring(self):
        '''Setup global click monitoring to close menus when clicking outside.'''
        def monitor_clicks():
            if self.current_dropdown and self.current_dropdown.window:
                try:
                    # Check if any mouse button is pressed
                    x, y = self.parent.winfo_pointerxy()
                    
                    # Get menu window bounds
                    window = self.current_dropdown.window
                    wx = window.winfo_rootx()
                    wy = window.winfo_rooty()
                    ww = window.winfo_width()
                    wh = window.winfo_height()
                    
                    # Get menu bar bounds  
                    fx = self.menubar_frame.winfo_rootx()
                    fy = self.menubar_frame.winfo_rooty()
                    fw = self.menubar_frame.winfo_width()
                    fh = self.menubar_frame.winfo_height()
                    
                    # Check if click is outside both menu window and menu bar
                    outside_dropdown = not (wx <= x <= wx + ww and wy <= y <= wy + wh)
                    outside_menubar = not (fx <= x <= fx + fw and fy <= y <= fy + fh)
                    
                    if outside_dropdown and outside_menubar:
                        # Check if mouse button is currently pressed
                        pass  # We'll rely on the event binding instead
                        
                except:
                    pass  # Widget might be destroyed
                    
            # Continue monitoring
            self.parent.after(100, monitor_clicks)
            
        self.parent.after(100, monitor_clicks)
        
    def add_menu(self, menu_name, items):
        '''
        Add a menu to the menu bar.
        
        Args:
            menu_name (str): Name of the menu (e.g., 'File', 'Edit')
            items (list): List of menu items. Each item can be:
                - str: Simple menu item (uses default callback)
                - tuple: (item_name, callback_function) for custom commands
                - '---': Separator
        '''
        # Store menu data
        self.menus[menu_name.lower()] = items
        
        # Create menu button
        menu_button = ctk.CTkButton(
            self.menubar_frame,
            text=menu_name,
            height=32,
            width=80,
            corner_radius=4,
            hover_color=("gray80", "gray20"),
            fg_color="transparent",
            text_color=("black", "white"),
            command=lambda: self._on_menu_button_click(menu_name)
        )
        menu_button.pack(side='left', padx=2, pady=4)
        
        # Store button reference
        self.menu_buttons[menu_name.lower()] = menu_button
        
    def _on_menu_button_click(self, menu_name):
        '''Handle menu button click.'''
        menu_key = menu_name.lower()
        
        # If this menu is already open, close it
        if (self.current_dropdown and 
            hasattr(self.current_dropdown, 'menu_name') and 
            self.current_dropdown.menu_name == menu_name):
            self.current_dropdown.hide()
            self.current_dropdown = None
            return
        
        # Close any open dropdown
        if self.current_dropdown:
            self.current_dropdown.hide()
            
        # Get button position
        button = self.menu_buttons[menu_key]
        button_x = button.winfo_rootx()
        button_y = button.winfo_rooty() + button.winfo_height()
        
        # Create and show dropdown
        items = self.menus[menu_key]
        self.current_dropdown = MenuDropdown(self.parent, items, self.callback, menu_name, self.scale_factor)
        self.current_dropdown.show(button_x, button_y)
        
    def _on_outside_click(self, event):
        '''Handle clicks outside menu area to close dropdowns.'''
        # Check if click was on a menu button
        widget = event.widget
        
        # Walk up the widget hierarchy to see if we clicked on a menu button
        while widget:
            if widget in self.menu_buttons.values():
                return  # Click was on a menu button, let it handle the event
            widget = widget.master
            
        # Click was outside menu area, close any open dropdown
        if self.current_dropdown:
            self.current_dropdown.hide()
            self.current_dropdown = None
    
    def _menu_callback(self, menu_name, item_name):
        '''Handle menu item selection.'''
        if self.callback:
            self.callback(menu_name, item_name)
        log(f'🎯 Menu action: {menu_name} -> {item_name}')
    
    def setup_menu(self):
        '''Setup the default File, Edit, View menus with example custom commands.'''
        
        def exit_app():
            log('👋 Exiting application...')
            if hasattr(self.parent, 'quit'):
                self.parent.quit()
        
        # File menu - mix of custom commands and default callback
        file_items = [
            ('New', None),              # Uses default callback
            ('Open...', None),          # Uses default callback
            '---',
            ('Save', None),             # Uses default callback
            'Save As...',               # Uses default callback
            '---',
            'Export PDF...',            # Uses default callback
            '---',
            ('Exit', exit_app)          # Custom command
        ]
        self.add_menu('File', file_items)

        # Edit menu - all default callback items
        edit_items = [
            ('Undo', None),
            ('Redo', None),
            '---',
            ('Cut', None),
            ('Copy', None),
            ('Paste', None),
            '---',
            ('Preferences...', None)
        ]
        self.add_menu('Edit', edit_items)

        # View menu - all default callback items
        view_items = [
            ('Zoom In', None),
            ('Zoom Out', None),
            ('Zoom to Fit', None),
            '---',
            ('Full Screen', None),
            '---',
            ('Show Grid', None),
            ('Show Rulers', None)
        ]
        self.add_menu('View', view_items)
    
    def add_menu_item(self, menu_name, item_name, callback=None, position=None):
        '''
        Add a menu item to an existing menu.
        
        Args:
            menu_name (str): Name of the menu to add to
            item_name (str): Name of the new item  
            callback (function): Custom callback for this item (optional)
            position (int): Position to insert at (None = append)
        '''
        menu_key = menu_name.lower()
        if menu_key in self.menus:
            items = self.menus[menu_key]
            
            if callback:
                new_item = (item_name, callback)
            else:
                new_item = (item_name, None)
                
            if position is not None:
                items.insert(position, new_item)
            else:
                items.append(new_item)
            
            log(f'📝 Added menu item: {menu_name} -> {item_name}')
        else:
            log(f'⚠️ Menu "{menu_name}" not found')
    
    def get_menu(self, menu_name):
        '''
        Get a specific menu's items for direct manipulation.
        
        Args:
            menu_name (str): Name of the menu
            
        Returns:
            list: The menu items list, or None if not found
        '''
        menu_key = menu_name.lower()
        return self.menus.get(menu_key, None)
    
    def get_menubar(self):
        '''
        Get the main menu bar frame.
        
        Returns:
            ctk.CTkFrame: The main menu bar frame
        '''
        return self.menubar_frame


# Demo/Test function
def demo_menu_bar():
    '''Demonstrate the custom MenuBar widget.'''
    
    def on_menu_action(menu_name, item_name):
        log(f'🎯 Menu action triggered: {menu_name} -> {item_name}')
        if item_name == 'Exit':
            root.quit()
    
    # Set CustomTkinter theme
    ctk.set_appearance_mode('dark')
    ctk.set_default_color_theme('blue')
    
    # Create test window
    root = ctk.CTk()
    root.title('Custom MenuBar Demo')
    root.geometry('800x600')
    
    # Create MenuBar
    menu_bar = MenuBar(root, on_menu_action)
    
    # Add some content below the menu
    content_frame = ctk.CTkFrame(root)
    content_frame.pack(fill='both', expand=True, padx=10, pady=10)
    
    info_label = ctk.CTkLabel(
        content_frame, 
        text='Custom CustomTkinter MenuBar\n\nUses styled buttons with popup menus!\nConsistent appearance across all platforms.',
        font=('Arial', 14)
    )
    info_label.pack(expand=True)
    
    root.mainloop()


if __name__ == '__main__':
    # Run demo if executed directly
    demo_menu_bar()