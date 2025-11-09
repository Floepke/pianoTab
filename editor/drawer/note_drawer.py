'''
Note drawing mixin for the Editor class.

Handles drawing note events on the piano roll canvas.
'''


class NoteDrawerMixin:
    '''Mixin for drawing notes.'''
    
    def _draw_notes(self):
        '''Draw all note events from all staves.'''
        # TODO: Implement note drawing
        # - Iterate through self.score.stave
        # - For each stave, iterate through stave.event.note
        # - Draw each note at its position using self.canvas.add_rectangle or similar
        # - Tag with ['notes', f'note_{stave_idx}_{note.id}']
        pass
