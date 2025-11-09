'''
Grace note drawing mixin for the Editor class.

Handles drawing grace note events on the piano roll canvas.
'''


class GraceNoteDrawerMixin:
    '''Mixin for drawing grace notes.'''
    
    def _draw_grace_notes(self):
        '''Draw all grace note events from all staves.'''
        # TODO: Implement grace note drawing
        # - Iterate through self.score.stave
        # - For each stave, iterate through stave.event.graceNote
        # - Draw each grace note (typically smaller than regular notes)
        # - Tag with ['graceNotes', f'gracenote_{stave_idx}_{gracenote.id}']
        pass
