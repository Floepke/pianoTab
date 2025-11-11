"""
Test Score Manipulation Script

This script is called from Help > Test Score Generation menu.
Use it to programmatically create test scores for performance testing.

The script receives:
- score: The current SCORE object
- editor: The Editor instance (optional, can be None)
"""

from file.SCORE import SCORE
from typing import Optional


def generate_test_score(score: SCORE, editor=None):
    """
    Generate a test score with programmatically created notes.
    
    Args:
        score: The SCORE object to populate
        editor: The Editor instance (optional, for triggering redraws)
    
    Example usage:
        - Create many notes for performance testing
        - Create specific patterns for visual testing
        - Generate complex musical structures
    """
    
    print("\n=== Test Score Generation ===")
    print(f"Current score has {len(score.stave)} staves")
    
    # Example: Create a chromatic scale
    stave_idx = 0
    start_time = 0.0
    duration = 256.0  # Quarter note
    
    # Clear existing notes (optional)
    # score.stave[stave_idx].event.note.clear()
    
    # Generate chromatic scale from C2 (pitch 24) to C5 (pitch 60)
    print("Generating chromatic scale from C2 to C5...")
    current_time = start_time
    
    for pitch in range(24, 61):  # C2 to C5 (36 notes)
        hand = '<' if pitch < 42 else '>'  # Lower notes left hand, higher right hand
        
        new_note = score.new_note(
            stave_idx=stave_idx,
            time=current_time,
            pitch=pitch,
            hand=hand,
            duration=duration,
            velocity=100
        )
        
        current_time += duration
        
        if (pitch - 24) % 12 == 0:
            print(f"  Octave at pitch {pitch}, time {current_time}")
    
    print(f"Generated {len(score.stave[stave_idx].event.note)} notes total")
    
    # Trigger redraw if editor is available
    if editor is not None and hasattr(editor, 'redraw_pianoroll'):
        print("Triggering piano roll redraw...")
        editor.redraw_pianoroll()
        
        # Mark as modified
        if hasattr(editor, 'on_modified') and editor.on_modified:
            editor.on_modified()
    
    print("=== Test Score Generation Complete ===\n")
    return True


def generate_performance_test(score: SCORE, editor=None, note_count: int = 1000):
    """
    Generate a large number of notes for performance testing.
    
    Args:
        score: The SCORE object
        editor: The Editor instance
        note_count: Number of notes to generate
    """
    
    print(f"\n=== Performance Test: Generating {note_count} notes ===")
    
    stave_idx = 0
    duration = 256.0  # Quarter note
    
    # Clear existing notes
    score.stave[stave_idx].event.note.clear()
    
    import random
    current_time = 0.0
    
    for i in range(note_count):
        pitch = random.randint(24, 84)  # Random pitch C2 to C6
        hand = '<' if pitch < 54 else '>'
        
        score.new_note(
            stave_idx=stave_idx,
            time=current_time,
            pitch=pitch,
            hand=hand,
            duration=duration,
            velocity=random.randint(60, 100)
        )
        
        current_time += duration / 2  # Half note spacing for density
        
        if (i + 1) % 100 == 0:
            print(f"  Generated {i + 1}/{note_count} notes...")
    
    print(f"Generated {note_count} notes")
    
    # Trigger redraw
    if editor is not None and hasattr(editor, 'redraw_pianoroll'):
        print("Triggering piano roll redraw...")
        editor.redraw_pianoroll()
        
        if hasattr(editor, 'on_modified') and editor.on_modified:
            editor.on_modified()
    
    print("=== Performance Test Complete ===\n")
    return True


# Default function called when Help > Test is clicked
def run_test(score: SCORE, editor=None):
    """
    Main entry point for test score generation.
    
    Modify this function to run different tests.
    """
    
    # Choose which test to run:
    
    # Option 1: Simple chromatic scale
    # return generate_test_score(score, editor)
    
    # Option 2: Performance test with many notes
    return generate_performance_test(score, editor, note_count=500)
    
    # Option 3: Your custom test
    # ... add your own test logic here ...
