'''
Text drawing mixin for the Editor class.

Handles drawing text events on the piano roll canvas.
'''


class TextDrawerMixin:
    '''Mixin for drawing text annotations.'''
    
    def _draw_texts(self):
        '''Draw all text events from all staves.'''
        # TODO: Implement text drawing
        # - Iterate through self.score.stave
        # - For each stave, iterate through stave.event.text
        # - Draw text at the specified position
        # - Tag with ['texts', f'text_{stave_idx}_{text.id}']
        pass
