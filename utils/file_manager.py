'''
Application-level file management for SCORE files using Kivy's FileChooserListView.
'''

from __future__ import annotations
from typing import Optional, Callable
import os

from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.textinput import TextInput
from kivy.metrics import dp
from kivy.logger import Logger
from kivy.properties import ObjectProperty
import shutil

from gui.colors import DARK, DARK_LIGHTER, LIGHT
from kivy.core.window import Window
from file.SCORE import SCORE
from font import FONT_NAME  # Import font name for Popup titles


DEFAULT_EXT = '.piano'
FILE_FILTERS = ['*.piano']

# Max size for Load/Save popups (tweak here to fine-tune on large screens like 4K)
LOAD_SAVE_MAX_WIDTH = 1400
LOAD_SAVE_MAX_HEIGHT = 900


class IconFileChooserListView(FileChooserListView):
    '''FileChooserListView with icons for folders and .piano files.'''
    
    def _create_entry_widget(self, entry):
        """Override to add icons to file/folder names."""
        # Call parent to create the default entry
        widget = super()._create_entry_widget(entry)
        
        # Find the label showing the filename
        for child in widget.walk():
            if isinstance(child, Label):
                # Add icon prefix based on entry type
                # entry is a dict with keys: name, size, path, isdir, etc.
                if entry.get('name', '').endswith('.piano'):
                    child.text = '♪ ' + child.text
                break
        
        return widget


