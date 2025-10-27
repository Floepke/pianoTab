#!/usr/bin/env python3
"""
Comprehensive test suite for SCORE dataclass implementation.
Tests all functionality to verify the @dataclass/@dataclasses-json version works correctly.
"""
import sys
import os
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from file.SCORE import SCORE, Event, Stave
from file.note import Note
from file.graceNote import GraceNote
from file.countLine import CountLine
from file.beam import Beam
from file.text import Text
from file.slur import Slur
from file.startRepeat import StartRepeat
from file.endRepeat import EndRepeat
from file.section import Section
from file.tempo import Tempo
from file.articulation import Articulation
from file.baseGrid import BaseGrid
from file.lineBreak import LineBreak
from file.staveRange import StaveRange


def test_score_creation():
    """Test 1: Basic SCORE creation with defaults"""
    print("\n=== Test 1: SCORE Creation ===")
    try:
        score = SCORE()
        print(f"✓ SCORE created successfully")
        print(f"  - Has {len(score.stave)} stave(s)")
        print(f"  - Has {len(score.lineBreak)} lineBreak(s)")
        print(f"  - Has {len(score.baseGrid)} baseGrid(s)")
        print(f"  - Meta info: {score.metaInfo.appName}")
        print(f"  - Header title: {score.header.title}")
        assert len(score.stave) > 0, "Should have at least one stave"
        assert len(score.lineBreak) > 0, "Should have at least one lineBreak"
        assert len(score.baseGrid) > 0, "Should have at least one baseGrid"
        return score
    except Exception as e:
        print(f"✗ FAILED: {e}")
        raise


def test_id_generation(score):
    """Test 2: ID generation and uniqueness"""
    print("\n=== Test 2: ID Generation ===")
    try:
        id1 = score._next_id()
        id2 = score._next_id()
        id3 = score._next_id()
        
        print(f"✓ Generated IDs: {id1}, {id2}, {id3}")
        assert id1 < id2 < id3, "IDs should be sequential"
        assert id1 != id2 != id3, "IDs should be unique"
        
        # Test reset
        score.reset_ids(100)
        id4 = score._next_id()
        print(f"✓ After reset to 100: {id4}")
        assert id4 == 100, "ID should reset correctly"
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        raise


def test_add_notes(score):
    """Test 3: Adding notes with various properties"""
    print("\n=== Test 3: Adding Notes ===")
    try:
        # Reset IDs for predictable testing
        score.reset_ids(1)
        
        # Add note with defaults
        note1 = score.new_note()
        print(f"✓ Added note with defaults (ID: {note1.id})")
        
        # Add note with custom properties
        note2 = score.new_note(
            stave_idx=0,
            time=256.0,
            duration=512.0,
            pitch=60,
            velocity=100,
            hand='<',
            color='#FF0000'
        )
        print(f"✓ Added custom note (ID: {note2.id}, pitch: {note2.pitch}, color: {note2.color})")
        
        # Add note with articulation
        artic = Articulation(type='staccato', color='#00FF00')
        note3 = score.new_note(
            time=512.0,
            pitch=72,
            articulation=[artic]
        )
        print(f"✓ Added note with articulation (ID: {note3.id}, articulations: {len(note3.articulation)})")
        
        # Verify notes are in the stave
        assert len(score.stave[0].event.note) == 3, "Should have 3 notes"
        print(f"✓ Total notes in stave: {len(score.stave[0].event.note)}")
        
        return [note1, note2, note3]
    except Exception as e:
        print(f"✗ FAILED: {e}")
        raise


