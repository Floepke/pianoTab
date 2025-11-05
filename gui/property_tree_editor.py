'''
Comprehensive Property Tree Editor for SCORE.

Updates:
- Event.* lists get transparent -/+ buttons:
  - “+” calls SCORE.new_{event_type}(stave_idx=…) to append a default object.
  - “−” removes the last element of that list.
- Visual/layout:
  - Rows use a uniform height equal to stripe size; background stripes behind content.
  - Buttons are transparent; inputs are white with black text; labels/buttons auto-contrast:
    • Labels/buttons on DARK_LIGHTER rows use white text.
    • Labels/buttons on LIGHT_DARKER rows use black text.
  - Aligned columns: editors start at a fixed right column regardless of indent depth.
  - No overlap with the scrollbar; editors stretch to end right next to the custom scrollbar.
- Scrollbar:
  - Replaces ScrollView's default bars with the same CustomScrollbar used by the Canvas.
  - Keeps content non-overlapping by reserving width for the scrollbar.
- Editor UX:
  - Int/Float spinboxes also accept manual numeric input; only digits and optional '.' allowed.
  - Expand/collapse “packs downward”: keeps visual scroll position stable after toggling.

Public API:
- set_score(score)
- on_change: Optional[Callable[[Any], None]]

'''

from __future__ import annotations

from typing import Any, Optional, Callable, List, Tuple, Union
from typing import get_origin, get_args
from dataclasses import is_dataclass, fields
import re
import math

from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.uix.colorpicker import ColorPicker
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle, InstructionGroup, Line
from kivy.properties import NumericProperty
from kivy.clock import Clock

from gui.colors import DARK_LIGHTER, LIGHT_DARKER, DARK, ACCENT_COLOR
from utils.canvas import CustomScrollbar
from file.SCORE import SCORE, Event
from icons.icon import IconLoader

# Visual constants
BLACK = (0, 0, 0, 1)
WHITE = (1, 1, 1, 1)
TRANSPARENT = (0, 0, 0, 0)

HEX_COLOR_RE = re.compile(r'^#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})$')


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _fmt_float(v: float) -> str:
    s = f'{v:.6f}'.rstrip('0').rstrip('.')
    return s if '.' in s else f'{s}.0'


def _rgba_to_hex(rgba: Tuple[float, float, float, float]) -> str:
    r = max(0, min(255, int(round(rgba[0] * 255))))
    g = max(0, min(255, int(round(rgba[1] * 255))))
    b = max(0, min(255, int(round(rgba[2] * 255))))
    return f'#{r:02X}{g:02X}{b:02X}'


def _hex_to_rgba(hex_color: str) -> Tuple[float, float, float, float]:
    s = hex_color.lstrip('#')
    if len(s) == 3:
        s = ''.join([c * 2 for c in s])
    if len(s) != 6:
        # Fallback to white if invalid
        return (1.0, 1.0, 1.0, 1.0)
    r = int(s[0:2], 16) / 255.0
    g = int(s[2:4], 16) / 255.0
    b = int(s[4:6], 16) / 255.0
    return (r, g, b, 1.0)


def _camel_to_snake(name: str) -> str:
    return re.sub(r'(?<!^)([A-Z])', r'_\1', name).lower()


class NumericTextInput(TextInput):
    '''
    TextInput that only accepts digits and optionally a single dot.
    allow_float=False -> digits only (ints)
    allow_float=True  -> digits + optional '.' (floats)
    '''
    def __init__(self, allow_float: bool, **kwargs):
        super().__init__(**kwargs)
        self.allow_float = allow_float

    def insert_text(self, substring, from_undo=False):
        # Filter characters
        allowed = '0123456789'
        if self.allow_float:
            allowed += '.'
            # prevent multiple dots
            if '.' in substring and '.' in self.text:
                substring = substring.replace('.', '')
        filtered = ''.join(ch for ch in substring if ch in allowed)
        return super().insert_text(filtered, from_undo=from_undo)


class ListNumericTextInput(TextInput):
    '''
    TextInput for space-separated numeric lists.
    - allow_float=False: allow digits and spaces only (ints). Loose '.' are filtered out.
    - allow_float=True: allow digits, spaces and '.' (floats). Loose '.' tokens are ignored during parse.
    '''
    def __init__(self, allow_float: bool, **kwargs):
        super().__init__(**kwargs)
        self.allow_float = allow_float

    def insert_text(self, substring, from_undo=False):
        # Always allow digits, spaces, and '.' so users can type floats even when list becomes ints.
        # Loose '.' tokens are ignored during parse.
        allowed = '0123456789 .'
        filtered = ''.join(ch for ch in substring if ch in allowed)
        return super().insert_text(filtered, from_undo=from_undo)


class NumericSpinBox(BoxLayout):
    '''
    Numeric spinbox with -/+ buttons and an editable TextInput.
    - int mode: step=1
    - float mode: step=0.05
    Validates and commits values via 'on_commit' callback.
    Visual: transparent buttons, white input with black text.
    '''

    def __init__(self, value: Union[int, float], is_float: bool, step: float,
                 on_commit: Callable[[Union[int, float]], None],
                 input_bg_color: Tuple[float, float, float, float] = (1, 1, 1, 0.001),
                 input_fg_color: Tuple[float, float, float, float] = (0, 0, 0, 1),
                 **kwargs):
        super().__init__(orientation='horizontal', spacing=dp(6), size_hint_y=None, height=dp(28), **kwargs)
        self._is_float = is_float
        self._step = float(step)
        self._on_commit = on_commit
        self._value: Union[int, float] = float(value) if is_float else int(value)

        # Text input (transparent) with numeric filtering
        self.input = NumericTextInput(
            allow_float=self._is_float,
            text=self._text_of(self._value),
            multiline=False,
            write_tab=False,
            size_hint_x=1,
            size_hint_y=1,
            background_normal='',
            background_active='',
            background_color=input_bg_color,
            foreground_color=input_fg_color,
            cursor_color=input_fg_color,
            selection_color=(ACCENT_COLOR[0], ACCENT_COLOR[1], ACCENT_COLOR[2], 0.35),
        )
        self.input.bind(on_text_validate=self._commit_from_text, focus=self._on_focus_change)
        self.add_widget(self.input)

        # - button (transparent) moved to the right of the textbox
        self.dec_btn = Button(
            text='−',
            size_hint_x=None,
            width=dp(28),
            background_normal='',
            background_down='',
            background_color=TRANSPARENT,
            color=ACCENT_COLOR,
        )
        self.dec_btn.bind(on_press=lambda *_: self._nudge(-self._step))
        self.add_widget(self.dec_btn)

        # + button (transparent)
        self.inc_btn = Button(
            text='+',
            size_hint_x=None,
            width=dp(28),
            background_normal='',
            background_down='',
            background_color=TRANSPARENT,
            color=ACCENT_COLOR,
        )
        self.inc_btn.bind(on_press=lambda *_: self._nudge(+self._step))
        self.add_widget(self.inc_btn)

    def _text_of(self, v: Union[int, float]) -> str:
        if self._is_float:
            return _fmt_float(float(v))
        return str(int(v))

    def _nudge(self, delta: float):
        if self._is_float:
            new_val = float(self._value) + delta
            step_units = round(new_val / self._step)
            new_val = step_units * self._step
            self._value = new_val
        else:
            self._value = int(self._value) + int(delta)
        self.input.text = self._text_of(self._value)
        self._on_commit(self._value if self._is_float else int(self._value))

    def _commit_from_text(self, *_):
        txt = self.input.text.strip()
        try:
            if self._is_float:
                v = float(txt) if txt != '' else float(self._value)
                self._value = v
                self.input.text = self._text_of(v)
                self._on_commit(v)
            else:
                v = int(round(float(txt))) if txt != '' else int(self._value)
                self._value = v
                self.input.text = self._text_of(v)
                self._on_commit(v)
        except Exception:
            # Revert on invalid parse
            self.input.text = self._text_of(self._value)

    def _on_focus_change(self, _inst, focused: bool):
        if not focused:
            self._commit_from_text()


