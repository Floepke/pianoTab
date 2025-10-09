#!/usr/bin/env python3
'''
Menu Bar Widget for PianoTab GUI.

Provides a simple menu bar with tkinter buttons for a clean, straightforward interface.
'''

import tkinter as tk
from tkinter import ttk


class MenuBar:
    '''
    A simple menu bar widget with tkinter buttons.
    '''
    
    def __init__(self, parent, callback=None):
        '''
        Initialize the MenuBar widget.
        
        Args:
            parent: Parent widget (tkinter container)
            callback: Optional callback function(menu_name, item_name)
        '''
        self.parent = parent
        self.callback = callback
        
        # Create the main container and menu
        self.container = None
        self.create_widget()
        
        # Setup default menus
        self.setup_menus()
    
    def create_widget(self):
        '''Create the menu bar widget.'''
        # Create a frame to hold the menu bar with dark grey background
        self.container = tk.Frame(self.parent, bd=0, bg='#2c2c2c')
        
        # Menu frame with matching dark grey background
        self.menu_frame = tk.Frame(self.container, bd=0, bg='#2c2c2c')
        self.menu_frame.pack(fill='x', padx=0, pady=0)
        
        # Configure ttk style for menu buttons
        style = ttk.Style()
        style.configure('MenuButton.TMenubutton',
                       background='#1c1c1c',
                       foreground='white',
                       relief='flat',
                       borderwidth=0,
                       focuscolor='none')
        style.map('MenuButton.TMenubutton',
                 background=[('active', '#1c1c1c'),
                           ('pressed', '#1c1c1c')])
    
    
    def pack(self, **kwargs):
        '''Pack the container widget.'''
        self.container.pack(**kwargs)
        
    def grid(self, **kwargs):
        '''Grid the container widget.'''
        self.container.grid(**kwargs)
        
    def place(self, **kwargs):
        '''Place the container widget.'''
        self.container.place(**kwargs)
    
    def add_menu(self, menu_name, items):
        '''
        Add a menu to the menu bar using native tkinter Menubutton.
        
        Args:
            menu_name (str): Name of the menu (e.g., 'File', 'Edit')
            items (list): List of menu items. Each item can be:
                - str: Simple menu item (uses default callback)
                - tuple: (item_name, callback_function) for custom commands
                - '---': Separator
        '''
        # Create native Menubutton with dark styling
        menu_button = ttk.Menubutton(self.menu_frame, text=menu_name, 
                                    style='MenuButton.TMenubutton')
        menu_button.pack(side='left', padx=2, pady=0)
        
        # Create the dropdown menu
        dropdown = tk.Menu(menu_button, tearoff=0,
                          bg='#4a4a4a', fg='white',  # Dark theme for dropdown
                          activebackground='#6a6a6a', activeforeground='white')
        
        # Add items to the dropdown
        for item in items:
            if item == '---':
                dropdown.add_separator()
            elif isinstance(item, tuple) and len(item) == 2:
                # Custom command: (item_name, callback_function)
                item_name, item_callback = item
                dropdown.add_command(label=item_name, command=item_callback)
            else:
                # Simple item using default callback
                dropdown.add_command(label=item, 
                                   command=lambda i=item: self._menu_callback(menu_name, i))
        
        # Associate menu with button
        menu_button.config(menu=dropdown)
        
        # Store reference
        setattr(self, f'{menu_name.lower()}_button', menu_button)
        setattr(self, f'{menu_name.lower()}_menu', dropdown)
    
    def _menu_callback(self, menu_name, item_name):
        '''Handle menu item selection.'''
        if self.callback:
            self.callback(menu_name, item_name)
        print(f'🎯 Menu action: {menu_name} -> {item_name}')
    
    def setup_menus(self):
        '''Setup the default File, Edit, View menus with example custom commands.'''
        
        def exit_app():
            print('👋 Exiting application...')
            if hasattr(self.parent, 'quit'):
                self.parent.quit()
        
        # File menu - mix of custom commands and default callback
        file_items = [
            ('New', None),           # Custom command
            ('Open...', None),      # Custom command
            '---',
            ('Save', None),         # Custom command
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

    
    def add_menu_item(self, menu_name, item_name, callback=None, position=None):
        '''
        Add a menu item to an existing menu.
        
        Args:
            menu_name (str): Name of the menu to add to
            item_name (str): Name of the new item  
            callback (function): Custom callback for this item (optional)
            position (int): Position to insert at (None = append)
        '''
        menu_attr = f'{menu_name.lower()}_menu'
        if hasattr(self, menu_attr):
            menu = getattr(self, menu_attr)
            
            if callback:
                # Custom callback provided
                if position is not None:
                    menu.insert_command(position, label=item_name, command=callback)
                else:
                    menu.add_command(label=item_name, command=callback)
            else:
                # Use default callback system
                if position is not None:
                    menu.insert_command(position, label=item_name, 
                                      command=lambda: self._menu_callback(menu_name, item_name))
                else:
                    menu.add_command(label=item_name, 
                                   command=lambda: self._menu_callback(menu_name, item_name))
            
            print(f'📝 Added menu item: {menu_name} -> {item_name}')
        else:
            print(f'⚠️ Menu "{menu_name}" not found')
    
    def get_menu(self, menu_name):
        '''
        Get a specific menu for direct manipulation.
        
        Args:
            menu_name (str): Name of the menu
            
        Returns:
            None: Simplified version doesn't expose menu objects
        '''
        return None


# Demo/Test function
def demo_menu_bar():
    '''Demonstrate the simple MenuBar widget.'''
    
    def on_menu_action(menu_name, item_name):
        print(f'🎯 Menu action triggered: {menu_name} -> {item_name}')
        if item_name == 'Exit':
            root.quit()
    
    # Create test window
    root = tk.Tk()
    root.title('Simple MenuBar Demo')
    root.geometry('800x600')
    
    # Create MenuBar at the top
    menu_bar = MenuBar(root, on_menu_action)
    menu_bar.pack(fill='x', side='top')
    
    # Add some content below the menu
    content_frame = tk.Frame(root, bg='white')
    content_frame.pack(fill='both', expand=True)
    
    info_label = tk.Label(content_frame, 
                         text='Simple tkinter MenuBar\n\nClick menu buttons to see dropdown menus!',
                         font=('Arial', 14), bg='white', fg='black')
    info_label.pack(expand=True)
    
    root.mainloop()


if __name__ == '__main__':
    # Run demo if executed directly
    demo_menu_bar()