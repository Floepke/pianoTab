"""
Kivy widget configuration to use FiraCode font by default.
"""
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView, FileChooserIconView
from kivy.core.text import LabelBase
from kivy.config import Config
from kivy.clock import Clock
from font import FONT_NAME
from font.font_loader import _font_file_path

# Store original __init__ methods
_Label_init = Label.__init__
_Button_init = Button.__init__
_TextInput_init = TextInput.__init__
_Popup_init = Popup.__init__
_FileChooserListView_init = FileChooserListView.__init__
_FileChooserIconView_init = FileChooserIconView.__init__

def _patch_label_init(self, **kwargs):
    """Patched Label.__init__ to use FiraCode font by default"""
    if 'font_name' not in kwargs:
        kwargs['font_name'] = FONT_NAME
    _Label_init(self, **kwargs)

def _patch_button_init(self, **kwargs):
    """Patched Button.__init__ to use FiraCode font by default"""
    if 'font_name' not in kwargs:
        kwargs['font_name'] = FONT_NAME
    _Button_init(self, **kwargs)

def _patch_textinput_init(self, **kwargs):
    """Patched TextInput.__init__ to use FiraCode font by default"""
    if 'font_name' not in kwargs:
        kwargs['font_name'] = FONT_NAME
    _TextInput_init(self, **kwargs)

def _patch_popup_init(self, **kwargs):
    """Patched Popup.__init__ to use FiraCode font in title"""
    if 'title_font' not in kwargs:
        kwargs['title_font'] = FONT_NAME
    _Popup_init(self, **kwargs)

def _apply_font_to_children(widget):
    """Recursively apply font to all Label children."""
    if isinstance(widget, Label):
        widget.font_name = FONT_NAME
    # Check if widget has children attribute
    if hasattr(widget, 'children'):
        for child in widget.children:
            _apply_font_to_children(child)

def _setup_recursive_font_binding(widget):
    """Bind to all descendant widgets' children property to catch dynamic label creation."""
    def on_any_children_change(instance, value):
        _apply_font_to_children(instance)
    
    # Bind this widget
    if hasattr(widget, 'children'):
        widget.bind(children=on_any_children_change)
        # Recursively bind all existing children
        for child in widget.children:
            _setup_recursive_font_binding(child)

def _patch_filechooserlistview_init(self, **kwargs):
    """Patched FileChooserListView.__init__ to use FiraCode font"""
    _FileChooserListView_init(self, **kwargs)
    
    # Patch the _update_files method to apply font after updating
    original_update_files = self._update_files
    def patched_update_files(*args, **kwargs):
        result = original_update_files(*args, **kwargs)
        _apply_font_to_children(self)
        _setup_recursive_font_binding(self)
        return result
    self._update_files = patched_update_files
    
    # Schedule font application for initial view (after FileChooser builds initial labels)
    def initial_setup(dt):
        _apply_font_to_children(self)
        _setup_recursive_font_binding(self)
    Clock.schedule_once(initial_setup, 0)
    Clock.schedule_once(initial_setup, 0.1)  # Second attempt for delayed rendering

def _patch_filechoosericonview_init(self, **kwargs):
    """Patched FileChooserIconView.__init__ to use FiraCode font"""
    _FileChooserIconView_init(self, **kwargs)
    
    # Patch the _update_files method to apply font after updating
    original_update_files = self._update_files
    def patched_update_files(*args, **kwargs):
        result = original_update_files(*args, **kwargs)
        _apply_font_to_children(self)
        _setup_recursive_font_binding(self)
        return result
    self._update_files = patched_update_files
    
    # Schedule font application for initial view (after FileChooser builds initial labels)
    def initial_setup(dt):
        _apply_font_to_children(self)
        _setup_recursive_font_binding(self)
    Clock.schedule_once(initial_setup, 0)
    Clock.schedule_once(initial_setup, 0.1)  # Second attempt for delayed rendering

def apply_default_font():
    """
    Monkey-patch Kivy widgets to use FiraCode font by default.
    Also sets the global default font for Kivy system widgets like Popup.
    Call this after loading the font but before creating any widgets.
    """
    # Set Kivy's config default font
    Config.set('kivy', 'default_font', [FONT_NAME, _font_file_path, _font_file_path, _font_file_path, _font_file_path])
    
    # Override Kivy's 'default' font to use FiraCode
    # This affects widgets that explicitly use 'default' font
    if _font_file_path:
        LabelBase.register(
            name='default',
            fn_regular=_font_file_path,
            fn_bold=_font_file_path,
            fn_italic=_font_file_path,
            fn_bolditalic=_font_file_path
        )
        
        # Also register 'Roboto' (Kivy's default) to use FiraCode instead
        LabelBase.register(
            name='Roboto',
            fn_regular=_font_file_path,
            fn_bold=_font_file_path,
            fn_italic=_font_file_path,
            fn_bolditalic=_font_file_path
        )
    
    # Patch individual widget classes
    Label.__init__ = _patch_label_init
    Button.__init__ = _patch_button_init
    TextInput.__init__ = _patch_textinput_init
    Popup.__init__ = _patch_popup_init
    FileChooserListView.__init__ = _patch_filechooserlistview_init
    FileChooserIconView.__init__ = _patch_filechoosericonview_init
    print(f"✓ Default font set to '{FONT_NAME}' for all widgets including FileChooser")
