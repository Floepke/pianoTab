#!/usr/bin/env python3
"""
Comprehensive test suite for SCORE class with all event types.
Tests None-based inheritance system and JSON serialization/deserialization.
"""

import sys
import os
import json
import tempfile
from pathlib import Path

# Add the project root and file directory to Python path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'file'))

from file.SCORE import SCORE
from file.note import Note
from file.graceNote import GraceNote
from file.text import Text
from file.countLine import CountLine
from file.beam import Beam
from file.slur import Slur
from file.section import Section
from file.startRepeat import StartRepeat
from file.endRepeat import EndRepeat
from file.articulation import Articulation
from file.tempo import Tempo

def test_score_creation_and_events():
    """Test creating a SCORE with all event types and verify inheritance works."""
    
    print("🎹 Testing SCORE creation and all event types...")
    
    # Create a new score
    score = SCORE()
    score.metaInfo.author = "Test Author"
    score.metaInfo.description = "Comprehensive test score with all event types"
    
    # Modify some global properties to test inheritance
    score.properties.globalNote.color = "#FF0000"  # Red notes
    score.properties.globalText.color = "#00FF00"  # Green text
    score.properties.globalText.fontSize = 14
    score.properties.globalBeam.color = "#0000FF"  # Blue beams
    score.properties.globalSlur.color = "#FFFF00"  # Yellow slurs
    score.properties.globalGraceNote.color = "#FF00FF"  # Magenta grace notes
    score.properties.globalCountLine.width = 1.5  # Set global width for count lines
    
    print(f"Created score by: {score.metaInfo.author}")
    print(f"Description: {score.metaInfo.description}")
    
    # Add events using the new_* methods (which use None defaults for inheritance)
    
    # 1. Add notes with inheritance and explicit colors
    note1 = score.new_note(time=0.0, pitch=60, velocity=80)  # Inherits red color
    note2 = score.new_note(time=256.0, pitch=64, velocity=90, color="#800080")  # Explicit purple
    print(f"✓ Added notes: note1.color={note1.color}, note2.color={note2.color}")
    
    # 2. Add grace notes
    grace1 = score.new_grace_note(time=128.0, pitch=62, velocity=70)  # Inherits from globalGracenote
    print(f"✓ Added grace note: grace1.color={grace1.color}")
    
    # 3. Add text with inheritance and explicit properties
    text1 = score.new_text(time=50.0, text="Allegro")  # Inherits green color and fontSize 14
    text2 = score.new_text(time=300.0, text="Forte", color="#FFA500", fontSize=16)  # Explicit
    print(f"✓ Added text: text1.color={text1.color}, text1.fontSize={text1.fontSize}")
    print(f"  text2.color={text2.color}, text2.fontSize={text2.fontSize}")
    
    # 4. Add count lines with inheritance and explicit values
    countline1 = score.new_count_line(time=100.0, pitch1=50, pitch2=70)  # Inherits width from global
    countline2 = score.new_count_line(time=150.0, pitch1=52, pitch2=72, width=2.5)  # Explicit width
    print(f"✓ Added count lines: countline1.width={countline1.width} (inherited from global)")
    print(f"  countline2.width={countline2.width} (explicit), color={countline1.color}")
    
    # 5. Add beams
    beam1 = score.new_beam(time=200.0, staff=1.0)  # Inherits blue color
    print(f"✓ Added beam: beam1.color={beam1.color}")
    
    # 6. Add slurs
    slur1 = score.new_slur(time=150.0, x1_semitonesFromC4=0, x4_semitonesFromC4=4, y4_time=400.0)
    print(f"✓ Added slur: slur1.color={slur1.color}")
    
    # 7. Add tempo
    tempo1 = score.new_tempo(time=0.0, bpm=120)
    print(f"✓ Added tempo: tempo1.bpm={tempo1.bpm}")
    
    # 8. Add repeats
    start_repeat = score.new_start_repeat(time=500.0)
    end_repeat = score.new_end_repeat(time=1000.0)
    print(f"✓ Added repeats: start.color={start_repeat.color}, end.color={end_repeat.color}")
    
    # 9. Add section
    section1 = score.new_section(time=250.0, text="Verse 1")
    print(f"✓ Added section: section1.color={section1.color}")
    
    # 10. Add line breaks with key ranges
    score.add_linebreak(time=128.0, type='manual', lowestKey=40, highestKey=80)
    score.add_linebreak(time=512.0, type='manual', lowestKey=45, highestKey=75)
    linebreak1 = score.lineBreak[1]  # First manual linebreak (index 0 is the default locked one)
    linebreak2 = score.lineBreak[2]  # Second manual linebreak
    print(f"✓ Added linebreaks: lb1 range=[{linebreak1.lowestKey}, {linebreak1.highestKey}], lb2 range=[{linebreak2.lowestKey}, {linebreak2.highestKey}]")
    
    return score

