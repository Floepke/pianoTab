'''
PyMuPDF Canvas Converter - Export Canvas to PDF with z-order support.

This module provides functionality to export any Canvas widget to a PDF document,
preserving the z-order (layering) of all drawn elements.

Features:
- Export entire Canvas to PDF in correct z-order
- Support for all Canvas primitives (lines, rectangles, ovals, polygons, paths, text)
- Dashed line support
- Multiple page support
- Programmatic drawing API similar to Canvas

Usage 1: Export existing Canvas to PDF
    from utils.pymupdf_converter import export_canvas_to_pdf
    
    # Export canvas to single-page PDF
    export_canvas_to_pdf(canvas, 'output.pdf')
    
    # Export with custom page configuration
    export_canvas_to_pdf(
        canvas, 
        'output.pdf',
        page_width_mm=210.0,   # A4 width
        page_height_mm=297.0,  # A4 height
    )

Usage 2: Programmatic multi-page PDF creation
    from utils.pymupdf_converter import PDFBuilder
    
    # Create PDF builder
    pdf = PDFBuilder()
    
    # Add first page and draw
    pdf.new_page(width_mm=210.0, height_mm=297.0)
    pdf.add_line(10, 10, 100, 10, color='#000000', width_mm=0.5)
    pdf.add_rectangle(10, 20, 60, 50, outline_color='#FF0000')
    pdf.add_text('Hello PDF', 10, 70, font_size_pt=12)
    
    # Add second page
    pdf.new_page(width_mm=210.0, height_mm=297.0)
    pdf.add_oval(50, 50, 100, 100, fill=True, fill_color='#0000FF')
    
    # Save
    pdf.save('output.pdf')
    pdf.close()

Usage 3: Export Canvas to specific page in existing PDF
    from utils.pymupdf_converter import PDFBuilder
    
    pdf = PDFBuilder()
    
    # Page 1: Custom drawing
    pdf.new_page(width_mm=210.0, height_mm=297.0)
    pdf.add_text('Cover Page', 105, 148.5, font_size_pt=24)
    
    # Page 2: Export canvas content
    pdf.new_page_from_canvas(canvas)
    
    pdf.save('output.pdf')
    pdf.close()
'''
from __future__ import annotations
from typing import Optional, Tuple, List, Any
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

from utils.canvas import Canvas


def _mm_to_pt(mm: float) -> float:
    """Convert millimeters to PDF points (72 points per inch)."""
    return float(mm) * 72.0 / 25.4


def _rgba_to_rgb(rgba: Tuple[float, float, float, float]) -> Tuple[float, float, float]:
    """Convert RGBA tuple to RGB tuple (drop alpha channel)."""
    return (rgba[0], rgba[1], rgba[2])


