"""
Custom SplitView widget for Kivy with draggable wide sash.
Similar to tkinter's PanedWindow but with customizable sash width.
"""

from kivy.uix.widget import Widget
from kivy.uix.button import Button, ButtonBehavior
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle
from kivy.properties import NumericProperty, ObjectProperty, ListProperty
from kivy.clock import Clock
from kivy.core.window import Window
from gui.colors import DARK, LIGHT_DARKER
from gui.callbacks import BUTTON_CONFIG, DEFAULT_SASH_BUTTONS
from functools import partial
from icons.icon import load_icon


class IconButton(ButtonBehavior, Image):
    """A button that displays an icon image with a colored background."""

    def __init__(self, icon_name: str = '', **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (64, 64)

        # Draw background rectangle
        with self.canvas.before:
            self._bg_color = Color(*LIGHT_DARKER)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)

        # Keep background in sync
        self.bind(pos=self._sync_bg, size=self._sync_bg)

        # Load and set the icon image
        if icon_name:
            icon = load_icon(icon_name)
            if icon:
                self.texture = icon.texture

    def _sync_bg(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def on_press(self):
        # Darken on press
        self._bg_color.rgba = DARK

    def on_release(self):
        # Restore color
        self._bg_color.rgba = LIGHT_DARKER


class ToolSash(Widget):
    """Draggable sash with embedded toolbar buttons.

    Buttons are direct children with inline positioning logic,
    ensuring they move perfectly in sync with the sash.
    """

    def __init__(self, split_view, button_keys=None, **kwargs):
        super().__init__(**kwargs)
        self.split_view = split_view
        self.dragging = False
        self.hovering = False

        # Draw sash background
        with self.canvas:
            self.bg_color = Color(*DARK)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

        # Create buttons directly as children from centralized config
        self.buttons = []
        # Determine which buttons to show:
        # - If explicit button_keys provided, use them.
        # - Otherwise start with DEFAULT_SASH_BUTTONS and append any extra keys
        #   from BUTTON_CONFIG so newly added actions appear automatically.
        if button_keys is not None:
            keys = list(button_keys)
        else:
            keys = list(DEFAULT_SASH_BUTTONS) if DEFAULT_SASH_BUTTONS else []
            for k in BUTTON_CONFIG.keys():
                if k not in keys:
                    keys.append(k)
        for key in keys:
            callback = BUTTON_CONFIG.get(key)

            icon = load_icon(key)
            if icon is not None:
                btn = IconButton(icon_name=key)
            else:
                # Fallback to text button if icon is missing
                btn = Button(text=key, size_hint=(None, None), size=(64, 64))

            # Bind callback if available; else print placeholder
            if callback is not None:
                btn.bind(on_release=partial(self._invoke_action, callback))
            else:
                btn.bind(on_release=partial(self._action_missing, key))

            self.add_widget(btn)
            self.buttons.append(btn)

        # Bind sash properties to update button positions immediately
        self.bind(pos=self._update_layout, size=self._update_layout, center_x=self._update_layout)

        # Hover detection for cursor feedback
        Window.bind(mouse_pos=self.on_mouse_pos)

        # First-frame sync
        Clock.schedule_once(lambda dt: self._update_layout(), 0)

    def _update_layout(self, *args):
        # Background matches sash
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

        # Position buttons vertically centered, stacked at top of sash
        btn_spacing = 10
        top_padding = 0
        current_y = self.top - top_padding
        
        for btn in self.buttons:
            btn.center_x = self.center_x
            btn.top = current_y
            current_y -= (btn.height + btn_spacing)

    # Centralized action invocation helpers
    def _invoke_action(self, cb, *_args):
        try:
            cb()
        except Exception as exc:
            print(f"Action error: {exc}")

    def _action_missing(self, key, *_args):
        print(f"No action configured for '{key}'")

    def on_mouse_pos(self, window, pos):
        # Avoid cursor flicker while dragging
        if self.dragging:
            return

        # Skip when sash disabled
        if (self.split_view.orientation == 'horizontal' and self.width == 0) or \
           (self.split_view.orientation == 'vertical' and self.height == 0):
            return

        # Hover logic - check if over any button
        is_hovering = self.collide_point(*self.to_widget(*pos))
        over_button = False
        for btn in self.buttons:
            if btn.collide_point(*btn.to_widget(*pos)):
                over_button = True
                break

        if is_hovering and not over_button and not self.hovering:
            self.hovering = True
            Window.set_system_cursor('size_we' if self.split_view.orientation == 'horizontal' else 'size_ns')
        elif (not is_hovering or over_button) and self.hovering:
            self.hovering = False
            Window.set_system_cursor('arrow')

    def on_touch_down(self, touch):
        # Disable dragging if sash width/height is 0
        if (self.split_view.orientation == 'horizontal' and self.width == 0) or \
           (self.split_view.orientation == 'vertical' and self.height == 0):
            return False

        # Let buttons handle touches first
        for btn in self.buttons:
            tp = btn.to_widget(*touch.pos)
            if btn.collide_point(*tp):
                if btn.on_touch_down(touch):
                    return True

        # Otherwise begin dragging if within sash bounds
        sp = self.to_widget(*touch.pos)
        if self.collide_point(*sp):
            self.dragging = True
            touch.grab(self)
            Window.set_system_cursor('size_we' if self.split_view.orientation == 'horizontal' else 'size_ns')
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self and self.dragging:
            self.split_view.update_split(touch.pos)
            # Force immediate sync so toolbar snaps in the same frame
            self._update_layout()
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            self.dragging = False
            touch.ungrab(self)
            Window.set_system_cursor('arrow')
            # One more sync in case final position snapped
            self._update_layout()
            return True
        return super().on_touch_up(touch)


class SplitView(Widget):
    """
    A split view widget with draggable sash.
    Similar to tkinter's PanedWindow but with Kivy styling.
    """
    
    sash_width = NumericProperty(20)  # Width of the draggable sash
    split_ratio = NumericProperty(0.5)  # Initial split ratio (0.0 to 1.0)
    left_widget = ObjectProperty(None, allownone=True)
    right_widget = ObjectProperty(None, allownone=True)
    sash_color = ListProperty(DARK)  # Use color system default
    orientation = 'horizontal'  # 'horizontal' or 'vertical'
    
    # Add minimum size properties
    min_left_size = NumericProperty(150)  # Minimum pixels for left panel
    min_right_size = NumericProperty(150)  # Minimum pixels for right panel
    
    # Snap-to-fit properties
    snap_threshold = NumericProperty(20)  # Pixels within which to snap
    snap_ratio = NumericProperty(None, allownone=True)  # Target ratio for snapping (calculated from paper dimensions)
    
    def __init__(self, orientation='horizontal', **kwargs):
        super().__init__(**kwargs)
        self.orientation = orientation
        self._user_set_ratio = False  # Track if user has manually set the ratio
        
        # Container for left/top widget
        self.left_container = Widget()
        self.add_widget(self.left_container)

        # Sash (integrated with toolbar)
        self.sash = ToolSash(self, size_hint=(None, 1) if orientation == 'horizontal' else (1, None))
        if orientation == 'horizontal':
            self.sash.width = self.sash_width
        else:
            self.sash.height = self.sash_width
        self.add_widget(self.sash)

        # Container for right/bottom widget
        self.right_container = Widget()
        self.add_widget(self.right_container)

        # Bind to size changes - only update layout, don't change ratio unless user hasn't set it
        self.bind(size=self._on_size_change, pos=self.update_layout)
        self.bind(sash_width=self.on_sash_width_change)
        self.bind(sash_color=self.update_sash_color)
    
    def _on_size_change(self, *args):
        """Handle size changes - update layout but preserve user's split ratio."""
        # Only update the layout, don't recalculate split_ratio
        self.update_layout()
    
    def on_sash_width_change(self, instance, value):
        """Update sash size when sash_width changes."""
        if self.orientation == 'horizontal':
            self.sash.width = value
        else:
            self.sash.height = value
        self.update_layout()
    
    def update_sash_color(self, *args):
        """Update sash background color."""
        self.sash.bg_color.rgba = self.sash_color
    
    def set_left(self, widget):
        """Set the left/top widget."""
        if self.left_widget:
            self.left_container.remove_widget(self.left_widget)
        
        self.left_widget = widget
        if widget:
            self.left_container.add_widget(widget)
            self.update_layout()
    
    def set_right(self, widget):
        """Set the right/bottom widget."""
        if self.right_widget:
            self.right_container.remove_widget(self.right_widget)
        
        self.right_widget = widget
        if widget:
            self.right_container.add_widget(widget)
            self.update_layout()
    
    def update_layout(self, *args):
        """Update the layout based on split ratio."""
        if self.orientation == 'horizontal':
            # Horizontal split
            total_width = self.width
            left_width = total_width * self.split_ratio - self.sash_width / 2
            right_width = total_width * (1 - self.split_ratio) - self.sash_width / 2
            
            # Position and size left container
            self.left_container.pos = self.pos
            self.left_container.size = (max(0, left_width), self.height)
            
            # Position and size sash - force immediate internal update
            new_sash_pos = (self.x + left_width, self.y)
            new_sash_size = (self.sash_width, self.height)
            self.sash.pos = new_sash_pos
            self.sash.size = new_sash_size
            # Bypass property binding delay - update toolbar immediately
            if hasattr(self.sash, '_update_layout'):
                self.sash._update_layout()
            
            # Position and size right container
            self.right_container.pos = (self.x + left_width + self.sash_width, self.y)
            self.right_container.size = (max(0, right_width), self.height)
            
            # Update child widgets
            if self.left_widget:
                self.left_widget.pos = self.left_container.pos
                self.left_widget.size = self.left_container.size
            
            if self.right_widget:
                self.right_widget.pos = self.right_container.pos
                self.right_widget.size = self.right_container.size
        else:
            # Vertical split
            total_height = self.height
            top_height = total_height * self.split_ratio - self.sash_width / 2
            bottom_height = total_height * (1 - self.split_ratio) - self.sash_width / 2
            
            # Position and size top container
            self.left_container.pos = (self.x, self.y + bottom_height + self.sash_width)
            self.left_container.size = (self.width, max(0, top_height))
            
            # Position and size sash
            self.sash.pos = (self.x, self.y + bottom_height)
            self.sash.size = (self.width, self.sash_width)
            
            # Position and size bottom container
            self.right_container.pos = self.pos
            self.right_container.size = (self.width, max(0, bottom_height))
            
            # Update child widgets
            if self.left_widget:
                self.left_widget.pos = self.left_container.pos
                self.left_widget.size = self.left_container.size
            
            if self.right_widget:
                self.right_widget.pos = self.right_container.pos
                self.right_widget.size = self.right_container.size
    
    def update_split(self, touch_pos):
        """Update split ratio based on touch position with snap-to-fit functionality."""
        if self.orientation == 'horizontal':
            # Calculate new ratio based on x position
            relative_x = touch_pos[0] - self.x
            new_ratio = relative_x / self.width
            
            # Clamp to respect minimum sizes
            min_ratio = self.min_left_size / self.width
            max_ratio = 1.0 - (self.min_right_size / self.width)
            new_ratio = max(min_ratio, min(max_ratio, new_ratio))
            
            # Snap to ideal ratio if close enough
            if self.snap_ratio is not None:
                # Calculate pixel position of current ratio and snap ratio
                current_x = new_ratio * self.width
                snap_x = self.snap_ratio * self.width
                
                # If within threshold, snap to ideal ratio
                if abs(current_x - snap_x) <= self.snap_threshold:
                    new_ratio = self.snap_ratio
        else:
            # Calculate new ratio based on y position
            relative_y = touch_pos[1] - self.y
            new_ratio = 1.0 - (relative_y / self.height)
            
            # Clamp to respect minimum sizes
            min_ratio = self.min_right_size / self.height
            max_ratio = 1.0 - (self.min_left_size / self.height)
            new_ratio = max(min_ratio, min(max_ratio, new_ratio))
            
            # Snap to ideal ratio if close enough
            if self.snap_ratio is not None:
                # Calculate pixel position of current ratio and snap ratio
                current_y = (1.0 - new_ratio) * self.height
                snap_y = (1.0 - self.snap_ratio) * self.height
                
                # If within threshold, snap to ideal ratio
                if abs(current_y - snap_y) <= self.snap_threshold:
                    new_ratio = self.snap_ratio
        
        self._user_set_ratio = True  # Mark that user has manually adjusted
        self.split_ratio = new_ratio
        self.update_layout()
    
    def set_snap_ratio_from_aspect(self, aspect_ratio):
        """
        Calculate and set the snap ratio based on paper aspect ratio (height/width).
        
        For horizontal split: calculates the split ratio where the right panel width
        equals right panel height divided by aspect_ratio, so the paper fits exactly.
        
        Args:
            aspect_ratio: Paper height / paper width (e.g., 297/210 for A4)
        """
        if self.orientation == 'horizontal':
            # For scale_to_width rendering: 
            # right_width should equal right_height / aspect_ratio for perfect fit
            # right_width = total_width * (1 - ratio) - sash_width/2
            # We want: right_width = height / aspect_ratio
            # So: total_width * (1 - ratio) - sash_width/2 = height / aspect_ratio
            # Solving: ratio = 1 - (height/aspect_ratio + sash_width/2) / total_width
            
            total_width = self.width
            total_height = self.height
            
            if total_width > 0 and total_height > 0 and aspect_ratio > 0:
                required_right_width = total_height / aspect_ratio
                snap_ratio = 1.0 - (required_right_width + self.sash_width / 2.0) / total_width
                
                # Clamp to valid range
                min_ratio = self.min_left_size / total_width
                max_ratio = 1.0 - (self.min_right_size / total_width)
                snap_ratio = max(min_ratio, min(max_ratio, snap_ratio))
                
                self.snap_ratio = snap_ratio
            else:
                self.snap_ratio = None

        else:
            # For vertical split, similar calculation
            total_width = self.width
            total_height = self.height

            if total_width > 0 and total_height > 0 and aspect_ratio > 0:
                required_bottom_height = total_width * aspect_ratio
                snap_ratio = 1.0 - (required_bottom_height + self.sash_width / 2.0) / total_height

                # Clamp to valid range
                min_ratio = self.min_right_size / total_height
                max_ratio = 1.0 - (self.min_left_size / total_height)
                snap_ratio = max(min_ratio, min(max_ratio, snap_ratio))

                self.snap_ratio = snap_ratio
            else:
                self.snap_ratio = None

# Backwards compatibility: export Sash name for existing imports
# New name is ToolSash, but some modules still import `Sash` from gui.split_view
Sash = ToolSash

# Explicit re-exports for clarity when using `from gui.split_view import *`
__all__ = ["SplitView", "ToolSash", "Sash"]
