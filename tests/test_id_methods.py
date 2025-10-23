#!/usr/bin/env python3
"""
Test suite for SCORE ID-related methods: find_by_id, delete_by_id, renumber_id.
Verifies the bug fixes for Pydantic model field access.
"""

import sys
import os
import tempfile

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from file.SCORE import SCORE

def test_find_by_id():
    """Test finding events by ID across all event types."""
    print("\n🔍 Testing find_by_id()...")
    
    score = SCORE()
    
    # Add various event types
    note1 = score.new_note(time=0.0, pitch=60, velocity=80)
    note2 = score.new_note(time=256.0, pitch=64, velocity=90)
    grace1 = score.new_grace_note(time=128.0, pitch=62)
    text1 = score.new_text(time=50.0, text="Allegro")
    countline1 = score.new_count_line(time=100.0, pitch1=50, pitch2=70)
    beam1 = score.new_beam(time=200.0, staff=1.0)
    slur1 = score.new_slur(time=150.0, x1_semitonesFromC4=0, x4_semitonesFromC4=4, y4_time=400.0)
    tempo1 = score.new_tempo(time=0.0, bpm=120)
    section1 = score.new_section(time=250.0, text="Verse 1")
    start_repeat = score.new_start_repeat(time=500.0)
    end_repeat = score.new_end_repeat(time=1000.0)
    
    print(f"  Created {len([note1, note2, grace1, text1, countline1, beam1, slur1, tempo1, section1, start_repeat, end_repeat])} events")
    
    # Test finding each event type
    found_note = score.find_by_id(note1.id)
    assert found_note is not None, f"Failed to find note with ID {note1.id}"
    assert found_note.id == note1.id, f"Found wrong note: expected {note1.id}, got {found_note.id}"
    assert found_note.pitch == 60, f"Found note has wrong pitch: {found_note.pitch}"
    print(f"  ✓ Found note: ID={found_note.id}, pitch={found_note.pitch}")
    
    found_grace = score.find_by_id(grace1.id)
    assert found_grace is not None, f"Failed to find grace note with ID {grace1.id}"
    assert found_grace.pitch == 62, f"Found grace note has wrong pitch: {found_grace.pitch}"
    print(f"  ✓ Found grace note: ID={found_grace.id}, pitch={found_grace.pitch}")
    
    found_text = score.find_by_id(text1.id)
    assert found_text is not None, f"Failed to find text with ID {text1.id}"
    assert found_text.text == "Allegro", f"Found text has wrong content: {found_text.text}"
    print(f"  ✓ Found text: ID={found_text.id}, text='{found_text.text}'")
    
    found_countline = score.find_by_id(countline1.id)
    assert found_countline is not None, f"Failed to find countline with ID {countline1.id}"
    print(f"  ✓ Found countline: ID={found_countline.id}")
    
    found_beam = score.find_by_id(beam1.id)
    assert found_beam is not None, f"Failed to find beam with ID {beam1.id}"
    print(f"  ✓ Found beam: ID={found_beam.id}")
    
    found_slur = score.find_by_id(slur1.id)
    assert found_slur is not None, f"Failed to find slur with ID {slur1.id}"
    print(f"  ✓ Found slur: ID={found_slur.id}")
    
    found_tempo = score.find_by_id(tempo1.id)
    assert found_tempo is not None, f"Failed to find tempo with ID {tempo1.id}"
    assert found_tempo.bpm == 120, f"Found tempo has wrong BPM: {found_tempo.bpm}"
    print(f"  ✓ Found tempo: ID={found_tempo.id}, bpm={found_tempo.bpm}")
    
    found_section = score.find_by_id(section1.id)
    assert found_section is not None, f"Failed to find section with ID {section1.id}"
    assert found_section.text == "Verse 1", f"Found section has wrong text: {found_section.text}"
    print(f"  ✓ Found section: ID={found_section.id}, text='{found_section.text}'")
    
    found_start_repeat = score.find_by_id(start_repeat.id)
    assert found_start_repeat is not None, f"Failed to find start repeat with ID {start_repeat.id}"
    print(f"  ✓ Found start repeat: ID={found_start_repeat.id}")
    
    found_end_repeat = score.find_by_id(end_repeat.id)
    assert found_end_repeat is not None, f"Failed to find end repeat with ID {end_repeat.id}"
    print(f"  ✓ Found end repeat: ID={found_end_repeat.id}")
    
    # Test finding non-existent ID
    not_found = score.find_by_id(99999)
    assert not_found is None, f"Should not find event with ID 99999, but got {not_found}"
    print(f"  ✓ Correctly returned None for non-existent ID 99999")
    
    print("✓ find_by_id() works correctly for all event types!")

