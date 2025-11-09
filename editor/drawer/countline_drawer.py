'''
Count line drawing mixin for the Editor class.

Handles drawing count line events on the piano roll canvas.
'''


class CountLineDrawerMixin:
    '''Mixin for drawing count lines.'''
    
    def _draw_count_lines(self):
        '''Draw all count line events from all staves.'''
        # TODO: Implement count line drawing
        # - Iterate through self.score.stave
        # - For each stave, iterate through stave.event.countLine
        # - Draw vertical count lines at specified positions
        # - Tag with ['countLines', f'countline_{stave_idx}_{countline.id}']
        pass