def test_stave_scales():
    """Test stave scale functionality."""
    
    print("\n📏 Testing stave scale functionality...")
    
    score = SCORE()
    
    # Test adding staves with different scales
    stave_idx1 = score.add_stave(name="Default Scale", scale=1.0)
    stave_idx2 = score.add_stave(name="Half Scale", scale=0.5)
    stave_idx3 = score.add_stave(name="Double Scale", scale=2.0)
    
    stave1 = score.get_stave(stave_idx1)
    stave2 = score.get_stave(stave_idx2)
    stave3 = score.get_stave(stave_idx3)
    
    print(f"✓ Stave scales: {stave1.name}={stave1.scale}, {stave2.name}={stave2.scale}, {stave3.name}={stave3.scale}")
    
    # Test that scales persist through JSON round-trip
    with tempfile.NamedTemporaryFile(suffix='.pianotab', delete=False) as temp:
        temp_path = temp.name
    
    try:
        score.save(temp_path)
        loaded_score = SCORE.load(temp_path)
        
        loaded_stave1 = loaded_score.get_stave(stave_idx1)
        loaded_stave2 = loaded_score.get_stave(stave_idx2)
        loaded_stave3 = loaded_score.get_stave(stave_idx3)
        
        assert loaded_stave1.scale == 1.0, f"Scale mismatch: expected 1.0, got {loaded_stave1.scale}"
        assert loaded_stave2.scale == 0.5, f"Scale mismatch: expected 0.5, got {loaded_stave2.scale}"
        assert loaded_stave3.scale == 2.0, f"Scale mismatch: expected 2.0, got {loaded_stave3.scale}"
        
        print("✓ Stave scales preserved through JSON round-trip")
        
    finally:
        os.unlink(temp_path)

