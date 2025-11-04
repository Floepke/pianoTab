"""
Comprehensive Property Tree Editor for SCORE.

Updates:
- Event.* lists get transparent −/+ buttons:
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
  - Replaces ScrollView’s default bars with the same CustomScrollbar used by the Canvas.
  - Keeps content non-overlapping by reserving width for the scrollbar.
- Editor UX:
  - Int/Float spinboxes also accept manual numeric input; only digits and optional '.' allowed.
  - Expand/collapse “packs downward”: keeps visual scroll position stable after toggling.

Public API:
- set_score(score)
- on_change: Optional[Callable[[Any], None]]

"""

from __future__ import annotations

from typing import Any, Optional, Callable, List, Tuple, Union
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
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle, InstructionGroup
from kivy.properties import NumericProperty
from kivy.clock import Clock

from gui.colors import DARK_LIGHTER, LIGHT_DARKER, ACCENT_COLOR
from utils.canvas import CustomScrollbar
from file.SCORE import SCORE, Event

# Visual constants
BLACK = (0, 0, 0, 1)
WHITE = (1, 1, 1, 1)
TRANSPARENT = (0, 0, 0, 0)

HEX_COLOR_RE = re.compile(r"^#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})$")


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _fmt_float(v: float) -> str:
    s = f"{v:.6f}".rstrip("0").rstrip(".")
    return s if "." in s else f"{s}.0"


def _rgba_to_hex(rgba: Tuple[float, float, float, float]) -> str:
    r = max(0, min(255, int(round(rgba[0] * 255))))
    g = max(0, min(255, int(round(rgba[1] * 255))))
    b = max(0, min(255, int(round(rgba[2] * 255))))
    return f"#{r:02X}{g:02X}{b:02X}"


def _hex_to_rgba(hex_color: str) -> Tuple[float, float, float, float]:
    s = hex_color.lstrip("#")
    if len(s) == 3:
        s = "".join([c * 2 for c in s])
    if len(s) != 6:
        # Fallback to white if invalid
        return (1.0, 1.0, 1.0, 1.0)
    r = int(s[0:2], 16) / 255.0
    g = int(s[2:4], 16) / 255.0
    b = int(s[4:6], 16) / 255.0
    return (r, g, b, 1.0)


def _camel_to_snake(name: str) -> str:
    return re.sub(r"(?<!^)([A-Z])", r"_\1", name).lower()


class NumericTextInput(TextInput):
    """
    TextInput that only accepts digits and optionally a single dot.
    allow_float=False -> digits only (ints)
    allow_float=True  -> digits + optional '.' (floats)
    """
    def __init__(self, allow_float: bool, **kwargs):
        super().__init__(**kwargs)
        self.allow_float = allow_float

    def insert_text(self, substring, from_undo=False):
        # Filter characters
        allowed = "0123456789"
        if self.allow_float:
            allowed += "."
            # prevent multiple dots
            if "." in substring and "." in self.text:
                substring = substring.replace(".", "")
        filtered = "".join(ch for ch in substring if ch in allowed)
        return super().insert_text(filtered, from_undo=from_undo)


