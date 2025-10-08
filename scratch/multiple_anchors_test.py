#!/usr/bin/env python3
"""
PdfCanvas Test with Multiple Anchors
====================================

Test if the hanging happens with multiple text anchor operations.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from utils.drawutil_tkinter2pymupdf import PdfCanvas

def test_multiple_anchors():
    """Test multiple text anchors to see if that causes hanging"""
    
    print("Step 1: Creating tkinter root...")
    root = tk.Tk()
    root.title("Multiple Anchors Test")
    root.geometry("600x500")
    
    print("Step 2: Creating PdfCanvas...")
    canvas = PdfCanvas(root, width=600, height=500, pdf_mode=True)
    canvas.pack()
    
    print("Step 3: Testing different anchors...")
    
    # Test positions
    test_positions = [
        (150, 150, 'nw', 'NW'),
        (300, 150, 'center', 'CENTER'), 
        (450, 150, 'ne', 'NE'),
        (150, 250, 'w', 'W'),
        (300, 250, 'center', 'CENTER'),
        (450, 250, 'e', 'E'),
        (150, 350, 'sw', 'SW'),
        (300, 350, 's', 'S'),
        (450, 350, 'se', 'SE')
    ]
    
    for i, (x, y, anchor, label) in enumerate(test_positions):
        print(f"Step {4+i}: Drawing text with anchor '{anchor}' at ({x}, {y})...")
        
        # Draw crosshair
        canvas.add_line(x-10, y, x+10, y, color='#FF0000', width=1)
        canvas.add_line(x, y-10, x, y+10, color='#FF0000', width=1)
        
        # Draw text with anchor
        canvas.add_text(x, y, label, size=12, color='#0000FF', font='Courier New', anchor=anchor)
    
    print("Step 13: Setting up auto-close...")
    def close_test():
        print("Saving PDF...")
        canvas.save_pdf("scratch/multiple_anchors_test.pdf")
        print("PDF saved!")
        root.destroy()
    
    # Auto-close after 5 seconds (more time to see the result)
    root.after(5000, close_test)
    
    print("Step 14: Starting mainloop...")
    root.mainloop()
    
    print("Test completed successfully!")

if __name__ == "__main__":
    test_multiple_anchors()