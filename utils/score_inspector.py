#!/usr/bin/env python3
"""
Score Inspector - Diagnostic tool for PianoTab pickle files

This tool safely loads and inspects PianoTab SCORE files saved in pickle format.
It provides formatted output to help debug corrupted or problematic files.

Usage:
    python utils/score_inspector.py <filename.pkl>
"""

import pickle
import sys
from pprint import pprint
from pathlib import Path

# Optional: set this to inspect a file without using command-line arguments.
# Example: FILE_TO_INSPECT = "/absolute/path/to/your_score.pkl"
FILE_TO_INSPECT: str = "/Users/philipbergwerf/Documents/pianoTab_kivy/test_score.pianotab"

# Add parent directory to path to ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all classes that might be in the pickle file
# This is required so pickle can deserialize them
from file.SCORE import SCORE, Event, Stave
from file.note import Note
from file.graceNote import GraceNote
from file.countLine import CountLine
from file.startRepeat import StartRepeat
from file.endRepeat import EndRepeat
from file.section import Section
from file.beam import Beam
from file.text import Text
from file.slur import Slur
from file.tempo import Tempo
from file.metaInfo import Metainfo
from file.header import Header
from file.properties import Properties
from file.baseGrid import BaseGrid
from file.lineBreak import LineBreak
from file.id import IDGenerator


def inspect_score(filename: str) -> None:
    """
    Load and inspect a SCORE pickle file.
    
    Args:
        filename: Path to the pickle file to inspect
    """
    filepath = Path(filename)
    
    # Check if file exists
    if not filepath.exists():
        print(f"Error: File '{filename}' not found")
        return
    
    # Check file extension (optional warning)
    if filepath.suffix not in ['.pkl', '.pickle', '.dat', '.pianotab']:
        print(f"Warning: File '{filename}' doesn't have a typical pickle extension (.pkl, .pickle, .dat, .pianotab)")
        print()
    
    print(f"Inspecting: {filepath.absolute()}")
    print(f"File size: {filepath.stat().st_size:,} bytes")
    print("=" * 80)
    print()
    
    try:
        # Try to load the pickle file
        with open(filepath, 'rb') as f:
            score = pickle.load(f)
        
        print("✓ Successfully loaded pickle file")
        print()
        print("-" * 80)
        print("SCORE Object Type:", type(score).__name__)
        print("-" * 80)
        print()
        
        # Pretty-print the entire structure
        print("SCORE Contents:")
        print("=" * 80)
        pprint(score, width=120, depth=None)
        print()
        
        # Additional validation checks
        print("=" * 80)
        print("Validation Checks:")
        print("-" * 80)
        
        # Check if it's a SCORE object
        if hasattr(score, 'stave'):
            print(f"✓ Valid SCORE object")
            print(f"  - Number of staves: {len(score.stave)}")
            
            # Count events in each stave
            for idx, stave in enumerate(score.stave):
                print(f"  - Stave {idx} ({stave.name}):")
                if hasattr(stave, 'event'):
                    event = stave.event
                    print(f"      Notes: {len(event.note)}")
                    print(f"      Grace notes: {len(event.graceNote)}")
                    print(f"      Count lines: {len(event.countLine)}")
                    print(f"      Start repeats: {len(event.startRepeat)}")
                    print(f"      End repeats: {len(event.endRepeat)}")
                    print(f"      Sections: {len(event.section)}")
                    print(f"      Beams: {len(event.beam)}")
                    print(f"      Text: {len(event.text)}")
                    print(f"      Slurs: {len(event.slur)}")
                    print(f"      Tempos: {len(event.tempo)}")
        else:
            print(f"⚠ Warning: Loaded object is not a valid SCORE (missing 'stave' attribute)")
        
        # Check for ID generator
        if hasattr(score, '_id'):
            print(f"✓ ID generator present")
            if hasattr(score._id, 'current_id'):
                print(f"  - Current ID: {score._id.current_id}")
        else:
            print(f"⚠ Warning: No ID generator found")
        
        # Check metadata
        if hasattr(score, 'metaInfo'):
            print(f"✓ MetaInfo present")
            if hasattr(score.metaInfo, 'title'):
                print(f"  - Title: {score.metaInfo.title}")
            if hasattr(score.metaInfo, 'composer'):
                print(f"  - Composer: {score.metaInfo.composer}")
        
        print()
        print("=" * 80)
        print("✓ Inspection complete - no errors detected")
        
    except pickle.UnpicklingError as e:
        print(f"✗ Error unpickling file: {e}")
        print()
        print("This file may be corrupted or not a valid pickle file.")
        
    except Exception as e:
        print(f"✗ Unexpected error: {type(e).__name__}: {e}")
        print()
        import traceback
        print("Full traceback:")
        traceback.print_exc()


def main():
    """Main entry point for the inspector tool."""
    # 1) Prefer inline path if provided
    if FILE_TO_INSPECT:
        inspect_score(FILE_TO_INSPECT)
        return

    # 2) Fallback to command-line argument
    if len(sys.argv) >= 2:
        filename = sys.argv[1]
        inspect_score(filename)
        return

    # 3) Neither provided
    print("No file provided.")
    print("- Set FILE_TO_INSPECT at the top of this file, e.g.:")
    print("    FILE_TO_INSPECT = '/absolute/path/to/your_score.pkl'")
    print("- Or run with a CLI argument:")
    print("    python utils/score_inspector.py my_score.pkl")
    sys.exit(1)


if __name__ == '__main__':
    main()
