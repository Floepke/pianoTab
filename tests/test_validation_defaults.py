#!/usr/bin/env python3
"""
Test validation and default-filling functionality.
Creates a JSON file with missing fields, then loads it to verify defaults are applied.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from file.SCORE import SCORE
import json

print("=== Testing Validation and Default Filling ===\n")

# 1. Create a complete score
print("1. Creating complete score...")
s = SCORE()
s.new_note(time=0, pitch=60, velocity=100, duration=512)
s.new_grace_note(time=0, pitch=72, velocity=80)
s.new_text(time=0, text="Test")
s.save('tests/test_complete.pianotab')
print("   ✓ Saved complete score\n")

# 2. Load and manually remove some fields to simulate old file format
print("2. Creating incomplete JSON (simulating old file format)...")
with open('tests/test_complete.pianotab', 'r') as f:
    data = json.load(f)

# Remove some fields from a note
note = data['stave'][0]['event']['note'][0]
original_dur = note.pop('dur', None)  # Remove duration (should get default 256.0)
original_vel = note.pop('vel', None)  # Remove velocity (should get default 80)
print(f"   Removed 'dur' (was: {original_dur})")
print(f"   Removed 'vel' (was: {original_vel})")

# Remove field from text
text = data['stave'][0]['event']['text'][0]
original_fonSz = text.pop('fonSz', None)  # Remove fontSize
print(f"   Removed 'fonSz' (was: {original_fonSz})")

# Remove field from graceNote
grace = data['stave'][0]['event']['graceNote'][0]
original_gn_vel = grace.pop('vel', None)
print(f"   Removed graceNote 'vel' (was: {original_gn_vel})")

# Save the incomplete JSON
with open('tests/test_incomplete.pianotab', 'w') as f:
    json.dump(data, f, indent=2)
print("   ✓ Saved incomplete JSON\n")

# 3. Load the incomplete file - should trigger validation
print("3. Loading incomplete file (validation should trigger)...\n")
loaded = SCORE.load('tests/test_incomplete.pianotab')

# 4. Verify defaults were applied
print("\n4. Verifying defaults were applied correctly...")
loaded_note = loaded.stave[0].event.note[0]
loaded_text = loaded.stave[0].event.text[0]
loaded_grace = loaded.stave[0].event.graceNote[0]

# Check note fields
assert loaded_note.duration == 256.0, f"Expected default duration 256.0, got {loaded_note.duration}"
print(f"   ✓ Note duration defaulted to: {loaded_note.duration}")

assert loaded_note.velocity == 80, f"Expected default velocity 80, got {loaded_note.velocity}"
print(f"   ✓ Note velocity defaulted to: {loaded_note.velocity}")

# Check text fontSize
assert loaded_text.fontSize == 12, f"Expected default fontSize 12, got {loaded_text.fontSize}"
print(f"   ✓ Text fontSize defaulted to: {loaded_text.fontSize}")

# Check graceNote velocity
assert loaded_grace.velocity == 80, f"Expected default graceNote velocity 80, got {loaded_grace.velocity}"
print(f"   ✓ GraceNote velocity defaulted to: {loaded_grace.velocity}")

# Verify that existing fields weren't changed
assert loaded_note.pitch == 60, f"Pitch should still be 60, got {loaded_note.pitch}"
print(f"   ✓ Existing fields unchanged (pitch={loaded_note.pitch})")

print("\n=== All Tests Passed! ===")
print("\nThe validation system successfully:")
print("  • Detected missing fields")
print("  • Filled in correct defaults from code")
print("  • Preserved existing values")
print("  • Provided helpful warnings")