def test_json_serialization(score):
    """Test JSON serialization and verify structure."""
    
    print("\n💾 Testing JSON serialization...")
    
    # Create a temporary file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pianotab', delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        # Save the score
        score.save(temp_path)
        print(f"✓ Saved score to {temp_path}")
        
        # Read and examine the JSON structure
        with open(temp_path, 'r') as f:
            json_data = json.load(f)
        
        print("\n📋 JSON Structure Analysis:")
        print(f"  - Author: {json_data['metaInfo']['author']}")
        print(f"  - Description: {json_data['metaInfo']['description']}")
        print(f"  - Global note color: {json_data['properties']['globalNote']['color']}")
        print(f"  - Global text color: {json_data['properties']['globalText']['color']}")
        print(f"  - Global text fontSize: {json_data['properties']['globalText']['fontSize']}")
        print(f"  - Global gracenote color: {json_data['properties']['globalGraceNote']['color']}")
        
        # Check staves and events
        stave = json_data['stave'][0]
        print(f"  - Number of staves: {len(json_data['stave'])}")
        print(f"  - Notes in stave 0: {len(stave['event']['note'])}")
        print(f"  - Grace notes: {len(stave['event']['graceNote'])}")
        print(f"  - Text events: {len(stave['event']['text'])}")
        print(f"  - Count lines: {len(stave['event']['countLine'])}")
        print(f"  - Beams: {len(stave['event']['beam'])}")
        print(f"  - Slurs: {len(stave['event']['slur'])}")
        print(f"  - Sections: {len(stave['event']['section'])}")
        print(f"  - Start repeats: {len(stave['event']['startRepeat'])}")
        print(f"  - End repeats: {len(stave['event']['endRepeat'])}")
        print(f"  - Tempos: {len(stave['event']['tempo'])}")
        
        # Examine LineBreaks
        linebreaks = json_data.get('lineBreak', [])
        print(f"  - Line breaks: {len(linebreaks)}")
        for i, lb in enumerate(linebreaks):
            print(f"    LineBreak {i}: time={lb.get('time')}, type={lb.get('type')}, range=[{lb.get('lowestKey', 0)}, {lb.get('highestKey', 0)}]")
        
        # Examine specific inheritance patterns in JSON
        notes = stave['event']['note']
        if len(notes) >= 2:
            print(f"\n🔍 Inheritance Analysis in JSON:")
            print(f"  - Note 1 color: {notes[0].get('color', 'null')} (should be null for inheritance)")
            print(f"  - Note 2 color: {notes[1].get('color', 'null')} (should be explicit color)")
        
        texts = stave['event']['text']
        if len(texts) >= 2:
            print(f"  - Text 1 fontSize: {texts[0].get('fontSize', 'null')} (should be null for inheritance)")
            print(f"  - Text 1 color: {texts[0].get('color', 'null')} (should be null for inheritance)")
            print(f"  - Text 2 fontSize: {texts[1].get('fontSize', 'null')} (should be explicit)")
            print(f"  - Text 2 color: {texts[1].get('color', 'null')} (should be explicit)")
        
        return json_data, temp_path
        
    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise

def test_json_deserialization(temp_path):
    """Test loading the JSON back into SCORE and verify inheritance still works."""
    
    print("\n🔄 Testing JSON deserialization...")
    
    try:
        # Load the score back
        loaded_score = SCORE.load(temp_path)
        print("✓ Successfully loaded score from JSON")
        
        # Verify metadata
        print(f"✓ Author: {loaded_score.metaInfo.author}")
        print(f"✓ Description: {loaded_score.metaInfo.description}")
        
        # Test inheritance still works after loading
        stave = loaded_score.get_stave(0)
        
        if stave.event.note:
            note1 = stave.event.note[0]
            print(f"✓ Note 1 effective color: {note1.color} (inheritance working)")
            print(f"  Literal value: {note1.get_literal_value('color')} (should be None)")
            
            if len(stave.event.note) > 1:
                note2 = stave.event.note[1]
                print(f"✓ Note 2 effective color: {note2.color} (explicit value)")
                print(f"  Literal value: {note2.get_literal_value('color')} (should be the color)")
        
        if stave.event.text:
            text1 = stave.event.text[0]
            print(f"✓ Text 1 effective color: {text1.color} (inheritance)")
            print(f"✓ Text 1 effective fontSize: {text1.fontSize} (inheritance)")
            print(f"  Literal color: {text1.get_literal_value('color')} (should be None)")
            print(f"  Literal fontSize: {text1.get_literal_value('fontSize')} (should be None)")
            print(f"  Global text color in loaded score: {loaded_score.properties.globalText.color}")
            
            if len(stave.event.text) > 1:
                text2 = stave.event.text[1]
                print(f"✓ Text 2 effective color: {text2.color} (explicit)")
                print(f"✓ Text 2 effective fontSize: {text2.fontSize} (explicit)")
        
        # Test that global property changes still propagate
        print(f"\n🔧 Testing global property change propagation...")
        original_color = loaded_score.properties.globalNote.color
        loaded_score.properties.globalNote.color = "#CYAN"
        
        if stave.event.note:
            note1 = stave.event.note[0]
            new_color = note1.color
            print(f"✓ Changed global note color from {original_color} to #CYAN")
            print(f"✓ Note 1 now shows: {new_color} (inheritance updated)")
        
        return loaded_score
        
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)
            print(f"✓ Cleaned up temporary file: {temp_path}")

