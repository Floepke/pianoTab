#!/usr/bin/env python3
"""
Test script to verify z-order export to PDF using pymupdf_converter.

This script:
1. Runs the normal PianoTab app
2. Waits for the editor to be ready (2 seconds)
3. Exports the editor canvas to PDF in z-order using the converter library
4. Saves to tests/output/zorder_export.pdf
5. Exits

This verifies that the z-order system works correctly for PDF export,
which is essential for print view functionality.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kivy.clock import Clock


def test_pdf_export():
    """Hook into the running app and export to PDF."""
    # Import here to get the running app instance
    from kivy.app import App
    from utils.pymupdf_converter import export_canvas_to_pdf
    
    app = App.get_running_app()
    if not app:
        print("ERROR: No running app found")
        return
    
    # Get the main GUI
    main_gui = app.root
    if not hasattr(main_gui, 'get_editor_widget'):
        print("ERROR: No get_editor_widget method in main GUI")
        app.stop()
        return
    
    # Get the custom Canvas widget directly from GUI
    canvas = main_gui.get_editor_widget()
    
    if not hasattr(canvas, '_items'):
        print("ERROR: Canvas doesn't have _items attribute (not our custom Canvas)")
        app.stop()
        return
    
    print("\n" + "="*60)
    print("EXPORTING EDITOR CANVAS TO PDF WITH Z-ORDER")
    print("="*60)
    
    # Get item count and z-index info
    total_items = len(canvas._items)
    print(f"\nTotal items to export: {total_items}")
    
    if total_items == 0:
        print("WARNING: No items to export. Editor may be empty.")
        app.stop()
        return
    
    # Show z-index statistics
    z_indices = [item.get('z_index', 0) for item in canvas._items.values()]
    print(f"Z-index range: {min(z_indices)} to {max(z_indices)}")
    print(f"Unique z-indices: {len(set(z_indices))}")
    
    # Export canvas to PDF using the converter library
    output_dir = Path(__file__).parent / 'output'
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / 'zorder_export.pdf'
    
    print(f"\nExporting to PDF: {output_file}")
    print(f"Canvas size: {canvas.width_mm:.1f}mm x {canvas.height_mm:.1f}mm")
    
    try:
        export_canvas_to_pdf(canvas, str(output_file))
        print("\n" + "="*60)
        print(f"PDF EXPORT COMPLETE: {output_file}")
        print("="*60)
    except Exception as e:
        print(f"\nERROR: PDF export failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Close app
    app.stop()


if __name__ == '__main__':
    print("="*60)
    print("PDF EXPORT Z-ORDER TEST")
    print("="*60)
    print("\nThis test will:")
    print("1. Run the normal PianoTab app")
    print("2. Wait for the editor to be ready (2 seconds)")
    print("3. Export the editor canvas to PDF in z-order")
    print("4. Save to tests/output/zorder_export.pdf")
    print("5. Exit the app")
    print("")
    
    # Import and run the main app
    import pianotab
    
    # Schedule the PDF export after app starts
    Clock.schedule_once(lambda dt: test_pdf_export(), 2.0)
    
    # Run the app
    pianotab.pianoTAB().run()
