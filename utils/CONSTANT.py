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
PIANOTICK: float = 256.0
