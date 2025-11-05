'''
Central, typed callbacks for all UI actions (menu + toolbar), with IntelliSense.

Goals achieved in this refactor:
- Strongly-typed 'app' surface using a Protocol, so callback bodies have
    IntelliSense for app methods (on_new, on_save_as, etc.).
- One single place to steer all buttons and menu items to organized callback_*
    functions at the bottom of this file.
- Menu and toolbar configs expose zero-arg callables via functools.partial,
    binding the 'app' instance once while keeping clean, typed callback bodies.

Configuration value forms remain compatible with MenuBar expectations:
- dict value: dropdown menu (submenu)
- callable: menu item or direct button (zero-arg callable)
- (callable, str): menu item with tooltip/shortcut hint
- None: disabled item
- '---' key: separator (menu-only)
'''

from functools import partial
from typing import Callable, Dict, Tuple, Union, Protocol


# Type aliases for clarity
MenuItemValue = Union[Callable[[], None], Tuple[Callable[[], None], str], None, Dict]
MenuConfig = Dict[str, MenuItemValue]
ButtonConfig = Dict[str, Callable[[], None]]

# Typed configs for sash toolbar buttons
ButtonWithTip = Tuple[Callable[[], None] | None, str]
ButtonConfigWithTips = Dict[str, ButtonWithTip]
ContextualToolbarConfig = Dict[str, ButtonConfigWithTips]


class AppCallbacks(Protocol):
    '''Interface for callbacks the GUI exposes. Used for IntelliSense.

    The main pianoTAB GUI should implement these methods. Keeping this in one
    Protocol gives strong typing without tight coupling.
    '''

    # File menu
    def on_new(self) -> None: ...
    def on_load(self) -> None: ...
    def on_save(self) -> None: ...
    def on_save_as(self) -> None: ...
    def on_export_pdf(self) -> None: ...
    def on_exit(self) -> None: ...

    # Edit menu (currently implemented subset)
    def on_draw_thinnest_line(self) -> None: ...

    # Help menu
    def on_about(self) -> None: ...

    # Toolbar buttons
    def on_selected_note_to_left(self) -> None: ...
    def on_selected_note_to_right(self) -> None: ...


def create_menu_config(app_instance: AppCallbacks) -> MenuConfig:
    '''
    Create menu bar configuration bound to application instance methods.
    
    Args:
        app_instance: The main application/GUI instance that provides callback methods
        
    Returns:
        Dictionary mapping menu names to their items and callbacks
        
    Example structure:
        {
            'File': {
                'New': app.on_new,
                'Open': (app.on_open, 'Ctrl+O'),
                '---': None,  # Separator
                'Exit': app.on_exit
            },
            'Help': app.on_help  # Direct button (no dropdown)
        }
    '''
    return {
        'File': {
            'New': partial(callback_new, app_instance),
            'Load...': (partial(callback_load, app_instance), 'cmd / ctrl + o'),
            'Save': partial(callback_save, app_instance),
            'Save as...': partial(callback_save_as, app_instance),
            'Export to PDF...': partial(callback_export_pdf, app_instance),
            '---': None,  # Separator
            'Exit': partial(callback_exit, app_instance),
        },
        'Edit': {
            'Undo': None,  # TODO: Implement
            'Redo': None,  # TODO: Implement
            '---': None,   # Separator
            'Cut': None,   # TODO: Implement
            'Copy': None,  # TODO: Implement
            'Paste': None, # TODO: Implement
            '---': None,
            'Draw thinnest line (Editor)': partial(callback_draw_thinnest_line, app_instance),
        },
        'Help': {
            'About': partial(callback_about, app_instance),
        },
    }


# (Removed legacy create_button_config and centralized BUTTON_CONFIG.
#  Use create_default_toolbar_config/create_contextual_toolbar_config instead.)


def create_default_toolbar_config(app_instance: AppCallbacks) -> ButtonConfigWithTips:
    '''
    Build the always-visible toolbar (top of sash).
    Keys are icon names; values are (callable|None, tooltip).
    '''
    return {
        'previous': (None, 'Previous item'),
        'next': (None, 'Next item'),
        'MyTest': (partial(callback_my_test, app_instance), 'Run render + PDF test'),
    }


