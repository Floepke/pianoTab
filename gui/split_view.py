'''
Custom SplitView widget for Kivy with draggable wide sash.
Similar to tkinter's PanedWindow but with customizable sash width.
'''

from kivy.uix.widget import Widget
from kivy.uix.button import Button, ButtonBehavior
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle
from kivy.properties import NumericProperty, ObjectProperty, ListProperty
from kivy.clock import Clock
from kivy.core.window import Window
from gui.colors import DARK, LIGHT_DARKER
from typing import Dict, Tuple, Callable, Optional, Any
from icons.icon import load_icon


class IconButton(ButtonBehavior, Image):
    '''A button that displays an icon image with a colored background.'''

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
    '''Draggable sash with embedded toolbar buttons.

    Buttons are direct children with inline positioning logic,
    ensuring they move perfectly in sync with the sash.
    '''

    def __init__(self, split_view, default_toolbar=None, contextual_toolbar=None, **kwargs):
        super().__init__(**kwargs)
        self.split_view = split_view
        self.dragging = False
        self.hovering = False
        self._drag_start_snap_ratio = None  # Store snap ratio at drag start to prevent flickering

        # Configs
        # default_toolbar: Dict[str, (callable|None, tooltip)]
        # contextual_toolbar: Dict[str, Dict[str, (callable|None, tooltip)]]
        self.default_toolbar = dict(default_toolbar or {})
        self.contextual_toolbar = dict(contextual_toolbar or {})
        self.current_context_key: Optional[str] = None
        # Optional cross-linked SplitView to synchronize with (e.g., vertical<->horizontal sashes)
        self.linked_split = None
        # Drag coupling state
        self._drag_origin_pos = None
        self._partner_start_ratio = None

        # Draw sash background
        with self.canvas:
            self.bg_color = Color(*DARK)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

        # Build default (always visible) buttons
        self.default_buttons = []
        for key, val in self.default_toolbar.items():
            cb = None
            tip = ''
            if isinstance(val, tuple) and len(val) >= 1:
                cb = val[0]
                tip = val[1] if len(val) >= 2 else ''
            elif callable(val) or val is None:
                cb = val
            btn = self._make_button(key, cb)
            self.add_widget(btn)
            self.default_buttons.append(btn)

        # Build initial contextual buttons (may be empty until context set)
        self.contextual_buttons = []
        self._rebuild_contextual_buttons(self.current_context_key)

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

        btn_spacing = 10

        if self.split_view.orientation == 'horizontal':
            # Vertical sash: default at top (stacked down), contextual at bottom (stacked up)
            top_padding = 0  # default buttons have menu bar above; no extra top padding
            bottom_padding = btn_spacing  # contextual buttons keep distance from screen edge

            # Top group: default buttons stacked downward from top
            current_y = self.top - top_padding
            for btn in self.default_buttons:
                btn.center_x = self.center_x
                btn.top = current_y
                current_y -= (btn.height + btn_spacing)

            # Bottom group: contextual buttons stacked upward from bottom
            current_bottom = self.y + bottom_padding
            for btn in self.contextual_buttons:
                btn.center_x = self.center_x
                btn.y = current_bottom
                current_bottom += (btn.height + btn_spacing)
        else:
            # Horizontal sash: arrange buttons horizontally with 5px padding/spacing
            # Also enforce 5px vertical padding by scaling buttons to fit sash height - 10px
            left_padding = 5
            right_padding = 5
            spacing = 5

            # Compute target button size to keep 5px top/bottom padding
            target_h = max(0, self.height - 10)

            # Left group: contextual buttons left-to-right
            current_x = self.x + left_padding
            for btn in self.contextual_buttons:
                # Make the button square and vertically padded inside the sash
                try:
                    btn.size = (target_h, target_h)
                except Exception:
                    btn.height = target_h
                btn.center_y = self.center_y
                btn.x = current_x
                current_x += (btn.width + spacing)

            # Right group: default buttons right-to-left (if any)
            current_right = self.right - right_padding
            for btn in self.default_buttons:
                try:
                    btn.size = (target_h, target_h)
                except Exception:
                    btn.height = target_h
                btn.center_y = self.center_y
                btn.right = current_right
                current_right -= (btn.width + spacing)

    # Centralized action invocation helpers
    def _invoke_action(self, cb, *_args):
        try:
            cb()
        except Exception as exc:
            print(f'Action error: {exc}')

    def _action_missing(self, key, *_args):
        print(f'No action configured for "{key}"')

    # Helpers and public API for contextual toolbar

    def _make_button(self, key: str, cb: Optional[Callable[[], None]]):
        icon = load_icon(key)
        if icon is not None:
            btn = IconButton(icon_name=key)
        else:
            btn = Button(text=key, size_hint=(None, None), size=(64, 64))
        if cb is not None:
            # Bind to invoke callback
            btn.bind(on_release=lambda *_: self._invoke_action(cb))
        else:
            btn.bind(on_release=lambda *_: self._action_missing(key))
        return btn

    def set_configs(self, default_toolbar: Optional[Dict[str, Any]] = None,
                    contextual_toolbar: Optional[Dict[str, Dict[str, Any]]] = None):
        '''Update toolbar configs and rebuild buttons.'''
        if default_toolbar is not None:
            self.default_toolbar = dict(default_toolbar)
            # Rebuild default buttons
            for b in self.default_buttons:
                if b.parent is self:
                    self.remove_widget(b)
            self.default_buttons = []
            for key, val in self.default_toolbar.items():
                cb = None
                if isinstance(val, tuple) and len(val) >= 1:
                    cb = val[0]
                elif callable(val) or val is None:
                    cb = val
                btn = self._make_button(key, cb)
                self.add_widget(btn)
                self.default_buttons.append(btn)

        if contextual_toolbar is not None:
            self.contextual_toolbar = dict(contextual_toolbar)

        # Rebuild contextual group for current context
        self._rebuild_contextual_buttons(self.current_context_key)
        self._update_layout()

    def set_context_key(self, key: Optional[str]):
        '''Set the active contextual key (e.g., 'note') to show its buttons at the sash bottom.'''
        if key == self.current_context_key:
            return
        self.current_context_key = key
        self._rebuild_contextual_buttons(key)
        self._update_layout()

    def set_linked_split(self, partner_split):
        '''Link this sash's SplitView to another SplitView for cross-axis synchronization.'''
        self.linked_split = partner_split

    def _rebuild_contextual_buttons(self, key: Optional[str]):
        # Remove existing contextual buttons
        for b in self.contextual_buttons:
            if b.parent is self:
                self.remove_widget(b)
        self.contextual_buttons = []

        if not key:
            return

        cfg = self.contextual_toolbar.get(key, {})
        for btn_key, val in cfg.items():
            cb = None
            if isinstance(val, tuple) and len(val) >= 1:
                cb = val[0]
            elif callable(val) or val is None:
                cb = val
            btn = self._make_button(btn_key, cb)
            self.add_widget(btn)
            self.contextual_buttons.append(btn)

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
        for btn in (self.default_buttons + self.contextual_buttons):
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
        for btn in (self.default_buttons + self.contextual_buttons):
            tp = btn.to_widget(*touch.pos)
            if btn.collide_point(*tp):
                if btn.on_touch_down(touch):
                    return True

        # Otherwise begin dragging if within sash bounds
        sp = self.to_widget(*touch.pos)
        if self.collide_point(*sp):
            self.dragging = True
            # Store the current snap ratio to prevent flickering during drag
            self._drag_start_snap_ratio = self.split_view.snap_ratio
            # Initialize cross-link drag coupling state
            try:
                self._drag_origin_pos = tuple(touch.pos)
            except Exception:
                self._drag_origin_pos = None
            try:
                partner = getattr(self, 'linked_split', None)
                self._partner_start_ratio = float(partner.split_ratio) if partner is not None else None
            except Exception:
                self._partner_start_ratio = None
            
            touch.grab(self)
            Window.set_system_cursor('size_we' if self.split_view.orientation == 'horizontal' else 'size_ns')
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self and self.dragging:
            # Update the active split from the real touch position
            self.split_view.update_split(touch.pos)

            # Cross-link partner split using the other axis of the mouse movement:
            # - Dragging horizontal sash (orientation == 'vertical'): use mouse Y to drive partner's X.
            # - Dragging vertical sash (orientation == 'horizontal'): use mouse X to drive partner's Y.
            partner = getattr(self, 'linked_split', None)
            if partner is not None:
                try:
                    # Delta-coupled cross-axis sync:
                    # - Dragging vertical sash (orientation == 'horizontal'): use mouse Y delta to drive partner (vertical)
                    # - Dragging horizontal sash (orientation == 'vertical'): use mouse X delta to drive partner (horizontal)
                    origin = self._drag_origin_pos or touch.pos
                    dx = float(touch.pos[0]) - float(origin[0])
                    dy = float(touch.pos[1]) - float(origin[1])

                    # Partner ratio at drag start (prevents jumps)
                    try:
                        base_r = float(self._partner_start_ratio) if self._partner_start_ratio is not None else float(partner.split_ratio)
                    except Exception:
                        base_r = float(partner.split_ratio)

                    # Compute new ratio using the other axis delta normalized by the PARTNER's dimension
                    if self.split_view.orientation == 'horizontal':
                        # We are dragging the vertical sash; drive the partner using Y delta
                        if partner.orientation == 'vertical':
                            delta_r = dy / max(1.0, float(partner.height))
                            # In vertical split, ratio decreases as Y increases -> invert
                            new_r = base_r - delta_r
                        else:
                            # Fallback: if partner is horizontal, use X delta
                            delta_r = dx / max(1.0, float(partner.width))
                            new_r = base_r + delta_r
                    else:
                        # We are dragging the horizontal sash; drive the partner using X delta
                        if partner.orientation == 'horizontal':
                            delta_r = dx / max(1.0, float(partner.width))
                            new_r = base_r + delta_r
                        else:
                            # Fallback: if partner is vertical, use Y delta with inversion
                            delta_r = dy / max(1.0, float(partner.height))
                            new_r = base_r - delta_r

                    # Clamp to partner's min sizes
                    if partner.orientation == 'horizontal':
                        min_r = float(partner.min_left_size) / max(1.0, float(partner.width))
                        max_r = 1.0 - (float(partner.min_right_size) / max(1.0, float(partner.width)))
                        new_r = max(min_r, min(max_r, new_r))
                        target_x = float(partner.x) + new_r * float(partner.width)
                        partner.update_split((target_x, partner.center_y))
                    else:
                        min_r = float(partner.min_right_size) / max(1.0, float(partner.height))
                        max_r = 1.0 - (float(partner.min_left_size) / max(1.0, float(partner.height)))
                        new_r = max(min_r, min(max_r, new_r))
                        target_y = float(partner.y) + (1.0 - new_r) * float(partner.height)
                        partner.update_split((partner.center_x, target_y))
                except Exception as _exc:
                    # Keep UI resilient even if partner isn't ready
                    pass

            # Force immediate sync so toolbar snaps in the same frame
            self._update_layout()
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            self.dragging = False
            self._drag_start_snap_ratio = None  # Clear stored snap ratio
            # Clear cross-link drag coupling state
            self._drag_origin_pos = None
            self._partner_start_ratio = None
            
            touch.ungrab(self)
            Window.set_system_cursor('arrow')
            # One more sync in case final position snapped
            self._update_layout()
            # Recalculate snap ratio after drag is complete
            if hasattr(self.split_view, '_last_aspect_ratio'):
                self.split_view.set_snap_ratio_from_aspect(self.split_view._last_aspect_ratio)
            return True
        return super().on_touch_up(touch)