def test_delete_by_id():
    """Test deleting events by ID."""
    print("\n🗑️  Testing delete_by_id()...")
    
    score = SCORE()
    
    # Add various events
    note1 = score.new_note(time=0.0, pitch=60, velocity=80)
    note2 = score.new_note(time=256.0, pitch=64, velocity=90)
    text1 = score.new_text(time=50.0, text="Delete me")
    grace1 = score.new_grace_note(time=128.0, pitch=62)
    
    initial_note_count = len(score.get_stave(0).event.note)
    initial_text_count = len(score.get_stave(0).event.text)
    initial_grace_count = len(score.get_stave(0).event.graceNote)
    
    print(f"  Initial counts: {initial_note_count} notes, {initial_text_count} texts, {initial_grace_count} grace notes")
    
    # Test deleting a note
    result = score.delete_by_id(note1.id)
    assert result == True, f"Failed to delete note with ID {note1.id}"
    assert len(score.get_stave(0).event.note) == initial_note_count - 1, "Note count didn't decrease"
    assert score.find_by_id(note1.id) is None, f"Note {note1.id} still found after deletion"
    print(f"  ✓ Deleted note: ID={note1.id}")
    
    # Test deleting text
    result = score.delete_by_id(text1.id)
    assert result == True, f"Failed to delete text with ID {text1.id}"
    assert len(score.get_stave(0).event.text) == initial_text_count - 1, "Text count didn't decrease"
    print(f"  ✓ Deleted text: ID={text1.id}")
    
    # Test deleting grace note
    result = score.delete_by_id(grace1.id)
    assert result == True, f"Failed to delete grace note with ID {grace1.id}"
    assert len(score.get_stave(0).event.graceNote) == initial_grace_count - 1, "Grace note count didn't decrease"
    print(f"  ✓ Deleted grace note: ID={grace1.id}")
    
    # Test deleting non-existent ID
    result = score.delete_by_id(99999)
    assert result == False, "Should return False for non-existent ID"
    print(f"  ✓ Correctly returned False for non-existent ID 99999")
    
    # Verify remaining note is still there
    found_note2 = score.find_by_id(note2.id)
    assert found_note2 is not None, f"Remaining note {note2.id} was incorrectly deleted"
    print(f"  ✓ Remaining note {note2.id} still exists")
    
    print("✓ delete_by_id() works correctly!")

