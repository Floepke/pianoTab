'''
Line break drawing mixin for the Editor class.

Handles drawing line break indicators on the piano roll canvas.
'''


class LineBreakDrawerMixin:
    '''Mixin for drawing line break indicators.'''
    
    def _draw_line_breaks(self):
        '''Draw all line break indicators.'''
        # TODO: Implement line break drawing
        # - Iterate through self.score.lineBreak
        # - Draw visual indicators at line break positions
        # - Distinguish between 'manual' and 'locked' types
        # - Tag with ['lineBreaks', f'linebreak_{linebreak.id}']
        pass
