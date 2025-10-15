#!/usr/bin/env python3
'''
Icon-based Vertical Toolbar Widget for PianoTab GUI.

CustomTkinter-based vertical toolbar with high-quality icon buttons.
'''

import customtkinter as ctk
import sys
import os
from PIL import Image, ImageDraw
from logger import log

# Add icons directory to path
icons_dir = os.path.join(os.path.dirname(__file__), '..', 'icons')
if icons_dir not in sys.path:
    sys.path.insert(0, icons_dir)

try:
    import icons_data
    load_icon = icons_data.load_icon
    get_available_icons = icons_data.get_available_icons
    ICONS_AVAILABLE = True
except ImportError:
    log("Warning: Could not import icons_data. Make sure to run icons/icon2base64.py first")
    ICONS_AVAILABLE = False
    load_icon = None
    get_available_icons = lambda: []


class Toolbar(ctk.CTkFrame):
    '''
    A CustomTkinter vertical toolbar widget with icon buttons.
    
    Features:
    - CTkFrame container with fixed width
    - Vertical layout with icon buttons
    - Base64-encoded icons for high quality
    - Fallback system for missing icons
    - Configurable button callbacks
    '''
    
    def __init__(self, parent, callback=None):
        '''
        Initialize the Toolbar widget.
        
        Args:
            parent: Parent widget (CustomTkinter container)
            callback: Optional callback function(button_command)
        '''
        super().__init__(parent)
        
        self.callback = callback
        
        # Configure frame with fixed size
        self.configure(corner_radius=6, width=60, fg_color=('gray90', 'gray20'))
        self.pack_propagate(False)  # Prevent frame from shrinking
        self.grid_propagate(False)  # Prevent frame from shrinking with grid
        
        # Define toolbar buttons: (icon_name, command, tooltip)
        self.toolbar_buttons = [
            ('select', 'select', 'Select Tool'),
            ('move', 'move', 'Move Tool'), 
            ('note', 'note', 'Add Note'),
            ('beam', 'beam', 'Add Beam'),
            ('gracenote', 'gracenote', 'Add Grace Note'),
            ('accidental', 'accidental', 'Add Accidental'),
            ('linebreak', 'linebreak', 'Line Break'),
            ('countline', 'countline', 'Count Line'),
            ('copy', 'copy', 'Copy'),
            ('delete', 'delete', 'Delete'),
            ('undo', 'undo', 'Undo'),
            ('redo', 'redo', 'Redo')
        ]
        
        self.buttons = {}
        self.create_widgets()
        
    def create_widgets(self):
        '''Create the toolbar button widgets.'''
        # Configure grid
        self.grid_rowconfigure(tuple(range(len(self.toolbar_buttons))), weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Create buttons
        for i, (icon_name, command, tooltip) in enumerate(self.toolbar_buttons):
            # Load icon
            icon_image = self.load_toolbar_icon(icon_name)
            
            # Create button
            button = ctk.CTkButton(
                self,
                text="",
                image=icon_image,
                width=50,
                height=45,
                command=lambda cmd=command: self.on_button_click(cmd),
                fg_color=('gray75', 'gray25'),
                hover_color=('gray85', 'gray15'),
                corner_radius=4
            )
            
            button.grid(row=i, column=0, padx=2, pady=1, sticky='ew')
            self.buttons[command] = button
            
            # Add simple tooltip handling
            button.bind("<Enter>", lambda e, tip=tooltip: self.show_tooltip(tip))
            button.bind("<Leave>", lambda e: self.hide_tooltip())
            
    def load_toolbar_icon(self, icon_name, size=(28, 28)):
        '''Load an icon for the toolbar.'''
        if not ICONS_AVAILABLE:
            return self.create_fallback_icon(icon_name, size)
        
        try:
            # Load icon using the generated icons_data module
            pil_image = load_icon(icon_name, size)
            
            # Convert to CTkImage
            ctk_image = ctk.CTkImage(
                light_image=pil_image, 
                dark_image=pil_image, 
                size=size
            )
            return ctk_image
            
        except Exception as e:
            log(f"Error loading icon '{icon_name}': {e}")
            return self.create_fallback_icon(icon_name, size)
    
    def create_fallback_icon(self, icon_name, size):
        '''Create a simple fallback icon when image loading fails.'''
        # Create simple colored rectangle with first letter
        img = Image.new('RGBA', size, (100, 100, 100, 255))
        draw = ImageDraw.Draw(img)
        
        # Draw border
        draw.rectangle([0, 0, size[0]-1, size[1]-1], outline=(150, 150, 150, 255), width=1)
        
        # Draw first letter of icon name
        if icon_name:
            letter = icon_name[0].upper()
            # Simple text drawing (center the letter)
            text_size = min(size) // 2
            text_x = size[0] // 2 - text_size // 4
            text_y = size[1] // 2 - text_size // 2
            draw.text((text_x, text_y), letter, fill=(255, 255, 255, 255))
        
        ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=size)
        return ctk_image
        
    def show_tooltip(self, text):
        '''Show tooltip (simplified version - prints to console).'''
        log(f"💡 {text}")
    
    def hide_tooltip(self):
        '''Hide tooltip.'''
        pass
        
    def on_button_click(self, command):
        '''Handle button click.'''
        log(f'🔧 Toolbar: {command} clicked')
        
        if self.callback:
            self.callback(command)
            
    def get_toolbar_width(self):
        '''Get the recommended width for the toolbar.'''
        return 60
        
    def add_button(self, icon_name, command, tooltip, position=None):
        '''Add a new button to the toolbar.'''
        if position is None:
            position = len(self.toolbar_buttons)
            
        self.toolbar_buttons.insert(position, (icon_name, command, tooltip))
        self._recreate_buttons()
        
    def remove_button(self, command):
        '''Remove a button from the toolbar by command.'''
        self.toolbar_buttons = [(icon, cmd, tip) for icon, cmd, tip in self.toolbar_buttons if cmd != command]
        self._recreate_buttons()
            
    def _recreate_buttons(self):
        '''Recreate all buttons after adding/removing.'''
        # Clear existing buttons
        for button in self.buttons.values():
            button.destroy()
        self.buttons.clear()
        
        # Recreate all buttons
        self.create_widgets()
        
    def set_button_state(self, command, enabled=True):
        '''Enable or disable a specific button.'''
        if command in self.buttons:
            button = self.buttons[command]
            if enabled:
                button.configure(state='normal', 
                               fg_color=('gray75', 'gray25'))
            else:
                button.configure(state='disabled', 
                               fg_color=('gray90', 'gray40'))
                
    def highlight_button(self, command, highlight=True):
        '''Highlight or unhighlight a specific button.'''
        if command in self.buttons:
            button = self.buttons[command]
            if highlight:
                button.configure(fg_color=('blue', 'blue'))
            else:
                button.configure(fg_color=('gray75', 'gray25'))
                
    def get_available_icons(self):
        '''Get list of available icon names.'''
        if ICONS_AVAILABLE:
            return get_available_icons()
        return []


