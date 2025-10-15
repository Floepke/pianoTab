#!/usr/bin/env python3
'''
Native Tkinter Menu Bar Widget for PianoTab GUI.

Provides a native system menu bar using tkinter's built-in Menu widget.
'''

import tkinter as tk
import tkinter.font as tkfont
from logger import log


class MenuBar:
    '''
    A native tkinter menu bar widget using the system menu bar.
    '''
    
    def __init__(self, parent, callback=None, scale_factor=1.0):
        '''
        Initialize the MenuBar widget.
        
        Args:
            parent: Parent widget (tkinter window - should be root or Toplevel)
            callback: Optional callback function(menu_name, item_name)
            scale_factor: Scaling factor for menu fonts (1.0 = normal, 1.5 = 50% larger)
        '''
        self.parent = parent
        self.callback = callback
        self.scale_factor = scale_factor
        
        # Calculate scaled font size
        self.menu_font = self._get_scaled_font()
        
        # Create the native menu bar
        self.menubar = None
        self.create_widget()
        
        # Setup pianoTab menu
        self.setup_menu()
    
    def _get_scaled_font(self):
        '''Get a scaled font for the menu.'''
        # Get the default font
        default_font = tkfont.nametofont("TkMenuFont")
        default_size = default_font.actual()['size']
        
        # Calculate new size based on scale factor
        new_size = int(default_size * self.scale_factor)
        
        # Create and return the scaled font
        return tkfont.Font(family=default_font.actual()['family'], 
                          size=new_size,
                          weight=default_font.actual()['weight'])
    
    def create_widget(self):
        '''Create the native menu bar widget.'''
        # Create the main menu bar with scaled font
        self.menubar = tk.Menu(self.parent, font=self.menu_font)
        
        # Configure the parent window to use this menu bar
        self.parent.config(menu=self.menubar)
        
        # Store menu references for later access
        self.menus = {}
    
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
        # Create a new menu with scaled font
        menu = tk.Menu(self.menubar, tearoff=0, font=self.menu_font)
        
        # Add items to the menu
        for item in items:
            if item == '---':
                menu.add_separator()
            elif isinstance(item, tuple) and len(item) == 2:
                # Custom command: (item_name, callback_function)
                item_name, item_callback = item
                if item_callback is None:
                    # Use default callback if callback is None
                    menu.add_command(label=item_name, 
                                   command=lambda i=item_name: self._menu_callback(menu_name, i))
                else:
                    menu.add_command(label=item_name, command=item_callback)
            else:
                # Simple item using default callback
                menu.add_command(label=item, 
                               command=lambda i=item: self._menu_callback(menu_name, i))
        
        # Add the menu to the menu bar
        self.menubar.add_cascade(label=menu_name, menu=menu)
        
        # Store reference for later access
        self.menus[menu_name.lower()] = menu
    
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
            menu = self.menus[menu_key]
            
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
            
            log(f'📝 Added menu item: {menu_name} -> {item_name}')
        else:
            log(f'⚠️ Menu "{menu_name}" not found')
    
    def get_menu(self, menu_name):
        '''
        Get a specific menu for direct manipulation.
        
        Args:
            menu_name (str): Name of the menu
            
        Returns:
            tk.Menu: The menu object, or None if not found
        '''
        menu_key = menu_name.lower()
        return self.menus.get(menu_key, None)
    
    def get_menubar(self):
        '''
        Get the main menu bar object.
        
        Returns:
            tk.Menu: The main menu bar
        '''
        return self.menubar


# Demo/Test function
def demo_menu_bar():
    '''Demonstrate the native MenuBar widget.'''
    
    def on_menu_action(menu_name, item_name):
        log(f'🎯 Menu action triggered: {menu_name} -> {item_name}')
        if item_name == 'Exit':
            root.quit()
    
    # Create test window
    root = tk.Tk()
    root.title('Native MenuBar Demo')
    root.geometry('800x600')
    
    # Create MenuBar (automatically attaches to window)
    menu_bar = MenuBar(root, on_menu_action)
    
    # Add some content below the menu
    content_frame = tk.Frame(root, bg='white')
    content_frame.pack(fill='both', expand=True)
    
    info_label = tk.Label(content_frame, 
                         text='Native Tkinter MenuBar\n\nUses the system menu bar!\nMenu items appear in the title bar area.',
                         font=('Arial', 14), bg='white', fg='black')
    info_label.pack(expand=True)
    
    root.mainloop()


if __name__ == '__main__':
    # Run demo if executed directly
    demo_menu_bar()