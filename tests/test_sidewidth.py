#!/usr/bin/env python3
"""
Unit test for CountLine sideWidth inheritance feature.
Run with: python3 tests/test_sidewidth.py
"""

import sys
import os
import tempfile

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from file.SCORE import SCORE

def test_sidewidth_inheritance():
    """Test sideWidth inheritance from globalCountLine."""
    print("Testing sideWidth inheritance...")
    
    score = SCORE()
    score.properties.globalCountLine.sideWidth = 2.5
    
    # Test inheritance
    countline = score.new_count_line(time=100.0, pitch1=50, pitch2=70)
    assert countline.sideWidth == 2.5, f"Expected 2.5, got {countline.sideWidth}"
    assert countline.get_literal_value('sideWidth') is None, "Should inherit (None)"
    
    print("✓ sideWidth inheritance works")

def test_sidewidth_explicit():
    """Test explicit sideWidth values."""
    print("Testing explicit sideWidth values...")
    
    score = SCORE()
    score.properties.globalCountLine.sideWidth = 2.5
    
    # Test explicit value
    countline = score.new_count_line(time=100.0, pitch1=50, pitch2=70, sideWidth=3.8)
    assert countline.sideWidth == 3.8, f"Expected 3.8, got {countline.sideWidth}"
    assert countline.get_literal_value('sideWidth') == 3.8, "Should be explicit"
    
    print("✓ Explicit sideWidth works")

def test_sidewidth_global_change():
    """Test that global sideWidth changes propagate."""
    print("Testing global sideWidth change propagation...")
    
    score = SCORE()
    score.properties.globalCountLine.sideWidth = 1.5
    
    countline = score.new_count_line(time=100.0, pitch1=50, pitch2=70)
    assert countline.sideWidth == 1.5, "Initial inheritance failed"
    
    # Change global property
    score.properties.globalCountLine.sideWidth = 3.0
    assert countline.sideWidth == 3.0, "Global sideWidth change didn't propagate"
    
    print("✓ Global sideWidth changes propagate")

def test_sidewidth_json_roundtrip():
    """Test sideWidth inheritance survives JSON round-trip."""
    print("Testing sideWidth JSON round-trip...")
    
    score = SCORE()
    score.properties.globalCountLine.sideWidth = 2.2
    
    countline1 = score.new_count_line(time=100.0, pitch1=50, pitch2=70)  # Inherit
    countline2 = score.new_count_line(time=200.0, pitch1=52, pitch2=72, sideWidth=4.4)  # Explicit
    
    # Save and load
    with tempfile.NamedTemporaryFile(suffix='.pianotab', delete=False) as temp:
        temp_path = temp.name
    
    try:
        score.save(temp_path)
        loaded_score = SCORE.load(temp_path)
        
        loaded_countline1 = loaded_score.get_stave(0).event.countLine[0]
        loaded_countline2 = loaded_score.get_stave(0).event.countLine[1]
        
        # Test inheritance still works
        assert loaded_countline1.sideWidth == 2.2, "sideWidth inheritance lost"
        assert loaded_countline2.sideWidth == 4.4, "Explicit sideWidth lost"
        assert loaded_countline1.get_literal_value('sideWidth') is None, "Should still inherit"
        assert loaded_countline2.get_literal_value('sideWidth') == 4.4, "Should still be explicit"
        
        print("✓ sideWidth JSON round-trip works")
        
    finally:
        os.unlink(temp_path)

def main():
    """Run all sideWidth tests."""
    print("🧪 Running CountLine sideWidth Tests")
    print("=" * 40)
    
    try:
        test_sidewidth_inheritance()
        test_sidewidth_explicit()
        test_sidewidth_global_change()
        test_sidewidth_json_roundtrip()
        
        print("=" * 40)
        print("🎉 ALL SIDEWIDTH TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)