class LoadDialog(BoxLayout):
    '''Load file dialog with file management features.'''
    
    def __init__(self, start_path: str, load_callback: Callable, cancel_callback: Callable, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 8
        self.padding = 8
        
        self._load_callback = load_callback
        self._cancel_callback = cancel_callback
        self._clipboard = None  # Stores (operation, filepath) where operation is 'copy' or 'cut'
        
        # Current path label
        self.path_label = Label(
            text=f'Path: {start_path}',
            size_hint_y=None,
            height=dp(30),
            color=LIGHT,
            halign='left',
            valign='middle',
            text_size=(None, None)
        )
        self.path_label.bind(size=lambda *args: setattr(self.path_label, 'text_size', (self.path_label.width - 20, None)))
        self.add_widget(self.path_label)
        
        # File chooser
        self.file_chooser = IconFileChooserListView(
            path=start_path,
            filters=FILE_FILTERS,
            size_hint=(1, 1),
            dirselect=True  # Allow folder selection
        )
        self.file_chooser.bind(on_submit=self._on_submit, path=self._update_path_label)
        self.add_widget(self.file_chooser)
        
        # File management button row
        mgmt_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(36),
            spacing=4
        )
        
        for text, callback in [
            ('New Folder', self._new_folder),
            ('Rename', self._rename),
            ('Delete', self._delete),
            ('Cut', self._cut),
            ('Copy', self._copy),
            ('Paste', self._paste)
        ]:
            btn = Button(
                text=text,
                size_hint_x=1,
                background_normal='',
                background_color=DARK_LIGHTER,
                color=LIGHT
            )
            btn.bind(on_release=callback)
            mgmt_row.add_widget(btn)
        
        self.add_widget(mgmt_row)
        
        # Main button row
        btn_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(42),
            spacing=8
        )
        
        cancel_btn = Button(
            text='Cancel',
            size_hint_x=0.5,
            background_normal='',
            background_color=DARK,
            color=LIGHT
        )
        cancel_btn.bind(on_release=self._on_cancel)
        btn_row.add_widget(cancel_btn)
        
        load_btn = Button(
            text='Load',
            size_hint_x=0.5,
            background_normal='',
            background_color=DARK,
            color=LIGHT
        )
        load_btn.bind(on_release=self._on_load)
        btn_row.add_widget(load_btn)
        
        self.add_widget(btn_row)
        
        # Set up keyboard handling when added to window
        self._keyboard_bound = False
        self.bind(on_parent=self._on_parent_change)
    
    def _on_parent_change(self, instance, value):
        '''Handle keyboard binding when added/removed from window.'''
        if value and not self._keyboard_bound:
            Window.bind(on_keyboard=self._on_keyboard)
            self._keyboard_bound = True
        elif not value and self._keyboard_bound:
            Window.unbind(on_keyboard=self._on_keyboard)
            self._keyboard_bound = False
    
    def _on_keyboard(self, instance, key, scancode, codepoint, modifier):
        '''Handle keyboard shortcuts for main dialog.'''
        if key == 27:  # Escape
            self._on_cancel(None)
            return True
        elif key == 13:  # Return/Enter
            self._on_load(None)
            return True
        return False

    def _update_path_label(self, instance, value):
        '''Update path label when directory changes.'''
        self.path_label.text = f'Path: {value}'

    def _new_folder(self, instance):
        '''Create a new folder in current directory.'''
        self._prompt_input('New Folder', 'Folder name:', 'New Folder', self._do_new_folder)
    
    def _do_new_folder(self, name):
        '''Actually create the folder.'''
        if not name:
            return
        try:
            new_path = os.path.join(self.file_chooser.path, name)
            os.makedirs(new_path, exist_ok=False)
            self.file_chooser._update_files()  # Refresh the view
        except Exception as e:
            self._show_error(f'Failed to create folder: {e}')
    
    def _rename(self, instance):
        '''Rename selected file or folder.'''
        if not self.file_chooser.selection:
            self._show_error('Please select a file or folder to rename')
            return
        old_path = self.file_chooser.selection[0]
        old_name = os.path.basename(old_path)
        self._prompt_input('Rename', 'New name:', old_name, lambda new_name: self._do_rename(old_path, new_name))
    
    def _do_rename(self, old_path, new_name):
        '''Actually rename the file/folder.'''
        if not new_name or new_name == os.path.basename(old_path):
            return
        try:
            # For files, ensure .piano extension
            if os.path.isfile(old_path) and not new_name.endswith('.piano'):
                new_name = new_name + '.piano'
            
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            os.rename(old_path, new_path)
            self.file_chooser._update_files()
        except Exception as e:
            self._show_error(f'Failed to rename: {e}')
    
    def _delete(self, instance):
        '''Delete selected file (folders are not deletable for safety).'''
        if not self.file_chooser.selection:
            self._show_error('Please select a file to delete')
            return
        path = self.file_chooser.selection[0]
        
        # Don't allow folder deletion for safety
        if os.path.isdir(path):
            self._show_error('Cannot delete folders for safety reasons')
            return
            
        name = os.path.basename(path)
        self._confirm(f'Delete "{name}"?', lambda: self._do_delete(path))
    
    def _do_delete(self, path):
        '''Actually delete the file.'''
        try:
            os.remove(path)
            self.file_chooser._update_files()
        except Exception as e:
            self._show_error(f'Failed to delete: {e}')
    
    def _cut(self, instance):
        '''Cut selected file or folder.'''
        if not self.file_chooser.selection:
            self._show_error('Please select a file or folder to cut')
            return
        path = self.file_chooser.selection[0]
        self._clipboard = ('cut', path)
    
    def _copy(self, instance):
        '''Copy selected file or folder.'''
        if not self.file_chooser.selection:
            self._show_error('Please select a file or folder to copy')
            return
        path = self.file_chooser.selection[0]
        self._clipboard = ('copy', path)
    
    def _paste(self, instance):
        '''Paste file or folder from clipboard.'''
        if not self._clipboard:
            return
        operation, src_path = self._clipboard
        try:
            dest_dir = self.file_chooser.path
            base_name = os.path.basename(src_path)
            dest_path = os.path.join(dest_dir, base_name)
            
            # Handle name conflicts - add (copy N) suffix
            if os.path.exists(dest_path):
                if os.path.isdir(src_path):
                    # For folders, don't add extension
                    counter = 1
                    while os.path.exists(dest_path):
                        dest_path = os.path.join(dest_dir, f'{base_name} (copy {counter})')
                        counter += 1
                else:
                    # For files, preserve extension
                    name, ext = os.path.splitext(base_name)
                    counter = 1
                    while os.path.exists(dest_path):
                        dest_path = os.path.join(dest_dir, f'{name} (copy {counter}){ext}')
                        counter += 1
            
            if operation == 'copy':
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, dest_path)
                else:
                    shutil.copy2(src_path, dest_path)
            elif operation == 'cut':
                shutil.move(src_path, dest_path)
                self._clipboard = None  # Clear clipboard after cut
            
            self.file_chooser._update_files()
        except Exception as e:
            self._show_error(f'Failed to paste: {e}')

    def _on_submit(self, chooser, selection, touch=None):
        """Handle double-click/enter on a file to confirm load immediately."""
        try:
            if not selection:
                return
            filepath = selection[0]
            if os.path.isdir(filepath):
                return
            self._on_load(None)
        except Exception:
            pass
    
    def _on_cancel(self, instance):
        if self._cancel_callback:
            self._cancel_callback()
    
    def _on_load(self, instance):
        if self._load_callback and self.file_chooser.selection:
            filepath = self.file_chooser.selection[0]
            if not os.path.isabs(filepath):
                filepath = os.path.join(self.file_chooser.path, filepath)
            self._load_callback(filepath)
    
    def _reclaim_keyboard(self):
        '''Reclaim keyboard focus for the editor canvas after dialogs close.'''
        from utils.canvas import Canvas
        if Canvas._global_keyboard_canvas:
            Canvas._global_keyboard_canvas._reclaim_keyboard()
    
    def _prompt_input(self, title, label_text, default_text, callback):
        '''Show input dialog.'''
        # Title bar
        title_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), padding=[dp(10), dp(5)])
        title_label = Label(text=title, color=LIGHT, font_name=FONT_NAME, halign='left', valign='middle')
        title_label.bind(size=lambda *args: setattr(title_label, 'text_size', (title_label.width, None)))
        title_bar.add_widget(title_label)
        
        # Content
        content = BoxLayout(orientation='vertical', spacing=dp(8), padding=[dp(8), dp(20), dp(8), dp(8)])
        
        content.add_widget(Label(text=label_text, size_hint_y=None, height=dp(30), color=LIGHT))
        
        text_input = TextInput(
            text=default_text,
            size_hint_y=None,
            height=dp(30),
            multiline=False,
            background_color=DARK_LIGHTER,
            foreground_color=LIGHT,
            padding=[dp(6), dp(6), dp(6), dp(6)]
        )
        content.add_widget(text_input)
        
        btn_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(8))
        cancel_btn = Button(text='Cancel', background_normal='', background_color=DARK, color=LIGHT)
        ok_btn = Button(text='OK', background_normal='', background_color=DARK, color=LIGHT)
        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(ok_btn)
        content.add_widget(btn_row)
        
        # Main container with title
        main_box = BoxLayout(orientation='vertical', spacing=0)
        main_box.add_widget(title_bar)
        main_box.add_widget(content)
        
        popup = ModalView(size_hint=(None, None), size=(dp(400), dp(200)), auto_dismiss=False)
        popup.add_widget(main_box)
        cancel_btn.bind(on_release=popup.dismiss)
        ok_btn.bind(on_release=lambda *args: (callback(text_input.text), popup.dismiss()))
        
        # Keyboard handling
        def on_keyboard(instance, key, scancode, codepoint, modifier):
            if key == 27:  # Escape
                popup.dismiss()
                return True
            elif key == 13:  # Return/Enter
                callback(text_input.text)
                popup.dismiss()
                return True
            return False
        
        popup.bind(on_open=lambda *args: Window.bind(on_keyboard=on_keyboard))
        popup.bind(on_dismiss=lambda *args: (Window.unbind(on_keyboard=on_keyboard), self._reclaim_keyboard()))
        popup.open()
    
    def _confirm(self, message, callback):
        '''Show confirmation dialog.'''
        # Title bar
        title_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), padding=[dp(10), dp(5)])
        title_label = Label(text='Confirm', color=LIGHT, font_name=FONT_NAME, halign='left', valign='middle')
        title_label.bind(size=lambda *args: setattr(title_label, 'text_size', (title_label.width, None)))
        title_bar.add_widget(title_label)
        
        # Content
        content = BoxLayout(orientation='vertical', spacing=dp(8), padding=[dp(8), dp(20), dp(8), dp(8)])
        
        content.add_widget(Label(text=message, size_hint_y=None, height=dp(50), color=LIGHT))
        
        btn_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(8))
        no_btn = Button(text='No', background_normal='', background_color=DARK, color=LIGHT)
        yes_btn = Button(text='Yes', background_normal='', background_color=DARK, color=LIGHT)
        btn_row.add_widget(no_btn)
        btn_row.add_widget(yes_btn)
        content.add_widget(btn_row)
        
        # Main container with title
        main_box = BoxLayout(orientation='vertical', spacing=0)
        main_box.add_widget(title_bar)
        main_box.add_widget(content)
        
        popup = ModalView(size_hint=(None, None), size=(dp(350), dp(170)), auto_dismiss=False)
        popup.add_widget(main_box)
        no_btn.bind(on_release=popup.dismiss)
        yes_btn.bind(on_release=lambda *args: (callback(), popup.dismiss()))
        
        # Keyboard handling
        def on_keyboard(instance, key, scancode, codepoint, modifier):
            if key == 27:  # Escape = No/Cancel
                popup.dismiss()
                return True
            elif key == 13:  # Return/Enter = Yes/Confirm
                callback()
                popup.dismiss()
                return True
            return False
        
        popup.bind(on_open=lambda *args: Window.bind(on_keyboard=on_keyboard))
        popup.bind(on_dismiss=lambda *args: (Window.unbind(on_keyboard=on_keyboard), self._reclaim_keyboard()))
        popup.open()
    
    def _show_error(self, message):
        '''Show error message.'''
        # Title bar
        title_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), padding=[dp(10), dp(5)])
        title_label = Label(text='Error', color=LIGHT, font_name=FONT_NAME, halign='left', valign='middle')
        title_label.bind(size=lambda *args: setattr(title_label, 'text_size', (title_label.width, None)))
        title_bar.add_widget(title_label)
        
        # Content
        content = BoxLayout(orientation='vertical', spacing=dp(8), padding=[dp(8), dp(20), dp(8), dp(8)])
        
        content.add_widget(Label(text=message, size_hint_y=None, height=dp(50), color=LIGHT))
        
        ok_btn = Button(text='OK', size_hint_y=None, height=dp(40), background_normal='', background_color=DARK, color=LIGHT)
        content.add_widget(ok_btn)
        
        # Main container with title
        main_box = BoxLayout(orientation='vertical', spacing=0)
        main_box.add_widget(title_bar)
        main_box.add_widget(content)
        
        popup = ModalView(size_hint=(None, None), size=(dp(350), dp(170)), auto_dismiss=False)
        popup.add_widget(main_box)
        ok_btn.bind(on_release=popup.dismiss)
        
        # Keyboard handling
        def on_keyboard(instance, key, scancode, codepoint, modifier):
            if key in (27, 13):  # Escape or Return/Enter
                popup.dismiss()
                return True
            return False
        
        popup.bind(on_open=lambda *args: Window.bind(on_keyboard=on_keyboard))
        popup.bind(on_dismiss=lambda *args: (Window.unbind(on_keyboard=on_keyboard), self._reclaim_keyboard()))
        popup.open()


