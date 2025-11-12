"""
Kivy widget configuration to use FiraCode font by default.
"""
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from font import FONT_NAME

# Store original __init__ methods
_Label_init = Label.__init__
_Button_init = Button.__init__
_TextInput_init = TextInput.__init__

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

def apply_default_font():
    """
    Monkey-patch Kivy widgets to use FiraCode font by default.
    Call this after loading the font but before creating any widgets.
    """
    Label.__init__ = _patch_label_init
    Button.__init__ = _patch_button_init
    TextInput.__init__ = _patch_textinput_init
    print(f"✓ Default font set to '{FONT_NAME}' for all widgets")