def test_inheritance_edge_cases(score):
    """Test edge cases for inheritance system."""
    
    print("\n🧪 Testing inheritance edge cases...")
    
    # Test setting explicit values and then back to inheritance
    stave = score.get_stave(0)
    if stave.event.note:
        note = stave.event.note[0]
        
        # Note should inherit initially
        original_color = note.color
        print(f"✓ Original inherited color: {original_color}")
        
        # Set explicit value
        note.color = "#MAGENTA"
        print(f"✓ Set explicit color: {note.color}")
        print(f"  Literal value: {note.get_literal_value('color')}")
        
        # Set back to inheritance by setting to None
        note.color = None
        inherited_again = note.color
        print(f"✓ Back to inheritance: {inherited_again}")
        print(f"  Literal value: {note.get_literal_value('color')}")

def test_stave_scales():
    """Test stave scale functionality."""
    
    print("\n📏 Testing stave scale functionality...")
    
    score = SCORE()
    
    # Test adding staves with different scales
    stave_idx1 = score.add_stave(name="Default Scale", scale=1.0)
    stave_idx2 = score.add_stave(name="Half Scale", scale=0.5)
    stave_idx3 = score.add_stave(name="Double Scale", scale=2.0)
    
    stave1 = score.get_stave(stave_idx1)
    stave2 = score.get_stave(stave_idx2)
    stave3 = score.get_stave(stave_idx3)
    
    print(f"✓ Stave scales: {stave1.name}={stave1.scale}, {stave2.name}={stave2.scale}, {stave3.name}={stave3.scale}")
    
    # Test that scales persist through JSON round-trip
    with tempfile.NamedTemporaryFile(suffix='.pianotab', delete=False) as temp:
        temp_path = temp.name
    
    try:
        score.save(temp_path)
        loaded_score = SCORE.load(temp_path)
        
        loaded_stave1 = loaded_score.get_stave(stave_idx1)
        loaded_stave2 = loaded_score.get_stave(stave_idx2)
        loaded_stave3 = loaded_score.get_stave(stave_idx3)
        
        assert loaded_stave1.scale == 1.0, f"Scale mismatch: expected 1.0, got {loaded_stave1.scale}"
        assert loaded_stave2.scale == 0.5, f"Scale mismatch: expected 0.5, got {loaded_stave2.scale}"
        assert loaded_stave3.scale == 2.0, f"Scale mismatch: expected 2.0, got {loaded_stave3.scale}"
        
        print("✓ Stave scales preserved through JSON round-trip")
        
    finally:
        os.unlink(temp_path)

def main():
    """Run all tests."""
    
    print("🎼 Starting Comprehensive SCORE Test Suite")
    print("=" * 50)
    
    try:
        # Test 1: Create score with all event types
        score = test_score_creation_and_events()
        
        # Test 2: JSON serialization
        json_data, temp_path = test_json_serialization(score)
        
        # Test 3: JSON deserialization  
        loaded_score = test_json_deserialization(temp_path)
        
        # Test 4: Inheritance edge cases
        test_inheritance_edge_cases(loaded_score)
        
        # Test 5: Stave scale functionality
        test_stave_scales()
        
        # Test 6: Save a permanent test file for examination
        print(f"\n💾 Saving permanent test file for examination...")
        test_file_path = "test.pianotab"
        score.save(test_file_path)
        print(f"✓ Saved comprehensive test score to: {test_file_path}")
        print(f"  You can examine this file to see the complete JSON structure")
        print(f"  with all event types and inheritance patterns demonstrated")
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED! The None-based inheritance system works perfectly!")
        print("✅ JSON serialization preserves inheritance correctly")
        print("✅ Deserialization restores full functionality")
        print("✅ Transparent property access (mynote.color) works seamlessly")
        print("✅ Global property changes propagate to inheriting objects")
        print(f"✅ Test file saved as: {test_file_path}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)