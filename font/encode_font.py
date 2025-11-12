#!/usr/bin/env python3
"""
Convert FiraCode-SemiBold.ttf to base64 for embedding.
Run this script to regenerate font_data.py if the font file changes.
"""
import base64
import os

def encode_font():
    """Encode font file to base64 and save to font_data.py"""
    font_path = os.path.join(os.path.dirname(__file__), 'FiraCode-SemiBold.ttf')
    
    if not os.path.exists(font_path):
        print(f"Error: {font_path} not found!")
        return
    
    # Read font file as binary
    with open(font_path, 'rb') as f:
        font_bytes = f.read()
    
    # Encode to base64
    font_b64 = base64.b64encode(font_bytes).decode('utf-8')
    
    # Write to font_data.py
    output_path = os.path.join(os.path.dirname(__file__), 'font_data.py')
    with open(output_path, 'w') as f:
        f.write('"""\n')
        f.write('Auto-generated font data for FiraCode-SemiBold.ttf\n')
        f.write('DO NOT EDIT MANUALLY!\n')
        f.write('Run encode_font.py to regenerate this file.\n')
        f.write('"""\n\n')
        f.write('FIRACODE_SEMIBOLD_B64 = """\\\n')
        
        # Split into lines of 80 characters for readability
        for i in range(0, len(font_b64), 80):
            f.write(font_b64[i:i+80] + '\n')
        
        f.write('"""\n')
    
    print(f"✓ Font encoded successfully to {output_path}")
    print(f"  Font size: {len(font_bytes):,} bytes")
    print(f"  Base64 size: {len(font_b64):,} characters")

if __name__ == '__main__':
    encode_font()
