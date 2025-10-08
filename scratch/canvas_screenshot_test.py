#!/usr/bin/env python3
"""
Canvas Screenshot Test
======================

Creates both a tkinter canvas screenshot and PDF for direct comparison.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from utils.drawutil_tkinter2pymupdf import PdfCanvas
from PIL import Image, ImageDraw, ImageFont
import io

def test_canvas_screenshot():
    """Test that captures tkinter canvas as image and creates matching PDF"""
    
    print("Creating canvas screenshot test...")
    
    root = tk.Tk()
    root.title("Canvas Screenshot Test")
    root.geometry("600x500")
    
    # Create PdfCanvas
    canvas = PdfCanvas(root, width=600, height=500, pdf_mode=True)
    canvas.pack()
    
    # Test positions (fixed the duplicate center issue)
    test_positions = [
        (150, 150, 'nw', 'NW'),
        (300, 150, 'n', 'N'),        # Fixed: was 'center', now 'n' 
        (450, 150, 'ne', 'NE'),
        (150, 250, 'w', 'W'),
        (300, 250, 'center', 'CENTER'),
        (450, 250, 'e', 'E'),
        (150, 350, 'sw', 'SW'),
        (300, 350, 's', 'S'),
        (450, 350, 'se', 'SE')
    ]
    
    print("Drawing test elements...")
    
    for x, y, anchor, label in test_positions:
        # Draw crosshair
        canvas.add_line(x-10, y, x+10, y, color='#FF0000', width=1)
        canvas.add_line(x, y-10, x, y+10, color='#FF0000', width=1)
        
        # Draw text with anchor
        canvas.add_text(x, y, label, size=12, color='#0000FF', font='Courier New', anchor=anchor)
    
    # Add title
    canvas.add_text(300, 50, "Anchor Positioning Test", size=16, color='#000000', font='Courier New', anchor='center')
    
    # Add grid lines for reference
    for i in range(0, 601, 50):
        canvas.add_line(i, 0, i, 500, color='#CCCCCC', width=1, dash_pattern="2 3")
    for i in range(0, 501, 50):
        canvas.add_line(0, i, 600, i, color='#CCCCCC', width=1, dash_pattern="2 3")
    
    def capture_and_save():
        print("Capturing tkinter canvas...")
        
        # Method 1: Use tkinter's built-in PostScript export and convert
        try:
            canvas.postscript(file="scratch/tkinter_canvas.ps")
            print("PostScript saved: scratch/tkinter_canvas.ps")
        except Exception as e:
            print(f"PostScript failed: {e}")
        
        # Method 2: Try to capture canvas area (this might not work on all systems)
        try:
            # Get canvas position on screen
            x = root.winfo_rootx() + canvas.winfo_x()
            y = root.winfo_rooty() + canvas.winfo_y()
            width = canvas.winfo_width()
            height = canvas.winfo_height()
            
            print(f"Canvas position: {x}, {y}, size: {width}x{height}")
            
            # Try to use PIL to capture screen (requires pillow and might need permissions)
            import PIL.ImageGrab as ImageGrab
            screenshot = ImageGrab.grab(bbox=(x, y, x+width, y+height))
            screenshot.save("scratch/tkinter_screenshot.png")
            print("Screenshot saved: scratch/tkinter_screenshot.png")
            
        except Exception as e:
            print(f"Screenshot capture failed: {e}")
            print("You may need to grant screen recording permissions to Terminal/Python")
        
        # Save PDF version
        print("Saving PDF version...")
        canvas.save_pdf("scratch/pdf_version.pdf")
        
        print("Closing window...")
        root.destroy()
    
    # Give time to see the window, then capture
    root.after(3000, capture_and_save)
    
    print("Showing window for 3 seconds before capture...")
    root.mainloop()
    
    print("Test completed!")
    print("Files created:")
    print("- scratch/tkinter_canvas.ps (PostScript from tkinter)")
    print("- scratch/tkinter_screenshot.png (if screen capture worked)")
    print("- scratch/pdf_version.pdf (PDF version)")

if __name__ == "__main__":
    test_canvas_screenshot()