class ColorField(BoxLayout):
    '''
    Color picker field with:
    - Swatch
    - Hex label
    - 'Pick…' button that opens a Popup with ColorPicker and Cancel/OK
    Commits only on OK; Cancel reverts.
    Visual: button transparent, label auto-contrasted by row color.
    '''

    def __init__(self, hex_value: str, on_commit: Callable[[str], None], label_color=BLACK, **kwargs):
        super().__init__(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(28), **kwargs)
        self._hex = hex_value if isinstance(hex_value, str) else '#000000'
        self._on_commit = on_commit

        # Swatch rectangle
        self.swatch = Widget(size_hint=(None, None), size=(dp(22), dp(22)))
        with self.swatch.canvas:
            self._swatch_color = Color(*_hex_to_rgba(self._hex))
            self._swatch_rect = Rectangle(pos=self.swatch.pos, size=self.swatch.size)
        self.swatch.bind(
            pos=lambda *_: setattr(self._swatch_rect, 'pos', self.swatch.pos),
            size=lambda *_: setattr(self._swatch_rect, 'size', self.swatch.size),
        )
        self.add_widget(self.swatch)

        # Hex label (auto color)
        self.lbl = Label(text=self._hex, color=label_color, size_hint_x=1, halign='left', valign='middle')
        self.lbl.bind(size=self.lbl.setter('text_size'))
        self.add_widget(self.lbl)

        # Pick button (transparent)
        self.btn = Button(
            text='Pick…',
            size_hint=(None, 1),
            width=dp(64),
            background_normal='',
            background_down='',
            background_color=TRANSPARENT,
            color=label_color,
        )
        self.btn.bind(on_press=lambda *_: self._open_picker())
        self.add_widget(self.btn)

    def _open_picker(self):
        rgba = _hex_to_rgba(self._hex)
        picker = ColorPicker(color=rgba, size_hint=(1, 1))
        buttons = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(8), padding=(dp(8), 0))

        cancel = Button(
            text='Cancel',
            size_hint_x=None,
            width=dp(100),
            background_normal='',
            background_down='',
            background_color=TRANSPARENT,
            color=BLACK,
        )
        ok = Button(
            text='OK',
            size_hint_x=None,
            width=dp(100),
            background_normal='',
            background_down='',
            background_color=TRANSPARENT,
            color=BLACK,
        )

        content = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(8))
        content.add_widget(picker)
        buttons.add_widget(Widget())
        buttons.add_widget(cancel)
        buttons.add_widget(ok)
        content.add_widget(buttons)

        popup = Popup(title='Select Color...', content=content, size_hint=(None, None), size=(dp(500), dp(400)))

        def _on_cancel(*_):
            popup.dismiss()

        def _on_ok(*_):
            col = picker.color  # RGBA floats
            hx = _rgba_to_hex(col)
            self._set_hex(hx)
            self._on_commit(hx)
            popup.dismiss()

        cancel.bind(on_press=_on_cancel)
        ok.bind(on_press=_on_ok)
        popup.open()

    def _set_hex(self, hx: str):
        self._hex = hx
        self.lbl.text = hx
        rgba = _hex_to_rgba(hx)
        self._swatch_color.rgba = rgba


