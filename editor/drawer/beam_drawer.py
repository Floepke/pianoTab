'''
Beam drawing mixin for the Editor class.

Handles drawing beam events on the piano roll canvas.
'''


class BeamDrawerMixin:
    '''Mixin for drawing beams.'''
    
    def _draw_beams(self):
        '''Draw all beam events from all staves.'''
        # TODO: Implement beam drawing
        # - Iterate through self.score.stave
        # - For each stave, iterate through stave.event.beam
        # - Draw beam lines connecting grouped notes
        # - Tag with ['beams', f'beam_{stave_idx}_{beam.id}']
        pass
