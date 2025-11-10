#!/usr/bin/env python3
"""
Test script to verify z-order export to PDF.

This script:
1. Runs the normal PianoTab app
2. Waits for the editor to be ready
3. Exports the entire editor canvas to PDF using z-order
4. Saves the PDF to tests/output/zorder_export.pdf
5. Exits

This verifies that the z-order system works correctly for PDF export,
which is essential for print view functionality.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kivy.clock import Clock


def test_pdf_export():
    """Hook into the running app and export to PDF."""
    # Import here to get the running app instance
    from kivy.app import App
    
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
    
    # Get all items sorted by z-index
    sorted_items = sorted(
        canvas._items.items(),
        key=lambda x: x[1].get('z_index', 0)
    )
    
    print(f"\nTotal items to export: {len(sorted_items)}")
    
    if len(sorted_items) == 0:
        print("WARNING: No items to export. Editor may be empty.")
        app.stop()
        return
    
    # Group by z-index for debugging
    z_groups = {}
    for item_id, item_data in sorted_items:
        z = item_data.get('z_index', 0)
        z_groups[z] = z_groups.get(z, 0) + 1
    
    print(f"Z-index range: {min(z_groups.keys())} to {max(z_groups.keys())}")
    print(f"Unique z-indices: {len(z_groups)}")
    
    # Sample some z-indices to show distribution
    sample_z = sorted(z_groups.keys())[:10]
    print(f"\nFirst 10 z-indices and counts:")
    for z in sample_z:
        tags = set()
        count = 0
        for item_id, item_data in sorted_items:
            if item_data.get('z_index', 0) == z:
                tags.update(item_data.get('tags', set()))
                count += 1
                if count > 3:  # Limit tag collection
                    break
        print(f"  z={z}: {z_groups[z]} items, sample tags={tags}")
    
    # Create a PyMuPDF canvas with same dimensions
    from utils.pymupdfexport import PyMuPDFCanvas
    import fitz
    
    # Create PDF document directly
    doc = fitz.open()
    
    # Convert canvas size to points (72 points per inch, 25.4mm per inch)
    def mm_to_pt(mm):
        return mm * 72.0 / 25.4
    
    width_pt = mm_to_pt(canvas.width_mm)
    height_pt = mm_to_pt(canvas.height_mm)
    
    # Create page
    page = doc.new_page(width=width_pt, height=height_pt)
    
    print(f"\nPDF page size: {width_pt:.1f}pt x {height_pt:.1f}pt ({canvas.width_mm:.1f}mm x {canvas.height_mm:.1f}mm)")
    
    print("\nExporting items in z-order...")
    
    # Helper to convert colors
    def rgba_to_rgb_tuple(rgba):
        return (rgba[0], rgba[1], rgba[2])
    
    # Helper to convert mm coords to PDF points
    def coords_mm_to_pt(x_mm, y_mm):
        return (mm_to_pt(x_mm), mm_to_pt(y_mm))
    
    # Export each item in z-order
    exported_count = 0
    skipped_count = 0
    
    for item_id, item_data in sorted_items:
        item_type = item_data.get('type')
        
        try:
            if item_type == 'rectangle':
                x_pt, y_pt = coords_mm_to_pt(item_data['x_mm'], item_data['y_mm'])
                w_pt = mm_to_pt(item_data['w_mm'])
                h_pt = mm_to_pt(item_data['h_mm'])
                rect = fitz.Rect(x_pt, y_pt, x_pt + w_pt, y_pt + h_pt)
                
                if item_data['fill']:
                    color = rgba_to_rgb_tuple(item_data['fill_color'])
                    page.draw_rect(rect, color=color, fill=color)
                
                if item_data['outline']:
                    color = rgba_to_rgb_tuple(item_data['outline_color'])
                    width = mm_to_pt(item_data['outline_w_mm']) * 2.0  # Scale like PyMuPDF does
                    page.draw_rect(rect, color=color, width=width)
                
                exported_count += 1
            
            elif item_type == 'oval':
                x_pt, y_pt = coords_mm_to_pt(item_data['x_mm'], item_data['y_mm'])
                w_pt = mm_to_pt(item_data['w_mm'])
                h_pt = mm_to_pt(item_data['h_mm'])
                rect = fitz.Rect(x_pt, y_pt, x_pt + w_pt, y_pt + h_pt)
                
                if item_data['fill']:
                    color = rgba_to_rgb_tuple(item_data['fill_color'])
                    page.draw_oval(rect, color=color, fill=color)
                
                if item_data['outline']:
                    color = rgba_to_rgb_tuple(item_data['outline_color'])
                    width = mm_to_pt(item_data['outline_w_mm']) * 2.0
                    page.draw_oval(rect, color=color, width=width)
                
                exported_count += 1
            
            elif item_type == 'line':
                pts_mm = item_data['points_mm']
                p1 = coords_mm_to_pt(pts_mm[0], pts_mm[1])
                p2 = coords_mm_to_pt(pts_mm[2], pts_mm[3])
                color = rgba_to_rgb_tuple(item_data['color'])
                width = mm_to_pt(item_data['w_mm']) * 2.0
                page.draw_line(p1, p2, color=color, width=width)
                exported_count += 1
            
            elif item_type in ('path', 'polygon'):
                pts_mm = item_data['points_mm']
                points = [coords_mm_to_pt(pts_mm[i], pts_mm[i+1]) for i in range(0, len(pts_mm), 2)]
                
                if item_type == 'polygon' and item_data.get('fill'):
                    color = rgba_to_rgb_tuple(item_data['fill_color'])
                    page.draw_polygon(points, color=color, fill=color)
                
                if item_type == 'polygon' and item_data.get('outline') or item_type == 'path':
                    color_key = 'outline_color' if item_type == 'polygon' else 'color'
                    width_key = 'outline_w_mm' if item_type == 'polygon' else 'w_mm'
                    color = rgba_to_rgb_tuple(item_data[color_key])
                    width = mm_to_pt(item_data[width_key]) * 2.0
                    close = (item_type == 'polygon')
                    page.draw_polyline(points, color=color, width=width, closePath=close)
                
                exported_count += 1
            
            elif item_type == 'text':
                x_pt, y_pt = coords_mm_to_pt(item_data['x_mm'], item_data['y_mm'])
                text = item_data['text']
                font_size = item_data['font_pt']
                color = rgba_to_rgb_tuple(item_data['color'])
                
                # Simple text insertion (baseline at y_pt)
                page.insert_text((x_pt, y_pt), text, fontsize=font_size, color=color)
                exported_count += 1
            
            else:
                skipped_count += 1
                continue
            
            # Progress indicator
            if exported_count % 500 == 0:
                print(f"  Exported {exported_count}/{len(sorted_items)} items...")
                
        except Exception as e:
            print(f"  WARNING: Failed to export item {item_id} (type={item_type}): {e}")
            skipped_count += 1
    
    print(f"\nExported {exported_count} items successfully")
    if skipped_count > 0:
        print(f"Skipped {skipped_count} items")
    
    # Save PDF
    output_dir = Path(__file__).parent / 'output'
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / 'zorder_export.pdf'
    
    print(f"\nSaving PDF to: {output_file}")
    doc.save(str(output_file))
    doc.close()
    
    print("="*60)
    print(f"PDF EXPORT COMPLETE: {output_file}")
    print("="*60)
    
    # Close app
    app.stop()


# Remove the old export helper functions since we're using PyMuPDF directly now


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