def create_contextual_toolbar_config(app_instance: AppCallbacks) -> ContextualToolbarConfig:
    '''
    Build the contextual toolbar map.
    Top-level key is the normalized ToolSelector value (e.g. 'note').
    Inner dict maps icon name -> (callable|None, tooltip).
    '''
    return {
        'note': {
            'noteLeft': (partial(callback_note_to_left, app_instance), 'Move selected note to left hand'),
            'noteRight': (partial(callback_note_to_right, app_instance), 'Move selected note to right hand'),
        }
    }


# Mutable, app-bound config stores (populated by GUI on startup)
DEFAULT_TOOLBAR_BUTTON_CONFIG: ButtonConfigWithTips = {}
CONTEXTUAL_TOOLBAR_CONFIG: ContextualToolbarConfig = {}


# Placeholder implementations for demonstration
def _not_implemented(action: str) -> Callable[[], None]:
    '''
    Create a placeholder callback for unimplemented actions.
    
    Args:
        action: Name of the action (for logging/debugging)
        
    Returns:
        A callable that prints a not-implemented message
    '''
    def _cb():
        print(f'Action "{action}" not implemented')
    return _cb


# Legacy BUTTON_CONFIG removed. New toolbar system uses:
# - DEFAULT_TOOLBAR_BUTTON_CONFIG (always visible at top of sash)
# - CONTEXTUAL_TOOLBAR_CONFIG (per-tool buttons shown at bottom of sash)


__all__ = [
    'create_menu_config',
    'create_default_toolbar_config',
    'create_contextual_toolbar_config',
    'DEFAULT_TOOLBAR_BUTTON_CONFIG',
    'CONTEXTUAL_TOOLBAR_CONFIG',
    'MenuConfig',
    'ButtonConfig',
    'AppCallbacks',
]


# -------------------------
# Callback implementations
# -------------------------

def _invoke(app: object, method_names: tuple[str, ...], fallback: Callable[[object], None] | None = None) -> None:
    '''Call the first available method on app by name, else run fallback.

    This keeps callbacks resilient even if some methods were removed on the app
    side. It also centralizes wiring here, as requested.
    '''
    for name in method_names:
        fn = getattr(app, name, None)
        if callable(fn):
            fn()
            return
    if fallback:
        fallback(app)
    else:
        # Last-resort informational message
        print(f'Action "{method_names[0]}" not implemented on app')

def callback_new(app: AppCallbacks) -> None:
    _invoke(app, ('on_new',), lambda _a: _not_implemented('New')())


def callback_load(app: AppCallbacks) -> None:
    _invoke(app, ('on_load',), lambda _a: _not_implemented('Load...')())


def callback_save(app: AppCallbacks) -> None:
    _invoke(app, ('on_save',), lambda _a: _not_implemented('Save')())


def callback_save_as(app: AppCallbacks) -> None:
    _invoke(app, ('on_save_as',), lambda _a: _not_implemented('Save as...')())


def callback_export_pdf(app: AppCallbacks) -> None:
    # Prefer app's implementation; otherwise print the local test message
    _invoke(app, ('on_export_pdf',), lambda _a: print('Export pdf triggered'))


def callback_exit(app: AppCallbacks) -> None:
    _invoke(app, ('on_exit',), lambda _a: _not_implemented('Exit')())


def callback_draw_thinnest_line(app: AppCallbacks) -> None:
    _invoke(app, ('on_draw_thinnest_line',), lambda _a: _not_implemented('Draw thinnest line (Editor)')())


def callback_about(app: AppCallbacks) -> None:
    _invoke(app, ('on_about',), lambda _a: _not_implemented('About')())


def callback_note_to_left(app: AppCallbacks) -> None:
    # Support either legacy or new naming on the app side
    _invoke(app, ('on_selected_note_to_left', 'on_note_to_left'), lambda _a: _not_implemented('Note to left')())


def callback_note_to_right(app: AppCallbacks) -> None:
    # Support either legacy or new naming on the app side
    _invoke(app, ('on_selected_note_to_right', 'on_note_to_right'), lambda _a: _not_implemented('Note to right')())


