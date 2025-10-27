import sys
import os
from pathlib import Path
import json

# Add parent directory to path (pianoTab directory, not tests directory)
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from file.SCORE import SCORE

def test_create_pianotab():
    """Test creating a simple PianoTab file with a single note."""
    # Create a new SCORE object
    score = SCORE()
    
    # Add a single note (Middle C = pitch 60, quarter note = 256 duration)
    note = score.new_note(pitch=60, duration=256.0, time=0.0, stave_idx=0)
    
    # Define the output file path
    output_path = Path('test_output.pianotab')
    
    # Save the score to a PianoTab file
    score.save(str(output_path))
    
    # Verify that the file was created
    assert output_path.exists(), "PianoTab file was not created."
    
    # Load the file back to verify contents
    loaded_score = SCORE.load(str(output_path))
    
    # Check that the loaded score has one note in the first stave
    assert len(loaded_score.stave) > 0, "Loaded score has no staves"
    assert len(loaded_score.stave[0].event.note) == 1, "Loaded score does not have the correct number of notes."
    assert loaded_score.stave[0].event.note[0].pitch == 60, "Note pitch doesn't match"
    
    # Keep the test file for inspection
    # output_path.unlink()    
    print(f"PianoTab file created and verified successfully: {output_path.absolute()}")
    return score

if __name__ == "__main__":
    test_create_pianotab()