class PDFBuilder:
    """
    Programmatic PDF builder with Canvas-like drawing API.
    
    Allows creating multi-page PDFs with direct drawing commands
    or by exporting existing Canvas widgets.
    """
    
    def __init__(self):
        """Initialize PDF builder with empty document."""
        if fitz is None:
            raise ImportError("PyMuPDF (fitz) is required for PDF export")
        
        self._doc = fitz.open()  # Create empty PDF
        self._current_page = None
        self._current_width_mm = 210.0  # A4 default
        self._current_height_mm = 297.0
    
    def new_page(self, width_mm: float = 210.0, height_mm: float = 297.0) -> Any:
        """
        Create a new blank page in the PDF.
        
        Args:
            width_mm: Page width in millimeters (default: 210 = A4 width)
            height_mm: Page height in millimeters (default: 297 = A4 height)
            
        Returns:
            The created PyMuPDF Page object
        """
        self._current_width_mm = width_mm
        self._current_height_mm = height_mm
        
        width_pt = _mm_to_pt(width_mm)
        height_pt = _mm_to_pt(height_mm)
        
        self._current_page = self._doc.new_page(width=width_pt, height=height_pt)
        
        # Add white background
        shape = self._current_page.new_shape()
        rect = fitz.Rect(0, 0, width_pt, height_pt)
        shape.draw_rect(rect)
        shape.finish(fill=(1.0, 1.0, 1.0))  # White fill
        shape.commit()
        
        return self._current_page
    
    def new_page_from_canvas(self, canvas: Canvas) -> Any:
        """
        Create a new page and export all Canvas items to it in z-order.
        
        Args:
            canvas: Canvas widget to export
            
        Returns:
            The created PyMuPDF Page object
        """
        # Create page matching canvas size
        page = self.new_page(width_mm=canvas.width_mm, height_mm=canvas.height_mm)
        
        # Export canvas items in z-order
        _export_canvas_items_to_page(canvas, page)
        
        return page
    
    def save(self, filepath: str) -> str:
        """
        Save the PDF to a file.
        
        Args:
            filepath: Path to save PDF file
            
        Returns:
            The filepath that was saved
        """
        self._doc.save(filepath)
        return filepath
    
    def close(self):
        """Close the PDF document and free resources."""
        if self._doc is not None:
            self._doc.close()
            self._doc = None
            self._current_page = None
    
    # Canvas-like drawing API (draws on current page)
    
    def add_line(
        self, 
        x1_mm: float, 
        y1_mm: float, 
        x2_mm: float, 
        y2_mm: float, 
        *,
        color: str = '#000000',
        width_mm: float = 0.25,
        dash: bool = False,
        dash_pattern_mm: Tuple[float, float] = (2.0, 2.0)
    ):
        """Draw a line on the current page."""
        if self._current_page is None:
            raise RuntimeError("No page created. Call new_page() first.")
        
        p1 = (_mm_to_pt(x1_mm), _mm_to_pt(y1_mm))
        p2 = (_mm_to_pt(x2_mm), _mm_to_pt(y2_mm))
        color_rgb = Canvas._parse_color(color)[:3]
        width_pt = _mm_to_pt(width_mm) * 2.0
        
        if dash:
            dashes = f"[{_mm_to_pt(dash_pattern_mm[0])} {_mm_to_pt(dash_pattern_mm[1])}] 0"
            self._current_page.draw_line(p1, p2, color=color_rgb, width=width_pt, dashes=dashes)
        else:
            self._current_page.draw_line(p1, p2, color=color_rgb, width=width_pt)
    
    def add_rectangle(
        self,
        x1_mm: float,
        y1_mm: float,
        x2_mm: float,
        y2_mm: float,
        *,
        fill: bool = False,
        fill_color: str = '#000000',
        outline: bool = True,
        outline_color: str = '#000000',
        outline_width_mm: float = 0.25
    ):
        """Draw a rectangle on the current page."""
        if self._current_page is None:
            raise RuntimeError("No page created. Call new_page() first.")
        
        x_pt = _mm_to_pt(min(x1_mm, x2_mm))
        y_pt = _mm_to_pt(min(y1_mm, y2_mm))
        w_pt = _mm_to_pt(abs(x2_mm - x1_mm))
        h_pt = _mm_to_pt(abs(y2_mm - y1_mm))
        rect = fitz.Rect(x_pt, y_pt, x_pt + w_pt, y_pt + h_pt)
        
        if fill:
            color_rgb = Canvas._parse_color(fill_color)[:3]
            self._current_page.draw_rect(rect, color=color_rgb, fill=color_rgb)
        
        if outline:
            color_rgb = Canvas._parse_color(outline_color)[:3]
            width_pt = _mm_to_pt(outline_width_mm) * 2.0
            self._current_page.draw_rect(rect, color=color_rgb, width=width_pt)
    
    def add_oval(
        self,
        x1_mm: float,
        y1_mm: float,
        x2_mm: float,
        y2_mm: float,
        *,
        fill: bool = False,
        fill_color: str = '#000000',
        outline: bool = True,
        outline_color: str = '#000000',
        outline_width_mm: float = 0.25
    ):
        """Draw an oval on the current page."""
        if self._current_page is None:
            raise RuntimeError("No page created. Call new_page() first.")
        
        x_pt = _mm_to_pt(min(x1_mm, x2_mm))
        y_pt = _mm_to_pt(min(y1_mm, y2_mm))
        w_pt = _mm_to_pt(abs(x2_mm - x1_mm))
        h_pt = _mm_to_pt(abs(y2_mm - y1_mm))
        rect = fitz.Rect(x_pt, y_pt, x_pt + w_pt, y_pt + h_pt)
        
        if fill:
            color_rgb = Canvas._parse_color(fill_color)[:3]
            self._current_page.draw_oval(rect, color=color_rgb, fill=color_rgb)
        
        if outline:
            color_rgb = Canvas._parse_color(outline_color)[:3]
            width_pt = _mm_to_pt(outline_width_mm) * 2.0
            self._current_page.draw_oval(rect, color=color_rgb, width=width_pt)
    
    def add_polygon(
        self,
        points_mm: List[float],
        *,
        fill: bool = False,
        fill_color: str = '#000000',
        outline: bool = True,
        outline_color: str = '#000000',
        outline_width_mm: float = 0.25
    ):
        """Draw a polygon on the current page."""
        if self._current_page is None:
            raise RuntimeError("No page created. Call new_page() first.")
        
        points = [(_mm_to_pt(points_mm[i]), _mm_to_pt(points_mm[i+1])) 
                  for i in range(0, len(points_mm), 2)]
        
        if fill:
            fill_rgb = Canvas._parse_color(fill_color)[:3]
            shape = self._current_page.new_shape()
            shape.draw_polyline(points)
            shape.finish(fill=fill_rgb, color=None, closePath=True)
            shape.commit()
        
        if outline:
            outline_rgb = Canvas._parse_color(outline_color)[:3]
            width_pt = _mm_to_pt(outline_width_mm) * 2.0
            self._current_page.draw_polyline(points, color=outline_rgb, width=width_pt, closePath=True)
    
    def add_polyline(
        self,
        points_mm: List[float],
        *,
        color: str = '#000000',
        width_mm: float = 0.25,
        dash: bool = False,
        dash_pattern_mm: Tuple[float, float] = (2.0, 2.0)
    ):
        """Draw a polyline (path) on the current page."""
        if self._current_page is None:
            raise RuntimeError("No page created. Call new_page() first.")
        
        points = [(_mm_to_pt(points_mm[i]), _mm_to_pt(points_mm[i+1])) 
                  for i in range(0, len(points_mm), 2)]
        color_rgb = Canvas._parse_color(color)[:3]
        width_pt = _mm_to_pt(width_mm) * 2.0
        
        if dash:
            dashes = f"[{_mm_to_pt(dash_pattern_mm[0])} {_mm_to_pt(dash_pattern_mm[1])}] 0"
            self._current_page.draw_polyline(points, color=color_rgb, width=width_pt, dashes=dashes)
        else:
            self._current_page.draw_polyline(points, color=color_rgb, width=width_pt)
    
    def add_text(
        self,
        text: str,
        x_mm: float,
        y_mm: float,
        font_size_pt: float,
        *,
        color: str = '#000000'
    ):
        """Draw text on the current page."""
        if self._current_page is None:
            raise RuntimeError("No page created. Call new_page() first.")
        
        x_pt = _mm_to_pt(x_mm)
        y_pt = _mm_to_pt(y_mm)
        color_rgb = Canvas._parse_color(color)[:3]
        
        self._current_page.insert_text((x_pt, y_pt), text, fontsize=font_size_pt, color=color_rgb)
    
    def __enter__(self):
        """Context manager support."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.close()


def export_canvas_to_pdf(
    canvas: Canvas,
    filepath: str,
    *,
    page_width_mm: Optional[float] = None,
    page_height_mm: Optional[float] = None
) -> str:
    """
    Export a Canvas widget to a PDF file in z-order.
    
    All canvas items are exported to a single PDF page, preserving
    their layering order (z-index).
    
    Args:
        canvas: Canvas widget to export
        filepath: Path to save PDF file
        page_width_mm: Optional custom page width (default: use canvas width)
        page_height_mm: Optional custom page height (default: use canvas height)
        
    Returns:
        The filepath that was saved
        
    Example:
        from utils.pymupdf_converter import export_canvas_to_pdf
        
        # Export canvas to PDF
        export_canvas_to_pdf(editor.canvas, 'score.pdf')
    """
    if fitz is None:
        raise ImportError("PyMuPDF (fitz) is required for PDF export")
    
    # Use canvas dimensions if not specified
    width_mm = page_width_mm if page_width_mm is not None else canvas.width_mm
    height_mm = page_height_mm if page_height_mm is not None else canvas.height_mm
    
    # Create PDF with single page
    with PDFBuilder() as pdf:
        pdf.new_page(width_mm=width_mm, height_mm=height_mm)
        _export_canvas_items_to_page(canvas, pdf._current_page)
        pdf.save(filepath)
    
    return filepath


def _export_canvas_items_to_page(canvas: Canvas, page: Any):
    """
    Export all Canvas items to a PyMuPDF page in z-order.
    
    Args:
        canvas: Canvas widget containing items to export
        page: PyMuPDF Page object to draw on
    """
    # Get all items sorted by z-index
    sorted_items = sorted(
        canvas._items.items(),
        key=lambda x: x[1].get('z_index', 0)
    )
    
    # Export each item in z-order
    for item_id, item_data in sorted_items:
        item_type = item_data.get('type')
        
        try:
            if item_type == 'rectangle':
                _export_rectangle(page, item_data)
            elif item_type == 'oval':
                _export_oval(page, item_data)
            elif item_type == 'line':
                _export_line(page, item_data)
            elif item_type == 'path':
                _export_path(page, item_data)
            elif item_type == 'polygon':
                _export_polygon(page, item_data)
            elif item_type == 'text':
                _export_text(page, item_data)
        except Exception as e:
            # Log warning but continue exporting other items
            print(f"Warning: Failed to export {item_type} item {item_id}: {e}")


def _export_rectangle(page: Any, item: dict):
    """Export a rectangle to PDF page."""
    x_pt = _mm_to_pt(item['x_mm'])
    y_pt = _mm_to_pt(item['y_mm'])
    w_pt = _mm_to_pt(item['w_mm'])
    h_pt = _mm_to_pt(item['h_mm'])
    rect = fitz.Rect(x_pt, y_pt, x_pt + w_pt, y_pt + h_pt)
    
    if item['fill']:
        color = _rgba_to_rgb(item['fill_color'])
        page.draw_rect(rect, color=color, fill=color)
    
    if item['outline']:
        color = _rgba_to_rgb(item['outline_color'])
        width = _mm_to_pt(item['outline_w_mm']) * 2.0
        page.draw_rect(rect, color=color, width=width)


def _export_oval(page: Any, item: dict):
    """Export an oval to PDF page."""
    x_pt = _mm_to_pt(item['x_mm'])
    y_pt = _mm_to_pt(item['y_mm'])
    w_pt = _mm_to_pt(item['w_mm'])
    h_pt = _mm_to_pt(item['h_mm'])
    rect = fitz.Rect(x_pt, y_pt, x_pt + w_pt, y_pt + h_pt)
    
    if item['fill']:
        color = _rgba_to_rgb(item['fill_color'])
        page.draw_oval(rect, color=color, fill=color)
    
    if item['outline']:
        color = _rgba_to_rgb(item['outline_color'])
        width = _mm_to_pt(item['outline_w_mm']) * 2.0
        page.draw_oval(rect, color=color, width=width)


def _export_line(page: Any, item: dict):
    """Export a line to PDF page."""
    pts_mm = item['points_mm']
    p1 = (_mm_to_pt(pts_mm[0]), _mm_to_pt(pts_mm[1]))
    p2 = (_mm_to_pt(pts_mm[2]), _mm_to_pt(pts_mm[3]))
    color = _rgba_to_rgb(item['color'])
    width = _mm_to_pt(item['w_mm']) * 2.0
    
    if item.get('dash', False):
        dash_pattern = item.get('dash_mm', (2.0, 2.0))
        dashes = f"[{_mm_to_pt(dash_pattern[0])} {_mm_to_pt(dash_pattern[1])}] 0"
        page.draw_line(p1, p2, color=color, width=width, dashes=dashes)
    else:
        page.draw_line(p1, p2, color=color, width=width)


def _export_path(page: Any, item: dict):
    """Export a polyline to PDF page."""
    pts_mm = item['points_mm']
    points = [(_mm_to_pt(pts_mm[i]), _mm_to_pt(pts_mm[i+1])) 
              for i in range(0, len(pts_mm), 2)]
    color = _rgba_to_rgb(item['color'])
    width = _mm_to_pt(item['w_mm']) * 2.0
    
    if item.get('dash', False):
        dash_pattern = item.get('dash_mm', (2.0, 2.0))
        dashes = f"[{_mm_to_pt(dash_pattern[0])} {_mm_to_pt(dash_pattern[1])}] 0"
        page.draw_polyline(points, color=color, width=width, dashes=dashes)
    else:
        page.draw_polyline(points, color=color, width=width)


def _export_polygon(page: Any, item: dict):
    """Export a polygon to PDF page."""
    pts_mm = item['points_mm']
    points = [(_mm_to_pt(pts_mm[i]), _mm_to_pt(pts_mm[i+1])) 
              for i in range(0, len(pts_mm), 2)]
    
    if item.get('fill'):
        fill_color = _rgba_to_rgb(item['fill_color'])
        shape = page.new_shape()
        shape.draw_polyline(points)
        shape.finish(fill=fill_color, color=None, closePath=True)
        shape.commit()
    
    if item.get('outline'):
        outline_color = _rgba_to_rgb(item['outline_color'])
        width = _mm_to_pt(item['outline_w_mm']) * 2.0
        page.draw_polyline(points, color=outline_color, width=width, closePath=True)


def _export_text(page: Any, item: dict):
    """Export text to PDF page."""
    x_pt = _mm_to_pt(item['x_mm'])
    y_pt = _mm_to_pt(item['y_mm'])
    text = item['text']
    font_size = item['font_pt']
    color = _rgba_to_rgb(item['color'])
    
    # Simple text insertion (baseline at y_pt)
    page.insert_text((x_pt, y_pt), text, fontsize=font_size, color=color)
