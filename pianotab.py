import tkinter as tk
from fpdf import FPDF

class PdfCanvas(tk.Canvas):
    def __init__(self, parent, width=800, height=600, **kwargs):
        # Set default background if not provided
        if 'bg' not in kwargs:
            kwargs['bg'] = 'white'
        
        # Initialize tkinter Canvas
        super().__init__(parent, width=width, height=height, **kwargs)
        
        # PDF setup
        self.pdf_width = width
        self.pdf_height = height
        self.pdf = FPDF(unit='pt', format=(width, height))
        self.pdf.add_page()
        
        # Drawing state
        self.current_color = (0, 0, 0)  # RGB 0-1 range
        self.current_line_width = 1
    
    def set_color(self, color):
        """Set drawing color for both canvas and PDF"""
        self.current_color = self._parse_color(color)
        return self
    
    def set_line_width(self, width):
        """Set line width for both canvas and PDF"""
        self.current_line_width = width
        self.pdf.set_line_width(width)
        return self
    
    def draw_line(self, x1, y1, x2, y2, color=None, width=None):
        """Draw line on both tkinter canvas and PDF"""
        # Use provided color/width or current state
        if color is not None:
            self.set_color(color)
        if width is not None:
            self.set_line_width(width)
        
        # Draw on tkinter canvas
        tk_color = self._rgb_to_hex(self.current_color)
        self.create_line(x1, y1, x2, y2, fill=tk_color, width=self.current_line_width)
        
        # Draw on PDF
        self.pdf.set_draw_color(*[int(c * 255) for c in self.current_color])
        self.pdf.set_line_width(self.current_line_width)
        self.pdf.line(x1, y1, x2, y2)
        
        return self
    
    def draw_oval(self, x, y, width, height, color=None, fill=True, outline_width=None):
        """Draw oval/circle on both tkinter canvas and PDF"""
        if color is not None:
            self.set_color(color)
        if outline_width is not None:
            self.set_line_width(outline_width)
        
        # Draw on tkinter canvas
        tk_color = self._rgb_to_hex(self.current_color)
        if fill:
            self.create_oval(x, y, x + width, y + height, 
                           fill=tk_color, outline=tk_color, width=self.current_line_width)
        else:
            self.create_oval(x, y, x + width, y + height, 
                           outline=tk_color, fill='', width=self.current_line_width)
        
        # Draw on PDF - FIXED: fpdf2 ellipse uses different coordinate system
        self.pdf.set_draw_color(*[int(c * 255) for c in self.current_color])
        if fill:
            self.pdf.set_fill_color(*[int(c * 255) for c in self.current_color])
        
        # fpdf2 ellipse expects: center_x, center_y, radius_x, radius_y
        # But we need to match tkinter's coordinate system
        center_x = x + width/2
        center_y = y + height/2
        radius_x = width/2
        radius_y = height/2
        
        # FIXED: Use the rect method for better control, or draw manually
        if fill:
            # Draw filled ellipse using arc approximation
            self._draw_pdf_ellipse_filled(x, y, width, height)
        else:
            # Draw outline ellipse
            self._draw_pdf_ellipse_outline(x, y, width, height)
        
        return self
    
    def draw_circle(self, x, y, radius, color=None, fill=True, outline_width=None):
        """Draw circle - convenience method"""
        return self.draw_oval(x - radius, y - radius, radius * 2, radius * 2, 
                            color, fill, outline_width)
    
    def draw_polygon(self, points, color=None, fill=True, outline=None, outline_width=None):
        """Draw polygon on both tkinter canvas and PDF"""
        if color is not None:
            self.set_color(color)
        if outline_width is not None:
            self.set_line_width(outline_width)
        
        # Determine fill and outline colors
        fill_color = None
        outline_color = None
        
        if fill:
            if isinstance(fill, str):
                fill_color = self._parse_color(fill)
            else:
                fill_color = self.current_color
        
        if outline:
            outline_color = self._parse_color(outline)
        else:
            outline_color = self.current_color
        
        # Draw on tkinter canvas
        flat_points = [coord for point in points for coord in point]
        if fill:
            tk_fill = self._rgb_to_hex(fill_color) if fill_color else self._rgb_to_hex(self.current_color)
        else:
            tk_fill = ''
        
        tk_outline = self._rgb_to_hex(outline_color) if outline_color else self._rgb_to_hex(self.current_color)
        
        self.create_polygon(flat_points, fill=tk_fill, outline=tk_outline, 
                          width=self.current_line_width)
        
        # Draw on PDF - FIXED: Force manual polygon drawing for reliability
        if fill_color:
            self.pdf.set_fill_color(*[int(c * 255) for c in fill_color])
        if outline_color:
            self.pdf.set_draw_color(*[int(c * 255) for c in outline_color])
        
        # Always use manual approach for better control
        if len(points) >= 3:
            self._draw_polygon_manual(points, fill)
        
        return self
    
    def draw_text(self, x, y, text, size=12, color=None, font='Arial', align='center'):
        """Draw text on both tkinter canvas and PDF"""
        if color is not None:
            self.set_color(color)
        
        # Draw on tkinter canvas
        tk_color = self._rgb_to_hex(self.current_color)
        anchor = 'center' if align == 'center' else 'w'
        self.create_text(x, y, text=str(text), fill=tk_color, 
                        font=(font, size), anchor=anchor)
        
        # Draw on PDF
        self.pdf.set_text_color(*[int(c * 255) for c in self.current_color])
        self.pdf.set_font('Arial', size=size)  # fpdf2 built-in fonts
        
        # Adjust position for alignment
        if align == 'center':
            text_width = self.pdf.get_string_width(str(text))
            pdf_x = x - text_width / 2
        else:
            pdf_x = x
        
        self.pdf.text(pdf_x, y, str(text))
        
        return self
    
    def _draw_pdf_ellipse_filled(self, x, y, width, height):
        """Draw filled ellipse on PDF using correct fpdf2 method"""
        # fpdf2 ellipse method signature: ellipse(x, y, w, h, style)
        # where (x,y) is the CENTER of the ellipse, and w,h are the full width/height
        center_x = x + width/2
        center_y = y + height/2
        
        # Adjust position: half radius up (subtract) and half radius left (subtract)
        adjusted_center_x = center_x - width/4
        adjusted_center_y = center_y - height/4
        
        self.pdf.ellipse(adjusted_center_x, adjusted_center_y, width, height, style='F')
    
    def _draw_pdf_ellipse_outline(self, x, y, width, height):
        """Draw ellipse outline on PDF"""
        # fpdf2 ellipse method for outline only
        center_x = x + width/2
        center_y = y + height/2
        
        # Adjust position: half radius up (subtract) and half radius left (subtract)
        adjusted_center_x = center_x - width/4
        adjusted_center_y = center_y - height/4
        
        self.pdf.ellipse(adjusted_center_x, adjusted_center_y, width, height, style='D')
    
    def _draw_polygon_manual(self, points, fill):
        """Manually draw polygon using lines and fill"""
        print(f"DEBUG: _draw_polygon_manual called with fill={fill}")
        
        if fill:
            # For filled polygons, draw scanline fill first
            print("DEBUG: Drawing fill...")
            # Make sure fill color is set
            if isinstance(fill, str):
                fill_color = self._parse_color(fill)
                self.pdf.set_draw_color(*[int(c * 255) for c in fill_color])
                print(f"DEBUG: Set fill color to {[int(c * 255) for c in fill_color]}")
            self._fill_polygon_scanline(points)
        
        # Then draw the outline on top
        print("DEBUG: Drawing outline...")
        self.pdf.set_line_width(self.current_line_width)
        for i in range(len(points)):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % len(points)]  # Wrap to first point
            self.pdf.line(x1, y1, x2, y2)
        print("DEBUG: Finished polygon")
    
    def _fill_polygon_scanline(self, points):
        """Fill polygon using horizontal scanlines"""
        if len(points) < 3:
            print("DEBUG: Not enough points for polygon")
            return
        
        # Find bounding box
        min_y = int(min(p[1] for p in points))
        max_y = int(max(p[1] for p in points))
        
        print(f"DEBUG: Filling polygon with {len(points)} points, y range {min_y} to {max_y}")
        
        # Set line width to 1 for fill lines to avoid gaps
        original_width = self.current_line_width
        self.pdf.set_line_width(1)
        
        total_lines = 0
        
        # For each horizontal line, find intersections and fill
        for y in range(min_y, max_y + 1):
            intersections = []
            
            # Find intersections with polygon edges
            for i in range(len(points)):
                x1, y1 = points[i]
                x2, y2 = points[(i + 1) % len(points)]
                
                # Check if horizontal line y intersects with edge (x1,y1) to (x2,y2)
                if (y1 <= y < y2) or (y2 <= y < y1):
                    if abs(y2 - y1) > 0.001:  # Avoid division by zero
                        x_intersect = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                        intersections.append(x_intersect)
            
            # Sort intersections and fill between pairs
            intersections.sort()
            for i in range(0, len(intersections) - 1, 2):
                if i + 1 < len(intersections):
                    x_start = intersections[i]
                    x_end = intersections[i + 1]
                    if x_end > x_start + 0.5:  # Only draw if line is long enough
                        self.pdf.line(x_start, y, x_end, y)
                        total_lines += 1
        
        print(f"DEBUG: Drew {total_lines} fill lines")
        
        # Restore original line width
        self.pdf.set_line_width(original_width)
    
    def save_pdf(self, filename):
        """Save the PDF to file"""
        self.pdf.output(filename)
        print(f"PDF saved: {filename}")
        return self
    
    def export_pdf(self, filename):
        """Export the PDF to file (alias for save_pdf)"""
        return self.save_pdf(filename)
    
    def clear_all(self):
        """Clear both canvas and start new PDF page"""
        # Clear tkinter canvas
        self.delete("all")
        
        # Start new PDF page
        self.pdf.add_page()
        
        return self
    
    def _parse_color(self, color):
        """Convert color to RGB tuple (0-1 range)"""
        if isinstance(color, str):
            if color.startswith('#'):
                # Hex color
                hex_color = color.lstrip('#')
                return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
            else:
                # Named color
                color_map = {
                    'black': (0, 0, 0), 'white': (1, 1, 1),
                    'red': (1, 0, 0), 'green': (0, 1, 0), 'blue': (0, 0, 1),
                    'yellow': (1, 1, 0), 'cyan': (0, 1, 1), 'magenta': (1, 0, 1),
                    'gray': (0.5, 0.5, 0.5), 'grey': (0.5, 0.5, 0.5),
                }
                return color_map.get(color.lower(), (0, 0, 0))
        elif isinstance(color, (tuple, list)) and len(color) == 3:
            # RGB tuple (assume 0-1 range)
            return tuple(color)
        else:
            return (0, 0, 0)  # Default to black
    
    def _rgb_to_hex(self, rgb):
        """Convert RGB tuple (0-1 range) to hex color"""
        return f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"