class NumericSpinBox(BoxLayout):
    """
    Numeric spinbox with -/+ buttons and an editable TextInput.
    - int mode: step=1
    - float mode: step=0.05
    Validates and commits values via 'on_commit' callback.
    Visual: transparent buttons, white input with black text.
    """

    def __init__(self, value: Union[int, float], is_float: bool, step: float,
                 on_commit: Callable[[Union[int, float]], None],
                 input_bg_color: Tuple[float, float, float, float] = (1, 1, 1, 0.001),
                 input_fg_color: Tuple[float, float, float, float] = (0, 0, 0, 1),
                 **kwargs):
        super().__init__(orientation="horizontal", spacing=dp(6), size_hint_y=None, height=dp(28), **kwargs)
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
            background_normal="",
            background_active="",
            background_color=input_bg_color,
            foreground_color=input_fg_color,
            cursor_color=input_fg_color,
            selection_color=(ACCENT_COLOR[0], ACCENT_COLOR[1], ACCENT_COLOR[2], 0.35),
        )
        self.input.bind(on_text_validate=self._commit_from_text, focus=self._on_focus_change)
        self.add_widget(self.input)

        # - button (transparent) moved to the right of the textbox
        self.dec_btn = Button(
            text="−",
            size_hint_x=None,
            width=dp(28),
            background_normal="",
            background_down="",
            background_color=TRANSPARENT,
            color=ACCENT_COLOR,
        )
        self.dec_btn.bind(on_press=lambda *_: self._nudge(-self._step))
        self.add_widget(self.dec_btn)

        # + button (transparent)
        self.inc_btn = Button(
            text="+",
            size_hint_x=None,
            width=dp(28),
            background_normal="",
            background_down="",
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
                v = float(txt) if txt != "" else float(self._value)
                self._value = v
                self.input.text = self._text_of(v)
                self._on_commit(v)
            else:
                v = int(round(float(txt))) if txt != "" else int(self._value)
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
    """
    Color picker field with:
    - Swatch
    - Hex label
    - 'Pick…' button that opens a Popup with ColorPicker and Cancel/OK
    Commits only on OK; Cancel reverts.
    Visual: button transparent, label auto-contrasted by row color.
    """

    def __init__(self, hex_value: str, on_commit: Callable[[str], None], label_color=BLACK, **kwargs):
        super().__init__(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(28), **kwargs)
        self._hex = hex_value if isinstance(hex_value, str) else "#000000"
        self._on_commit = on_commit

        # Swatch rectangle
        self.swatch = Widget(size_hint=(None, None), size=(dp(22), dp(22)))
        with self.swatch.canvas:
            self._swatch_color = Color(*_hex_to_rgba(self._hex))
            self._swatch_rect = Rectangle(pos=self.swatch.pos, size=self.swatch.size)
        self.swatch.bind(
            pos=lambda *_: setattr(self._swatch_rect, "pos", self.swatch.pos),
            size=lambda *_: setattr(self._swatch_rect, "size", self.swatch.size),
        )
        self.add_widget(self.swatch)

        # Hex label (auto color)
        self.lbl = Label(text=self._hex, color=label_color, size_hint_x=1, halign="left", valign="middle")
        self.lbl.bind(size=self.lbl.setter("text_size"))
        self.add_widget(self.lbl)

        # Pick button (transparent)
        self.btn = Button(
            text="Pick…",
            size_hint=(None, 1),
            width=dp(64),
            background_normal="",
            background_down="",
            background_color=TRANSPARENT,
            color=label_color,
        )
        self.btn.bind(on_press=lambda *_: self._open_picker())
        self.add_widget(self.btn)

    def _open_picker(self):
        rgba = _hex_to_rgba(self._hex)
        picker = ColorPicker(color=rgba, size_hint=(1, 1))
        buttons = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40), spacing=dp(8), padding=(dp(8), 0))

        cancel = Button(
            text="Cancel",
            size_hint_x=None,
            width=dp(100),
            background_normal="",
            background_down="",
            background_color=TRANSPARENT,
            color=BLACK,
        )
        ok = Button(
            text="OK",
            size_hint_x=None,
            width=dp(100),
            background_normal="",
            background_down="",
            background_color=TRANSPARENT,
            color=BLACK,
        )

        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(8))
        content.add_widget(picker)
        buttons.add_widget(Widget())
        buttons.add_widget(cancel)
        buttons.add_widget(ok)
        content.add_widget(buttons)

        popup = Popup(title="Select Color", content=content, size_hint=(None, None), size=(dp(500), dp(400)))

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
    """
    Property tree editor for SCORE with foldable nodes and type-aware editors.
    """

    STRIPE_HEIGHT = dp(28)
    INDENT = dp(50)
    LEFT_COL_WIDTH = dp(420)  # fixed left column (indent + arrow + label) so editors align

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", size_hint=(1, 1), **kwargs)

        # Container to overlay ScrollView and custom scrollbar (avoids ScrollView 1-child limit)
        self.container = FloatLayout(size_hint=(1, 1))
        self.add_widget(self.container)

        # ScrollView with hidden native scrollbar
        self.sv = ScrollView(
            size_hint=(None, None),
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=0,
            scroll_type=["bars", "content"],
        )

        # Content layout (no vertical gaps; align rows to stripes)
        self.layout = BoxLayout(
            orientation="vertical",
            spacing=0,
            padding=(dp(10), 0, dp(10), 0),
            size_hint_y=None,
            size_hint_x=None,
            width=100,  # will be updated by view metrics
        )
        self.layout.bind(minimum_height=self.layout.setter("height"))
        self.sv.add_widget(self.layout)
        self.container.add_widget(self.sv)

        # Background stripes behind content
        self._bg_group = InstructionGroup()
        self.layout.canvas.before.add(self._bg_group)

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
        self._rebuild()

    # ---------- Rendering ----------

    def _update_background(self):
        # Draw alternating stripes from the top of the layout downward
        if not hasattr(self, "_bg_group") or self._bg_group is None:
            return
        self._bg_group.clear()
        tgt = getattr(self, "layout", None) or self
        w = float(getattr(tgt, "width", 0.0))
        h = float(getattr(tgt, "height", 0.0))
        x0 = float(getattr(tgt, "x", 0.0))
        # Pixel-align the starting top to avoid subpixel drift between rebuilds
        y_top_float = float(getattr(tgt, "top", getattr(tgt, "y", 0.0) + h))
        y_top = float(int(round(y_top_float)))
        if w <= 0 or h <= 0:
            return

        # Exact number of visible stripes; no extra "+2" rows
        n = int(math.ceil(h / self.STRIPE_HEIGHT))
        y = y_top
        for i in range(n):
            color = LIGHT_DARKER if (i % 2 == 0) else DARK_LIGHTER
            self._bg_group.add(Color(*color))
            self._bg_group.add(Rectangle(pos=(x0, y - self.STRIPE_HEIGHT), size=(w, self.STRIPE_HEIGHT)))
            y -= self.STRIPE_HEIGHT

    def _rebuild(self):
        # Capture current pixel scroll so we can restore after rebuild (pack downwards)
        prev_px = float(self._scroll_px)

        self.layout.clear_widgets()
        self._row_counter = 0

        if self._score is None:
            self._add_info_row("No SCORE bound")
            # Ensure scrollbar reflects new content
            Clock.schedule_once(lambda dt: self.custom_scrollbar.update_layout(), 0)
            return

        # Render root object
        self._build_object_row(title="SCORE", obj=self._score, path=(), level=0, is_root=True)

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
                return " ".join(parts)
            if isinstance(val, str):
                return val
            return str(val)
        except Exception:
            return str(val)

    def _bind_textinput_commit(self, ti: TextInput, path: Tuple[Union[str, int], ...], get_value: Callable[[], Any]):
        # Debounced focus-out commit; immediate commit on Enter; no tree rebuild for scalar edits.
        ti._pending_commit = None

        def _cancel_pending():
            ev = getattr(ti, "_pending_commit", None)
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
        row = BoxLayout(orientation="horizontal", size_hint_y=None, height=self.STRIPE_HEIGHT)
        lbl = Label(text=text, color=tc, halign="left", valign="middle")
        lbl.bind(size=lbl.setter("text_size"))
        row.add_widget(lbl)
        self._finalize_row(row)

    # ---------- Node Builders ----------

    def _build_object_row(self, title: str, obj: Any, path: Tuple[Union[str, int], ...], level: int, is_root: bool = False):
        tc = self._row_text_color()
        # Header row with toggle
        row = BoxLayout(orientation="horizontal", size_hint_y=None, height=self.STRIPE_HEIGHT, spacing=dp(6))

        # Left fixed column (indent + arrow + title)
        left = BoxLayout(orientation="horizontal", size_hint_x=None, width=self.LEFT_COL_WIDTH, spacing=dp(6))
        # indent spacer inside fixed column so editor start aligns across rows
        left.add_widget(Widget(size_hint_x=None, width=self.INDENT * level))
        # arrow (transparent button)
        opened = self._is_open(path)
        arrow = "<" if not opened else ">"
        btn = Button(
            text=arrow,
            size_hint_x=None,
            width=dp(28),
            background_normal="",
            background_down="",
            background_color=TRANSPARENT,
            color=tc,
        )
        btn.bind(on_press=lambda *_: self._toggle_node(path))
        left.add_widget(btn)
        # title button (transparent, toggles)
        lbl_btn = Button(
            text=str(title),
            background_normal="",
            background_down="",
            background_color=TRANSPARENT,
            color=tc,
            halign="left",
            valign="middle",
        )
        lbl_btn.bind(size=lbl_btn.setter("text_size"))
        lbl_btn.bind(on_press=lambda *_: self._toggle_node(path))
        left.add_widget(lbl_btn)

        # Right filler to keep structure consistent (no editor on object header)
        right = BoxLayout(orientation="horizontal", size_hint_x=1)

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
                    key_label=f"[{i}]", attr_name=i, value=v, parent=obj, path=path + (i,), level=level + 1
                )
        else:
            self._build_scalar_row(key_label=title, value=obj, path=path, level=level + 1)

    def _build_value_row(self, key_label: str, attr_name: Union[str, int], value: Any, parent: Any,
                         path: Tuple[Union[str, int], ...], level: int):
        if is_dataclass(value):
            self._build_object_row(title=key_label, obj=value, path=path, level=level)
            return

        if isinstance(value, list):
            if self._list_is_numeric(value):
                self._build_number_list_row(key_label, value, path, level)
            else:
                self._build_list_object_row(key_label, value, path, level)
            return

        if isinstance(value, str):
            if HEX_COLOR_RE.match(value or ""):
                self._build_color_row(key_label, value, path, level)
            else:
                self._build_string_row(key_label, value, path, level)
            return

        if isinstance(value, (int, float)) and self._key_json_name_ends_with_qmark(parent, attr_name):
            self._build_bool_row(key_label, int(value), path, level)
            return

        if isinstance(value, int):
            self._build_int_row(key_label, value, path, level)
            return

        if isinstance(value, float):
            self._build_float_row(key_label, value, path, level)
            return

        self._build_scalar_row(key_label, value, path, level)

    def _make_kv_row(self, level: int, key_text: str) -> Tuple[BoxLayout, BoxLayout]:
        """
        Create a row split into:
        - left fixed column (indent + key label)
        - right stretch column (editor)
        Returns (row, right_container)
        """
        tc = self._row_text_color()
        row = BoxLayout(orientation="horizontal", size_hint_y=None, height=self.STRIPE_HEIGHT, spacing=dp(6))

        left = BoxLayout(orientation="horizontal", size_hint_x=None, width=self.LEFT_COL_WIDTH, spacing=dp(6))
        left.add_widget(Widget(size_hint_x=None, width=self.INDENT * level))
        k = Label(text=f"{key_text}:", color=tc, size_hint_x=None, width=dp(260), halign="left", valign="middle")
        k.bind(size=k.setter("text_size"))
        left.add_widget(k)

        right = BoxLayout(orientation="horizontal", size_hint_x=1, spacing=dp(6))

        row.add_widget(left)
        row.add_widget(right)
        return row, right

    def _build_scalar_row(self, key: str, value: Any, path: Tuple[Union[str, int], ...], level: int):
        row, right = self._make_kv_row(level, key)
        vtxt = str(value)
        if len(vtxt) > 128:
            vtxt = vtxt[:125] + "..."
        tc = self._row_text_color()
        v = Label(text=vtxt, color=tc, halign="left", valign="middle")
        v.bind(size=v.setter("text_size"))
        right.add_widget(v)
        self._finalize_row(row)

    def _build_string_row(self, key: str, value: str, path: Tuple[Union[str, int], ...], level: int):
        row, right = self._make_kv_row(key_text=key, level=level)
        _bg = self._row_bg_color()
        _tc = self._row_text_color()
        ti = TextInput(
            text=value or "",
            multiline=False,
            write_tab=False,
            background_normal="",
            background_active="",
            background_color=_bg,
            foreground_color=_tc,
            cursor_color=_tc,
            selection_color=(ACCENT_COLOR[0], ACCENT_COLOR[1], ACCENT_COLOR[2], 0.35),
            size_hint_y=1,
            size_hint_x=1,
        )
        ti.bind(on_text_validate=lambda *_: self._commit_value(path, ti.text),
                focus=lambda inst, f: (not f) and self._commit_value(path, ti.text))
        right.add_widget(ti)
        self._finalize_row(row)

    def _build_color_row(self, key: str, value: str, path: Tuple[Union[str, int], ...], level: int):
        row, right = self._make_kv_row(key_text=key, level=level)
        field = ColorField(hex_value=value or "#000000", on_commit=lambda hx: self._commit_value(path, hx),
                           label_color=self._row_text_color())
        right.add_widget(field)
        self._finalize_row(row)

    def _build_int_row(self, key: str, value: int, path: Tuple[Union[str, int], ...], level: int):
        row, right = self._make_kv_row(key_text=key, level=level)
        spin = NumericSpinBox(
            value=value,
            is_float=False,
            step=1.0,
            on_commit=lambda v: self._commit_value(path, int(v)),
            input_bg_color=self._row_bg_color(),
            input_fg_color=self._row_text_color(),
        )
        right.add_widget(spin)
        self._finalize_row(row)

    def _build_float_row(self, key: str, value: float, path: Tuple[Union[str, int], ...], level: int):
        row, right = self._make_kv_row(key_text=key, level=level)
        spin = NumericSpinBox(
            value=value,
            is_float=True,
            step=0.05,
            on_commit=lambda v: self._commit_value(path, float(v)),
            input_bg_color=self._row_bg_color(),
            input_fg_color=self._row_text_color(),
        )
        right.add_widget(spin)
        self._finalize_row(row)

    def _build_bool_row(self, key: str, value01: int, path: Tuple[Union[str, int], ...], level: int):
        row, right = self._make_kv_row(key_text=key, level=level)
        cb = CheckBox(active=bool(value01), size_hint=(None, None), size=(dp(22), dp(22)))
        cb.bind(active=lambda inst, a: self._commit_value(path, 1 if a else 0))
        right.add_widget(cb)
        self._finalize_row(row)

    def _build_number_list_row(self, key: str, values: List[Union[int, float]],
                               path: Tuple[Union[str, int], ...], level: int):
        row, right = self._make_kv_row(key_text=key, level=level)

        # left bracket + text + right bracket
        bl = Label(text="[", color=self._row_text_color(), size_hint_x=None, width=dp(10), halign="center", valign="middle")
        bl.bind(size=bl.setter("text_size"))
        right.add_widget(bl)

        txt = " ".join(
            _fmt_float(v) if isinstance(v, float) and not float(v).is_integer() else str(int(v))
            if isinstance(v, (int, float)) else str(v)
            for v in values
        )
        _bg = self._row_bg_color()
        _tc = self._row_text_color()
        ti = TextInput(
            text=txt,
            multiline=False,
            write_tab=False,
            background_normal="",
            background_active="",
            background_color=_bg,
            foreground_color=_tc,
            cursor_color=_tc,
            selection_color=(ACCENT_COLOR[0], ACCENT_COLOR[1], ACCENT_COLOR[2], 0.35),
            size_hint_y=1,
            size_hint_x=1,
        )

        def _parse_list_text_to_values(s: str) -> List[Union[int, float]]:
            parts = [p for p in s.strip().split() if p]
            parsed: List[Union[int, float]] = []
            saw_float = False
            for p in parts:
                try:
                    fv = float(p)
                    if fv.is_integer():
                        parsed.append(int(fv))
                    else:
                        parsed.append(fv)
                        saw_float = True
                except Exception:
                    # ignore invalid tokens
                    pass
            if saw_float:
                # promote ints to float to preserve type consistency
                parsed = [float(v) if isinstance(v, int) else v for v in parsed]
            return parsed

        ti.bind(
            on_text_validate=lambda *_: self._commit_value(path, _parse_list_text_to_values(ti.text)),
            focus=lambda inst, f: (not f) and self._commit_value(path, _parse_list_text_to_values(ti.text))
        )
        right.add_widget(ti)

        br = Label(text="]", color=self._row_text_color(), size_hint_x=None, width=dp(10), halign="center", valign="middle")
        br.bind(size=br.setter("text_size"))
        right.add_widget(br)

        self._finalize_row(row)


    def _build_list_object_row(self, key: str, lst: List[Any], path: Tuple[Union[str, int], ...], level: int):
        tc = self._row_text_color()
        # Header for the list
        header_path = path
        row = BoxLayout(orientation="horizontal", size_hint_y=None, height=self.STRIPE_HEIGHT, spacing=dp(6))

        left = BoxLayout(orientation="horizontal", size_hint_x=None, width=self.LEFT_COL_WIDTH, spacing=dp(6))
        left.add_widget(Widget(size_hint_x=None, width=self.INDENT * level))
        opened = self._is_open(header_path)
        arrow = "<" if not opened else ">"
        btn = Button(
            text=arrow,
            size_hint_x=None,
            width=dp(28),
            background_normal="",
            background_down="",
            background_color=TRANSPARENT,
            color=tc,
        )
        btn.bind(on_press=lambda *_: self._toggle_node(header_path))
        left.add_widget(btn)

        title_btn = Button(
            text=f"{key} (list)",
            background_normal="",
            background_down="",
            background_color=TRANSPARENT,
            color=tc,
            halign="left",
            valign="middle",
        )
        title_btn.bind(size=title_btn.setter("text_size"))
        title_btn.bind(on_press=lambda *_: self._toggle_node(header_path))
        left.add_widget(title_btn)

        # Right column for controls (+/−) aligned to the right
        right = BoxLayout(orientation="horizontal", size_hint_x=1, spacing=dp(6))
        # If this is an Event.* list, add transparent − / + buttons on the right
        is_event_list = isinstance(key, str) and (key in getattr(Event, "__dataclass_fields__", {}))
        if is_event_list:
            stave_idx = self._path_to_stave_index(path)
            right.add_widget(Widget(size_hint_x=1))
            minus_btn = Button(
                text="−",
                size_hint_x=None,
                width=dp(28),
                background_normal="",
                background_down="",
                background_color=TRANSPARENT,
                color=tc,
            )
            minus_btn.bind(on_press=lambda *_: self._event_remove_last(lst))
            plus_btn = Button(
                text="+",
                size_hint_x=None,
                width=dp(28),
                background_normal="",
                background_down="",
                background_color=TRANSPARENT,
                color=tc,
            )
            plus_btn.bind(on_press=lambda *_: self._event_add(key, stave_idx))
            right.add_widget(minus_btn)
            right.add_widget(plus_btn)

        row.add_widget(left)
        row.add_widget(right)
        self._finalize_row(row)

        if not opened:
            return

        # Items
        for i, v in enumerate(lst):
            title = f"[{i}]"
            if is_dataclass(v):
                self._build_object_row(title, v, path + (i,), level + 1)
            else:
                self._build_value_row(title, i, v, lst, path + (i,), level + 1)

    # ---------- Helpers ----------

    def _list_is_numeric(self, lst: List[Any]) -> bool:
        if not isinstance(lst, list):
            return False
        if not lst:
            return True
        return all(_is_number(x) for x in lst)

    def _json_field_name(self, f) -> str:
        try:
            meta = getattr(f, "metadata", None) or {}
            cfg = meta.get("dataclasses_json", None)
            if cfg is not None:
                name = getattr(cfg, "field_name", None)
                if isinstance(name, str) and name:
                    return name
        except Exception:
            pass
        return f.name

    def _key_json_name_ends_with_qmark(self, parent_obj: Any, attr_name: Union[str, int]) -> bool:
        if not is_dataclass(parent_obj):
            return False
        if not isinstance(attr_name, str):
            return False
        try:
            for f in fields(parent_obj):
                if f.name == attr_name:
                    jn = self._json_field_name(f)
                    return isinstance(jn, str) and jn.endswith("?")
        except Exception:
            return False
        return False

    def _path_to_stave_index(self, path: Tuple[Union[str, int], ...]) -> int:
        try:
            for i, p in enumerate(path):
                if p == "stave" and i + 1 < len(path) and isinstance(path[i + 1], int):
                    return int(path[i + 1])
        except Exception:
            pass
        return 0

    def _event_add(self, event_key: str, stave_idx: int):
        """Add a new event of type event_key to given stave via SCORE factory."""
        if not self._score:
            return
        snake = _camel_to_snake(event_key)
        method_name = f"new_{snake}"
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
        """Remove last item from the given list, if any."""
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
        self._rebuild()
        # Ensure background is refreshed immediately after model mutations
        self._update_background()
        # Also refresh full metrics to simulate sash-resize behavior and fix stripes anchoring
        self._update_view_and_graphics()
        Clock.schedule_once(lambda dt: self._update_view_and_graphics(), 0)

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
        """Write the new value into the bound SCORE object and rebuild the tree (full refresh)."""
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
        # Full rebuild and sash-like refresh to keep background aligned
        self._rebuild()
        self._update_background()
        self._update_view_and_graphics()
        Clock.schedule_once(lambda dt: self._update_view_and_graphics(), 0)

    def _write_at_path(self, root: Any, path: Tuple[Union[str, int], ...], value: Any):
        """Traverse dataclass/list attributes by attr/index path and set the value."""
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


__all__ = ["PropertyTreeEditor"]