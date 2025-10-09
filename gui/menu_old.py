#!/usr/bin/env python3
"""
Menu Bar Widget for PianoTab GUI.

Provides a custom menu bar that displays within the main window instead of
using the native system menu bar. This ensures the menu is always visible
and consistent across all platforms, including macOS.
"""

import tkinter as tk
from tkinter import ttk


class MenuBar:
    """
    A custom menu bar widget that displays in the main window.
    
    This widget creates a horizontal menu bar with dropdown menus that
    stays visible in the main window rather than using the system menu bar.
    This is particularly useful on macOS where native menus are moved to
    the system menu bar.
    """
    
    def __init__(self, parent, callback=None):
        """
        Initialize the MenuBar widget.
        
        Args:
            parent: Parent widget (tkinter container)
            callback: Optional callback function(menu_name, item_name)
        """
        self.parent = parent
        self.callback = callback
        self.menu_buttons = {}
        self.dropdown_menus = {}
        self.active_menu = None
        self.hover_delay_id = None
        
        # Create the main container
        self.container = None
        self.create_widget()
        
        # Setup default menus
        self.setup_default_menus()
    
    def create_widget(self):
        """Create the menu bar widget components."""
        # Main container frame with border to look like a menu bar
        self.container = tk.Frame(self.parent, relief="solid", bd=1, bg="#f8f8f8")
        
        # Force focus to prevent macOS from taking over colors
        self.container.focus_set()
        
        # Bind click outside to close menus
        self.parent.bind_all("<Button-1>", self._close_all_menus)
    
    def pack(self, **kwargs):
        """Pack the container widget."""
        self.container.pack(**kwargs)
        
    def grid(self, **kwargs):
        """Grid the container widget."""
        self.container.grid(**kwargs)
        
    def place(self, **kwargs):
        """Place the container widget."""
        self.container.place(**kwargs)
    
    def add_menu(self, menu_name, items):
        """
        Add a menu to the menu bar.
        
        Args:
            menu_name (str): Name of the menu (e.g., "File", "Edit")
            items (list): List of menu items. Each item can be:
                - str: Simple menu item
                - tuple: (item_name, callback_function)
                - "---": Separator
        """
        # Create menu button using Frame+Canvas to avoid macOS color override
        button_frame = tk.Frame(self.container, bg="#f8f8f8", bd=0, height=28)
        button_frame.pack(side="left", padx=2)
        button_frame.pack_propagate(False)
        
        button_canvas = tk.Canvas(button_frame, bg="#f8f8f8", height=28,
                                 highlightthickness=0, bd=0, cursor="hand2")
        button_canvas.pack(fill="both", expand=True, padx=8)
        
        # Calculate text width and adjust canvas width
        temp_label = tk.Label(self.container, text=menu_name, font=("Arial", 9, "normal"))
        temp_label.update_idletasks()
        text_width = temp_label.winfo_reqwidth()
        temp_label.destroy()
        
        button_canvas.configure(width=text_width + 16)
        
        # Draw text on canvas
        text_id = button_canvas.create_text(8, 14, text=menu_name,
                                          fill="#000000", anchor="w",
                                          font=("Arial", 9, "normal"))
        
        # Store references
        menu_button = button_frame  # Use frame as the main button reference
        menu_button._canvas = button_canvas
        menu_button._text_id = text_id
        
        # Store button reference
        self.menu_buttons[menu_name] = menu_button
        
        # Create dropdown menu (initially hidden)
        dropdown = tk.Toplevel(self.parent)
        dropdown.withdraw()  # Hide initially
        dropdown.overrideredirect(True)  # Remove window decorations
        dropdown.configure(bg="#ffffff", relief="solid", bd=1)
        dropdown.wm_attributes("-topmost", True)  # Keep on top
        
        # Populate dropdown with items
        for item in items:
            if item == "---":
                # Separator
                sep = tk.Frame(dropdown, height=1, bg="#d0d0d0", bd=0)
                sep.pack(fill="x", padx=4, pady=2)
            elif isinstance(item, tuple):
                # Item with custom callback
                item_name, item_callback = item
                self._create_menu_item(dropdown, item_name, menu_name, item_callback)
            else:
                # Simple item using default callback
                self._create_menu_item(dropdown, item, menu_name)
        
        # Store dropdown reference
        self.dropdown_menus[menu_name] = dropdown
        
        # Bind menu button events to both frame and canvas
        for widget in [button_frame, button_canvas]:
            widget.bind("<Button-1>", lambda e: self._toggle_menu(menu_name))
            widget.bind("<Enter>", lambda e: self._on_menu_hover(menu_name))
            widget.bind("<Leave>", lambda e: self._on_menu_leave(menu_name))
    
    def _create_menu_item(self, dropdown, item_name, menu_name, custom_callback=None):
        """Create a single menu item in the dropdown using Canvas for color control."""
        # Create a frame container
        item_frame = tk.Frame(dropdown, bg="#ffffff", bd=0, height=24)
        item_frame.pack(fill="x", padx=1, pady=0)
        item_frame.pack_propagate(False)  # Maintain height
        
        # Create canvas for text rendering (prevents macOS color override)
        canvas = tk.Canvas(item_frame, bg="#ffffff", height=24, 
                          highlightthickness=0, bd=0, cursor="hand2")
        canvas.pack(fill="both", expand=True)
        
        # Draw the text on canvas
        text_id = canvas.create_text(16, 12, text=item_name, 
                                   fill="#000000", anchor="w",
                                   font=("Arial", 9, "normal"))
        
        # Store original colors
        item_frame._original_bg = "#ffffff"
        item_frame._hover_bg = "#0078d4"
        item_frame._text_id = text_id
        item_frame._canvas = canvas
        
        # Hover effects that work on macOS
        def on_enter(e):
            canvas.configure(bg="#0078d4")
            canvas.itemconfig(text_id, fill="#ffffff")
            item_frame.configure(bg="#0078d4")
            
        def on_leave(e):
            canvas.configure(bg="#ffffff")
            canvas.itemconfig(text_id, fill="#000000")
            item_frame.configure(bg="#ffffff")
            
        def on_click(e):
            self._close_all_menus()
            if custom_callback:
                custom_callback()
            elif self.callback:
                self.callback(menu_name, item_name)
            print(f"🍎 Menu action: {menu_name} -> {item_name}")
        
        # Bind events to both frame and canvas
        for widget in [item_frame, canvas]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)
    
    def _toggle_menu(self, menu_name):
        """Toggle the visibility of a menu dropdown."""
        if self.active_menu == menu_name:
            self._close_all_menus()
        else:
            self._show_menu(menu_name)
    
    def _show_menu(self, menu_name):
        """Show a specific menu dropdown."""
        # Close any open menu first
        self._close_all_menus()
        
        if menu_name in self.dropdown_menus:
            dropdown = self.dropdown_menus[menu_name]
            button = self.menu_buttons[menu_name]
            
            # Calculate position
            button.update_idletasks()
            x = button.winfo_rootx()
            y = button.winfo_rooty() + button.winfo_height()
            
            # Position and show dropdown
            dropdown.geometry(f"+{x}+{y}")
            dropdown.deiconify()
            dropdown.lift()
            
            # Highlight the active menu button using canvas
            if hasattr(button, '_canvas') and hasattr(button, '_text_id'):
                button.configure(bg="#0078d4")
                button._canvas.configure(bg="#0078d4")
                button._canvas.itemconfig(button._text_id, fill="#ffffff")
            else:
                button.configure(bg="#0078d4", fg="#ffffff")
            
            self.active_menu = menu_name
    
    def _close_all_menus(self, event=None):
        """Close all open dropdown menus."""
        for menu_name, dropdown in self.dropdown_menus.items():
            dropdown.withdraw()
            # Reset button appearance using canvas
            if menu_name in self.menu_buttons:
                button = self.menu_buttons[menu_name]
                if hasattr(button, '_canvas') and hasattr(button, '_text_id'):
                    button.configure(bg="#f8f8f8")
                    button._canvas.configure(bg="#f8f8f8")
                    button._canvas.itemconfig(button._text_id, fill="#000000")
                else:
                    button.configure(bg="#f8f8f8", fg="#000000")
        
        self.active_menu = None
    
    def _on_menu_hover(self, menu_name):
        """Handle mouse hover over menu button."""
        if self.active_menu is None:
            # Just highlight on hover if no menu is active
            button = self.menu_buttons[menu_name]
            if hasattr(button, '_canvas') and hasattr(button, '_text_id'):
                button.configure(bg="#e8e8e8")
                button._canvas.configure(bg="#e8e8e8")
                button._canvas.itemconfig(button._text_id, fill="#000000")
            else:
                button.configure(bg="#e8e8e8", fg="#000000")
        elif self.active_menu != menu_name:
            # If another menu is active, switch to this one
            self._show_menu(menu_name)
    
    def _on_menu_leave(self, menu_name):
        """Handle mouse leave from menu button."""
        if self.active_menu != menu_name:
            # Reset appearance if this menu is not active
            button = self.menu_buttons[menu_name]
            if hasattr(button, '_canvas') and hasattr(button, '_text_id'):
                button.configure(bg="#f8f8f8")
                button._canvas.configure(bg="#f8f8f8")
                button._canvas.itemconfig(button._text_id, fill="#000000")
            else:
                button.configure(bg="#f8f8f8", fg="#000000")
    
    def setup_default_menus(self):
        """Setup the default File, Edit, View menus."""
        # File menu
        file_items = [
            "New",
            "Open...",
            "---",
            "Save", 
            "Save As...",
            "---",
            "Export PDF...",
            "---",
            "Exit"
        ]
        self.add_menu("File", file_items)
        
        # Edit menu
        edit_items = [
            "Undo",
            "Redo",
            "---",
            "Cut",
            "Copy",
            "Paste",
            "---",
            "Select All",
            "---",
            "Preferences..."
        ]
        self.add_menu("Edit", edit_items)
        
        # View menu
        view_items = [
            "Zoom In",
            "Zoom Out",
            "Zoom to Fit",
            "---",
            "Show Grid",
            "Show Rulers",
            "---",
            "Full Screen"
        ]
        self.add_menu("View", view_items)
    
    def add_custom_menu_item(self, menu_name, item_name, callback=None, position=None):
        """
        Add a custom menu item to an existing menu.
        
        Args:
            menu_name (str): Name of the menu to add to
            item_name (str): Name of the new item
            callback (function): Optional callback for this item
            position (int): Optional position to insert at (None = append)
        """
        if menu_name in self.dropdown_menus:
            dropdown = self.dropdown_menus[menu_name]
            
            # For simplicity, we'll just add to the end
            # In a full implementation, you'd need to rebuild the menu
            # to insert at a specific position
            self._create_menu_item(dropdown, item_name, menu_name, callback)
            print(f"📝 Added custom menu item: {menu_name} -> {item_name}")
        else:
            print(f"⚠️ Menu '{menu_name}' not found")


# Demo/Test function
def demo_menu_bar():
    """Demonstrate the MenuBar widget."""
    
    def on_menu_action(menu_name, item_name):
        print(f"🎯 Menu action triggered: {menu_name} -> {item_name}")
        if item_name == "Exit":
            root.quit()
    
    # Create test window
    root = tk.Tk()
    root.title("MenuBar Demo")
    root.geometry("800x600")
    
    # Create MenuBar at the top
    menu_bar = MenuBar(root, on_menu_action)
    menu_bar.pack(fill="x", side="top")
    
    # Add some content below the menu
    content_frame = tk.Frame(root, bg="white")
    content_frame.pack(fill="both", expand=True)
    
    info_label = tk.Label(content_frame, 
                         text="Custom Menu Bar Demo\n\nThis menu stays in the main window\neven on macOS!",
                         font=("Arial", 14), bg="white", fg="black")
    info_label.pack(expand=True)
    
    # Add a custom menu item as example
    def custom_action():
        print("🎵 Custom action executed!")
    
    menu_bar.add_custom_menu_item("File", "Custom Action", custom_action)
    
    root.mainloop()


if __name__ == "__main__":
    # Run demo if executed directly
    demo_menu_bar()