class PropertyTreeEditor(BoxLayout):
    '''
    Property tree editor for SCORE with foldable nodes and type-aware editors.
    '''

    STRIPE_HEIGHT = dp(28)
    INDENT = dp(50)
    # Minimum left column width; actual width is auto-sized based on model depth and view width
    MIN_LEFT_COL_WIDTH = dp(420)
    # Dynamic left column width (indent + arrow + label). All rows bind to this.
    left_col_width = NumericProperty(dp(420))

    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', size_hint=(1, 1), **kwargs)

        # Unified left indent for column content (in dp):
        # - spacing between left column and divider
        # - spacing from divider to start of value widgets
        # - header right-column spacer before the 'Value' label
        self.indent_px = -10

        # Container to overlay ScrollView and custom scrollbar (avoids ScrollView 1-child limit)
        self.container = FloatLayout(size_hint=(1, 1))
        self.add_widget(self.container)

        # ScrollView with hidden native scrollbar
        self.sv = ScrollView(
            size_hint=(None, None),
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=0,
            scroll_type=['bars', 'content'],
        )

        # Content layout (no vertical gaps; align rows to stripes)
        self.layout = BoxLayout(
            orientation='vertical',
            spacing=0,
            padding=(dp(10), 0, dp(0), 0),
            size_hint_y=None,
            size_hint_x=None,
            width=100,  # will be updated by view metrics
        )
        self.layout.bind(minimum_height=self.layout.setter('height'))
        self.sv.add_widget(self.layout)
        self.container.add_widget(self.sv)

        # Background stripes behind content
        self._bg_group = InstructionGroup()      # base + stripes
        self._col_group = InstructionGroup()     # value column divider line
        self.layout.canvas.before.add(self._bg_group)
        self.layout.canvas.before.add(self._col_group)

        # Custom scrollbar (shared look & feel), bound to this adapter widget
        self.custom_scrollbar = CustomScrollbar(self)
        self.container.add_widget(self.custom_scrollbar)

        # Expose view metrics expected by CustomScrollbar
        self._view_x = int(self.x)
        self._view_y = int(self.y)
        self._view_w = int(max(1, self.width - getattr(self.custom_scrollbar, 'scrollbar_width', 40)))
        self._view_h = int(self.height)
        self._scroll_px = 0.0  # pixel scroll for CustomScrollbar
        # Adapter flag used by CustomScrollbar to enable scrolling behavior
        self.scale_to_width = True

        # Bind layout/scroll
        self.bind(pos=self._update_view_and_graphics, size=self._update_view_and_graphics)
        self.sv.bind(scroll_y=self._on_sv_scroll_y)
        self.layout.bind(pos=lambda *_: self._update_background(), size=lambda *_: self._update_background())
        # When left column width changes, apply to existing rows and redraw divider
        self.bind(left_col_width=lambda *_: self._on_left_col_width_change())

        self._score: Optional[Any] = None
        self.on_change: Optional[Callable[[Any], None]] = None

        # Track open/closed nodes via attribute-path tuples
        self._open_paths: set[Tuple[Union[str, int], ...]] = set()
        self._open_paths.add(())  # root open

        # Row index for alternating text color bound to stripes
        self._row_counter: int = 0

        # Initial geometry
        self._update_view_and_graphics()

        # Show placeholder initially
        self._rebuild()
        # Debounce flag for rebuilds scheduled within the same frame
        self._rebuild_pending = False

    # ---------- CustomScrollbar adapter API ----------

    def _content_height_px(self) -> int:
        return int(self.layout.height)

    def _redraw_all(self):
        # For tree editor, nothing to redraw in canvas terms; just update ScrollView position.
        self._apply_scroll_px()

    def _update_border(self):
        # No border for tree editor; method present for CustomScrollbar compatibility.
        pass

    # Map pixel scroll to ScrollView.scroll_y
    def _apply_scroll_px(self):
        max_scroll = max(0, self._content_height_px() - self._view_h)
        if max_scroll <= 0:
            self.sv.scroll_y = 1.0
            self._scroll_px = 0.0
        else:
            self._scroll_px = max(0.0, min(max_scroll, float(self._scroll_px)))
            # ScrollView.scroll_y: 1.0 = top, 0.0 = bottom
            self.sv.scroll_y = 1.0 - (self._scroll_px / max_scroll)
        # Update scrollbar geometry
        try:
            self.custom_scrollbar.update_layout()
        except Exception:
            pass

    def _on_sv_scroll_y(self, *_):
        # When ScrollView changes (e.g., mouse wheel), sync _scroll_px so CustomScrollbar reflects it
        max_scroll = max(0, self._content_height_px() - self._view_h)
        if max_scroll <= 0:
            self._scroll_px = 0.0
        else:
            self._scroll_px = max(0.0, min(max_scroll, (1.0 - float(self.sv.scroll_y)) * max_scroll))
        try:
            self.custom_scrollbar.update_layout()
        except Exception:
            pass

    def _update_view_and_graphics(self, *_):
        # Reserve width for custom scrollbar; prevent overlap
        sbw = getattr(self.custom_scrollbar, 'scrollbar_width', 40)
        self._view_x = int(self.x)
        self._view_y = int(self.y)
        self._view_w = int(max(1, self.width - sbw))
        self._view_h = int(self.height)

        # Position/size ScrollView within container
        self.sv.pos = (self._view_x, self._view_y)
        self.sv.size = (self._view_w, self._view_h)

        # Make content layout fill the view width
        self.layout.width = self._view_w

        # Auto-size left column to accommodate deepest indent while keeping minimum right column
        self._auto_size_left_column()

        # Update background and scrollbar
        self._update_background()
        try:
            self.custom_scrollbar.update_layout()
        except Exception:
            pass
        # Keep scroll pixel position consistent after size changes
        self._apply_scroll_px()

    # ---------- Public API ----------

    def set_score(self, score: Any):
        self._score = score
        # Recompute left column width against the bound model
        self._auto_size_left_column()
        self._rebuild()

    # ---------- Rendering ----------

    def _update_background(self):
        # Draw base background (LIGHT_DARKER) once and only DARK_LIGHTER stripes to reduce draw calls
        if not hasattr(self, '_bg_group') or self._bg_group is None:
            return
        self._bg_group.clear()
        tgt = getattr(self, 'layout', None) or self
        w = float(getattr(tgt, 'width', 0.0))
        h_content = float(getattr(tgt, 'height', 0.0))
        # Ensure we fill at least the visible viewport height so the area under short content is not dark
        h = float(max(h_content, float(getattr(self, '_view_h', h_content))))
        x0 = float(getattr(tgt, 'x', 0.0))
        # Pixel-align the starting top to avoid subpixel drift between rebuilds
        y_top_float = float(getattr(tgt, 'y', 0.0)) + h_content
        y_top = float(int(round(y_top_float)))
        if w <= 0 or h <= 0:
            return

        # Base fill (LIGHT_DARKER) for the full visible area
        self._bg_group.add(Color(*LIGHT_DARKER))
        self._bg_group.add(Rectangle(pos=(x0, y_top - h), size=(w, h)))

        # Only draw DARK_LIGHTER stripes on every other row to halve rectangle count
        # Optimization: draw stripes only for the content height, not the full viewport
        n = int(math.ceil(h_content / self.STRIPE_HEIGHT))
        y = y_top
        # Start with row 0 at the top; draw DARK_LIGHTER for odd rows only
        for i in range(n):
            if (i % 2) == 1:
                self._bg_group.add(Color(*DARK_LIGHTER))
                self._bg_group.add(Rectangle(pos=(x0, y - self.STRIPE_HEIGHT), size=(w, self.STRIPE_HEIGHT)))
            y -= self.STRIPE_HEIGHT

        # Update value column divider after background
        self._update_value_column_divider()

    def _update_value_column_divider(self):
        # Draw a thick vertical line just before value labels (at start of right column)
        if not hasattr(self, '_col_group') or self._col_group is None:
            return
        self._col_group.clear()
        # Horizontal spacing between the left column and the divider
        row_spacing = dp(self.indent_px)
        try:
            pad_left = float(self.layout.padding[0]) if isinstance(self.layout.padding, (list, tuple)) else 0.0
        except Exception:
            pad_left = 0.0
        x_line = float(self.layout.x) + pad_left + float(self.left_col_width) + row_spacing
        sbw = float(getattr(self.custom_scrollbar, 'scrollbar_width', 40))
        # Ensure the line stays within the scrollview content area
        view_right = float(self.x) + float(self.width) - sbw
        if x_line >= view_right:
            return
        line_w = dp(3)
        # Draw divider only for the rendered content height (stop at last row)
        h_content = float(self.layout.height)
        y_start = float(self.layout.y)
        self._col_group.add(Color(*DARK))  # divider uses the DARK base color
        self._col_group.add(Rectangle(pos=(x_line - line_w/2.0, y_start), size=(line_w, h_content)))

    def _rebuild(self):
        # Capture current pixel scroll so we can restore after rebuild (pack downwards)
        prev_px = float(self._scroll_px)

        self.layout.clear_widgets()
        self._row_counter = 0

        if self._score is None:
            self._add_info_row('No SCORE bound')
            # Ensure scrollbar reflects new content
            Clock.schedule_once(lambda dt: self.custom_scrollbar.update_layout(), 0)
            return

        # Ensure left column is sized before creating rows
        self._auto_size_left_column()

        # Render header row: Tree | Value (root is not collapsible)
        self._build_header_row()

        # Render children of SCORE at top level (no extra root indent)
        root = self._score
        if is_dataclass(root):
            for f in fields(root):
                attr_name = f.name
                json_name = self._json_field_name(f)
                try:
                    val = getattr(root, attr_name)
                except Exception:
                    val = None
                self._build_value_row(
                    key_label=json_name,
                    attr_name=attr_name,
                    value=val,
                    parent=root,
                    path=(attr_name,),
                    level=0,
                )
        elif isinstance(root, dict):
            for k, v in root.items():
                self._build_value_row(
                    key_label=str(k), attr_name=str(k), value=v, parent=root, path=(k,), level=0
                )
        elif isinstance(root, list):
            for i, v in enumerate(root):
                self._build_value_row(
                    key_label=f'[{i}]', attr_name=i, value=v, parent=root, path=(i,), level=0
                )
        else:
            self._build_scalar_row(key_label='root', value=root, path=(), level=0)

        # Immediate background refresh to avoid stripe misalignment after clicks
        self._update_background()

        # Recompute full view metrics like a sash move would, and force redraw
        self._update_view_and_graphics()
        try:
            self.layout.canvas.ask_update()
            self.container.canvas.ask_update()
        except Exception:
            pass
        # Also schedule a metrics refresh next frame after Kivy settles sizes
        Clock.schedule_once(lambda dt: self._update_view_and_graphics(), 0)

        # Update scrollbar after content size change
        Clock.schedule_once(lambda dt: self._restore_scroll_after_rebuild(prev_px), 0)

    def _rebuild_debounced(self, delay: float = 0.0):
        '''Schedule a rebuild once per frame to coalesce rapid updates.'''
        try:
            if self._rebuild_pending:
                return
            self._rebuild_pending = True
            Clock.schedule_once(lambda dt: self._do_rebuild(), delay)
        except Exception:
            # Fallback to immediate rebuild if scheduling fails
            self._rebuild()

    def _do_rebuild(self):
        self._rebuild_pending = False
        self._rebuild()

    def _restore_scroll_after_rebuild(self, prev_px: float):
        self._scroll_px = prev_px
        self._apply_scroll_px()

    def _row_text_color(self) -> Tuple[float, float, float, float]:
        # Match stripes: row 0 at top has LIGHT_DARKER, row 1 has DARK_LIGHTER
        # Make DARK_LIGHTER row labels white for readability
        return WHITE if (self._row_counter % 2 == 1) else BLACK

    def _row_bg_color(self) -> Tuple[float, float, float, float]:
        # Background color for current row index to match zebra stripes
        return (DARK_LIGHTER if (self._row_counter % 2 == 1) else LIGHT_DARKER)

    def _humanize_label(self, name: Any) -> str:
        """Convert camelCase/PascalCase or snake_case to a human-friendly label.
        - globalNote -> "global note"
        - blackNoteDirection -> "black note direction"
        Preserves a trailing '?' and leaves bracket-index labels (e.g., "[0]") unchanged.
        """
        try:
            s = str(name)
        except Exception:
            return str(name)
        if not s:
            return s
        if s.startswith('['):
            return s
        trailing_q = s.endswith('?')
        if trailing_q:
            s = s[:-1]
        # Replace underscores with spaces
        s = s.replace('_', ' ')
        # Insert space before capitals that follow a lowercase letter or digit
        try:
            import re as _re
            s = _re.sub(r'(?<=[a-z0-9])([A-Z])', r' \1', s)
        except Exception:
            pass
        s = s.strip().lower()
        if trailing_q:
            s += '?'
        return s

    def _format_value_for_text(self, val: Any) -> str:
        # Normalize a value to a string for the TextInput display
        try:
            if isinstance(val, float):
                return _fmt_float(val)
            if isinstance(val, int):
                return str(int(val))
            if isinstance(val, list):
                parts = []
                for x in val:
                    if isinstance(x, float):
                        parts.append(_fmt_float(x))
                    elif isinstance(x, int):
                        parts.append(str(int(x)))
                    else:
                        parts.append(str(x))
                return ' '.join(parts)
            if isinstance(val, str):
                return val
            return str(val)
        except Exception:
            return str(val)

    def _bind_textinput_commit(self, ti: TextInput, path: Tuple[Union[str, int], ...], get_value: Callable[[], Any]):
        # Debounced focus-out commit; immediate commit on Enter; no tree rebuild for scalar edits.
        ti._pending_commit = None

        def _cancel_pending():
            ev = getattr(ti, '_pending_commit', None)
            if ev is not None:
                try:
                    ev.cancel()
                except Exception:
                    pass
                ti._pending_commit = None

        def _do_commit_immediate(*_):
            _cancel_pending()
            val = get_value()
            # scalar commit without rebuild; normalize the field text after write
            self._commit_value(path, val, rebuild=False, normalize_target=ti)

        def _on_focus(inst, focused: bool):
            if focused:
                _cancel_pending()
            else:
                _cancel_pending()
                ti._pending_commit = Clock.schedule_once(lambda dt: _do_commit_immediate(), 0.02)

        ti.bind(on_text_validate=_do_commit_immediate, focus=_on_focus)

    def _finalize_row(self, row: Widget):
        self.layout.add_widget(row)
        self._row_counter += 1

    def _add_info_row(self, text: str):
        tc = self._row_text_color()
        row = BoxLayout(orientation='horizontal', size_hint_y=None, height=self.STRIPE_HEIGHT)
        lbl = Label(text=text, color=tc, halign='left', valign='middle')
        lbl.bind(size=lbl.setter('text_size'))
        row.add_widget(lbl)
        self._finalize_row(row)

    # ---------- Node Builders ----------

    def _build_header_row(self):
        '''Build the non-collapsible header row with 'Tree' and 'Value' labels.
        Removes the usual indent in the left column for this first row.
        '''
        tc = self._row_text_color()
        row = BoxLayout(orientation='horizontal', size_hint_y=None, height=self.STRIPE_HEIGHT, spacing=dp(6))
        # Accent-colored background behind the entire header row but leave a gap for the divider line
        try:
            with row.canvas.before:
                Color(*ACCENT_COLOR)
                header_bg_left = Rectangle()
                header_bg_right = Rectangle()

            def _sync_header_bg(*_):
                try:
                    pad_left = float(self.layout.padding[0]) if isinstance(self.layout.padding, (list, tuple)) else 0.0
                except Exception:
                    pad_left = 0.0
                x0 = float(self.layout.x)
                y0 = float(row.y)
                h = float(row.height)
                sbw = float(getattr(self.custom_scrollbar, 'scrollbar_width', 40))
                view_right = float(self.x) + float(self.width) - sbw
                # Compute divider x position consistent with _update_value_column_divider
                x_line = x0 + pad_left + float(self.left_col_width) + float(dp(self.indent_px))
                line_w = float(dp(3))
                # Left segment
                left_w = max(0.0, (x_line - line_w / 2.0) - x0)
                header_bg_left.pos = (x0, y0)
                header_bg_left.size = (left_w, h)
                # Right segment
                right_x = x_line + line_w / 2.0
                right_w = max(0.0, view_right - right_x)
                header_bg_right.pos = (right_x, y0)
                header_bg_right.size = (right_w, h)

            _sync_header_bg()
            # Keep background synced with geometry changes
            row.bind(pos=_sync_header_bg, size=_sync_header_bg)
            self.bind(left_col_width=lambda *args: _sync_header_bg(), pos=lambda *args: _sync_header_bg(), size=lambda *args: _sync_header_bg())
            self.layout.bind(pos=lambda *args: _sync_header_bg(), size=lambda *args: _sync_header_bg())
        except Exception:
            pass

        # Left fixed column without indent
        left = BoxLayout(orientation='horizontal', size_hint_x=None, width=self.left_col_width, spacing=dp(6))
        # Small adjustable spacer before the header label
        left.add_widget(Widget(size_hint_x=None, width=dp(self.indent_px)))
        k = Label(text='[b]File Tree[/b]', markup=True, color=tc, size_hint_x=1, halign='left', valign='middle')
        k.bind(size=k.setter('text_size'))
        left.add_widget(k)

        # Right column with the same initial spacer used for values
        right = BoxLayout(orientation='horizontal', size_hint_x=1, spacing=dp(6))
        right.add_widget(Widget(size_hint_x=None, width=dp(self.indent_px)))
        v = Label(text='[b]Value[/b]', markup=True, color=tc, halign='left', valign='middle')
        v.bind(size=v.setter('text_size'))
        right.add_widget(v)

        row.add_widget(left)
        row.add_widget(right)
        self._finalize_row(row)

    def _build_object_row(self, title: str, obj: Any, path: Tuple[Union[str, int], ...], level: int, is_root: bool = False):
        tc = self._row_text_color()
        # Header row with toggle
        row = BoxLayout(orientation='horizontal', size_hint_y=None, height=self.STRIPE_HEIGHT, spacing=dp(6))

        # Left fixed column (indent + arrow + title)
        left = BoxLayout(orientation='horizontal', size_hint_x=None, width=self.left_col_width, spacing=dp(6))
        # indent spacer inside fixed column so editor start aligns across rows
        left.add_widget(Widget(size_hint_x=None, width=self.INDENT * level))
        # expand/collapse icon button (uses 'add' for closed, 'sub' for open)
        opened = self._is_open(path)
        icon_name = 'sub' if opened else 'add'
        fallback = '−' if opened else '+'
        btn = self._icon_button(icon_name, fallback, lambda *_: self._toggle_node(path))
        left.add_widget(btn)
        # small adjustable spacer before the title label/button
        left.add_widget(Widget(size_hint_x=None, width=dp(self.indent_px)))
        # title button (transparent, toggles)
        lbl_btn = Button(
            text=str(self._humanize_label(title)),
            background_normal='',
            background_down='',
            background_color=TRANSPARENT,
            color=tc,
            halign='left',
            valign='middle',
        )
        lbl_btn.bind(size=lbl_btn.setter('text_size'))
        lbl_btn.bind(on_press=lambda *_: self._toggle_node(path))
        left.add_widget(lbl_btn)

        # Right filler to keep structure consistent (no editor on object header)
        right = BoxLayout(orientation='horizontal', size_hint_x=1)

        row.add_widget(left)
        row.add_widget(right)
        self._finalize_row(row)

        if not opened and not is_root:
            return

        # Children
        if is_dataclass(obj):
            for f in fields(obj):
                attr_name = f.name
                json_name = self._json_field_name(f)
                try:
                    val = getattr(obj, attr_name)
                except Exception:
                    val = None
                self._build_value_row(
                    key_label=json_name,
                    attr_name=attr_name,
                    value=val,
                    parent=obj,
                    path=path + (attr_name,),
                    level=level + 1,
                )
        elif isinstance(obj, dict):
            for k, v in obj.items():
                self._build_value_row(
                    key_label=str(k), attr_name=str(k), value=v, parent=obj, path=path + (k,), level=level + 1
                )
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                self._build_value_row(
                    key_label=f'[{i}]', attr_name=i, value=v, parent=obj, path=path + (i,), level=level + 1
                )
        else:
            self._build_scalar_row(key_label=title, value=obj, path=path, level=level + 1)

    def _build_value_row(self, key_label: str, attr_name: Union[str, int], value: Any, parent: Any,
                         path: Tuple[Union[str, int], ...], level: int):
        if is_dataclass(value):
            self._build_object_row(title=key_label, obj=value, path=path, level=level)
            return

        if isinstance(value, list):
            # Event.* lists are lists of objects; never use numeric list editor even if empty
            if isinstance(parent, Event):
                self._build_list_object_row(key_label, value, path, level)
            else:
                if self._list_is_numeric(value):
                    self._build_number_list_row(key_label, value, path, level)
                else:
                    self._build_list_object_row(key_label, value, path, level)
            return

        # Literal choice fields (e.g., blackNoteDirection: Literal['^','v']) -> choice popup with icons
        try:
            if isinstance(attr_name, str):
                choices = self._field_literal_choices(parent, attr_name)
            else:
                choices = None
        except Exception:
            choices = None
        if choices:
            self._build_literal_choice_row(key_label, str(value), choices, parent, attr_name, path, level)
            return

        if isinstance(value, str):
            if HEX_COLOR_RE.match(value or ''):
                self._build_color_row(key_label, value, path, level)
            else:
                self._build_string_row(key_label, value, path, level)
            return

        # Detect boolean-alias fields (alias endswith '?').
        # Only render as checkbox if the underlying value is bool or int (not float).
        try:
            alias_is_bool = False
            if isinstance(attr_name, str):
                alias_is_bool = self._key_json_name_ends_with_qmark(parent, attr_name)
                # Fallback: if JSON label itself ends with '?' (extra safety)
                if not alias_is_bool and isinstance(key_label, str) and key_label.endswith('?'):
                    alias_is_bool = True
            if alias_is_bool and (isinstance(value, bool) or (isinstance(value, int) and not isinstance(value, bool))):
                self._build_bool_row(key_label, bool(value), path, level)
                return
        except Exception:
            pass

        if isinstance(value, int):
            self._build_int_row(key_label, value, path, level)
            return

        if isinstance(value, float):
            self._build_float_row(key_label, value, path, level)
            return

        self._build_scalar_row(key_label, value, path, level)

    def _make_kv_row(self, level: int, key_text: str, icon_name: Optional[str] = None) -> Tuple[BoxLayout, BoxLayout]:
        '''
        Create a row split into:
        - left fixed column (indent + key label)
        - right stretch column (editor)
        Returns (row, right_container)
        '''
        tc = self._row_text_color()
        row = BoxLayout(orientation='horizontal', size_hint_y=None, height=self.STRIPE_HEIGHT, spacing=dp(6))

        left = BoxLayout(orientation='horizontal', size_hint_x=None, width=self.left_col_width, spacing=dp(6))
        left.add_widget(Widget(size_hint_x=None, width=self.INDENT * level))
        # Optional property icon (non-collapsible rows)
        if icon_name:
            try:
                icon_widget = self._icon_button(icon_name, '·', lambda *_: None)
            except Exception:
                icon_widget = None
            if icon_widget is not None:
                left.add_widget(icon_widget)
        # Small adjustable spacer before the key label
        left.add_widget(Widget(size_hint_x=None, width=dp(self.indent_px)))
        display_key = self._humanize_label(key_text)
        k = Label(text=f'{display_key}:', color=tc, size_hint_x=1, halign='left', valign='middle')
        k.bind(size=k.setter('text_size'))
        left.add_widget(k)

        right = BoxLayout(orientation='horizontal', size_hint_x=1, spacing=dp(6))
        # Add left spacer to move value start slightly to the right (better readability vs divider)
        right.add_widget(Widget(size_hint_x=None, width=dp(self.indent_px)))

        row.add_widget(left)
        row.add_widget(right)
        return row, right

    def _build_scalar_row(self, key: str, value: Any, path: Tuple[Union[str, int], ...], level: int):
        row, right = self._make_kv_row(level, key, icon_name='property')
        vtxt = str(value)
        if len(vtxt) > 128:
            vtxt = vtxt[:125] + '...'
        tc = self._row_text_color()
        v = Label(text=vtxt, color=tc, halign='left', valign='middle')
        v.bind(size=v.setter('text_size'))
        right.add_widget(v)
        self._finalize_row(row)

    def _build_string_row(self, key: str, value: str, path: Tuple[Union[str, int], ...], level: int):
        row, right = self._make_kv_row(key_text=key, level=level, icon_name='property')
        _tc = self._row_text_color()
        lbl = Label(text=value or '', color=_tc, halign='left', valign='middle')
        lbl.bind(size=lbl.setter('text_size'))
        right.add_widget(lbl)

        # Make entire row clickable to edit via dialog
        row.bind(on_touch_down=lambda inst, touch: self._on_row_edit_touch(inst, touch, path, 'str', value))
        self._finalize_row(row)

    def _build_color_row(self, key: str, value: str, path: Tuple[Union[str, int], ...], level: int):
        row, right = self._make_kv_row(key_text=key, level=level, icon_name='colorproperty')
        # Draw a color bar as a padded button-like area that spans the right column height
        container = BoxLayout(orientation='vertical', size_hint=(1, 1), padding=dp(4))
        color_widget = Widget(size_hint=(1, 1))
        rgba = _hex_to_rgba(value or '#000000')
        inv = (1.0 - rgba[0], 1.0 - rgba[1], 1.0 - rgba[2], 1.0)
        with color_widget.canvas:
            cf = Color(*rgba)
            r = Rectangle(pos=color_widget.pos, size=color_widget.size)
            cb = Color(*inv)
            # Border rectangle uses complementary color and is half the previous thickness
            border_w = dp(1.5)
            ln = Line(rectangle=(color_widget.x, color_widget.y, color_widget.width, color_widget.height), width=border_w)
        def _sync_color_rect(*_):
            r.pos = color_widget.pos
            r.size = color_widget.size
            ln.rectangle = (color_widget.x, color_widget.y, color_widget.width, color_widget.height)
        color_widget.bind(pos=_sync_color_rect, size=_sync_color_rect)
        container.add_widget(color_widget)
        right.add_widget(container)

        # Entire row acts as color picker button
        row.bind(on_touch_down=lambda inst, touch: self._on_row_edit_touch(inst, touch, path, 'color', value))
        self._finalize_row(row)

    def _build_int_row(self, key: str, value: int, path: Tuple[Union[str, int], ...], level: int):
        row, right = self._make_kv_row(key_text=key, level=level, icon_name='property')
        lbl = Label(text=str(int(value)), color=self._row_text_color(), halign='left', valign='middle')
        lbl.bind(size=lbl.setter('text_size'))
        right.add_widget(lbl)
        row.bind(on_touch_down=lambda inst, touch: self._on_row_edit_touch(inst, touch, path, 'int', value))
        self._finalize_row(row)

    def _build_float_row(self, key: str, value: float, path: Tuple[Union[str, int], ...], level: int):
        row, right = self._make_kv_row(key_text=key, level=level, icon_name='property')
        lbl = Label(text=_fmt_float(float(value)), color=self._row_text_color(), halign='left', valign='middle')
        lbl.bind(size=lbl.setter('text_size'))
        right.add_widget(lbl)
        row.bind(on_touch_down=lambda inst, touch: self._on_row_edit_touch(inst, touch, path, 'float', value))
        self._finalize_row(row)

    def _build_literal_choice_row(self, key: str, current: str, choices: List[str], parent: Any,
                                  attr_name: str, path: Tuple[Union[str, int], ...], level: int):
        row, right = self._make_kv_row(key_text=key, level=level, icon_name='property')

        # Show current selection as an icon if available; fallback to text
        icon_name = self._literal_icon_name(attr_name, current)
        def open_popup(*_):
            self._open_literal_choice_popup(path, attr_name, current, choices)

        if icon_name:
            try:
                btn = self._icon_button(icon_name, current, lambda *_: open_popup())
            except Exception:
                btn = Button(text=current, background_normal='', background_down='',
                             background_color=TRANSPARENT, color=self._row_text_color())
                btn.bind(on_press=open_popup)
        else:
            btn = Button(text=current, background_normal='', background_down='',
                         background_color=TRANSPARENT, color=self._row_text_color())
            btn.bind(on_press=open_popup)
        right.add_widget(btn)
        # Also allow clicking anywhere in the row to open the popup
        row.bind(on_touch_down=lambda inst, touch: self._on_row_literal_touch(inst, touch, path, attr_name, current, choices))
        self._finalize_row(row)

    def _build_bool_row(self, key: str, value_bool: bool, path: Tuple[Union[str, int], ...], level: int):
        row, right = self._make_kv_row(key_text=key, level=level, icon_name='property')
        cb = CheckBox(active=bool(value_bool), size_hint=(None, None), size=(dp(22), dp(22)))
        # Commit boolean True/False directly so JSON writes 'true/false' and Python model keeps bools
        cb.bind(active=lambda inst, a: self._commit_value(path, bool(a)))
        right.add_widget(cb)
        self._finalize_row(row)

    def _build_number_list_row(self, key: str, values: List[Union[int, float]],
                               path: Tuple[Union[str, int], ...], level: int):
        row, right = self._make_kv_row(key_text=key, level=level, icon_name='property')

        # Show a compact preview like: [ 1 2 3 ] and open a dialog on click
        bl = Label(text='[', color=self._row_text_color(), size_hint_x=None, width=dp(10), halign='center', valign='middle')
        bl.bind(size=bl.setter('text_size'))
        right.add_widget(bl)

        preview = ' '.join(
            _fmt_float(v) if isinstance(v, float) and not float(v).is_integer() else str(int(v))
            if isinstance(v, (int, float)) else str(v)
            for v in values
        )
        pv_lbl = Label(text=preview, color=self._row_text_color(), halign='left', valign='middle')
        pv_lbl.bind(size=pv_lbl.setter('text_size'))
        right.add_widget(pv_lbl)

        br = Label(text=']', color=self._row_text_color(), size_hint_x=None, width=dp(10), halign='center', valign='middle')
        br.bind(size=br.setter('text_size'))
        right.add_widget(br)

        # Determine if this list should be treated as float list
        is_float_list = any(isinstance(v, float) and not float(v).is_integer() for v in values)

        # Whole row opens the dialog editor
        row.bind(on_touch_down=lambda inst, touch: self._on_row_number_list_touch(inst, touch, path, values, is_float_list))
        self._finalize_row(row)

    def _on_row_number_list_touch(self, row: Widget, touch, path, values, is_float_list: bool):
        if not row.collide_point(*touch.pos):
            return False
        # Avoid triggering when clicking on interactive children
        if hasattr(touch, 'grab_current') and touch.grab_current is not None:
            return False
        self._open_number_list_dialog(path, values, is_float_list)
        return True

    def _on_row_literal_touch(self, row: Widget, touch, path, attr_name: str, current: str, choices: List[str]):
        if not row.collide_point(*touch.pos):
            return False
        # Avoid triggering when clicking on interactive children (like buttons)
        if hasattr(touch, 'grab_current') and touch.grab_current is not None:
            return False
        self._open_literal_choice_popup(path, attr_name, current, choices)
        return True

    def _open_literal_choice_popup(self, path: Tuple[Union[str, int], ...], attr_name: str,
                                   current: str, choices: List[str]):
        prompt = f'Set {self._path_to_prompt(path)}:'
        content = BoxLayout(orientation='vertical', spacing=dp(12), padding=dp(12))

        # Bigger, high-contrast buttons row
        BTN_SIZE = dp(64)     # ~2x previous button footprint
        ICON_SIZE = dp(40)    # ~2x previous icon size
        btn_row = BoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=BTN_SIZE + dp(8))
        # Add flexible left spacer so choices can be centered
        btn_row.add_widget(Widget())

        def do_choose(choice: str):
            self._commit_value(path, choice)
            popup.dismiss()

        for ch in choices:
            # Try to use icon; fallback to text '^'/'v'
            icon_name = self._literal_icon_name(attr_name, ch)
            tile = PropertyTreeEditor.ChoiceTile(size_hint=(None, None), size=(BTN_SIZE, BTN_SIZE))
            # Draw solid background to ensure contrast and place content above it
            try:
                with tile.canvas.before:
                    Color(*ACCENT_COLOR)
                    rect = Rectangle(pos=tile.pos, size=tile.size)
                # Capture rect and tile per-iteration to avoid late binding bug
                tile.bind(
                    pos=lambda *_args, r=rect, t=tile: setattr(r, 'pos', t.pos),
                    size=lambda *_args, r=rect, t=tile: setattr(r, 'size', t.size),
                )
            except Exception:
                pass

            # Centered content: icon or text
            added = False
            if icon_name:
                try:
                    icon = IconLoader.load_icon(icon_name)
                    if icon is not None and getattr(icon, 'texture', None) is not None:
                        img = Image(texture=icon.texture, size_hint=(None, None), size=(ICON_SIZE, ICON_SIZE))
                        tile.add_widget(img)
                        added = True
                except Exception:
                    added = False
            if not added:
                lbl = Label(text=str(ch), color=WHITE)
                lbl.bind(size=lbl.setter('text_size'))
                tile.add_widget(lbl)

            tile.bind(on_press=lambda _inst, choice=ch: do_choose(choice))
            btn_row.add_widget(tile)

        # Add flexible right spacer to mirror left spacer and center tiles
        btn_row.add_widget(Widget())

        # Add flexible spacers to vertically center the row within the popup
        content.add_widget(Widget())
        content.add_widget(btn_row)
        content.add_widget(Widget())
        popup = Popup(title=prompt, content=content, size_hint=(None, None), size=(dp(420), dp(200)))
        popup.open()

    def _open_number_list_dialog(self, path: Tuple[Union[str, int], ...], values: List[Union[int, float]], is_float_list: bool):
        hint = '(Give numbers seperated by <space> e.g. 256.0 512.0 768.0)'
        prompt = f'Set {self._path_to_prompt(path)}: {hint}'
        txt = ' '.join(
            _fmt_float(v) if isinstance(v, float) and not float(v).is_integer() else str(int(v))
            if isinstance(v, (int, float)) else str(v)
            for v in values
        )
        ti = ListNumericTextInput(
            allow_float=is_float_list,
            text=txt,
            multiline=False,
            size_hint_y=None,
            height=dp(36),
            halign='left',
            cursor_blink=True,
        )
        self._style_dialog_input(ti, font_points=18.0)

        btns = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(8))
        cancel = Button(text='Cancel')
        ok = Button(text='OK')
        btns.add_widget(Widget())
        btns.add_widget(cancel)
        btns.add_widget(ok)
        content = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(10))
        content.add_widget(ti)
        content.add_widget(btns)
        popup = Popup(title=prompt, content=content, size_hint=(None, None), size=(dp(560), dp(180)))

        def parse_int_list(s: str) -> List[int]:
            parts = [p for p in s.strip().split() if p and p != '.']
            out: List[int] = []
            for p in parts:
                try:
                    # Round floats to nearest int if provided
                    v = int(round(float(p)))
                    out.append(v)
                except Exception:
                    # ignore invalid tokens
                    pass
            return out

        def parse_float_list(s: str) -> List[float]:
            parts = [p for p in s.strip().split() if p and p != '.']
            out: List[float] = []
            for p in parts:
                try:
                    v = float(p)
                    out.append(v)
                except Exception:
                    pass
            return out

        def do_ok(*_):
            s = ti.text or ''
            if is_float_list:
                parsed = parse_float_list(s)
            else:
                parsed = parse_int_list(s)
            self._commit_value(path, parsed)
            popup.dismiss()

        cancel.bind(on_press=lambda *_: popup.dismiss())
        ok.bind(on_press=do_ok)
        ti.bind(on_text_validate=do_ok)
        popup.open()
        # Focus input immediately and on next frame to ensure focus sticks
        try:
            ti.focus = True
            Clock.schedule_once(lambda dt: setattr(ti, 'focus', True), 0)
        except Exception:
            pass


    def _build_list_object_row(self, key: str, lst: List[Any], path: Tuple[Union[str, int], ...], level: int):
        tc = self._row_text_color()
        # Header for the list
        header_path = path
        row = BoxLayout(orientation='horizontal', size_hint_y=None, height=self.STRIPE_HEIGHT, spacing=dp(6))

        left = BoxLayout(orientation='horizontal', size_hint_x=None, width=self.left_col_width, spacing=dp(6))
        left.add_widget(Widget(size_hint_x=None, width=self.INDENT * level))
        opened = self._is_open(header_path)
        arrow = '<' if not opened else '>'
        btn = self._icon_button('sub' if opened else 'add', '-' if opened else '+', lambda *_: self._toggle_node(header_path))
        left.add_widget(btn)

        # If this is an Event.* list, show the corresponding tool icon before the title
        event_icon_name = None
        try:
            if isinstance(key, str) and (key in getattr(Event, '__dataclass_fields__', {})):
                event_icon_name = self._event_icon_name_for_key(key)
        except Exception:
            event_icon_name = None
        if event_icon_name:
            try:
                icon_w = self._icon_button(event_icon_name, '·', lambda *_: None)
            except Exception:
                icon_w = None
            if icon_w is not None:
                left.add_widget(icon_w)

        # small adjustable spacer before the list title button
        left.add_widget(Widget(size_hint_x=None, width=dp(self.indent_px)))
        title_btn = Button(
            text=f"{self._humanize_label(key)} (list)",
            background_normal='',
            background_down='',
            background_color=TRANSPARENT,
            color=tc,
            halign='left',
            valign='middle',
        )
        title_btn.bind(size=title_btn.setter('text_size'))
        title_btn.bind(on_press=lambda *_: self._toggle_node(header_path))
        left.add_widget(title_btn)

        # Right column (no +/− controls in value column for Event.* lists)
        right = BoxLayout(orientation='horizontal', size_hint_x=1, spacing=dp(6))

        row.add_widget(left)
        row.add_widget(right)
        self._finalize_row(row)

        if not opened:
            return

        # Items
        for i, v in enumerate(lst):
            title = f'[{i}]'
            if is_dataclass(v):
                self._build_object_row(title, v, path + (i,), level + 1)
            else:
                self._build_value_row(title, i, v, lst, path + (i,), level + 1)

    # ---------- Helpers ----------

    def _list_is_numeric(self, lst: List[Any]) -> bool:
        if not isinstance(lst, list):
            return False
        if not lst:
            # Empty lists are ambiguous; treat as numeric only when not under Event
            return False
        return all(_is_number(x) for x in lst)

    def _json_field_name(self, f) -> str:
        try:
            meta = getattr(f, 'metadata', None) or {}
            cfg = meta.get('dataclasses_json', None)
            if cfg is not None:
                # dataclasses_json.config stores a dict under 'dataclasses_json'
                if isinstance(cfg, dict):
                    name = cfg.get('field_name', None)
                    if isinstance(name, str) and name:
                        return name
                    # Sometimes alias lives on marshmallow field
                    mm = cfg.get('mm_field', None)
                    try:
                        data_key = getattr(mm, 'data_key', None)
                        if isinstance(data_key, str) and data_key:
                            return data_key
                    except Exception:
                        pass
                else:
                    # Some versions may provide an object-like accessor
                    name = getattr(cfg, 'field_name', None)
                    if isinstance(name, str) and name:
                        return name
                    try:
                        mm = getattr(cfg, 'mm_field', None)
                        data_key = getattr(mm, 'data_key', None)
                        if isinstance(data_key, str) and data_key:
                            return data_key
                    except Exception:
                        pass
        except Exception:
            pass
        return f.name

    def _field_literal_choices(self, parent_obj: Any, attr_name: Union[str, int]) -> Optional[List[str]]:
        '''Return Literal choices for a dataclass field if annotated with typing.Literal of strings.'''
        if not is_dataclass(parent_obj) or not isinstance(attr_name, str):
            return None
        try:
            for f in fields(parent_obj):
                if f.name == attr_name:
                    t = getattr(f, 'type', None)
                    if t is None:
                        return None
                    origin = get_origin(t)
                    if origin is not None and str(origin).endswith('Literal'):
                        args = list(get_args(t))
                        if all(isinstance(a, str) for a in args):
                            return args
                    # Some environments stringify Literal annotations; try parsing best-effort
        except Exception:
            return None
        return None

    def _key_json_name_ends_with_qmark(self, parent_obj: Any, attr_name: Union[str, int]) -> bool:
        if not is_dataclass(parent_obj):
            return False
        if not isinstance(attr_name, str):
            return False
        try:
            for f in fields(parent_obj):
                if f.name == attr_name:
                    jn = self._json_field_name(f)
                    if isinstance(jn, str) and jn.endswith('?'):
                        return True
                    # Heuristic fallback: treat common visibility fields as booleans
                    if f.name == 'visible' or f.name.endswith('Visible'):
                        return True
        except Exception:
            return False
        return False

    def _path_to_stave_index(self, path: Tuple[Union[str, int], ...]) -> int:
        try:
            for i, p in enumerate(path):
                if p == 'stave' and i + 1 < len(path) and isinstance(path[i + 1], int):
                    return int(path[i + 1])
        except Exception:
            pass
        return 0

    def _event_icon_name_for_key(self, key: str) -> Optional[str]:
        '''Map Event.* list keys to tool selector icon names.
        Falls back to None if no matching icon is available.
        '''
        mapping = {
            'note': 'note',
            'graceNote': 'gracenote',
            'countLine': 'countline',
            'beam': 'beam',
            'text': 'text',
            'slur': 'slur',
            'tempo': 'tempo',
            'startRepeat': 'repeats',
            'endRepeat': 'repeats',
            # section might not have an icon; return None
        }
        return mapping.get(key, None)

    def _literal_icon_name(self, attr_name: str, choice: str) -> Optional[str]:
        '''Map specific Literal fields + choice to icon names. Fallback to None if not available.
        Currently supports blackNoteDirection: '^' -> blacknoteup, 'v' -> blacknotedown.
        '''
        try:
            if attr_name == 'blackNoteDirection':
                return {
                    '^': 'blacknoteup',
                    'v': 'blacknotedown',
                }.get(choice)
        except Exception:
            pass
        return None

    # ---------- Icon helpers ----------

    class IconImageButton(ButtonBehavior, Image):
        pass

    class ChoiceTile(ButtonBehavior, AnchorLayout):
        '''Square pressable tile with colored background and centered content (icon or text).'''
        pass

    def _icon_button(self, icon_name: str, fallback_text: str, on_press: Callable[[Any], None]) -> Widget:
        '''Create a clickable icon centered in a fixed-width container; fallback to text button.
        icon_name: key in icons.icons_data ICONS
        fallback_text: shown if icon not found
        on_press: callback
        '''
        try:
            icon = IconLoader.load_icon(icon_name)
        except Exception:
            icon = None
        if icon is not None and getattr(icon, 'texture', None) is not None:
            container = AnchorLayout(size_hint_x=None, width=dp(28), anchor_x='center', anchor_y='center')
            imgbtn = PropertyTreeEditor.IconImageButton(texture=icon.texture, size_hint=(None, None), size=(dp(20), dp(20)))
            imgbtn.bind(on_press=on_press)
            container.add_widget(imgbtn)
            return container
        # Fallback to simple text button
        btn = Button(
            text=fallback_text,
            size_hint_x=None,
            width=dp(28),
            background_normal='',
            background_down='',
            background_color=TRANSPARENT,
            color=self._row_text_color(),
        )
        btn.bind(on_press=on_press)
        return btn

    # ---------- Auto-size left column ----------

    def _compute_max_row_level(self, obj: Any, level: int = 0) -> int:
        '''Compute the maximum indentation level needed for any row if fully expanded.
        - Dataclass/dict/list containers increase level for their children.
        - Numeric lists are treated as scalar rows (no deeper rows).
        Returns the maximum 'level' value used by any row.
        '''
        try:
            max_level = level
            if is_dataclass(obj):
                for f in fields(obj):
                    try:
                        v = getattr(obj, f.name)
                    except Exception:
                        v = None
                    max_level = max(max_level, self._compute_max_row_level(v, level + 1))
                return max_level
            if isinstance(obj, dict):
                for v in obj.values():
                    max_level = max(max_level, self._compute_max_row_level(v, level + 1))
                return max_level
            if isinstance(obj, list):
                if self._list_is_numeric(obj):
                    return max_level  # numeric list renders at current level only
                for v in obj:
                    max_level = max(max_level, self._compute_max_row_level(v, level + 1))
                return max_level
            # Scalars: level stays as is for this row
            return max_level
        except Exception:
            return level

    def _auto_size_left_column(self):
        '''Auto-set left_col_width based on model depth and view width constraints.
        Keeps a minimum right-column width so editors remain usable.
        '''
        try:
            # Baselines
            min_left = float(self.MIN_LEFT_COL_WIDTH)
            # Keep the right editor column usable
            min_right = float(dp(260))
            view_w = float(max(1, getattr(self, '_view_w', 0)))
            # Compute max model depth across entire SCORE to avoid jumps when expanding
            max_level = 0
            if self._score is not None:
                max_level = max(0, int(self._compute_max_row_level(self._score, 0)))
            # Space needed: indent*depth + arrow + inner spacings + baseline label width
            arrow_w = float(dp(28))
            inner_spacings = float(dp(12))  # dp(6) between indent/arrow and arrow/label
            baseline_label = float(dp(260))
            required = float(self.INDENT) * float(max_level) + arrow_w + inner_spacings + baseline_label
            # Clamp to keep right column >= min_right
            max_left_allowed = max(float(dp(200)), view_w - min_right)
            new_w = max(min_left, min(required, max_left_allowed))
            if abs(float(self.left_col_width) - new_w) > 0.5:
                self.left_col_width = new_w
        except Exception:
            # Fallback to minimum if anything goes wrong
            try:
                self.left_col_width = float(self.MIN_LEFT_COL_WIDTH)
            except Exception:
                pass

    def _apply_left_col_width_to_rows(self):
        '''Apply current left_col_width to all existing row left containers.'''
        try:
            for row in getattr(self, 'layout', None).children if hasattr(self, 'layout') else []:
                if isinstance(row, BoxLayout) and getattr(row, 'orientation', 'horizontal') == 'horizontal':
                    # Identify left container: BoxLayout child with size_hint_x=None
                    for child in row.children:
                        if isinstance(child, BoxLayout) and child.size_hint_x is None:
                            child.width = float(self.left_col_width)
                            break
        except Exception:
            pass

    def _on_left_col_width_change(self, *_):
        # Update existing rows and divider when width changes
        self._apply_left_col_width_to_rows()
        self._update_value_column_divider()
        try:
            self.layout.canvas.ask_update()
            self.container.canvas.ask_update()
        except Exception:
            pass

    def _event_add(self, event_key: str, stave_idx: int):
        '''Add a new event of type event_key to given stave via SCORE factory.'''
        if not self._score:
            return
        snake = _camel_to_snake(event_key)
        method_name = f'new_{snake}'
        fn = getattr(self._score, method_name, None)
        try:
            if callable(fn):
                try:
                    fn(stave_idx=stave_idx)
                except TypeError:
                    fn()
            self._fire_change_and_rebuild()
        except Exception:
            pass

    def _event_remove_last(self, list_ref: list):
        '''Remove last item from the given list, if any.'''
        try:
            if list_ref:
                list_ref.pop()
                self._fire_change_and_rebuild()
        except Exception:
            pass

    def _fire_change_and_rebuild(self):
        if callable(self.on_change):
            try:
                self.on_change(self._score)
            except Exception:
                pass
        # Debounced rebuild to avoid stutter when multiple changes happen quickly
        self._rebuild_debounced(0)

    def _is_open(self, path: Tuple[Union[str, int], ...]) -> bool:
        return tuple(path) in self._open_paths

    def _toggle_node(self, path: Tuple[Union[str, int], ...]):
        # Preserve current pixel scroll so expansion packs downward
        prev_px = float(self._scroll_px)
        t = tuple(path)
        if t in self._open_paths:
            if t == ():
                return
            self._open_paths.remove(t)
        else:
            self._open_paths.add(t)
        self._rebuild()
        # Immediate background update on click to keep stripes aligned
        self._update_background()
        # Run full metrics refresh like a sash move (fixes stripe anchoring)
        self._update_view_and_graphics()
        Clock.schedule_once(lambda dt: self._update_view_and_graphics(), 0)
        # Restore scroll on next frame to keep anchor stable
        Clock.schedule_once(lambda dt: self._restore_scroll_after_rebuild(prev_px), 0)

    def _commit_value(self, path: Tuple[Union[str, int], ...], new_value: Any):
        '''Write the new value into the bound SCORE object and rebuild the tree (full refresh).'''
        if self._score is None or not path:
            return
        try:
            self._write_at_path(self._score, path, new_value)
        except Exception:
            return
        if callable(self.on_change):
            try:
                self.on_change(self._score)
            except Exception:
                pass
        # Debounce rebuild to one per frame
        self._rebuild_debounced(0)

    # ---------- Row editing via dialogs ----------

    def _on_row_edit_touch(self, row: Widget, touch, path: Tuple[Union[str, int], ...], kind: str, current: Any):
        if not row.collide_point(*touch.pos):
            return False
        # Avoid triggering when clicking on interactive children (e.g., arrow buttons or checkboxes)
        if hasattr(touch, 'grab_current') and touch.grab_current is not None:
            return False
        if kind == 'str':
            self._open_text_dialog(path, str(current) if current is not None else '')
            return True
        if kind == 'int':
            self._open_number_dialog(path, str(int(current)), allow_float=False)
            return True
        if kind == 'float':
            self._open_number_dialog(path, _fmt_float(float(current)), allow_float=True)
            return True
        if kind == 'color':
            self._open_color_dialog(path, str(current) if current else '#000000')
            return True
        return False

    # ---------- Dialog input styling ----------

    def _style_dialog_input(self, ti: TextInput, font_points: float = 18.0):
        '''Increase font size a bit and vertically center text via padding within current height.
        Keeps the existing widget height; padding makes the text slightly smaller than the entry.
        '''
        try:
            ti.font_size = sp(font_points)
            ti.foreground_color = BLACK
            ti.cursor_color = BLACK
            ti.background_normal = ''
            ti.background_active = ''
            ti.background_color = (1, 1, 1, 1)
            ti.write_tab = False

            # Recompute padding to vertically center based on line height; use a safe fallback
            def _repad(*_):
                try:
                    lh = float(getattr(ti, 'line_height', 0.0))
                    if lh <= 0.0:
                        # conservative fallback for line height before the label is laid out
                        lh = float(ti.font_size) * 1.15
                    h = float(ti.height)
                    pad_y = max(0.0, (h - lh) / 2.0)
                    # Use 4-tuple padding: (left, top, right, bottom)
                    ti.padding = (dp(10), pad_y, dp(10), pad_y)
                except Exception:
                    ti.padding = (dp(10), dp(6), dp(10), dp(6))

            # Apply now, schedule once for next frame (when textures exist), and bind to changes
            _repad()
            Clock.schedule_once(lambda dt: _repad(), 0)
            ti.bind(size=lambda *_: _repad(), font_size=lambda *_: _repad())
        except Exception:
            pass

    def _path_to_prompt(self, path: Tuple[Union[str, int], ...]) -> str:
        parts: List[str] = []
        for p in path:
            if isinstance(p, int):
                parts.append(f'[{p}]')
            else:
                if parts:
                    parts.append('.')
                parts.append(str(p))
        return ''.join(parts) or 'value'

    def _open_text_dialog(self, path: Tuple[Union[str, int], ...], current: str):
        prompt = f'Set {self._path_to_prompt(path)}:'
        ti = TextInput(
            text=current or '',
            multiline=False,
            size_hint_y=None,
            height=dp(36),
            halign='left',
            cursor_blink=True,
        )
        self._style_dialog_input(ti, font_points=18.0)
        btns = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(8))
        cancel = Button(text='Cancel')
        ok = Button(text='OK')
        btns.add_widget(Widget())
        btns.add_widget(cancel)
        btns.add_widget(ok)
        content = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(10))
        content.add_widget(ti)
        content.add_widget(btns)
        popup = Popup(title=prompt, content=content, size_hint=(None, None), size=(dp(520), dp(160)))

        def do_ok(*_):
            self._commit_value(path, ti.text)
            popup.dismiss()

        cancel.bind(on_press=lambda *_: popup.dismiss())
        ok.bind(on_press=do_ok)
        ti.bind(on_text_validate=do_ok)
        popup.open()
        # Focus input immediately and on next frame to ensure focus sticks
        try:
            ti.focus = True
            Clock.schedule_once(lambda dt: setattr(ti, 'focus', True), 0)
        except Exception:
            pass

    def _open_number_dialog(self, path: Tuple[Union[str, int], ...], current: str, allow_float: bool):
        prompt = f'Set {self._path_to_prompt(path)}:'
        ti = NumericTextInput(
            allow_float=allow_float,
            text=current or '',
            multiline=False,
            size_hint_y=None,
            height=dp(36),
            halign='left',
            cursor_blink=True,
        )
        self._style_dialog_input(ti, font_points=18.0)
        btns = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(8))
        cancel = Button(text='Cancel')
        ok = Button(text='OK')
        btns.add_widget(Widget())
        btns.add_widget(cancel)
        btns.add_widget(ok)
        content = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(10))
        content.add_widget(ti)
        content.add_widget(btns)
        popup = Popup(title=prompt, content=content, size_hint=(None, None), size=(dp(520), dp(160)))

        def do_ok(*_):
            txt = ti.text.strip()
            try:
                val = float(txt) if allow_float else int(txt)
                if not allow_float:
                    self._commit_value(path, int(val))
                else:
                    self._commit_value(path, float(val))
                popup.dismiss()
            except Exception:
                # Invalid input -> no commit; keep dialog open or dismiss silently
                pass

        cancel.bind(on_press=lambda *_: popup.dismiss())
        ok.bind(on_press=do_ok)
        ti.bind(on_text_validate=do_ok)
        popup.open()
        # Focus input immediately and on next frame to ensure focus sticks
        try:
            ti.focus = True
            Clock.schedule_once(lambda dt: setattr(ti, 'focus', True), 0)
        except Exception:
            pass

    def _open_color_dialog(self, path: Tuple[Union[str, int], ...], current_hex: str):
        prompt = f'Set {self._path_to_prompt(path)}:'
        picker = ColorPicker(color=_hex_to_rgba(current_hex), size_hint=(1, 1))
        btns = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(8), padding=(dp(8), 0))
        cancel = Button(text='Cancel', size_hint_x=None, width=dp(100))
        ok = Button(text='OK', size_hint_x=None, width=dp(100))
        btns.add_widget(Widget())
        btns.add_widget(cancel)
        btns.add_widget(ok)
        content = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(8))
        content.add_widget(picker)
        content.add_widget(btns)
        popup = Popup(title=prompt, content=content, size_hint=(None, None), size=(dp(500), dp(420)))

        def do_ok(*_):
            hx = _rgba_to_hex(picker.color)
            self._commit_value(path, hx)
            popup.dismiss()

        cancel.bind(on_press=lambda *_: popup.dismiss())
        ok.bind(on_press=do_ok)
        popup.open()

    def _write_at_path(self, root: Any, path: Tuple[Union[str, int], ...], value: Any):
        '''Traverse dataclass/list attributes by attr/index path and set the value.'''
        if not path:
            return
        obj = root
        for step in path[:-1]:
            if isinstance(step, int):
                obj = obj[step]
                continue
            obj = getattr(obj, step)
        last = path[-1]
        if isinstance(last, int):
            obj[last] = value
        else:
            setattr(obj, last, value)


__all__ = ['PropertyTreeEditor']