from __future__ import annotations

from typing import List, Optional

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.metrics import dp
from kivy.properties import ObjectProperty
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle

from gui.colors import DARK, DARK_LIGHTER, LIGHT, ACCENT

# Local BLACK color to match ToolSelector styling
BLACK = (0, 0, 0, 1)

try:
    from file.baseGrid import BaseGrid
except Exception:
    # Lightweight fallback structure if import fails (for standalone use)
    class BaseGrid:
        def __init__(self, numerator=4, denominator=4, gridCountsEnabled=None, measureAmount=8, timeSignatureIndicatorVisible=1):
            self.numerator = numerator
            self.denominator = denominator
            self.gridCountsEnabled = gridCountsEnabled or [1, 2, 3, 4]
            self.measureAmount = measureAmount
            self.timeSignatureIndicatorVisible = timeSignatureIndicatorVisible


class _NumericTextInput(TextInput):
    """TextInput that only accepts a single integer (digits only)."""
    def __init__(self, **kwargs):
        super().__init__(multiline=False, write_tab=False, **kwargs)

    def insert_text(self, substring, from_undo=False):
        filtered = ''.join(ch for ch in substring if ch.isdigit())
        return super().insert_text(filtered, from_undo=from_undo)


class _NumericListTextInput(TextInput):
    """TextInput that accepts integers separated by spaces (e.g., '1 2 3 4')."""
    def __init__(self, **kwargs):
        super().__init__(multiline=False, write_tab=False, **kwargs)

    def insert_text(self, substring, from_undo=False):
        filtered = ''.join(ch for ch in substring if (ch.isdigit() or ch == ' '))
        return super().insert_text(filtered, from_undo=from_undo)

    def get_int_list(self) -> List[int]:
        parts = [p for p in self.text.strip().split(' ') if p]
        out: List[int] = []
        for p in parts:
            try:
                out.append(int(p))
            except Exception:
                # Ignore invalid tokens silently
                pass
        return out


class _EntryRow(BoxLayout):
    """Row with a left label and a right input widget."""
    def __init__(self, label_text: str, input_widget: Widget, **kwargs):
        super().__init__(orientation='horizontal', padding=(0, 6, 0, 6), spacing=8, size_hint_y=None, height=dp(32), **kwargs)
        self.add_widget(Label(text=label_text, size_hint_x=0.4))
        input_widget.size_hint_x = 0.6
        self.add_widget(input_widget)


class _GridListItem(BoxLayout):
    """Styled list item mirroring ToolSelector buttons (no icon)."""
    def __init__(self, text: str, on_select=None, **kwargs):
        super().__init__(
            orientation='horizontal',
            size_hint_y=None,
            height=60,
            spacing=8,
            padding=[8, 0, 8, 0],
            **kwargs
        )
        self.text = text
        self._on_select = on_select
        self.is_selected = False

        with self.canvas.before:
            self.bg_color = Color(*DARK_LIGHTER)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.label = Label(
            text=text,
            font_size='16sp',
            bold=False,
            color=LIGHT,
            halign='left',
            valign='middle',
            text_size=(None, None)
        )
        self.label.bind(size=self._update_text_size)
        self.add_widget(self.label)

        self.bind(on_touch_down=self._on_touch_down)
        self._update_style()

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def _update_text_size(self, *args):
        self.label.text_size = (self.label.width, None)

    def _on_touch_down(self, instance, touch):
        if self.collide_point(*touch.pos):
            if self._on_select:
                try:
                    self._on_select()
                except Exception:
                    pass
            return True
        return False

    def set_selected(self, selected: bool):
        self.is_selected = selected
        self._update_style()

    def _update_style(self):
        if self.is_selected:
            self.bg_color.rgba = ACCENT
            self.label.color = BLACK
            self.label.bold = True
        else:
            self.bg_color.rgba = DARK_LIGHTER
            self.label.color = LIGHT
            self.label.bold = False