class SaveDialog(BoxLayout):
    '''Save file dialog with file management features.'''
    
    def __init__(self, start_path: str, suggested_name: str, save_callback: Callable, cancel_callback: Callable, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 8
        self.padding = 8
        
        self._save_callback = save_callback
        self._cancel_callback = cancel_callback
        self._clipboard = None  # Stores (operation, filepath) where operation is 'copy' or 'cut'
        
        # Current path label
        self.path_label = Label(
            text=f'Path: {start_path}',
            size_hint_y=None,
            height=dp(30),
            color=LIGHT,
            halign='left',
            valign='middle',
            text_size=(None, None)
        )
        self.path_label.bind(size=lambda *args: setattr(self.path_label, 'text_size', (self.path_label.width - 20, None)))
        self.add_widget(self.path_label)
        
        # File chooser
        self.file_chooser = IconFileChooserListView(
            path=start_path,
            filters=FILE_FILTERS,
            dirselect=True,  # Allow folder selection
            size_hint=(1, 1)
        )
        self.file_chooser.bind(selection=self._on_selection, on_submit=self._on_submit, path=self._update_path_label)
        self.add_widget(self.file_chooser)
        
        # Filename input
        self.text_input = TextInput(
            text=suggested_name,
            size_hint_y=None,
            height=dp(30),
            multiline=False,
            background_color=DARK_LIGHTER,
            foreground_color=LIGHT,
            padding=[dp(6), dp(6), dp(6), dp(6)]
        )
        self.add_widget(self.text_input)
        
        # File management button row
        mgmt_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(36),
            spacing=4
        )
        
        for text, callback in [
            ('New Folder', self._new_folder),
            ('Rename', self._rename),
            ('Delete', self._delete),
            ('Cut', self._cut),
            ('Copy', self._copy),
            ('Paste', self._paste)
        ]:
            btn = Button(
                text=text,
                size_hint_x=1,
                background_normal='',
                background_color=DARK_LIGHTER,
                color=LIGHT
            )
            btn.bind(on_release=callback)
            mgmt_row.add_widget(btn)
        
        self.add_widget(mgmt_row)
        
        # Main button row
        btn_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(42),
            spacing=8
        )
        
        cancel_btn = Button(
            text='Cancel',
            size_hint_x=0.5,
            background_normal='',
            background_color=DARK,
            color=LIGHT
        )
        cancel_btn.bind(on_release=self._on_cancel)
        btn_row.add_widget(cancel_btn)
        
        save_btn = Button(
            text='Save',
            size_hint_x=0.5,
            background_normal='',
            background_color=DARK,
            color=LIGHT
        )
        save_btn.bind(on_release=self._on_save)
        btn_row.add_widget(save_btn)
        
        self.add_widget(btn_row)
        
        # Set up keyboard handling when added to window
        self._keyboard_bound = False
        self.bind(on_parent=self._on_parent_change)
    
    def _on_parent_change(self, instance, value):
        '''Handle keyboard binding when added/removed from window.'''
        if value and not self._keyboard_bound:
            Window.bind(on_keyboard=self._on_keyboard)
            self._keyboard_bound = True
        elif not value and self._keyboard_bound:
            Window.unbind(on_keyboard=self._on_keyboard)
            self._keyboard_bound = False
    
    def _on_keyboard(self, instance, key, scancode, codepoint, modifier):
        '''Handle keyboard shortcuts for main dialog.'''
        if key == 27:  # Escape
            self._on_cancel(None)
            return True
        elif key == 13:  # Return/Enter
            self._on_save(None)
            return True
        return False

    def _update_path_label(self, instance, value):
        '''Update path label when directory changes.'''
        self.path_label.text = f'Path: {value}'

    def _new_folder(self, instance):
        '''Create a new folder in current directory.'''
        self._prompt_input('New Folder', 'Folder name:', 'New Folder', self._do_new_folder)
    
    def _do_new_folder(self, name):
        '''Actually create the folder.'''
        if not name:
            return
        try:
            new_path = os.path.join(self.file_chooser.path, name)
            os.makedirs(new_path, exist_ok=False)
            self.file_chooser._update_files()
        except Exception as e:
            self._show_error(f'Failed to create folder: {e}')
    
    def _rename(self, instance):
        '''Rename selected file or folder.'''
        if not self.file_chooser.selection:
            self._show_error('Please select a file or folder to rename')
            return
        old_path = self.file_chooser.selection[0]
        old_name = os.path.basename(old_path)
        self._prompt_input('Rename', 'New name:', old_name, lambda new_name: self._do_rename(old_path, new_name))
    
    def _do_rename(self, old_path, new_name):
        '''Actually rename the file/folder.'''
        if not new_name or new_name == os.path.basename(old_path):
            return
        try:
            # For files, ensure .piano extension
            if os.path.isfile(old_path) and not new_name.endswith('.piano'):
                new_name = new_name + '.piano'
            
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            os.rename(old_path, new_path)
            self.file_chooser._update_files()
        except Exception as e:
            self._show_error(f'Failed to rename: {e}')
    
    def _delete(self, instance):
        '''Delete selected file (folders are not deletable for safety).'''
        if not self.file_chooser.selection:
            self._show_error('Please select a file to delete')
            return
        path = self.file_chooser.selection[0]
        
        # Don't allow folder deletion for safety
        if os.path.isdir(path):
            self._show_error('Cannot delete folders for safety reasons')
            return
            
        name = os.path.basename(path)
        self._confirm(f'Delete "{name}"?', lambda: self._do_delete(path))
    
    def _do_delete(self, path):
        '''Actually delete the file.'''
        try:
            os.remove(path)
            self.file_chooser._update_files()
        except Exception as e:
            self._show_error(f'Failed to delete: {e}')
    
    def _cut(self, instance):
        '''Cut selected file or folder.'''
        if not self.file_chooser.selection:
            self._show_error('Please select a file or folder to cut')
            return
        path = self.file_chooser.selection[0]
        self._clipboard = ('cut', path)
    
    def _copy(self, instance):
        '''Copy selected file or folder.'''
        if not self.file_chooser.selection:
            self._show_error('Please select a file or folder to copy')
            return
        path = self.file_chooser.selection[0]
        self._clipboard = ('copy', path)
    
    def _paste(self, instance):
        '''Paste file or folder from clipboard.'''
        if not self._clipboard:
            return
        operation, src_path = self._clipboard
        try:
            dest_dir = self.file_chooser.path
            base_name = os.path.basename(src_path)
            dest_path = os.path.join(dest_dir, base_name)
            
            # Handle name conflicts - add (copy N) suffix
            if os.path.exists(dest_path):
                if os.path.isdir(src_path):
                    # For folders, don't add extension
                    counter = 1
                    while os.path.exists(dest_path):
                        dest_path = os.path.join(dest_dir, f'{base_name} (copy {counter})')
                        counter += 1
                else:
                    # For files, preserve extension
                    name, ext = os.path.splitext(base_name)
                    counter = 1
                    while os.path.exists(dest_path):
                        dest_path = os.path.join(dest_dir, f'{name} (copy {counter}){ext}')
                        counter += 1
            
            if operation == 'copy':
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, dest_path)
                else:
                    shutil.copy2(src_path, dest_path)
            elif operation == 'cut':
                shutil.move(src_path, dest_path)
                self._clipboard = None
            
            self.file_chooser._update_files()
        except Exception as e:
            self._show_error(f'Failed to paste: {e}')

    def _on_submit(self, chooser, selection, touch=None):
        """Handle double-click/enter on a file to confirm save immediately."""
        try:
            if not selection:
                return
            filepath = selection[0]
            if os.path.isdir(filepath):
                return
            self.text_input.text = os.path.basename(filepath)
            self._on_save(None)
        except Exception:
            pass
    
    def _on_selection(self, instance, selection):
        '''Update text input when file is selected.'''
        if selection:
            self.text_input.text = os.path.basename(selection[0])
    
    def _on_cancel(self, instance):
        if self._cancel_callback:
            self._cancel_callback()
    
    def _on_save(self, instance):
        if self._save_callback and self.text_input.text:
            filepath = os.path.join(self.file_chooser.path, self.text_input.text)
            self._save_callback(filepath)
    
    def _reclaim_keyboard(self):
        '''Reclaim keyboard focus for the editor canvas after dialogs close.'''
        from utils.canvas import Canvas
        if Canvas._global_keyboard_canvas:
            Canvas._global_keyboard_canvas._reclaim_keyboard()
    
    def _prompt_input(self, title, label_text, default_text, callback):
        '''Show input dialog.'''
        # Title bar
        title_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), padding=[dp(10), dp(5)])
        title_label = Label(text=title, color=LIGHT, font_name=FONT_NAME, halign='left', valign='middle')
        title_label.bind(size=lambda *args: setattr(title_label, 'text_size', (title_label.width, None)))
        title_bar.add_widget(title_label)
        
        # Content
        content = BoxLayout(orientation='vertical', spacing=dp(8), padding=[dp(8), dp(20), dp(8), dp(8)])
        
        content.add_widget(Label(text=label_text, size_hint_y=None, height=dp(30), color=LIGHT))
        
        text_input = TextInput(
            text=default_text,
            size_hint_y=None,
            height=dp(30),
            multiline=False,
            background_color=DARK_LIGHTER,
            foreground_color=LIGHT,
            padding=[dp(6), dp(6), dp(6), dp(6)]
        )
        content.add_widget(text_input)
        
        btn_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(8))
        cancel_btn = Button(text='Cancel', background_normal='', background_color=DARK, color=LIGHT)
        ok_btn = Button(text='OK', background_normal='', background_color=DARK, color=LIGHT)
        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(ok_btn)
        content.add_widget(btn_row)
        
        # Main container with title
        main_box = BoxLayout(orientation='vertical', spacing=0)
        main_box.add_widget(title_bar)
        main_box.add_widget(content)
        
        popup = ModalView(size_hint=(None, None), size=(dp(400), dp(200)), auto_dismiss=False)
        popup.add_widget(main_box)
        cancel_btn.bind(on_release=popup.dismiss)
        ok_btn.bind(on_release=lambda *args: (callback(text_input.text), popup.dismiss()))
        
        # Keyboard handling
        def on_keyboard(instance, key, scancode, codepoint, modifier):
            if key == 27:  # Escape
                popup.dismiss()
                return True
            elif key == 13:  # Return/Enter
                callback(text_input.text)
                popup.dismiss()
                return True
            return False
        
        popup.bind(on_open=lambda *args: Window.bind(on_keyboard=on_keyboard))
        popup.bind(on_dismiss=lambda *args: Window.unbind(on_keyboard=on_keyboard))
        popup.open()
    
    def _confirm(self, message, callback):
        '''Show confirmation dialog.'''
        # Title bar
        title_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), padding=[dp(10), dp(5)])
        title_label = Label(text='Confirm', color=LIGHT, font_name=FONT_NAME, halign='left', valign='middle')
        title_label.bind(size=lambda *args: setattr(title_label, 'text_size', (title_label.width, None)))
        title_bar.add_widget(title_label)
        
        # Content
        content = BoxLayout(orientation='vertical', spacing=dp(8), padding=[dp(8), dp(20), dp(8), dp(8)])
        
        content.add_widget(Label(text=message, size_hint_y=None, height=dp(50), color=LIGHT))
        
        btn_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(8))
        no_btn = Button(text='No', background_normal='', background_color=DARK, color=LIGHT)
        yes_btn = Button(text='Yes', background_normal='', background_color=DARK, color=LIGHT)
        btn_row.add_widget(no_btn)
        btn_row.add_widget(yes_btn)
        content.add_widget(btn_row)
        
        # Main container with title
        main_box = BoxLayout(orientation='vertical', spacing=0)
        main_box.add_widget(title_bar)
        main_box.add_widget(content)
        
        popup = ModalView(size_hint=(None, None), size=(dp(350), dp(170)), auto_dismiss=False)
        popup.add_widget(main_box)
        no_btn.bind(on_release=popup.dismiss)
        yes_btn.bind(on_release=lambda *args: (callback(), popup.dismiss()))
        
        # Keyboard handling
        def on_keyboard(instance, key, scancode, codepoint, modifier):
            if key == 27:  # Escape = No/Cancel
                popup.dismiss()
                return True
            elif key == 13:  # Return/Enter = Yes/Confirm
                callback()
                popup.dismiss()
                return True
            return False
        
        popup.bind(on_open=lambda *args: Window.bind(on_keyboard=on_keyboard))
        popup.bind(on_dismiss=lambda *args: (Window.unbind(on_keyboard=on_keyboard), self._reclaim_keyboard()))
        popup.open()
    
    def _show_error(self, message):
        '''Show error message.'''
        # Title bar
        title_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), padding=[dp(10), dp(5)])
        title_label = Label(text='Error', color=LIGHT, font_name=FONT_NAME, halign='left', valign='middle')
        title_label.bind(size=lambda *args: setattr(title_label, 'text_size', (title_label.width, None)))
        title_bar.add_widget(title_label)
        
        # Content
        content = BoxLayout(orientation='vertical', spacing=dp(8), padding=[dp(8), dp(20), dp(8), dp(8)])
        
        content.add_widget(Label(text=message, size_hint_y=None, height=dp(50), color=LIGHT))
        
        ok_btn = Button(text='OK', size_hint_y=None, height=dp(40), background_normal='', background_color=DARK, color=LIGHT)
        content.add_widget(ok_btn)
        
        # Main container with title
        main_box = BoxLayout(orientation='vertical', spacing=0)
        main_box.add_widget(title_bar)
        main_box.add_widget(content)
        
        popup = ModalView(size_hint=(None, None), size=(dp(350), dp(170)), auto_dismiss=False)
        popup.add_widget(main_box)
        ok_btn.bind(on_release=popup.dismiss)
        
        # Keyboard handling
        def on_keyboard(instance, key, scancode, codepoint, modifier):
            if key in (27, 13):  # Escape or Return/Enter
                popup.dismiss()
                return True
            return False
        
        popup.bind(on_open=lambda *args: Window.bind(on_keyboard=on_keyboard))
        popup.bind(on_dismiss=lambda *args: (Window.unbind(on_keyboard=on_keyboard), self._reclaim_keyboard()))
        popup.open()


