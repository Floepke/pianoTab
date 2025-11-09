'''
Slur drawing mixin for the Editor class.

Handles drawing slur events on the piano roll canvas.
'''


class SlurDrawerMixin:
    '''Mixin for drawing slurs.'''
    
    def _draw_slurs(self):
        '''Draw all slur events from all staves.'''
        # TODO: Implement slur drawing
        # - Iterate through self.score.stave
        # - For each stave, iterate through stave.event.slur
        # - Draw curved lines from slur.time to slur.y4_time
        # - Tag with ['slurs', f'slur_{stave_idx}_{slur.id}']
        pass