# Demo function for testing
def demo_toolbar():
    '''Demonstrate the Toolbar widget.'''
    
    def on_toolbar_action(command):
        log(f'Callback: Toolbar action {command}')
        
        # Example of button state management
        if command == 'select':
            toolbar.highlight_button('select', True)
            toolbar.highlight_button('move', False)
        elif command == 'move':
            toolbar.highlight_button('select', False) 
            toolbar.highlight_button('move', True)
    
    # Create test window
    ctk.set_appearance_mode('dark')
    ctk.set_default_color_theme('blue')
    
    root = ctk.CTk()
    root.title('Icon Toolbar Demo')
    root.geometry('300x700')
    
    # Create main frame
    main_frame = ctk.CTkFrame(root)
    main_frame.pack(fill='both', expand=True, padx=10, pady=10)
    
    # Create Toolbar
    toolbar = Toolbar(main_frame, on_toolbar_action)
    toolbar.pack(side='right', fill='y', padx=(0, 5), pady=5)
    
    # Create sample content area
    content_area = ctk.CTkFrame(main_frame)
    content_area.pack(side='left', fill='both', expand=True, padx=(5, 0), pady=5)
    
    content_label = ctk.CTkLabel(content_area, 
                                text='Content Area\n\nClick toolbar buttons\nto test functionality\n\nIcons loaded from\nbase64 data',
                                font=ctk.CTkFont(size=14))
    content_label.pack(expand=True)
    
    # Test information
    info_frame = ctk.CTkFrame(root)
    info_frame.pack(fill='x', padx=10, pady=(0, 10))
    
    if ICONS_AVAILABLE:
        available_icons = toolbar.get_available_icons()
        info_text = f"✅ Icons loaded: {len(available_icons)} available"
    else:
        info_text = "⚠️ Icons not loaded - using fallback mode"
        
    info_label = ctk.CTkLabel(info_frame, text=info_text)
    info_label.pack(pady=5)
    
    root.mainloop()


if __name__ == '__main__':
    # Run demo if executed directly
    demo_toolbar()