def callback_my_test(app: AppCallbacks) -> None:
    '''Draw a mm-grid and text samples on the print preview, then export a PDF copy.

    - Uses the app.print_preview Canvas if present.
    - Creates a PyMuPDFCanvas of the same size, mirrors the same drawing, and saves to tests/output/text_grid_test.pdf
    '''
    # Attempt to find a print preview canvas on the app
    cv = getattr(app, 'print_preview', None)
    if cv is None:
        print('No print_preview canvas on app; cannot run MyTest')
        return
    try:
        from utils.pymupdfexport import PyMuPDFCanvas
    except Exception as e:
        print(f'PyMuPDF not available: {e}')
        pdf_cv = None
    else:
        pdf_cv = PyMuPDFCanvas(width_mm=getattr(cv, 'width_mm', 210.0), height_mm=getattr(cv, 'height_mm', 297.0), pdf_mode=True)
        pdf_cv.new_page()
        # Fine-tune: nudge baseline up to match on-screen text (points). Set AFTER new_page()
        # so page creation doesn't accidentally reset any instance fields.
        try:
            pdf_cv.pdf_text_baseline_adjust_pt = -2.5
        except Exception:
            pass

    # Clear and draw on the on-screen print preview
    cv.clear()
    _draw_text_grid_and_samples(cv)

    # Mirror to PDF canvas if available
    if pdf_cv is not None:
        _draw_text_grid_and_samples(pdf_cv)
        # Save to tests/output
        import os
        out_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tests', 'output')
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, 'text_grid_test.pdf')
        saved = pdf_cv.save_pdf(out_path)
        if saved:
            print(f'Saved PDF test to: {saved}')
        pdf_cv.close_pdf()


def _draw_text_grid_and_samples(c) -> None:
    '''Draw a 10mm grid and several text samples onto a Canvas-like object 'c'.'''
    # Grid parameters
    w_mm = float(getattr(c, 'width_mm', 210.0))
    h_mm = float(getattr(c, 'height_mm', 297.0))
    step = 10.0
    light = '#CCCCCC'
    dark = '#666666'
    # Vertical lines
    x = 0.0
    while x <= w_mm + 1e-6:
        c.add_line(x, 0.0, x, h_mm, stroke_color=light, stroke_width_mm=0.2)
        x += step
    # Horizontal lines
    y = 0.0
    while y <= h_mm + 1e-6:
        c.add_line(0.0, y, w_mm, y, stroke_color=light, stroke_width_mm=0.2)
        y += step
    # Axes (darker)
    c.add_line(0.0, 0.0, 0.0, h_mm, stroke_color=dark, stroke_width_mm=0.4)
    c.add_line(0.0, 0.0, w_mm, 0.0, stroke_color=dark, stroke_width_mm=0.4)

    # Labels for grid at every 20mm
    for x in range(0, int(w_mm) + 1, 20):
        c.add_text(str(x), x, 2.0, 8.0, 0.0, 'top', '#333333')
        _draw_anchor_dot(c, x, 2.0, '#333333')
    for y in range(0, int(h_mm) + 1, 20):
        c.add_text(str(y), 2.0, y, 8.0, 0.0, 'left', '#333333')
        _draw_anchor_dot(c, 2.0, y, '#333333')

    # Sample texts with different anchors laid out in a 3x3 grid to avoid overlap
    base_x, base_y = w_mm * 0.5, h_mm * 0.22
    dx, dy = 35.0, 16.0  # spacing in mm
    anchors_grid = [
        ('top_left', 'top', 'top_right'),
        ('left', 'center', 'right'),
        ('bottom_left', 'bottom', 'bottom_right'),
    ]
    for row, row_anchors in enumerate(anchors_grid):
        for col, anc in enumerate(row_anchors):
            x = base_x + (col - 1) * dx
            y = base_y + (row - 1) * dy
            label = anc
            c.add_text(label, x, y, 14, 0, anc, '#a41717')
            _draw_anchor_dot(c, x, y, '#a41717')

    # Rotated samples around a different anchor, each on its own line
    rx, ry_start = w_mm * 0.15, h_mm * 0.55
    for idx, ang in enumerate((0, 15, 30, 45, 60, 75, 90, 120, 150)):
        ry = ry_start + idx * 10.0
        c.add_text(f'rot {ang}° tl', rx, ry, 12, ang, 'top_left', '#000000')
        _draw_anchor_dot(c, rx, ry, '#000000')


def _draw_anchor_dot(c, x_mm: float, y_mm: float, color_hex: str):
    '''Draw a small filled dot centered at (x_mm, y_mm).'''
    r = 0.4  # mm
    c.add_oval(x_mm - r, y_mm - r, x_mm + r, y_mm + r, fill=True, fill_color=color_hex, outline=False)