class BaseGridEditor(BoxLayout):
    """Editor for a list of BaseGrid objects.

    Layout:
    - entry_part (vertical): Numerator, Denominator, Measure Amount, Grid (space-separated ints)
    - select_part (vertical): ListBox to select current BaseGrid + control buttons (^ v - +)
    """
    grids: List[BaseGrid]
    selected_index: int
    on_change = ObjectProperty(None, allownone=True)  # Optional callback when grids change

    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=10, spacing=0, **kwargs)
        # Make the outer container grow to fit its children when placed inside a ScrollView
        self.size_hint_y = None
        self.bind(minimum_height=self.setter('height'))
        # Outer background: DARK_LIGHTER
        with self.canvas.before:
            Color(*DARK_LIGHTER)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *_: setattr(self._bg_rect, 'pos', self.pos),
                  size=lambda *_: setattr(self._bg_rect, 'size', self.size))
        self.grids = []
        self.selected_index = -1

        # entry_part
        self.entry_part = BoxLayout(orientation='vertical', padding=0, spacing=8, size_hint_y=None)
        self.entry_part.bind(minimum_height=self.entry_part.setter('height'))

        # Numerator (integer)
        self.num_input = _NumericTextInput(text='4')
        self.entry_part.add_widget(_EntryRow('Numerator', self.num_input))

        # Denominator (choices)
        self.den_spinner = Spinner(text='4', values=('1', '2', '4', '8', '16', '32'), size_hint_y=None, height=dp(32))
        self.entry_part.add_widget(_EntryRow('Denominator', self.den_spinner))

        # Measure Amount (integer)
        self.meas_input = _NumericTextInput(text='8')
        self.entry_part.add_widget(_EntryRow('Measure Amount', self.meas_input))

        # Grid (space-separated ints)
        self.grid_input = _NumericListTextInput(text='1 2 3 4')
        self.entry_part.add_widget(_EntryRow('Grid', self.grid_input))

        # select_part
        self.select_part = BoxLayout(orientation='vertical', padding=0, spacing=8, size_hint_y=None)
        self.select_part.bind(minimum_height=self.select_part.setter('height'))
        # ListBox area
        # Make the list box visible by giving ScrollView a fixed height
        self.list_scroll = ScrollView(size_hint=(1, None), height=dp(200))
        self.list_container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=4)
        self.list_container.bind(minimum_height=self.list_container.setter('height'))
        # Rounded DARK_LIGHTER background similar to ToolSelector
        with self.list_container.canvas.before:
            Color(*DARK_LIGHTER)
            self._list_bg = RoundedRectangle(pos=self.list_container.pos, size=self.list_container.size, radius=[6])
        self.list_container.bind(pos=lambda *_: setattr(self._list_bg, 'pos', self.list_container.pos),
                                 size=lambda *_: setattr(self._list_bg, 'size', self.list_container.size))
        self.list_scroll.add_widget(self.list_container)
        self.select_part.add_widget(self.list_scroll)

        # Control buttons row
        self.btn_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(36), spacing=6)
        self.btn_up = Button(text='^')
        self.btn_down = Button(text='v')
        self.btn_del = Button(text='-')
        self.btn_add = Button(text='+')
        self.btn_row.add_widget(self.btn_up)
        self.btn_row.add_widget(self.btn_down)
        self.btn_row.add_widget(self.btn_del)
        self.btn_row.add_widget(self.btn_add)
        self.select_part.add_widget(self.btn_row)

        # Assemble
        self.add_widget(self.entry_part)
        self.add_widget(self.select_part)

        # Bindings
        self.num_input.bind(text=lambda *_: self._commit_entry_changes())
        self.den_spinner.bind(text=lambda *_: self._commit_entry_changes())
        self.meas_input.bind(text=lambda *_: self._commit_entry_changes())
        self.grid_input.bind(text=lambda *_: self._commit_entry_changes())

        self.btn_up.bind(on_release=lambda *_: self._move_selected(-1))
        self.btn_down.bind(on_release=lambda *_: self._move_selected(+1))
        self.btn_add.bind(on_release=lambda *_: self._add_grid())
        self.btn_del.bind(on_release=lambda *_: self._delete_selected())

        # Initialize with one default grid
        Clock.schedule_once(lambda dt: self._ensure_initial_grid(), 0)

    # Public API
    def set_grids(self, grids: List[BaseGrid]):
        self.grids = list(grids or [])
        self.selected_index = 0 if self.grids else -1
        self._refresh_list()
        self._load_selected_into_entries()

    def get_grids(self) -> List[BaseGrid]:
        return list(self.grids)

    # Internals
    def _ensure_initial_grid(self):
        if not self.grids:
            self.grids.append(BaseGrid())
            self.selected_index = 0
            self._refresh_list()
            self._load_selected_into_entries()

    def _refresh_list(self):
        self._list_items = {}
        self.list_container.clear_widgets()
        for idx, g in enumerate(self.grids):
            label = f"{idx+1}. {g.numerator}/{g.denominator} x {g.measureAmount} \u2014 Grid: {' '.join(map(str, g.gridCountsEnabled))}"
            item = _GridListItem(text=label, on_select=lambda i=idx: self._select_index(i))
            self._list_items[idx] = item
            self.list_container.add_widget(item)
        self._refresh_selection_state()

    def _select_index(self, i: int):
        self.selected_index = i
        self._load_selected_into_entries()
        self._refresh_selection_state()

    def _refresh_selection_state(self):
        for i, item in getattr(self, '_list_items', {}).items():
            item.set_selected(i == self.selected_index)

    def _load_selected_into_entries(self):
        i = self.selected_index
        if i < 0 or i >= len(self.grids):
            return
        g = self.grids[i]
        # Update entries without triggering excessive commits
        self.num_input.text = str(int(g.numerator))
        self.den_spinner.text = str(int(g.denominator))
        self.meas_input.text = str(int(g.measureAmount))
        self.grid_input.text = ' '.join(map(str, g.gridCountsEnabled or []))

    def _commit_entry_changes(self):
        i = self.selected_index
        if i < 0 or i >= len(self.grids):
            return
        g = self.grids[i]
        try:
            g.numerator = int(self.num_input.text or str(g.numerator))
        except Exception:
            pass
        try:
            g.denominator = int(self.den_spinner.text or str(g.denominator))
        except Exception:
            pass
        try:
            g.measureAmount = int(self.meas_input.text or str(g.measureAmount))
        except Exception:
            pass
        # Update grid counts from list
        lst = self.grid_input.get_int_list()
        if lst:
            g.gridCountsEnabled = lst
        self._refresh_list()
        self._emit_change()

    def _move_selected(self, delta: int):
        i = self.selected_index
        if i < 0:
            return
        j = i + delta
        if j < 0 or j >= len(self.grids):
            return
        self.grids[i], self.grids[j] = self.grids[j], self.grids[i]
        self.selected_index = j
        self._refresh_list()
        self._emit_change()

    def _add_grid(self):
        # Add a new grid with current entry values
        try:
            new_g = BaseGrid(
                numerator=int(self.num_input.text or '4'),
                denominator=int(self.den_spinner.text or '4'),
                gridCountsEnabled=self.grid_input.get_int_list() or [1, 2, 3, 4],
                measureAmount=int(self.meas_input.text or '8'),
            )
        except Exception:
            new_g = BaseGrid()
        self.grids.append(new_g)
        self.selected_index = len(self.grids) - 1
        self._refresh_list()
        self._emit_change()

    def _delete_selected(self):
        i = self.selected_index
        if i < 0 or i >= len(self.grids):
            return
        del self.grids[i]
        # Reselect a sensible index
        if not self.grids:
            self.selected_index = -1
        else:
            self.selected_index = max(0, min(i, len(self.grids) - 1))
        self._refresh_list()
        self._load_selected_into_entries()
        self._emit_change()

    def _emit_change(self):
        cb = getattr(self, 'on_change', None)
        if cb and callable(cb):
            try:
                cb(self.get_grids())
            except Exception:
                pass

__all__ = ['BaseGridEditor']