# Example usage with your SCORE class
def render_score_to_pdf_canvas(score, canvas):
    """Render a SCORE object to PdfCanvas"""
    
    # Example: Draw staff lines from baseGrid
    for base_grid in score.baseGrid:
        for i, pos in enumerate(base_grid.gridlinePositions):
            # Staff lines
            width = base_grid.barlineWidth if i % 4 == 0 else base_grid.gridlineWidth
            color = base_grid.barlineColor if i % 4 == 0 else base_grid.gridlineColor
            canvas.draw_line(50, pos, 750, pos, color=color, width=width)
    
    # Example: Draw notes from all staves
    for stave in score.stave:
        for note in stave.event.note:
            # Convert note position to canvas coordinates
            x = 100 + (note.time / 256.0) * 500  # Scale time to pixels
            y = 200 - (note.pitch - 40) * 3      # Scale pitch to pixels
            
            # Draw note
            canvas.draw_circle(x, y, 8, color='black', fill=True)
    
    # Example: Draw text elements
    for stave in score.stave:
        for text in stave.event.text:
            x = 100 + (text.time / 256.0) * 500
            y = 100
            canvas.draw_text(x, y, text.text, size=text.fontSize or 12)

# Test the PdfCanvas
if __name__ == "__main__":
    root = tk.Tk()
    root.title("PDF Canvas Test")
    
    # Create PdfCanvas with custom dimensions
    canvas = PdfCanvas(root, width=800, height=600)
    canvas.pack()
    
    # Draw some test elements
    canvas.draw_line(100, 100, 700, 100, color='black', width=2)
    canvas.draw_line(100, 150, 700, 150, color='black', width=1)
    canvas.draw_line(100, 200, 700, 200, color='black', width=1)
    canvas.draw_line(100, 250, 700, 250, color='black', width=1)
    canvas.draw_line(100, 300, 700, 300, color='black', width=2)
    
    # Draw notes
    canvas.draw_circle(200, 100, 10, color='black', fill=True)
    canvas.draw_circle(300, 150, 10, color='red', fill=False)
    canvas.draw_circle(400, 200, 10, color='blue', fill=True)
    
    # Draw polygon (sharp symbol)
    sharp_points = [(500, 90), (505, 88), (505, 112), (500, 110)]
    canvas.draw_polygon(sharp_points, color='black', fill=True)
    
    # Draw text
    canvas.draw_text(400, 50, "PDF Canvas Music Score", size=16, color='blue')
    
    # Save PDF
    canvas.save_pdf("music_score.pdf")
    
    root.mainloop()