class FileManager:
    '''Application-level file management for SCORE files.'''

    def __init__(self, *, app, gui, editor):
        self.app = app
        self.gui = gui
        self.editor = editor
        self.current_path: Optional[str] = None
        self.dirty: bool = False
        # Load last dialog path from settings, fallback to home directory
        try:
            settings = getattr(self.app, 'settings', None)
            saved_path = settings.get('last_file_dialog_path', '') if settings else ''
            self._last_dir = saved_path if saved_path and os.path.isdir(saved_path) else os.path.expanduser('~')
        except Exception:
            self._last_dir = os.path.expanduser('~')
        self._popup: Optional[ModalView] = None
    
    def _reclaim_keyboard(self):
        '''Reclaim keyboard focus for the editor canvas after dialogs close.'''
        from utils.canvas import Canvas
        if Canvas._global_keyboard_canvas:
            Canvas._global_keyboard_canvas._reclaim_keyboard()
    
    def _update_window_title(self):
        '''Update the window title to show current filepath.'''
        if self.current_path:
            title = f'pianoTAB - music notation editor - {self.current_path}'
        else:
            title = 'pianoTAB - music notation editor - Untitled'
        
        # Add asterisk if file has unsaved changes
        if self.dirty:
            title += ' *'
        
        Window.set_title(title)

    def new_file(self):
        '''Create a new empty score.'''
        def _do_new():
            # Create new score and load it (which sets it in GUI and redraws)
            self.editor.new_score()
            self.current_path = None
            self.dirty = False
            self._update_window_title()
        self._guard_unsaved_then(_do_new)

    def open_file(self):
        '''Open an existing score file.'''
        def _do_open(filepath: str):
            try:
                score = SCORE.load(filepath)
                # Load score (which sets it in GUI and redraws)
                self.editor.load_score(score)
                self.current_path = filepath
                self._last_dir = os.path.dirname(filepath)
                self.dirty = False
                self._update_window_title()
                self._dismiss_popup()
                # Update settings: last opened + recent files + dialog path
                try:
                    settings = getattr(self.app, 'settings', None)
                    if settings is not None:
                        settings.add_recent_file(filepath)
                        settings.set('last_file_dialog_path', self._last_dir)
                except Exception:
                    pass
            except Exception as e:
                import traceback
                traceback.print_exc()  # Print full traceback to console for debugging
                self._dismiss_popup()
                self._error(f'Failed to load file:\n{e}')
        
        def _show_load_dialog():
            content = LoadDialog(
                start_path=self._last_dir,
                load_callback=_do_open,
                cancel_callback=self._dismiss_popup
            )
            # Size capped for very large screens while remaining responsive
            target_w = min(int(Window.width * 0.9), LOAD_SAVE_MAX_WIDTH)
            target_h = min(int(Window.height * 0.9), LOAD_SAVE_MAX_HEIGHT)
            
            # Title bar
            title_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), padding=[dp(10), dp(5)])
            title_label = Label(text='Load File', color=LIGHT, font_name=FONT_NAME, halign='left', valign='middle')
            title_label.bind(size=lambda *args: setattr(title_label, 'text_size', (title_label.width, None)))
            title_bar.add_widget(title_label)
            
            # Main container with title
            main_box = BoxLayout(orientation='vertical', spacing=0)
            main_box.add_widget(title_bar)
            main_box.add_widget(content)
            
            self._popup = ModalView(
                size_hint=(None, None),
                size=(target_w, target_h),
                auto_dismiss=False
            )
            self._popup.add_widget(main_box)
            self._popup.bind(on_dismiss=lambda *args: self._reclaim_keyboard())
            self._popup.open()
        
        self._guard_unsaved_then(_show_load_dialog)

    def load_file_manually(self, filepath: str):
        '''Load a score file from a given path without showing a dialog.
        
        Args:
            filepath: Absolute path to the .piano file to load
            
        Returns:
            bool: True if successful, False otherwise
        '''
        if not os.path.exists(filepath):
            Logger.warning(f'FileManager: File does not exist: {filepath}')
            return False
        
        if not os.path.isfile(filepath):
            Logger.warning(f'FileManager: Path is not a file: {filepath}')
            return False
        
        try:
            score = SCORE.load(filepath)
            # Load score (which sets it in GUI and redraws)
            self.editor.load_score(score)
            self.current_path = filepath
            self._last_dir = os.path.dirname(filepath)
            self.dirty = False
            self._update_window_title()
            
            # Update settings: last opened + recent files + dialog path
            try:
                settings = getattr(self.app, 'settings', None)
                if settings is not None:
                    settings.add_recent_file(filepath)
                    settings.set('last_file_dialog_path', self._last_dir)
            except Exception:
                pass
            
            Logger.info(f'FileManager: Successfully loaded file: {filepath}')
            return True
            
        except Exception as e:
            import traceback
            traceback.print_exc()  # Print full traceback to console for debugging
            Logger.error(f'FileManager: Failed to load file: {e}')
            return False

    def save_file(self):
        '''Save the current score.'''
        if self.current_path:
            self._save_to_path(self.current_path)
        else:
            self.save_file_as()

    def save_file_as(self):
        '''Save the current score to a new path.'''
        def _do_save(filepath: str):
            root, ext = os.path.splitext(filepath)
            if not ext:
                filepath = root + DEFAULT_EXT
            elif ext.lower() not in ('.piano', '.pianoTAB', '.json'):
                filepath = filepath + DEFAULT_EXT
            
            # Check if file exists and confirm overwrite
            if os.path.exists(filepath):
                self._confirm_overwrite(filepath, lambda: self._complete_save(filepath))
            else:
                self._dismiss_popup()
                self._save_to_path(filepath)
        
        suggested = os.path.basename(self.current_path) if self.current_path else self._suggest_name()
        content = SaveDialog(
            start_path=self._last_dir,
            suggested_name=suggested,
            save_callback=_do_save,
            cancel_callback=self._dismiss_popup
        )
        # Size capped for very large screens while remaining responsive
        target_w = min(int(Window.width * 0.9), LOAD_SAVE_MAX_WIDTH)
        target_h = min(int(Window.height * 0.9), LOAD_SAVE_MAX_HEIGHT)
        
        # Title bar
        title_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), padding=[dp(10), dp(5)])
        title_label = Label(text='Save File As', color=LIGHT, font_name=FONT_NAME, halign='left', valign='middle')
        title_label.bind(size=lambda *args: setattr(title_label, 'text_size', (title_label.width, None)))
        title_bar.add_widget(title_label)
        
        # Main container with title
        main_box = BoxLayout(orientation='vertical', spacing=0)
        main_box.add_widget(title_bar)
        main_box.add_widget(content)
        
        self._popup = ModalView(
            size_hint=(None, None),
            size=(target_w, target_h),
            auto_dismiss=False
        )
        self._popup.add_widget(main_box)
        self._popup.bind(on_dismiss=lambda *args: self._reclaim_keyboard())
        self._popup.open()

    def exit_app(self):
        '''Exit the application.'''
        self._guard_unsaved_then(lambda: self.app.stop())

    def mark_dirty(self):
        '''Mark the current file as having unsaved changes and trigger print preview update.'''
        self.dirty = True
        self._update_window_title()  # Update title to show asterisk
        
        # Trigger engraver to update print preview
        try:
            from engraver import get_engraver_instance
            score = self.get_score()
            if score and hasattr(self, 'gui') and self.gui:
                preview_canvas = self.gui.get_preview_widget()
                if preview_canvas:
                    engraver = get_engraver_instance()
                    engraver.do_engrave(score, preview_canvas, None)
        except Exception as e:
            print(f"FileManager: Failed to trigger engraver: {e}")

    # Convenience: single place to access the current SCORE
    def get_score(self) -> Optional[SCORE]:
        '''Return the currently loaded SCORE model (or None).'''
        try:
            return getattr(self.editor, 'score', None)
        except Exception:
            return None

    def _save_to_path(self, path: str):
        '''Actually save the score to the given path.'''
        try:
            score = self.editor.score
            if score is None:
                raise RuntimeError('No score to save')
            score.save(path)
            self.current_path = path
            self._last_dir = os.path.dirname(path) or self._last_dir
            self.dirty = False
            self._update_window_title()
            # Update settings: last opened + recent files + dialog path
            try:
                settings = getattr(self.app, 'settings', None)
                if settings is not None:
                    settings.add_recent_file(path)
                    settings.set('last_file_dialog_path', self._last_dir)
            except Exception:
                pass
        except Exception as e:
            self._error(f'Failed to save file:\n{e}')

    def _suggest_name(self) -> str:
        '''Generate a default filename.'''
        return 'Untitled' + DEFAULT_EXT

    def _dismiss_popup(self):
        '''Dismiss the current popup if open.'''
        if self._popup:
            self._popup.dismiss()
            self._popup = None

    def _complete_save(self, filepath: str):
        '''Complete the save operation after overwrite confirmation.'''
        # Don't dismiss popup here - already dismissed in _confirm_overwrite
        self._save_to_path(filepath)
    
    def _complete_save_then_action(self, filepath: str, action: Callable[[], None]):
        '''Complete save then execute action (for unsaved changes flow).'''
        # Don't dismiss popup here - already dismissed in _confirm_overwrite
        self._save_to_path(filepath)
        if not self.dirty:
            action()

    def _confirm_overwrite(self, filepath: str, on_confirm: Callable[[], None]):
        '''Ask user to confirm overwriting an existing file.'''
        filename = os.path.basename(filepath)
        # Store reference to save dialog before opening confirmation
        save_dialog_popup = self._popup
        
        def on_yes_wrapper():
            # First dismiss the save dialog
            if save_dialog_popup:
                save_dialog_popup.dismiss()
            self._popup = None
            # Then execute the confirm callback
            on_confirm()
        
        self._confirm_yes_no(
            title='File Exists',
            message=f'"{filename}" already exists.\nDo you want to replace it?',
            on_yes=on_yes_wrapper,
            on_no=lambda: None  # Do nothing, keep save dialog open
        )

    def _guard_unsaved_then(self, action: Callable[[], None]):
        '''Check for unsaved changes before executing an action.
        
        Shows a Yes/No/Cancel dialog:
        - Yes: Save changes, then execute action
        - No: Discard changes and execute action
        - Cancel: Do nothing
        '''
        if not self.dirty:
            action()
            return
        
        def on_yes():
            '''Save then execute action.'''
            def after_save():
                if not self.dirty:  # Save succeeded
                    action()
            
            # If we have a path, save directly
            if self.current_path:
                self._save_to_path(self.current_path)
                after_save()
            else:
                # Need to show save dialog
                original_action = action
                
                def _do_save(filepath: str):
                    root, ext = os.path.splitext(filepath)
                    if not ext:
                        filepath = root + DEFAULT_EXT
                    elif ext.lower() not in ('.piano', '.pianoTAB', '.json'):
                        filepath = filepath + DEFAULT_EXT
                    
                    # Check if file exists and confirm overwrite
                    if os.path.exists(filepath):
                        self._confirm_overwrite(filepath, lambda: self._complete_save_then_action(filepath, original_action))
                    else:
                        self._dismiss_popup()
                        self._save_to_path(filepath)
                        # Execute action after save if successful
                        if not self.dirty:
                            original_action()
                
                suggested = self._suggest_name()
                content = SaveDialog(
                    start_path=self._last_dir,
                    suggested_name=suggested,
                    save_callback=_do_save,
                    cancel_callback=self._dismiss_popup
                )
                # Size capped for very large screens while remaining responsive
                target_w = min(int(Window.width * 0.9), LOAD_SAVE_MAX_WIDTH)
                target_h = min(int(Window.height * 0.9), LOAD_SAVE_MAX_HEIGHT)
                
                # Title bar
                title_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), padding=[dp(10), dp(5)])
                title_label = Label(text='Save File As', color=LIGHT, font_name=FONT_NAME, halign='left', valign='middle')
                title_label.bind(size=lambda *args: setattr(title_label, 'text_size', (title_label.width, None)))
                title_bar.add_widget(title_label)
                
                # Main container with title
                main_box = BoxLayout(orientation='vertical', spacing=0)
                main_box.add_widget(title_bar)
                main_box.add_widget(content)
                
                self._popup = ModalView(
                    size_hint=(None, None),
                    size=(target_w, target_h),
                    auto_dismiss=False
                )
                self._popup.add_widget(main_box)
                self._popup.bind(on_dismiss=lambda *args: self._reclaim_keyboard())
                self._popup.open()
        
        def on_no():
            '''Discard changes and execute action.'''
            self.dirty = False
            action()
        
        self._confirm_yes_no_cancel(
            title='Unsaved Changes',
            message='Do you want to save your changes?',
            on_yes=on_yes,
            on_no=on_no,
            on_cancel=lambda: None
        )

    def _confirm_yes_no_cancel(self, *, title: str, message: str, 
                            on_yes: Callable[[], None],
                            on_no: Callable[[], None],
                            on_cancel: Callable[[], None]):
        '''Show a Yes/No/Cancel confirmation dialog.'''
        lbl = Label(
            text=message, 
            color=LIGHT, 
            size_hint=(1, 1),
            valign='center',
            halign='center',
            padding=[20, 20]
        )
        lbl.bind(size=lbl.setter('text_size'))  # Enable text wrapping and alignment
        
        btn_cancel = Button(text='Cancel', size_hint=(None, None), width=120, height=34)
        btn_no = Button(text='No', size_hint=(None, None), width=120, height=34)
        btn_yes = Button(text='Yes', size_hint=(None, None), width=120, height=34)
        
        popup = _dialog_shell(title, lbl, btns=[btn_cancel, btn_no, btn_yes])
        
        # Store reference to Canvas to release/reclaim keyboard
        from utils.canvas import Canvas
        canvas_widget = Canvas._global_keyboard_canvas

        # Keyboard handling - Escape = Cancel, Enter = Yes
        def on_key_down(instance, key, scancode, codepoint, modifier):
            if key == 27:  # Escape = Cancel
                print("DEBUG: Dialog keyboard handler - Escape pressed")
                Window.unbind(on_key_down=on_key_down)
                popup.dismiss()
                on_cancel()
                return True  # Consume the key event - prevents propagation
            elif key == 13:  # Return/Enter = Yes
                Window.unbind(on_key_down=on_key_down)
                popup.dismiss()
                on_yes()
                return True  # Consume the key event
            return False  # Let other keys pass through
        
        def do_yes(*args):
            print("DEBUG: Yes button clicked")
            Window.unbind(on_key_down=on_key_down)
            popup.dismiss()
            on_yes()
        
        def do_no(*args):
            print("DEBUG: No button clicked")
            Window.unbind(on_key_down=on_key_down)
            popup.dismiss()
            on_no()
        
        def do_cancel(*args):
            print("DEBUG: Cancel button clicked")
            Window.unbind(on_key_down=on_key_down)
            popup.dismiss()
            on_cancel()
        
        btn_yes.bind(on_release=do_yes)
        btn_no.bind(on_release=do_no)
        btn_cancel.bind(on_release=do_cancel)
        
        def on_popup_open(*args):
            # Release Canvas keyboard so dialog can capture keys
            if canvas_widget and canvas_widget._keyboard:
                canvas_widget._keyboard.release()
                canvas_widget._keyboard = None
            # Bind dialog keyboard handler
            Window.bind(on_key_down=on_key_down)
        
        def on_popup_dismiss(*args):
            # Unbind dialog keyboard handler (safety check - should already be unbound)
            try:
                Window.unbind(on_key_down=on_key_down)
            except Exception:
                pass
            Window.unbind(on_key_down=on_key_down)
            # Reclaim keyboard focus for Canvas
            self._reclaim_keyboard()
        
        popup.bind(on_open=on_popup_open)
        popup.bind(on_dismiss=on_popup_dismiss)
        popup.open()

    def _confirm_yes_no(self, *, title: str, message: str, 
                        on_yes: Callable[[], None],
                        on_no: Callable[[], None]):
        '''Show a Yes/No confirmation dialog.'''
        lbl = Label(
            text=message, 
            color=LIGHT, 
            size_hint=(1, 1),
            valign='center',
            halign='center',
            padding=[20, 20]
        )
        lbl.bind(size=lbl.setter('text_size'))  # Enable text wrapping and alignment
        
        btn_no = Button(text='No', size_hint=(None, None), width=120, height=34)
        btn_yes = Button(text='Yes', size_hint=(None, None), width=120, height=34)
        
        popup = _dialog_shell(title, lbl, btns=[btn_no, btn_yes])
        
        # Keyboard handling - Escape = No, Enter = Yes
        def on_key_down(instance, key, scancode, codepoint, modifier):
            if key == 27:  # Escape = No
                Window.unbind(on_key_down=on_key_down)
                popup.dismiss()
                on_no()
                return True  # Consume the key event
            elif key == 13:  # Return/Enter = Yes
                Window.unbind(on_key_down=on_key_down)
                popup.dismiss()
                on_yes()
                return True
            return False
        
        def do_yes(*_):
            Window.unbind(on_key_down=on_key_down)
            popup.dismiss()
            on_yes()
        
        def do_no(*_):
            Window.unbind(on_key_down=on_key_down)
            popup.dismiss()
            on_no()
        
        btn_yes.bind(on_release=do_yes)
        btn_no.bind(on_release=do_no)
        
        popup.bind(on_open=lambda *args: Window.bind(on_key_down=on_key_down))
        popup.bind(on_dismiss=lambda *args: self._reclaim_keyboard())
        popup.open()

    def _error(self, message: str):
        '''Show an error dialog.'''
        lbl = Label(
            text=message, 
            color=LIGHT, 
            size_hint=(1, 1),
            valign='center',
            halign='center',
            padding=[20, 20]
        )
        lbl.bind(size=lbl.setter('text_size'))  # Enable text wrapping and alignment
        btn_ok = Button(text='OK', size_hint=(None, None), width=120, height=34)
        popup = _dialog_shell('Error', lbl, btns=[btn_ok])
        btn_ok.bind(on_release=lambda *_: popup.dismiss())
        
        # Keyboard handling - Escape or Enter = OK
        def on_key_down(instance, key, scancode, codepoint, modifier):
            if key in (27, 13):  # Escape or Return/Enter
                popup.dismiss()
                return True
            return False
        
        popup.bind(on_open=lambda *args: Window.bind(on_key_down=on_key_down))
        popup.bind(on_dismiss=lambda *args: (Window.unbind(on_key_down=on_key_down), self._reclaim_keyboard()))
        popup.open()

    def _info(self, message: str):
        '''Show an info dialog.'''
        lbl = Label(
            text=message, 
            color=LIGHT, 
            size_hint=(1, 1),
            valign='center',
            halign='center',
            padding=[20, 20]
        )
        lbl.bind(size=lbl.setter('text_size'))  # Enable text wrapping and alignment
        btn_ok = Button(text='OK', size_hint=(None, None), width=120, height=34)
        popup = _dialog_shell('Info', lbl, btns=[btn_ok])
        btn_ok.bind(on_release=lambda *_: popup.dismiss())
        
        # Keyboard handling - Escape or Enter = OK
        def on_key_down(instance, key, scancode, codepoint, modifier):
            if key in (27, 13):  # Escape or Return/Enter
                popup.dismiss()
                return True
            return False
        
        popup.bind(on_open=lambda *args: Window.bind(on_key_down=on_key_down))
        popup.bind(on_dismiss=lambda *args: (Window.unbind(on_key_down=on_key_down), self._reclaim_keyboard()))
        popup.open()


