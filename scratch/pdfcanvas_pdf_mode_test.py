#!/usr/bin/env python3
"""
PdfCanvas Test with PDF Mode Enabled
====================================

Test if the hanging happens when PDF mode is enabled.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from utils.drawutil_tkinter2pymupdf import PdfCanvas

def test_pdfcanvas_with_pdf_mode():
    """Test PdfCanvas with PDF mode enabled"""
    
    print("Step 1: Creating tkinter root...")
    root = tk.Tk()
    root.title("PdfCanvas Test - PDF Mode ON")
    root.geometry("400x300")
    
    print("Step 2: Creating PdfCanvas with pdf_mode=True...")
    canvas = PdfCanvas(root, width=400, height=300, pdf_mode=True)
    
    print("Step 3: Packing canvas...")
    canvas.pack()
    
    print("Step 4: Drawing simple line...")
    canvas.add_line(50, 50, 350, 50, color='#FF0000', width=2)
    
    print("Step 5: Drawing simple text...")
    canvas.add_text(200, 100, "Test Text", size=14, color='#000000', font='Arial', anchor='center')
    
    print("Step 6: Setting up auto-close...")
    def close_test():
        print("Closing test...")
        canvas.save_pdf("scratch/test_output.pdf")
        print("PDF saved!")
        root.destroy()
    
    # Auto-close after 3 seconds
    root.after(3000, close_test)
    
    print("Step 7: Starting mainloop...")
    root.mainloop()
    
    print("Test completed successfully!")

if __name__ == "__main__":
    test_pdfcanvas_with_pdf_mode()