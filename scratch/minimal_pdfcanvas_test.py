#!/usr/bin/env python3
"""
Minimal PdfCanvas Test - Isolate Hanging Issue
==============================================

This is the simplest possible test to identify where the hanging occurs.
We'll add one thing at a time to find the exact cause.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from utils.drawutil_tkinter2pymupdf import PdfCanvas

def test_minimal_pdfcanvas():
    """Test the absolute minimum PdfCanvas functionality"""
    
    print("Step 1: Creating tkinter root...")
    root = tk.Tk()
    root.title("Minimal PdfCanvas Test")
    root.geometry("400x300")
    
    print("Step 2: Creating PdfCanvas...")
    # Start with PDF mode disabled to see if that's the issue
    canvas = PdfCanvas(root, width=400, height=300, pdf_mode=False)
    
    print("Step 3: Packing canvas...")
    canvas.pack()
    
    print("Step 4: Drawing simple line...")
    canvas.add_line(50, 50, 350, 50, color='#FF0000', width=2)
    
    print("Step 5: Drawing simple text...")
    canvas.add_text(200, 100, "Test Text", size=14, color='#000000', font='Arial', anchor='center')
    
    print("Step 6: Setting up auto-close...")
    def close_test():
        print("Closing test...")
        root.destroy()
    
    # Auto-close after 3 seconds
    root.after(3000, close_test)
    
    print("Step 7: Starting mainloop...")
    root.mainloop()
    
    print("Test completed successfully!")

if __name__ == "__main__":
    test_minimal_pdfcanvas()