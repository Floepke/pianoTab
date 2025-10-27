#!/usr/bin/env python3
"""
Test saving and loading a SCORE with all Event types.
Creates test.pianotab file that persists for inspection.
"""

import sys
import os

# Add parent directory to path so we can import file module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from file.SCORE import SCORE

def test_save_load_all_events():
    """Test creating, saving, and loading a score with all event types."""
    
    print("Creating SCORE with all event types...")
    
    # Create a new score
    score = SCORE()
    
    # Add one of each event type to the first stave
    print("Adding events...")
    
    # Note
    score.new_note(stave_idx=0, time=0.0, duration=256.0, pitch=60, velocity=100)
    print("  ✓ Note added")
    
    # GraceNote
    score.new_grace_note(stave_idx=0, time=128.0, pitch=64, velocity=80)
    print("  ✓ GraceNote added")
    
    # Beam
    score.new_beam(stave_idx=0, time=256.0, staff=0.0, hand='<')
    print("  ✓ Beam added")
    
    # Text
    score.new_text(stave_idx=0, time=384.0, text='Test Text', side='>')
    print("  ✓ Text added")
    
    # Slur
    score.new_slur(stave_idx=0, time=512.0, 
                   x1_semitonesFromC4=0, 
                   x2_semitonesFromC4=5, y2_time=640.0,
                   x3_semitonesFromC4=10, y3_time=768.0,
                   x4_semitonesFromC4=12, y4_time=896.0)
    print("  ✓ Slur added")
    
    # CountLine
    score.new_count_line(stave_idx=0, time=1024.0, pitch1=60, pitch2=67)
    print("  ✓ CountLine added")
    
    # Section
    score.new_section(stave_idx=0, time=1152.0, text='Section A')
    print("  ✓ Section added")
    
    # StartRepeat
    score.new_start_repeat(stave_idx=0, time=1280.0)
    print("  ✓ StartRepeat added")
    
    # EndRepeat
    score.new_end_repeat(stave_idx=0, time=1408.0)
    print("  ✓ EndRepeat added")
    
    # Tempo
    score.new_tempo(stave_idx=0, time=1536.0, bpm=120)
    print("  ✓ Tempo added")
    
    # Save to disk
    test_file = os.path.join(os.path.dirname(__file__), 'test.pianotab')
    print(f"\nSaving to {test_file}...")
    score.save(test_file)
    print("  ✓ File saved")
    
    # Verify file exists
    assert os.path.exists(test_file), "File was not created!"
    file_size = os.path.getsize(test_file)
    print(f"  File size: {file_size:,} bytes")
    
    # Load from disk
    print("\nLoading from disk...")
    loaded_score = SCORE.from_json(open(test_file).read())
    print("  ✓ File loaded successfully")
    
    # Verify all event types are present
    print("\nVerifying loaded events...")
    stave = loaded_score.stave[0]
    
    assert len(stave.event.note) == 1, f"Expected 1 note, got {len(stave.event.note)}"
    print("  ✓ Note verified")
    
    assert len(stave.event.graceNote) == 1, f"Expected 1 graceNote, got {len(stave.event.graceNote)}"
    print("  ✓ GraceNote verified")
    
    assert len(stave.event.beam) == 1, f"Expected 1 beam, got {len(stave.event.beam)}"
    print("  ✓ Beam verified")
    
    assert len(stave.event.text) == 1, f"Expected 1 text, got {len(stave.event.text)}"
    print("  ✓ Text verified")
    
    assert len(stave.event.slur) == 1, f"Expected 1 slur, got {len(stave.event.slur)}"
    print("  ✓ Slur verified")
    
    assert len(stave.event.countLine) == 1, f"Expected 1 countLine, got {len(stave.event.countLine)}"
    print("  ✓ CountLine verified")
    
    assert len(stave.event.section) == 1, f"Expected 1 section, got {len(stave.event.section)}"
    print("  ✓ Section verified")
    
    assert len(stave.event.startRepeat) == 1, f"Expected 1 startRepeat, got {len(stave.event.startRepeat)}"
    print("  ✓ StartRepeat verified")
    
    assert len(stave.event.endRepeat) == 1, f"Expected 1 endRepeat, got {len(stave.event.endRepeat)}"
    print("  ✓ EndRepeat verified")
    
    assert len(stave.event.tempo) == 1, f"Expected 1 tempo, got {len(stave.event.tempo)}"
    print("  ✓ Tempo verified")
    
    # Verify some field values with shortened names
    print("\nVerifying field shortenings in loaded data...")
    note = stave.event.note[0]
    assert note.duration == 256.0, f"Note duration mismatch: {note.duration}"
    assert note.velocity == 100, f"Note velocity mismatch: {note.velocity}"
    print("  ✓ Note fields correct (dur, vel work)")
    
    text = stave.event.text[0]
    assert text.text == 'Test Text', f"Text content mismatch: {text.text}"
    print("  ✓ Text fields correct")
    
    slur = stave.event.slur[0]
    assert slur.x1_semitonesFromC4 == 0, f"Slur x1 mismatch: {slur.x1_semitonesFromC4}"
    assert slur.x4_semitonesFromC4 == 12, f"Slur x4 mismatch: {slur.x4_semitonesFromC4}"
    print("  ✓ Slur fields correct (x1-x4 work)")
    
    # Verify BaseGrid fields
    print("\nVerifying BaseGrid fields...")
    assert len(loaded_score.baseGrid) > 0, "No baseGrid found"
    bg = loaded_score.baseGrid[0]
    assert bg.numerator == 4, f"BaseGrid numerator mismatch: {bg.numerator}"
    assert bg.denominator == 4, f"BaseGrid denominator mismatch: {bg.denominator}"
    print("  ✓ BaseGrid fields correct (num, den work)")
    
    print("\n" + "="*50)
    print("✓ ALL TESTS PASSED!")
    print("="*50)
    print(f"\nTest file preserved at: {test_file}")
    print("You can inspect it to see the shortened JSON field names.")

if __name__ == '__main__':
    test_save_load_all_events()