def _dialog_shell(title: str, inner, *, btns: list[Button]) -> ModalView:
    '''Create a simple styled modal dialog.'''
    # Title bar
    title_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), padding=[dp(10), dp(5)])
    title_label = Label(text=title, color=LIGHT, font_name=FONT_NAME, halign='left', valign='middle')
    title_label.bind(size=lambda *args: setattr(title_label, 'text_size', (title_label.width, None)))
    title_bar.add_widget(title_label)
    
    # Content container
    content_box = BoxLayout(orientation='vertical', spacing=16, padding=[16, 24, 16, 16])  # Generous padding
    content_box.add_widget(inner)
    btn_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=44, spacing=12)
    for b in btns:
        b.background_normal = ''
        b.background_color = DARK
        b.color = LIGHT
        btn_row.add_widget(b)
    content_box.add_widget(btn_row)
    
    # Main container with title
    root = BoxLayout(orientation='vertical', spacing=0)
    root.add_widget(title_bar)
    root.add_widget(content_box)
    
    popup = ModalView(
        size_hint=(None, None),
        size=(500, 260),  # Larger dialog with more vertical space
        auto_dismiss=False
    )
    popup.add_widget(root)
    
    from kivy.graphics import Color, Rectangle
    with popup.canvas.before:
        Color(*DARK_LIGHTER)
        bg = Rectangle(pos=popup.pos, size=popup.size)
    popup.bind(pos=lambda *_: setattr(bg, 'pos', popup.pos), size=lambda *_: setattr(bg, 'size', popup.size))
    return popup
