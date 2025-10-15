from file.SCORE import SCORE
from utils.CONSTANT import PIANOTICK

def calc_score_length_in_ticks(score: SCORE):
    '''Calculate total ticks in the SCORE based on time signatures/grid.'''
    total_ticks = 0
    for grid in score.baseGrid:
        measure_ticks = (PIANOTICK * 4) * (grid.numerator / grid.denominator)
        total_ticks += measure_ticks * grid.measureAmount
    return total_ticks

def calc_editor_height_in_pixels(score: SCORE):
    '''Calculate editor height in pixels based on score length and pixels per quarter note.'''
    total_ticks = calc_score_length_in_ticks(score)
    pixels_per_quarter = score.properties.editorZoomPixelsQuarter
    height_pixels = (total_ticks / PIANOTICK) * pixels_per_quarter
    return int(height_pixels)