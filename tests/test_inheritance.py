#!/usr/bin/env python3
"""
Simple unit tests for the None-based inheritance system.
Run with: python3 tests/test_inheritance.py
"""

import sys
import os
import tempfile

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from file.SCORE import SCORE

def test_note_inheritance():
    """Test note color inheritance."""
    print("Testing note inheritance...")
    
    score = SCORE()
    score.properties.globalNote.color = "#FF0000"
    
    # Test inheritance
    note1 = score.new_note(time=0.0, pitch=60)
    assert note1.color == "#FF0000", f"Expected #FF0000, got {note1.color}"
    assert note1.get_literal_value('color') is None, "Should inherit (None)"
    
    # Test explicit value
    note2 = score.new_note(time=256.0, pitch=64, color="#0000FF")
    assert note2.color == "#0000FF", f"Expected #0000FF, got {note2.color}"
    assert note2.get_literal_value('color') == "#0000FF", "Should be explicit"
    
    print("✓ Note inheritance works")

def test_text_inheritance():
    """Test text color and fontSize inheritance."""
    print("Testing text inheritance...")
    
    score = SCORE()
    score.properties.globalText.color = "#00FF00"
    score.properties.globalText.fontSize = 16
    
    # Test inheritance
    text1 = score.new_text(time=0.0, text="Test")
    assert text1.color == "#00FF00", f"Expected #00FF00, got {text1.color}"
    assert text1.fontSize == 16, f"Expected 16, got {text1.fontSize}"
    assert text1.get_literal_value('color') is None, "Color should inherit"
    assert text1.get_literal_value('fontSize') is None, "FontSize should inherit"
    
    print("✓ Text inheritance works")

def test_json_roundtrip():
    """Test JSON save/load preserves inheritance."""
    print("Testing JSON round-trip...")
    
    score = SCORE()
    score.properties.globalNote.color = "#FF0000"
    score.properties.globalText.color = "#00FF00"
    
    note = score.new_note(time=0.0, pitch=60)
    text = score.new_text(time=100.0, text="Test")
    
    # Save and load
    with tempfile.NamedTemporaryFile(suffix='.pianotab', delete=False) as temp:
        temp_path = temp.name
    
    try:
        score.save(temp_path)
        loaded_score = SCORE.load(temp_path)
        
        loaded_note = loaded_score.get_stave(0).event.note[0]
        loaded_text = loaded_score.get_stave(0).event.text[0]
        
        # Test inheritance still works
        assert loaded_note.color == "#FF0000", "Note color inheritance lost"
        assert loaded_text.color == "#00FF00", "Text color inheritance lost"
        assert loaded_note.get_literal_value('color') is None, "Note should still inherit"
        assert loaded_text.get_literal_value('color') is None, "Text should still inherit"
        
        print("✓ JSON round-trip preserves inheritance")
        
    finally:
        os.unlink(temp_path)

def test_global_property_changes():
    """Test that global property changes propagate."""
    print("Testing global property change propagation...")
    
    score = SCORE()
    score.properties.globalNote.color = "#FF0000"
    
    note = score.new_note(time=0.0, pitch=60)
    assert note.color == "#FF0000", "Initial inheritance failed"
    
    # Change global property
    score.properties.globalNote.color = "#00FF00"
    assert note.color == "#00FF00", "Global property change didn't propagate"
    
    print("✓ Global property changes propagate")

def main():
    """Run all tests."""
    print("🧪 Running Inheritance Unit Tests")
    print("=" * 40)
    
    try:
        test_note_inheritance()
        test_text_inheritance()
        test_json_roundtrip()
        test_global_property_changes()
        
        print("=" * 40)
        print("🎉 ALL TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)