def test_inheritance_system(score, notes):
    """Test 4: Property inheritance with '*' marker"""
    print("\n=== Test 4: Property Inheritance ===")
    try:
        note1, note2, note3 = notes
        
        # Note 1: uses '*' for inheritance
        print(f"Note 1 color field: '{note1.color}' (should be '*' for inherit)")
        if callable(getattr(note1, 'get_color', None)):
            actual_color = note1.get_color(score)
            print(f"✓ Note 1 inherited color: {actual_color}")
            expected = score.properties.globalNote.color
            print(f"  (from globalNote.color: {expected})")
        else:
            print(f"⚠ Note doesn't have get_color() method - check inheritance implementation")
        
        # Note 2: has explicit color
        print(f"Note 2 color field: '{note2.color}' (should be '#FF0000')")
        if callable(getattr(note2, 'get_color', None)):
            actual_color = note2.get_color(score)
            print(f"✓ Note 2 explicit color: {actual_color}")
            assert actual_color == '#FF0000', "Should use explicit color"
        
        # Test articulation inheritance
        if note3.articulation:
            artic = note3.articulation[0]
            print(f"Articulation color field: '{artic.color}' (should be '#00FF00')")
            if callable(getattr(artic, 'get_color', None)):
                artic_color = artic.get_color(score)
                print(f"✓ Articulation color: {artic_color}")
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_other_events(score):
    """Test 5: Adding other event types"""
    print("\n=== Test 5: Other Event Types ===")
    try:
        # Grace note
        grace = score.new_grace_note(time=100.0, pitch=50, velocity=60)
        print(f"✓ Added grace note (ID: {grace.id})")
        
        # Count line
        count = score.new_count_line(time=200.0, pitch1=40, pitch2=50, color='#0000FF')
        print(f"✓ Added count line (ID: {count.id})")
        
        # Beam
        beam = score.new_beam(time=300.0, staff=0.0, hand='<')
        print(f"✓ Added beam (ID: {beam.id})")
        
        # Text
        text = score.new_text(time=400.0, text='Allegro', side='<')
        print(f"✓ Added text (ID: {text.id}, text: '{text.text}')")
        
        # Slur
        slur = score.new_slur(time=500.0, x1_semitonesFromC4=0, y2_time=600.0)
        print(f"✓ Added slur (ID: {slur.id})")
        
        # Start/End repeat
        start_repeat = score.new_start_repeat(time=700.0)
        end_repeat = score.new_end_repeat(time=800.0)
        print(f"✓ Added repeats (start ID: {start_repeat.id}, end ID: {end_repeat.id})")
        
        # Section
        section = score.new_section(time=900.0, text='Verse 1')
        print(f"✓ Added section (ID: {section.id}, text: '{section.text}')")
        
        # Tempo
        tempo = score.new_tempo(time=1000.0, bpm=120)
        print(f"✓ Added tempo (ID: {tempo.id}, bpm: {tempo.bpm})")
        
        # Verify all events
        events = score.stave[0].event
        print(f"\n✓ Event counts:")
        print(f"  - notes: {len(events.note)}")
        print(f"  - graceNotes: {len(events.graceNote)}")
        print(f"  - countLines: {len(events.countLine)}")
        print(f"  - beams: {len(events.beam)}")
        print(f"  - text: {len(events.text)}")
        print(f"  - slurs: {len(events.slur)}")
        print(f"  - startRepeats: {len(events.startRepeat)}")
        print(f"  - endRepeats: {len(events.endRepeat)}")
        print(f"  - sections: {len(events.section)}")
        print(f"  - tempos: {len(events.tempo)}")
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_stave_management(score):
    """Test 6: Adding and managing staves"""
    print("\n=== Test 6: Stave Management ===")
    try:
        initial_count = len(score.stave)
        print(f"Initial stave count: {initial_count}")
        
        # Add new stave
        idx = score.new_stave(name="Piano Right Hand", scale=1.2)
        print(f"✓ Added stave at index {idx}: '{score.stave[idx].name}'")
        assert len(score.stave) == initial_count + 1, "Stave count should increase"
        
        # Get stave
        stave = score.get_stave(idx)
        print(f"✓ Retrieved stave: {stave.name}, scale: {stave.scale}")
        
        # Add note to new stave
        note = score.new_note(stave_idx=idx, pitch=80)
        print(f"✓ Added note to new stave (ID: {note.id})")
        assert len(score.stave[idx].event.note) == 1, "New stave should have 1 note"
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_basegrid_linebreak(score):
    """Test 7: BaseGrid and LineBreak management"""
    print("\n=== Test 7: BaseGrid & LineBreak ===")
    try:
        # Add basegrid
        initial_bg = len(score.baseGrid)
        score.new_basegrid(numerator=3, denominator=4, measureAmount=12)
        print(f"✓ Added basegrid (count: {initial_bg} → {len(score.baseGrid)})")
        
        # Add linebreak
        initial_lb = len(score.lineBreak)
        score.new_linebreak(time=2000.0, type='manual')
        print(f"✓ Added linebreak (count: {initial_lb} → {len(score.lineBreak)})")
        
        # Verify locked linebreak at time 0
        locked = [lb for lb in score.lineBreak if lb.type == 'locked' and lb.time == 0.0]
        print(f"✓ Locked linebreaks at time 0: {len(locked)}")
        assert len(locked) > 0, "Should have at least one locked linebreak at time 0"
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_find_delete_by_id(score):
    """Test 8: Finding and deleting events by ID"""
    print("\n=== Test 8: Find & Delete by ID ===")
    try:
        # Add a note with known ID
        score.reset_ids(9999)
        test_note = score.new_note(pitch=55)
        test_id = test_note.id
        print(f"Created test note with ID: {test_id}")
        
        # Find by ID
        found = score.find_by_id(test_id)
        print(f"✓ Found event by ID {test_id}: {type(found).__name__}")
        assert found is not None, "Should find the note"
        assert found.id == test_id, "IDs should match"
        
        # Delete by ID
        initial_count = len(score.stave[0].event.note)
        deleted = score.delete_by_id(test_id)
        print(f"✓ Deleted event (success: {deleted})")
        assert deleted == True, "Delete should succeed"
        assert len(score.stave[0].event.note) == initial_count - 1, "Note count should decrease"
        
        # Try to find deleted note
        found_after = score.find_by_id(test_id)
        print(f"✓ After delete, find returns: {found_after}")
        assert found_after is None, "Should not find deleted note"
        
        # Try to delete non-existent ID
        deleted2 = score.delete_by_id(99999)
        print(f"✓ Delete non-existent ID returns: {deleted2}")
        assert deleted2 == False, "Should return False for non-existent ID"
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_renumber_ids(score):
    """Test 9: Renumbering all IDs"""
    print("\n=== Test 9: Renumber IDs ===")
    try:
        print("Before renumbering:")
        sample_ids = []
        for note in score.stave[0].event.note[:3]:
            sample_ids.append(note.id)
        print(f"  Sample note IDs: {sample_ids}")
        
        # Renumber
        score.renumber_id()
        print("After renumbering:")
        
        new_ids = []
        for note in score.stave[0].event.note[:3]:
            new_ids.append(note.id)
        print(f"  Sample note IDs: {new_ids}")
        
        # Check all IDs are unique
        all_ids = set()
        for stave in score.stave:
            for note in stave.event.note:
                assert note.id not in all_ids, f"Duplicate ID found: {note.id}"
                all_ids.add(note.id)
        print(f"✓ All {len(all_ids)} note IDs are unique")
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_json_serialization(score):
    """Test 10: JSON save and load (most critical test!)"""
    print("\n=== Test 10: JSON Serialization ===")
    try:
        test_file = Path(__file__).parent / 'test_score_output.json'
        
        # Save to JSON
        print("Saving to JSON...")
        score.save(str(test_file))
        print(f"✓ Saved to {test_file}")
        
        # Check file exists and has content
        assert test_file.exists(), "JSON file should exist"
        file_size = test_file.stat().st_size
        print(f"  File size: {file_size} bytes")
        assert file_size > 0, "JSON file should not be empty"
        
        # Load from JSON
        print("Loading from JSON...")
        loaded_score = SCORE.load(str(test_file))
        print(f"✓ Loaded SCORE from JSON")
        
        # Compare key properties
        print("\nComparing original vs loaded:")
        print(f"  Staves: {len(score.stave)} vs {len(loaded_score.stave)}")
        print(f"  Notes in stave 0: {len(score.stave[0].event.note)} vs {len(loaded_score.stave[0].event.note)}")
        print(f"  LineBreaks: {len(score.lineBreak)} vs {len(loaded_score.lineBreak)}")
        print(f"  BaseGrids: {len(score.baseGrid)} vs {len(loaded_score.baseGrid)}")
        print(f"  Header title: '{score.header.title}' vs '{loaded_score.header.title}'")
        
        # Verify counts match
        assert len(loaded_score.stave) == len(score.stave), "Stave count mismatch"
        assert len(loaded_score.stave[0].event.note) == len(score.stave[0].event.note), "Note count mismatch"
        
        # Verify a specific note
        if len(score.stave[0].event.note) > 0:
            orig_note = score.stave[0].event.note[0]
            loaded_note = loaded_score.stave[0].event.note[0]
            print(f"\n  First note comparison:")
            print(f"    Pitch: {orig_note.pitch} vs {loaded_note.pitch}")
            print(f"    Time: {orig_note.time} vs {loaded_note.time}")
            print(f"    Duration: {orig_note.duration} vs {loaded_note.duration}")
            assert orig_note.pitch == loaded_note.pitch, "Note pitch mismatch"
            assert orig_note.time == loaded_note.time, "Note time mismatch"
        
        print(f"\n✓ JSON save/load successful!")
        
        # Clean up
        test_file.unlink()
        print(f"✓ Cleaned up test file")
        
        return loaded_score
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_dataclasses_json_direct():
    """Test 11: Direct dataclasses-json methods"""
    print("\n=== Test 11: dataclasses-json Direct Methods ===")
    try:
        score = SCORE()
        score.new_note(pitch=60, time=0.0)
        score.new_note(pitch=64, time=256.0)
        
        # to_dict
        print("Testing to_dict()...")
        score_dict = score.to_dict()
        print(f"✓ to_dict() returned {type(score_dict)} with {len(score_dict)} keys")
        assert 'stave' in score_dict, "Should have 'stave' key"
        assert 'properties' in score_dict, "Should have 'properties' key"
        
        # to_json
        print("Testing to_json()...")
        score_json = score.to_json()
        print(f"✓ to_json() returned string of length {len(score_json)}")
        assert isinstance(score_json, str), "Should return string"
        assert len(score_json) > 0, "JSON string should not be empty"
        
        # from_dict
        print("Testing from_dict()...")
        loaded_from_dict = SCORE.from_dict(score_dict)
        print(f"✓ from_dict() created SCORE with {len(loaded_from_dict.stave)} stave(s)")
        assert len(loaded_from_dict.stave[0].event.note) == 2, "Should have 2 notes"
        
        # from_json
        print("Testing from_json()...")
        loaded_from_json = SCORE.from_json(score_json)
        print(f"✓ from_json() created SCORE with {len(loaded_from_json.stave)} stave(s)")
        assert len(loaded_from_json.stave[0].event.note) == 2, "Should have 2 notes"
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise


def run_all_tests():
    """Run all tests in sequence"""
    print("=" * 60)
    print("SCORE DATACLASS COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    tests_passed = 0
    tests_failed = 0
    
    try:
        # Test 1
        score = test_score_creation()
        tests_passed += 1
        
        # Test 2
        test_id_generation(score)
        tests_passed += 1
        
        # Test 3
        notes = test_add_notes(score)
        tests_passed += 1
        
        # Test 4
        test_inheritance_system(score, notes)
        tests_passed += 1
        
        # Test 5
        test_other_events(score)
        tests_passed += 1
        
        # Test 6
        test_stave_management(score)
        tests_passed += 1
        
        # Test 7
        test_basegrid_linebreak(score)
        tests_passed += 1
        
        # Test 8
        test_find_delete_by_id(score)
        tests_passed += 1
        
        # Test 9
        test_renumber_ids(score)
        tests_passed += 1
        
        # Test 10 (Critical!)
        loaded_score = test_json_serialization(score)
        tests_passed += 1
        
        # Test 11
        test_dataclasses_json_direct()
        tests_passed += 1
        
    except Exception as e:
        tests_failed += 1
        print(f"\n{'='*60}")
        print(f"TEST SUITE STOPPED - Error encountered")
        print(f"{'='*60}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"✓ Passed: {tests_passed}")
    print(f"✗ Failed: {tests_failed}")
    print(f"Total:    {tests_passed + tests_failed}")
    
    if tests_failed == 0:
        print(f"\n🎉 ALL TESTS PASSED! 🎉")
        print(f"The SCORE dataclass implementation is working correctly!")
    else:
        print(f"\n⚠️  SOME TESTS FAILED")
        print(f"Check the output above for details.")
    
    print(f"{'='*60}\n")
    
    return tests_failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
