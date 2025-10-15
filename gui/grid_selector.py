#!/usr/bin/env python3
'''
Grid Selector Widget for PianoTab GUI.

CustomTkinter-based grid selection widget for piano notation timing.
'''

import customtkinter as ctk
from logger import log


class GridSelector(ctk.CTkFrame):
    '''
    A CustomTkinter grid selector widget for timing/rhythm grid.
    
    Features:
    - CTkFrame with 5px padding
    - Label showing calculated grid step in piano ticks
    - CTkScrollableFrame with note length selection
    - Spinbox for subdivision
    - Real-time calculation display
    '''
    
    def __init__(self, parent, callback=None):
        '''
        Initialize the GridSelector widget.
        
        Args:
            parent: Parent widget (CustomTkinter container)
            callback: Optional callback function(grid_step_value)
        '''
        super().__init__(parent)
        
        self.callback = callback
        self.current_grid = '4 - Quarter'
        self.subdivision = 1
        self.quarter_note_ticks = 256.0  # Piano ticks for quarter note
        
        # Configure frame
        self.configure(corner_radius=6)
        
        # Define grid lengths with their pianotick values
        self.grid_lengths = [
            ('1 - Whole', 1024.0),
            ('2 - Half', 512.0), 
            ('4 - Quarter', 256.0),
            ('8 - Eighth', 128.0),
            ('16 - Sixteenth', 64.0),
            ('32 - ...', 32.0),
            ('64 - ...', 16.0),
            ('128 - ...', 8.0)
        ]
        
        self.create_widgets()
        self.update_grid_step()
        
    def create_widgets(self):
        '''Create the widget components.'''
        # Add internal padding
        self.grid_columnconfigure(0, weight=1)
        
        # Grid step label
        self.grid_label = ctk.CTkLabel(
            self,
            text='Grid Step: 256.0',
            font=ctk.CTkFont(size=14, weight='bold')
        )
        self.grid_label.grid(row=0, column=0, padx=5, pady=(5, 10), sticky='w')
        
        # Scrollable frame for grid lengths
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self,
            height=150,
            corner_radius=6
        )
        self.scrollable_frame.grid(row=1, column=0, padx=5, pady=(0, 3), sticky='ew')
        
        # Create grid length buttons
        self.grid_buttons = {}
        for i, (grid_name, ticks) in enumerate(self.grid_lengths):
            button = ctk.CTkButton(
                self.scrollable_frame,
                text=grid_name,
                height=28,
                command=lambda n=grid_name: self.select_grid(n),
                fg_color='transparent',
                hover_color=('gray75', 'gray25'),
                anchor='w'
            )
            button.grid(row=i, column=0, padx=5, pady=1, sticky='ew')
            self.grid_buttons[grid_name] = button
            
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        
        # Subdivision frame
        subdivision_frame = ctk.CTkFrame(self, corner_radius=6)
        subdivision_frame.grid(row=2, column=0, padx=5, pady=(0, 5), sticky='ew')
        subdivision_frame.grid_columnconfigure(1, weight=1)
        
        # Subdivision label
        sub_label = ctk.CTkLabel(
            subdivision_frame,
            text='Divide by:',
            font=ctk.CTkFont(size=12)
        )
        sub_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')
        
        # Subdivision spinbox (using entry with buttons)
        self.spinbox_frame = ctk.CTkFrame(subdivision_frame, corner_radius=4)
        self.spinbox_frame.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        self.spinbox_frame.grid_columnconfigure(1, weight=1)
        
        # Decrease button
        self.decrease_btn = ctk.CTkButton(
            self.spinbox_frame,
            text='-',
            width=30,
            height=28,
            command=self.decrease_subdivision,
            font=ctk.CTkFont(size=16, weight='bold')
        )
        self.decrease_btn.grid(row=0, column=0, padx=2, pady=2)
        
        # Value entry
        self.subdivision_var = ctk.StringVar(value='1')
        self.subdivision_entry = ctk.CTkEntry(
            self.spinbox_frame,
            textvariable=self.subdivision_var,
            width=60,
            height=28,
            justify='center'
        )
        self.subdivision_entry.grid(row=0, column=1, padx=2, pady=2, sticky='ew')
        self.subdivision_entry.bind('<KeyRelease>', self.on_subdivision_change)
        self.subdivision_entry.bind('<FocusOut>', self.on_subdivision_change)
        self.subdivision_entry.bind('<MouseWheel>', self.on_mouse_wheel)
        self.subdivision_entry.bind('<Button-4>', self.on_mouse_wheel)  # Linux scroll up
        self.subdivision_entry.bind('<Button-5>', self.on_mouse_wheel)  # Linux scroll down
        
        # Increase button
        self.increase_btn = ctk.CTkButton(
            self.spinbox_frame,
            text='+',
            width=30,
            height=28,
            command=self.increase_subdivision,
            font=ctk.CTkFont(size=16, weight='bold')
        )
        self.increase_btn.grid(row=0, column=2, padx=2, pady=2)
        
        # Highlight initial selection
        self.update_selection()
        
    def select_grid(self, grid_name):
        '''Handle grid length selection.'''
        self.current_grid = grid_name
        self.update_selection()
        self.update_grid_step()
        
        if self.callback:
            grid_step = self.get_grid_step()
            self.callback(grid_step)
            
        log(f'🎵 Grid selected: {grid_name}')
        
    def decrease_subdivision(self):
        '''Decrease subdivision value.'''
        try:
            current = int(self.subdivision_var.get())
            if current > 1:
                self.subdivision_var.set(str(current - 1))
                self.on_subdivision_change()
        except ValueError:
            self.subdivision_var.set('1')
            
    def increase_subdivision(self):
        '''Increase subdivision value.'''
        try:
            current = int(self.subdivision_var.get())
            if current < 999:  # Reasonable maximum
                self.subdivision_var.set(str(current + 1))
                self.on_subdivision_change()
        except ValueError:
            self.subdivision_var.set('1')
            
    def on_subdivision_change(self, event=None):
        '''Handle subdivision value change.'''
        try:
            value = int(self.subdivision_var.get())
            if value < 1:
                value = 1
                self.subdivision_var.set('1')
            elif value > 999:
                value = 999
                self.subdivision_var.set('999')
            
            self.subdivision = value
            self.update_grid_step()
            
            if self.callback:
                grid_step = self.get_grid_step()
                self.callback(grid_step)
                
        except ValueError:
            # Reset to valid value
            self.subdivision_var.set(str(self.subdivision))
            
    def on_mouse_wheel(self, event):
        '''Handle mouse wheel scroll over the entry widget.'''
        try:
            current = int(self.subdivision_var.get())
            
            # Determine scroll direction (cross-platform)
            if event.delta > 0 or event.num == 4:  # Scroll up
                if current < 999:
                    self.subdivision_var.set(str(current + 1))
                    self.on_subdivision_change()
            elif event.delta < 0 or event.num == 5:  # Scroll down
                if current > 1:
                    self.subdivision_var.set(str(current - 1))
                    self.on_subdivision_change()
                    
        except ValueError:
            # If invalid value, reset to current subdivision
            self.subdivision_var.set(str(self.subdivision))
            
    def update_selection(self):
        '''Update visual selection state.'''
        for grid, button in self.grid_buttons.items():
            if grid == self.current_grid:
                button.configure(
                    fg_color=('gray75', 'gray25'),
                    text_color=('gray10', 'gray90')
                )
            else:
                button.configure(
                    fg_color='transparent',
                    text_color=('gray10', '#DCE4EE')
                )
                
    def update_grid_step(self):
        '''Update the grid step label with calculated value (always as float).'''
        grid_step = self.get_grid_step()
        
        # Always format as float with appropriate precision
        grid_text = f'{grid_step:.6f}'.rstrip('0').rstrip('.')
        # Ensure it always shows at least one decimal place
        if '.' not in grid_text:
            grid_text += '.0'
            
        self.grid_label.configure(text=f'Grid Step: {grid_text}')
        
    def get_grid_step(self):
        '''Calculate and return current grid step value in piano ticks.'''
        # Find the tick value for current grid
        grid_ticks = 256.0  # Default to quarter note
        for grid_name, ticks in self.grid_lengths:
            if grid_name == self.current_grid:
                grid_ticks = ticks
                break
                
        # Calculate grid step (piano ticks divided by subdivision)
        grid_step = grid_ticks / float(self.subdivision)
        return grid_step
        
    def get(self):
        '''Get the currently selected grid length.'''
        return self.current_grid
        
    def get_subdivision(self):
        '''Get the current subdivision value.'''
        return self.subdivision
            
    def set_subdivision(self, value):
        '''Set the subdivision value programmatically.'''
        try:
            value = int(value)
            if 1 <= value <= 99:
                self.subdivision_var.set(str(value))
                self.on_subdivision_change()
            else:
                log(f'Warning: Subdivision value {value} out of range (1-99)')
        except (ValueError, TypeError):
            log(f'Warning: Invalid subdivision value: {value}')