class SplitView(Widget):
    '''
    A split view widget with draggable sash.
    Similar to tkinter's PanedWindow but with Kivy styling.
    '''
    
    sash_width = NumericProperty(20)  # Width of the draggable sash
    split_ratio = NumericProperty(0.5)  # Initial split ratio (0.0 to 1.0)
    left_widget = ObjectProperty(None, allownone=True)
    right_widget = ObjectProperty(None, allownone=True)
    sash_color = ListProperty(DARK)  # Use color system default
    orientation = 'horizontal'  # 'horizontal' or 'vertical'
    
    # Add minimum size properties
    min_left_size = NumericProperty(0)  # Minimum pixels for left panel (0 = can be completely hidden)
    min_right_size = NumericProperty(0)  # Minimum pixels for right panel (0 = can be completely hidden)
    
    # Snap-to-fit properties
    snap_threshold = NumericProperty(100)  # Pixels within which to snap (also used for near-zero snaps)
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
        '''Handle size changes - update layout but preserve user's split ratio.'''
        # Only update the layout, don't recalculate split_ratio
        self.update_layout()
    
    def on_sash_width_change(self, instance, value):
        '''Update sash size when sash_width changes.'''
        if self.orientation == 'horizontal':
            self.sash.width = value
        else:
            self.sash.height = value
        self.update_layout()
    
    def update_sash_color(self, *args):
        '''Update sash background color.'''
        self.sash.bg_color.rgba = self.sash_color
    
    def set_left(self, widget):
        '''Set the left/top widget.'''
        if self.left_widget:
            self.left_container.remove_widget(self.left_widget)
        
        self.left_widget = widget
        if widget:
            self.left_container.add_widget(widget)
            self.update_layout()
    
    def set_right(self, widget):
        '''Set the right/bottom widget.'''
        if self.right_widget:
            self.right_container.remove_widget(self.right_widget)
        
        self.right_widget = widget
        if widget:
            self.right_container.add_widget(widget)
            self.update_layout()
    
    def update_layout(self, *args):
        '''Update the layout based on split ratio.'''
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

            # Clamp to avoid negative sizes when panels collapse
            top_h = max(0, top_height)
            bottom_h = max(0, bottom_height)

            # Snap very small bottom heights to 0 to avoid residual strip from rounding/padding
            epsilon = 2.0
            if bottom_h <= epsilon:
                bottom_h = 0
                # Ensure top fills exactly (total - sash), avoiding 1-2px gaps
                top_h = max(0, total_height - self.sash_width)
            
            # Position and size top container
            self.left_container.pos = (self.x, self.y + bottom_h + self.sash_width)
            self.left_container.size = (self.width, top_h)
            
            # Position and size sash
            self.sash.pos = (self.x, self.y + bottom_h)
            self.sash.size = (self.width, self.sash_width)
            
            # Position and size bottom container
            self.right_container.pos = self.pos
            self.right_container.size = (self.width, bottom_h)
            
            # Update child widgets
            if self.left_widget:
                self.left_widget.pos = self.left_container.pos
                self.left_widget.size = self.left_container.size
            
            if self.right_widget:
                self.right_widget.pos = self.right_container.pos
                self.right_widget.size = self.right_container.size
                # Explicitly hide/show the bottom widget when collapsed/expanded to avoid residual text
                try:
                    collapsed = bottom_h <= 0.5
                    # Disable interactions and hide drawing when collapsed
                    self.right_widget.disabled = collapsed
                    # Opacity helps suppress any child drawing that might ignore container bounds
                    self.right_widget.opacity = 0.0 if collapsed else 1.0
                except Exception:
                    pass
    
    def update_split(self, touch_pos):
        '''Update split ratio based on touch position with snap-to-fit functionality.'''
        if self.orientation == 'horizontal':
            # Calculate new ratio based on x position
            relative_x = touch_pos[0] - self.x
            new_ratio = relative_x / self.width
            
            # Clamp to respect minimum sizes (account for half sash width)
            min_ratio = (self.min_left_size + self.sash_width / 2.0) / max(1.0, self.width)
            max_ratio = 1.0 - (self.min_right_size + self.sash_width / 2.0) / max(1.0, self.width)
            new_ratio = max(min_ratio, min(max_ratio, new_ratio))
            
            # Snap-to-zero for near-edge widths using the same snap_threshold
            try:
                left_w = self.width * new_ratio - self.sash_width / 2.0
                right_w = self.width * (1.0 - new_ratio) - self.sash_width / 2.0
                th = float(self.snap_threshold)
                if left_w <= th:
                    new_ratio = min_ratio
                elif right_w <= th:
                    new_ratio = max_ratio
            except Exception:
                pass
            
            # Use stored snap ratio during dragging to prevent flickering
            snap_ratio_to_use = None
            if hasattr(self.sash, '_drag_start_snap_ratio') and self.sash._drag_start_snap_ratio is not None:
                # Use the snap ratio that was calculated at the start of dragging
                snap_ratio_to_use = self.sash._drag_start_snap_ratio
            else:
                # Not dragging or no stored ratio, use current snap ratio
                snap_ratio_to_use = self.snap_ratio
            
            # Snap to ideal ratio if close enough
            if snap_ratio_to_use is not None:
                # Calculate pixel position of current ratio and snap ratio
                current_x = new_ratio * self.width
                snap_x = snap_ratio_to_use * self.width
                
                # If within threshold, snap to ideal ratio
                if abs(current_x - snap_x) <= self.snap_threshold:
                    new_ratio = snap_ratio_to_use
        else:
            # Calculate new ratio based on y position
            relative_y = touch_pos[1] - self.y
            new_ratio = 1.0 - (relative_y / self.height)
            
            # Clamp to respect minimum sizes (account for half sash height)
            # top >= min_left_size and bottom >= min_right_size
            min_ratio = (self.min_left_size + self.sash_width / 2.0) / max(1.0, self.height)
            max_ratio = 1.0 - (self.min_right_size + self.sash_width / 2.0) / max(1.0, self.height)
            new_ratio = max(min_ratio, min(max_ratio, new_ratio))
            
            # Snap-to-zero for near-edge heights using the same snap_threshold
            try:
                top_h = self.height * new_ratio - self.sash_width / 2.0
                bottom_h = self.height * (1.0 - new_ratio) - self.sash_width / 2.0
                th = float(self.snap_threshold)
                if top_h <= th:
                    new_ratio = min_ratio
                elif bottom_h <= th:
                    new_ratio = max_ratio
            except Exception:
                pass
            
            # Use stored snap ratio during dragging to prevent flickering
            snap_ratio_to_use = None
            if hasattr(self.sash, '_drag_start_snap_ratio') and self.sash._drag_start_snap_ratio is not None:
                snap_ratio_to_use = self.sash._drag_start_snap_ratio
            else:
                snap_ratio_to_use = self.snap_ratio
            
            # Snap to ideal ratio if close enough
            if snap_ratio_to_use is not None:
                # Calculate pixel position of current ratio and snap ratio
                current_y = (1.0 - new_ratio) * self.height
                snap_y = (1.0 - snap_ratio_to_use) * self.height
                
                # If within threshold, snap to ideal ratio
                if abs(current_y - snap_y) <= self.snap_threshold:
                    new_ratio = snap_ratio_to_use
        
        self._user_set_ratio = True  # Mark that user has manually adjusted
        self.split_ratio = new_ratio
        self.update_layout()
    
    def set_snap_ratio_from_aspect(self, aspect_ratio):
        '''
        Calculate and set the snap ratio based on paper aspect ratio (height/width).
        
        For horizontal split: calculates the split ratio where the right panel width
        equals right panel height divided by aspect_ratio, so the paper fits exactly.
        
        Args:
            aspect_ratio: Paper height / paper width (e.g., 297/210 for A4)
        '''
        # Store aspect ratio for recalculation during sash dragging
        self._last_aspect_ratio = aspect_ratio
        
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
                
                # For snap-to-fit, we don't account for scrollbar width because
                # the goal is to fit the content perfectly, which means no scrolling
                # and therefore no scrollbar should be visible after snapping
                scrollbar_width = 0
                
                # Calculate snap ratio for perfect fit (without scrollbar)
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
__all__ = ['SplitView', 'ToolSash', 'Sash']