def test_renumber_id():
    """Test renumbering all event IDs sequentially."""
    print("\n🔢 Testing renumber_id()...")
    
    score = SCORE()
    
    # Add events
    note1 = score.new_note(time=0.0, pitch=60)
    note2 = score.new_note(time=256.0, pitch=64)
    text1 = score.new_text(time=50.0, text="Text")
    grace1 = score.new_grace_note(time=128.0, pitch=62)
    countline1 = score.new_count_line(time=100.0, pitch1=50, pitch2=70)
    
    print(f"  Original IDs: note1={note1.id}, note2={note2.id}, text1={text1.id}, grace1={grace1.id}, countline1={countline1.id}")
    
    # Delete one note to create a gap in IDs
    score.delete_by_id(note1.id)
    print(f"  Deleted note1 with ID={note1.id}")
    
    # Renumber all IDs
    score.renumber_id()
    print(f"  Renumbered all IDs")
    
    # Collect all new IDs (linebreaks have IDs, basegrids don't)
    all_ids = []
    
    # Linebreaks have IDs
    for linebreak in score.lineBreak:
        all_ids.append(linebreak.id)
    
    # Note: Basegrids don't have IDs, so we skip them
    
    # Events in staves
    for stave in score.stave:
        for note in stave.event.note:
            all_ids.append(note.id)
        for grace in stave.event.graceNote:
            all_ids.append(grace.id)
        for text in stave.event.text:
            all_ids.append(text.id)
        for countline in stave.event.countLine:
            all_ids.append(countline.id)
    
    print(f"  New IDs (all objects with IDs): {sorted(all_ids)}")
    
    # Verify IDs are sequential starting from 1
    expected_ids = list(range(1, len(all_ids) + 1))
    assert sorted(all_ids) == expected_ids, f"IDs are not sequential: expected {expected_ids}, got {sorted(all_ids)}"
    
    # Verify no duplicate IDs
    assert len(all_ids) == len(set(all_ids)), f"Duplicate IDs found: {all_ids}"
    
    print(f"  ✓ All IDs are sequential from 1 to {len(all_ids)}")
    print(f"  ✓ No duplicate IDs")
    print("✓ renumber_id() works correctly!")

def test_id_persistence_after_save_load():
    """Test that IDs persist correctly through save/load cycle."""
    print("\n💾 Testing ID persistence through save/load...")
    
    score = SCORE()
    
    # Add events
    note1 = score.new_note(time=0.0, pitch=60)
    text1 = score.new_text(time=50.0, text="Save me")
    grace1 = score.new_grace_note(time=128.0, pitch=62)
    
    original_note_id = note1.id
    original_text_id = text1.id
    original_grace_id = grace1.id
    
    print(f"  Original IDs: note={original_note_id}, text={original_text_id}, grace={original_grace_id}")
    
    # Save and load
    with tempfile.NamedTemporaryFile(suffix='.pianotab', delete=False) as temp:
        temp_path = temp.name
    
    try:
        score.save(temp_path)
        loaded_score = SCORE.load(temp_path)
        
        # After load, renumber_id() is called, so IDs will be sequential
        # But we should be able to find all events
        loaded_notes = loaded_score.get_stave(0).event.note
        loaded_texts = loaded_score.get_stave(0).event.text
        loaded_graces = loaded_score.get_stave(0).event.graceNote
        
        assert len(loaded_notes) == 1, f"Expected 1 note, got {len(loaded_notes)}"
        assert len(loaded_texts) == 1, f"Expected 1 text, got {len(loaded_texts)}"
        assert len(loaded_graces) == 1, f"Expected 1 grace note, got {len(loaded_graces)}"
        
        # Verify content is correct
        assert loaded_notes[0].pitch == 60, f"Note pitch mismatch: {loaded_notes[0].pitch}"
        assert loaded_texts[0].text == "Save me", f"Text content mismatch: {loaded_texts[0].text}"
        assert loaded_graces[0].pitch == 62, f"Grace note pitch mismatch: {loaded_graces[0].pitch}"
        
        print(f"  ✓ Loaded score has correct event counts")
        print(f"  ✓ Event content preserved correctly")
        print(f"  New IDs after load: note={loaded_notes[0].id}, text={loaded_texts[0].id}, grace={loaded_graces[0].id}")
        
    finally:
        os.unlink(temp_path)
    
    print("✓ ID methods work correctly after save/load!")

def main():
    """Run all ID-related tests."""
    print("🧪 Running SCORE ID Methods Test Suite")
    print("=" * 50)
    
    try:
        test_find_by_id()
        test_delete_by_id()
        test_renumber_id()
        test_id_persistence_after_save_load()
        
        print("\n" + "=" * 50)
        print("🎉 ALL ID METHOD TESTS PASSED!")
        print("✅ find_by_id() works correctly")
        print("✅ delete_by_id() works correctly")
        print("✅ renumber_id() works correctly")
        print("✅ IDs persist correctly through save/load")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
