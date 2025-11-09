'''
Tempo drawing mixin for the Editor class.

Handles drawing tempo events on the piano roll canvas.
'''


class TempoDrawerMixin:
    '''Mixin for drawing tempo markings.'''
    
    def _draw_tempos(self):
        '''Draw all tempo events from all staves.'''
        # TODO: Implement tempo drawing
        # - Iterate through self.score.stave
        # - For each stave, iterate through stave.event.tempo
        # - Draw tempo markings (text + optional metronome symbol)
        # - Tag with ['tempos', f'tempo_{stave_idx}_{tempo.id}']
        pass
