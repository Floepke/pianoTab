from file.SCORE import SCORE
from utils.CONSTANT import PIANOTICK_QUARTER
from logger import log

def get_score_length_in_ticks(score: SCORE):
    '''Calculate total ticks in the SCORE based on time signatures/grid.'''
    total_ticks = 0
    for grid in score.baseGrid:
        measure_ticks = (PIANOTICK_QUARTER * 4) * (grid.numerator / grid.denominator)
        total_ticks += measure_ticks * grid.measureAmount
    return total_ticks

def get_editor_height_in_pixels(score: SCORE):
    '''Calculate editor height in pixels based on score length and pixels per quarter note.'''
    total_ticks = get_score_length_in_ticks(score)
    pixels_per_quarter = score.properties.editorZoomPixelsQuarter
    height_pixels = (total_ticks / PIANOTICK_QUARTER) * pixels_per_quarter
    return int(height_pixels)

def get_editor_barline_positions(score: SCORE):
    '''Calculate the x positions of barlines in pixels based on score grid.'''
    barline_positions = []
    total_ticks = 0
    pixels_per_quarter = score.properties.editorZoomPixelsQuarter
    for grid in score.baseGrid:
        measure_ticks = (PIANOTICK_QUARTER * 4) * (grid.numerator / grid.denominator)
        for _ in range(grid.measureAmount):
            y_pos = (total_ticks / PIANOTICK_QUARTER) * pixels_per_quarter
            barline_positions.append(y_pos)
            total_ticks += measure_ticks
    return barline_positions

def get_editor_gridline_positions(score: SCORE):
    '''Calculate the y positions of gridlines in pixels based on score grid.'''
    gridline_positions = []
    total_ticks = 0
    pixels_per_quarter = score.properties.editorZoomPixelsQuarter
    for grid in score.baseGrid:
        measure_ticks = (PIANOTICK_QUARTER * 4) * (grid.numerator / grid.denominator)
        subdivision_ticks = measure_ticks / grid.numerator
        for _ in range(grid.measureAmount):
            for i in range(1, grid.numerator):
                y_pos = ((total_ticks + i * subdivision_ticks) / PIANOTICK_QUARTER) * pixels_per_quarter
                gridline_positions.append(y_pos)
            total_ticks += measure_ticks
    return gridline_positions

def get_ticks2pixels(ticks: float, score: SCORE) -> int:
    '''Convert ticks to pixels based on score's pixels per quarter note.'''
    pixels_per_quarter = score.properties.editorZoomPixelsQuarter
    pixels = (ticks / PIANOTICK_QUARTER) * pixels_per_quarter
    return int(pixels)
