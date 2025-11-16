'''
Engraver module for PianoTab.

The engraver performs complex layout calculations and rendering tasks
in a background thread to keep the UI responsive.
'''

from engraver.engraver import Engraver, get_engraver_instance

__all__ = ['Engraver', 'get_engraver_instance']
