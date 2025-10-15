'''
    Constants for the PianoTab application.
'''

# PIANOTICK is the amount of ticks per quarter note (1/4 note)
# time is expressed in floats where 1024.0 = whole note (1/1)
# thus, 256.0 ticks per quarter note (1/4 note)
# 512.0 ticks per half note (1/2 note)
# 128.0 ticks per eighth note (1/8 note)
# 64.0 ticks per sixteenth note (1/16 note)
# etc...
PIANOTICK_QUARTER: float = 256.0

# the black keys of a piano keyboard as a list of integers starting from 1 and ending at 88
BLACK_KEYS = [2, 5, 7, 10, 12, 14, 17, 19, 22, 24, 26, 29, 31, 34, 36, 38, 41, 43, 46,
              48, 50, 53, 55, 58, 60, 62, 65, 67, 70, 72, 74, 77, 79, 82, 84, 86]

# the white keys of a piano keyboard as a list of integers starting from 1 and ending at 88
WHITE_KEYS = [1, 3, 4, 6, 8, 9, 11, 13, 15, 16, 18, 20, 21, 23, 25, 27,
              28, 30, 32, 33, 35, 37, 39, 40, 42, 44, 45, 47, 49,
              51, 52, 54, 56, 57, 59, 61, 63, 64, 66, 68, 69,
              71, 73, 75, 76, 78, 80, 81, 83, 85, 87, 88]

# the number of physical semitone positions in the pianoTab 88 key stave
PHYSICAL_SEMITONE_POSITIONS = 103

# the pianoTab stave has a special design where some semitone positions are skipped 
# to get bigger gaps between the groups of two and three.
BE = [3, 8, 15, 20, 27, 32, 39, 44, 51, 56, 63, 68, 75, 80]
