"""
Kivy UI for selecting MIDI output ports.
Delegated from GUI to keep midi-related UI logic centralized.
"""

from typing import Optional

try:
    from kivy.uix.popup import Popup
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.button import Button
    from kivy.uix.label import Label
    from kivy.uix.scrollview import ScrollView
except Exception:
    Popup = None
    BoxLayout = None
    Button = None
    Label = None
    ScrollView = None

try:
    from .player import list_output_ports, get_selected_port, set_selected_port
except Exception:
    # Fallback shims if player import fails
    def list_output_ports():
        return []
    def get_selected_port(_settings):
        return None
    def set_selected_port(_settings, _port_name):
        return None


def open_midi_port_dialog(settings_manager: Optional[object]) -> None:
    """Open a dialog to choose a MIDI output port and save to settings.

    Args:
        settings_manager: SettingsManager-like object with get/set/save methods.
    """
    if Popup is None:
        print('Kivy UI not available to open MIDI port dialog')
        return

    layout = BoxLayout(orientation='vertical', spacing=8, padding=8)
    header = BoxLayout(orientation='horizontal', size_hint_y=None, height=32, spacing=8)
    header.add_widget(Label(text='Select MIDI Output Port'))
    refresh_btn = Button(text='Refresh', size_hint_x=None, width=100)
    header.add_widget(refresh_btn)
    layout.add_widget(header)

    sv = ScrollView(size_hint=(1, 1))
    inner = BoxLayout(orientation='vertical', size_hint_y=None, spacing=6)
    inner.bind(minimum_height=inner.setter('height'))
    sv.add_widget(inner)
    layout.add_widget(sv)

    popup = Popup(title='Settings', content=layout, size_hint=(None, None), size=(520, 420))

    def _populate():
        inner.clear_widgets()
        try:
            ports = list_output_ports() or []
        except Exception:
            ports = []
        current = get_selected_port(settings_manager) if settings_manager else None
        if not ports:
            inner.add_widget(Label(text='No MIDI ports found', size_hint_y=None, height=28))
        else:
            for p in ports:
                txt = p if p != current else f"{p} (selected)"
                btn = Button(text=txt, size_hint_y=None, height=32)
                def _on_select(instance, port_name=p):
                    try:
                        if settings_manager:
                            set_selected_port(settings_manager, port_name)
                        print(f'Selected MIDI port: {port_name}')
                    except Exception:
                        pass
                    popup.dismiss()
                btn.bind(on_release=_on_select)
                inner.add_widget(btn)

    refresh_btn.bind(on_release=lambda *_: _populate())
    _populate()

    popup.open()
