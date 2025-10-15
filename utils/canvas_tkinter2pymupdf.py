import tkinter as tk
import fitz  # PyMuPDF
from logger import log

class PdfCanvas(tk.Canvas):
    '''
        Multi-page tkinter Canvas that generates PDF using PyMuPDF.
        
        Canvas display size matches PDF page dimensions for accurate preview.

        === MINI TUTORIAL ===
        
        🎨 SKETCH MODE (pdf_mode=False) - Fast tkinter preview only:
            canvas = PdfCanvas(parent, pdf_mode=False)          # No PDF generation
            canvas.add_line(10, 10, 100, 100, color='#FF0000') # Draw immediately
            canvas.add_rectangle(50, 50, 100, 50, color='#00FF00')
            canvas.add_text(100, 200, 'Sketching...', color='#0000FF')
            # No new_page() needed - just sketch freely!
        
        📄 PDF EXPORT MODE (pdf_mode=True) - Multi-page documents:
            canvas = PdfCanvas(parent, pdf_mode=True)           # Enable PDF generation
            
            # Page 1
            canvas.new_page()                                   # Required for PDF mode
            canvas.add_line(50, 50, 300, 50, color='#FF0000', width=2)
            canvas.add_text(200, 100, 'Page 1', size=16, color='#000000')
            
            # Page 2 (different size)
            canvas.new_page(width=612, height=792)              # Letter size override
            canvas.add_rectangle(100, 100, 200, 150, color='#0000FF', fill=False)
            canvas.add_text(200, 200, 'Page 2 - Letter size', color='#0000FF')
            
            # Export to PDF
            canvas.save_pdf('multi_page_document.pdf')
        
        🔄 DYNAMIC WORKFLOW - Switch between modes:
            canvas = PdfCanvas(parent, pdf_mode=False)          # Start with preview
            canvas.add_line(0, 0, 100, 100)                    # Sketch ideas
            
            canvas.enable_pdf_mode()                           # Ready to export
            canvas.new_page()                                  # Start clean page
            canvas.add_line(0, 0, 100, 100, color='#FF0000')   # Final version
            canvas.save_pdf('final.pdf')
            
            canvas.disable_pdf_mode()                          # Back to sketching
            canvas.add_text(50, 150, 'More ideas...')          # Continue sketching

        📏 COMMON PAGE SIZES:
            PdfCanvas(parent, page_width=595, page_height=842)  # A4 (default)
            PdfCanvas(parent, page_width=612, page_height=792)  # US Letter
            PdfCanvas(parent, page_width=420, page_height=595)  # A5
            PdfCanvas(parent, page_width=297, page_height=420)  # A6

        Tested with Python 3.13.5, Tkinter, and PyMuPDF 1.18.19+ on macOS.
    '''

    def __init__(self, parent, pdf_mode=False, page_width=595, page_height=842):
        super().__init__(parent, width=page_width, height=page_height, bg='white', relief='flat', borderwidth=0)
        
        # Canvas display dimensions (same as PDF page dimensions)
        self.original_width = page_width
        self.original_height = page_height
        
        # Default PDF page dimensions
        self.default_page_width = page_width
        self.default_page_height = page_height
        
        # Current page state
        self.current_page_commands = []
        self.all_pages_commands = []
        self.current_page_index = -1  # -1 means no page started
        self.page_active = False
        
        # PDF document
        self.pdf_mode = pdf_mode
        self.doc = fitz.open() if pdf_mode else None
        
        # Canvas scaling
        self.current_scale = 1.0
        self.content_offset_x = 0
        self.content_offset_y = 0

        self.configure(highlightthickness=0)
        
        # Add a vertical scrollbar
        self.scrollbar = tk.Scrollbar(parent, orient='vertical', command=self.yview)
        self.scrollbar.pack(side='right', fill='y')

        # Link the scrollbar to the canvas
        self.configure(yscrollcommand=self.scrollbar.set)

        # Bind resize events
        self.bind('<Configure>', self._on_canvas_resize)
    
    def enable_pdf_mode(self):
        '''Enable PDF generation mode for export.'''
        if not self.pdf_mode:
            self.pdf_mode = True
            if not self.doc:
                self.doc = fitz.open()
            log('PDF mode enabled')
        return self

    def disable_pdf_mode(self):
        '''Disable PDF mode for better performance (tkinter preview only).'''
        if self.pdf_mode:
            self.pdf_mode = False
            if self.doc:
                self.doc.close()
                self.doc = None
            log('PDF mode disabled - tkinter preview only')
        return self

    def is_pdf_mode_enabled(self):
        '''Check if PDF mode is currently enabled.'''
        return self.pdf_mode

    def new_page(self, width=None, height=None):
        '''Start a new page. Must be called before any drawing operations.'''
        # Save current page if it has content
        if self.page_active and self.current_page_commands:
            page_width = getattr(self, 'current_page_width', self.default_page_width)
            page_height = getattr(self, 'current_page_height', self.default_page_height)
            
            self.all_pages_commands.append({
                'commands': self.current_page_commands.copy(),
                'width': page_width,
                'height': page_height
            })
            log(f'Saved page {len(self.all_pages_commands)} with {len(self.current_page_commands)} commands')
        
        # Set up new page
        self.current_page_width = width or self.default_page_width
        self.current_page_height = height or self.default_page_height
        self.current_page_commands = []
        self.current_page_index += 1
        self.page_active = True
        
        # Clear canvas for new page
        self.delete('all')
        
        log(f'Started page {self.current_page_index + 1} ({self.current_page_width}x{self.current_page_height})')
        return self
    
    def set_page_dimensions(self, page_width, page_height):
        '''Set default page dimensions and update canvas scroll region.
        
        Args:
            page_width (int): New default page width in points
            page_height (int): New default page height in points
            
        Returns:
            self: For method chaining
        '''
        self.default_page_width = page_width
        self.default_page_height = page_height
        
        # Update canvas scroll region to match new dimensions
        self.configure(scrollregion=(0, 0, page_width, page_height))
        
        # If there's an active page, update its dimensions too
        if self.page_active:
            self.current_page_width = page_width
            self.current_page_height = page_height
            
        log(f'Page dimensions set to {page_width}x{page_height}')
        return self
    
    def _check_page_active(self):
        '''Check if a page is active before drawing operations.'''
        if self.pdf_mode and not self.page_active:
            raise RuntimeError('No page active! Call new_page() before drawing when pdf_mode is enabled.')
    
    def get_page_count(self):
        '''Get total number of pages.'''
        return len(self.all_pages_commands) + (1 if self.page_active else 0)
    
    def get_page_info(self):
        '''Get current page information.'''
        return {
            'page_number': self.current_page_index + 1,
            'commands_count': len(self.current_page_commands),
            'dimensions': (getattr(self, 'current_page_width', 0), 
                          getattr(self, 'current_page_height', 0)),
            'total_pages': self.get_page_count(),
            'page_active': self.page_active
        }
    
    def save_pdf(self, filename):
        '''Save all pages as PDF.'''
        if not self.pdf_mode:
            raise RuntimeError('PDF mode is disabled')
        
        # Save current page if active
        if self.page_active and self.current_page_commands:
            self.all_pages_commands.append({
                'commands': self.current_page_commands.copy(),
                'width': self.current_page_width,
                'height': self.current_page_height
            })
            log(f'Saved final page {len(self.all_pages_commands)}')
        
        if not self.all_pages_commands:
            raise RuntimeError('No pages to save! Call new_page() and draw content first.')
        
        # Create PDF
        if self.doc:
            self.doc.close()
        self.doc = fitz.open()
        
        for i, page_data in enumerate(self.all_pages_commands):
            log(f'Processing page {i + 1}/{len(self.all_pages_commands)}...')
            
            pdf_page = self.doc.new_page(width=page_data['width'], height=page_data['height'])
            
            for cmd in page_data['commands']:
                self._execute_pdf_command(cmd, pdf_page)
        
        self.doc.save(filename)
        log(f'✅ PDF saved: {filename} ({len(self.all_pages_commands)} pages)')
        return self
    
    def _draw_solid_line_pdf(self, pdf_page, x1, y1, x2, y2, color, width):
        '''Draw solid line on PDF.'''
        shape = pdf_page.new_shape()
        shape.draw_line(fitz.Point(x1, y1), fitz.Point(x2, y2))
        shape.finish(color=color, width=width, fill=None, lineCap=1)
        shape.commit()
    
    def _draw_dashed_line_pdf(self, pdf_page, x1, y1, x2, y2, color, width, dash_pattern):
        '''Draw dashed line on PDF.'''
        dash_parts = [float(x) for x in dash_pattern.split()]
        dx, dy = x2 - x1, y2 - y1
        length = (dx*dx + dy*dy)**0.5
        
        if length == 0:
            return
        
        unit_x, unit_y = dx/length, dy/length
        pos, dash_idx, drawing = 0.0, 0, True
        
        while pos < length:
            segment_len = dash_parts[dash_idx % len(dash_parts)]
            end_pos = min(pos + segment_len, length)
            
            if drawing:
                start_x = x1 + pos * unit_x
                start_y = y1 + pos * unit_y
                end_x = x1 + end_pos * unit_x
                end_y = y1 + end_pos * unit_y
                self._draw_solid_line_pdf(pdf_page, start_x, start_y, end_x, end_y, color, width)
            
            pos, dash_idx, drawing = end_pos, dash_idx + 1, not drawing
    
    def _draw_text_pdf(self, pdf_page, x, y, text, size, color, font, anchor):
        '''Draw text on PDF with proper positioning.'''
        font_map = {
            'Arial': 'helv', 'Helvetica': 'helv', 'Times': 'times',
            'Courier': 'cour', 'Courier New': 'cour'
        }
        fontname = font_map.get(font, 'helv')
        
        font_obj = fitz.Font(fontname)
        lines = text.split('\n')
        raw_width = max(font_obj.text_length(line, fontsize=size) for line in lines)
        
        # Apply calibrated corrections
        width = raw_width + 3.0
        height = len(lines) * (size + 2)
        
        # Calculate offset based on anchor
        offset_x, offset_y = 0, 0
        if anchor in ['center', 'n', 's']:
            offset_x = -width / 2
        elif anchor in ['ne', 'e', 'se']:
            offset_x = -width
        
        if anchor in ['center', 'w', 'e']:
            offset_y = -height / 2
        elif anchor in ['sw', 's', 'se']:
            offset_y = -height
        
        offset_y -= 1.5  # Empirical correction
        
        ascender = font_obj.ascender * size
        final_x = x + offset_x
        final_y = y + offset_y + ascender
        
        for i, line in enumerate(lines):
            line_y = final_y + (i * size * 1.2)
            line_x = final_x
            
            if anchor in ['center', 'n', 's']:
                line_width = font_obj.text_length(line, fontsize=size)
                line_x = x - line_width / 2
            elif anchor in ['ne', 'e', 'se']:
                line_width = font_obj.text_length(line, fontsize=size)
                line_x = x - line_width
            
            pdf_page.insert_text(fitz.Point(line_x, line_y), line, 
                                fontsize=size, fontname=fontname, color=color)
    
    def _draw_polygon_pdf(self, pdf_page, points, color, fill, outline, outline_width):
        '''Draw polygon on PDF with proper fill and outline handling.'''
        fill_color = self._parse_color(color) if fill and color is not None else None
        
        # Handle outline parameters
        draw_outline = outline is not None and outline != '' and outline_width != 0
        outline_color = self._parse_color(outline) if draw_outline else self._parse_color(color) if color else (0, 0, 0)
        line_width = outline_width if outline_width is not None and outline_width > 0 else 1
        
        shape = pdf_page.new_shape()
        fitz_points = [fitz.Point(x, y) for x, y in points]
        shape.draw_polyline(fitz_points)
        shape.draw_line(fitz_points[-1], fitz_points[0])  # Close polygon
        
        if fill and draw_outline:
            shape.finish(fill=fill_color, color=outline_color, width=line_width)
        elif fill:
            shape.finish(fill=fill_color, color=None, width=0)
        elif draw_outline:
            shape.finish(fill=None, color=outline_color, width=line_width)
        else:
            shape.finish(fill=None, color=(0, 0, 0), width=line_width)
        shape.commit()

    def _store_command(self, cmd):
        '''Store command for the current page.'''
        self._check_page_active()
        self.current_page_commands.append(cmd)
    
    def add_line(self, x1, y1, x2, y2, color=None, width=None, dash_pattern=None):
        '''
        Draw a line from (x1,y1) to (x2,y2) with optional styling.
        
        Always renders to tkinter for preview. Conditionally renders to PDF if pdf_mode is enabled.
        Supports solid and dashed lines with precise dash patterns.
        
        Args:
            x1, y1 (int/float): Starting point coordinates
            x2, y2 (int/float): Ending point coordinates  
            color (str|tuple|None): Line color as hex '#FF0000' or RGB tuple (1,0,0)
            width (int|None): Line width in points (default: current_line_width)
            dash_pattern (str|None): Dash pattern like '10 5' (10pt dash, 5pt gap)
                                   or '15 3 3 3' (dash-dot pattern)
                                   
        Returns:
            self: For method chaining
            
        Examples:
            canvas.add_line(0, 0, 100, 100)  # Solid black line
            canvas.add_line(0, 0, 100, 100, color='#FF0000', width=3)  # Red thick line
            canvas.add_line(0, 0, 100, 100, dash_pattern='10 5')  # Dashed line
            canvas.add_line(0, 0, 100, 100, color='#0000FF', dash_pattern='5 5')  # Blue dashed
        '''
        # Store command for potential PDF replay
        pdf_dash = ' '.join(str(x) for x in dash_pattern) if isinstance(dash_pattern, (list, tuple)) else dash_pattern
        cmd = ('line', x1, y1, x2, y2, color, width, pdf_dash)
        self._store_command(cmd)
        
        # Use provided parameters or defaults
        line_color = self._parse_color(color) if color is not None else (0, 0, 0)
        line_width = width if width is not None else 1
        
        # ALWAYS draw to tkinter (for preview)
        tk_color = self._rgb_to_hex(line_color)
        if dash_pattern:
            tk_dash = dash_pattern
            self.create_line(x1, y1, x2, y2, fill=tk_color, width=line_width, 
                           dash=tk_dash, capstyle=tk.ROUND)
        else:
            self.create_line(x1, y1, x2, y2, fill=tk_color, width=line_width, 
                           capstyle=tk.ROUND)
        
        # CONDITIONALLY draw to PDF (only if we have an active page)
        if self.pdf_mode and hasattr(self, 'page') and self.page:
            self._execute_pdf_command(cmd)
        
        return self
    
    def _execute_pdf_command(self, cmd, pdf_page=None):
        '''Execute a single drawing command on the specified PDF page or current page'''
        if not self.pdf_mode:
            return
        
        # Use specified page or current page
        target_page = pdf_page or (self.page if hasattr(self, 'page') else None)
        if not target_page:
            return
        
        cmd_type = cmd[0]
        
        if cmd_type == 'line':
            _, x1, y1, x2, y2, color, width, dash_pattern = cmd
            line_color = self._parse_color(color) if color is not None else (0, 0, 0)
            line_width = width if width is not None else 1
            
            if dash_pattern:
                self._draw_dashed_line_pdf(target_page, x1, y1, x2, y2, line_color, line_width, dash_pattern)
            else:
                self._draw_solid_line_pdf(target_page, x1, y1, x2, y2, line_color, line_width)
        
        elif cmd_type == 'rectangle':
            _, x, y, width, height, color, fill, outline, outline_width = cmd
            fill_color = self._parse_color(color) if color is not None and fill else None
            
            # Handle outline parameters
            draw_outline = outline is not None and outline != '' and outline_width != 0
            outline_color = self._parse_color(outline) if draw_outline else self._parse_color(color) if color else (0, 0, 0)
            line_width = outline_width if outline_width is not None and outline_width > 0 else 1
            
            shape = target_page.new_shape()
            rect = fitz.Rect(x, y, x + width, y + height)
            shape.draw_rect(rect)
            
            if fill and draw_outline:
                shape.finish(fill=fill_color, color=outline_color, width=line_width)
            elif fill:
                shape.finish(fill=fill_color, color=None, width=0)
            elif draw_outline:
                shape.finish(fill=None, color=outline_color, width=line_width)
            else:
                shape.finish(fill=None, color=(0, 0, 0), width=line_width)
            shape.commit()
        
        elif cmd_type == 'oval':
            _, x, y, width, height, color, fill, outline_width = cmd
            oval_color = self._parse_color(color) if color is not None else (0, 0, 0)
            line_width = outline_width if outline_width is not None else 1
            
            shape = target_page.new_shape()
            center_x = x + width / 2
            center_y = y + height / 2
            radius_x = width / 2
            radius_y = height / 2
            
            if abs(radius_x - radius_y) < 0.1:
                shape.draw_circle(fitz.Point(center_x, center_y), radius_x)
            else:
                rect = fitz.Rect(x, y, x + width, y + height)
                shape.draw_oval(rect)
            
            if fill:
                shape.finish(fill=oval_color, color=oval_color, width=line_width)
            else:
                shape.finish(fill=None, color=oval_color, width=line_width)
            shape.commit()
        
        elif cmd_type == 'polygon':
            _, points, color, fill, outline, outline_width = cmd
            self._draw_polygon_pdf(target_page, points, color, fill, outline, outline_width)
        
        elif cmd_type == 'text':
            _, x, y, text, size, color, font, anchor = cmd
            text_color = self._parse_color(color) if color is not None else (0, 0, 0)
            self._draw_text_pdf(target_page, x, y, text, size, text_color, font, anchor)
    
    def add_polygon(self, points, color=None, fill=True, outline=None, outline_width=None):
        '''
        Draw polygon on both tkinter canvas and PDF.
        
        Args:
            points (list): List of (x,y) coordinate tuples [(x1,y1), (x2,y2), ...]
            color (str|tuple): Fill color as hex '#FF0000' or RGB tuple (1,0,0)
            fill (bool): Whether to fill the polygon (default: True)
            outline (str|tuple): Outline color, disabled if '' or None
            outline_width (int): Outline width, disabled if 0 (default: 1)
        '''
        # Store command for potential PDF replay
        cmd = ('polygon', points, color, fill, outline, outline_width)
        self._store_command(cmd)
        
        # Use explicit parameters with defaults
        default_color = (0, 0, 0)
        
        # Handle fill color
        fill_color = self._parse_color(color) if color is not None else default_color
        
        # Handle outline parameters
        draw_outline = outline is not None and outline != '' and outline_width != 0
        outline_color = self._parse_color(outline) if draw_outline else fill_color
        line_width = outline_width if outline_width is not None and outline_width > 0 else 1
        
        # ALWAYS draw to tkinter
        flat_points = [coord for point in points for coord in point]
        tk_fill = self._rgb_to_hex(fill_color) if fill else ''
        tk_outline = self._rgb_to_hex(outline_color) if draw_outline else ''
        
        self.create_polygon(flat_points, fill=tk_fill, outline=tk_outline, 
                          width=line_width)
        
        # CONDITIONALLY draw to PDF
        if self.pdf_mode and hasattr(self, 'page') and self.page:
            self._execute_pdf_command(cmd)
        
        return self
    
    def add_oval(self, x, y, width, height, color=None, fill=True, outline_width=None):
        '''Draw oval - always to tkinter, conditionally to PDF'''
        # Store command for potential PDF replay
        cmd = ('oval', x, y, width, height, color, fill, outline_width)
        self._store_command(cmd)
        
        # Use explicit parameters with defaults
        oval_color = self._parse_color(color) if color is not None else (0, 0, 0)
        line_width = outline_width if outline_width is not None else 1
        
        # ALWAYS draw to tkinter
        tk_color = self._rgb_to_hex(oval_color)
        if fill:
            self.create_oval(x, y, x + width, y + height, 
                           fill=tk_color, outline=tk_color, width=line_width)
        else:
            self.create_oval(x, y, x + width, y + height, 
                           outline=tk_color, fill='', width=line_width)
        
        # CONDITIONALLY draw to PDF
        if self.pdf_mode and hasattr(self, 'page') and self.page:
            self._execute_pdf_command(cmd)
        
        return self
    
    def _draw_solid_line(self, x1, y1, x2, y2, color, width):
        '''Draw a solid line in PDF'''
        shape = self.page.new_shape()
        shape.draw_line(fitz.Point(x1, y1), fitz.Point(x2, y2))
        shape.finish(
            color=self._color_to_fitz_rgb(color), 
            width=width,
            fill=None,
            closePath=False,
            lineCap=1,
            lineJoin=1
        )
        shape.commit()
    
    def _draw_manual_dashed_line(self, x1, y1, x2, y2, color, width, dash_pattern):
        '''Draw a dashed line by creating multiple line segments'''
        # Parse dash pattern
        dash_parts = [float(x) for x in dash_pattern.split()]
        
        # Calculate line length and direction
        dx = x2 - x1
        dy = y2 - y1
        line_length = (dx * dx + dy * dy) ** 0.5
        
        if line_length == 0:
            return
        
        # Normalize direction vector
        unit_x = dx / line_length
        unit_y = dy / line_length
        
        # Draw dashed segments
        current_pos = 0.0
        dash_index = 0
        drawing = True  # Start with a dash
        
        while current_pos < line_length:
            # Get current dash/space length
            segment_length = dash_parts[dash_index % len(dash_parts)]
            
            # Calculate segment end position
            segment_end = min(current_pos + segment_length, line_length)
            
            if drawing:
                # Draw dash segment
                start_x = x1 + current_pos * unit_x
                start_y = y1 + current_pos * unit_y
                end_x = x1 + segment_end * unit_x
                end_y = y1 + segment_end * unit_y
                
                shape = self.page.new_shape()
                shape.draw_line(fitz.Point(start_x, start_y), fitz.Point(end_x, end_y))
                shape.finish(
                    color=self._color_to_fitz_rgb(color), 
                    width=width,
                    fill=None,
                    closePath=False,
                    lineCap=1,
                    lineJoin=1
                )
                shape.commit()
            
            # Move to next segment
            current_pos = segment_end
            dash_index += 1
            drawing = not drawing  # Alternate between dash and space
        
        return self
    
    def add_text(self, x, y, text, size=12, color=None, font='Arial', anchor='center'):
        '''
        Draw text at specified position with proper alignment handling.
        
        Args:
            x, y (float): Text position coordinates
            text (str): Text to display
            size (int): Font size in points (default: 12)
            color (str|tuple): Text color as hex '#000000' or RGB tuple (0,0,0)
            font (str): Font family name (default: 'Arial')
            anchor (str): Text anchor point - 'center', 'nw', 'n', 'ne', 'w', 'e', 'sw', 's', 'se'
                         'center' = center both horizontally and vertically
                         'nw' = top-left, 'ne' = top-right, 'sw' = bottom-left, 'se' = bottom-right
                         'n' = top-center, 's' = bottom-center, 'w' = middle-left, 'e' = middle-right
        
        Returns:
            self: For method chaining
            
        Examples:
            canvas.add_text(100, 50, 'Title', size=16, color='#000000', anchor='center')
            canvas.add_text(10, 10, 'Top-left', anchor='nw')
            canvas.add_text(400, 300, 'Centered', anchor='center')
        '''
        # Store command for potential PDF replay
        cmd = ('text', x, y, text, size, color, font, anchor)
        self._store_command(cmd)
        
        # Use explicit parameters with defaults
        text_color = self._parse_color(color) if color is not None else (0, 0, 0)
        
        # ALWAYS draw to tkinter
        tk_color = self._rgb_to_hex(text_color)
        tk_font = (font, size)
        
        self.create_text(x, y, text=text, fill=tk_color, font=tk_font, anchor=anchor)
        
        # CONDITIONALLY draw to PDF
        if self.pdf_mode and hasattr(self, 'page') and self.page:
            self._execute_pdf_command(cmd)
        
        return self

    def add_bezier_curve(self, x1, y1, x2, y2, x3, y3, x4, y4, color=None, width=None, dash_pattern=None):
        '''Draw bezier curve with 4 control points on both tkinter canvas and PDF
        
        Args:
            x1, y1: Start point
            x2, y2: First control point  
            x3, y3: Second control point
            x4, y4: End point
            color: Line color (optional)
            width: Line width (optional)
            dash_pattern: Dash pattern (optional)
        '''
        # Store command for potential PDF replay
        cmd = ('bezier', x1, y1, x2, y2, x3, y3, x4, y4, color, width, dash_pattern)
        self._store_command(cmd)
        
        # Use explicit parameters with defaults
        bezier_color = self._parse_color(color) if color is not None else (0, 0, 0)
        line_width = width if width is not None else 1
        
        # Draw on tkinter canvas (approximate with line segments)
        tk_color = self._rgb_to_hex(bezier_color)
        
        # For tkinter, we need to approximate the bezier with line segments
        bezier_points = self._bezier_to_points(x1, y1, x2, y2, x3, y3, x4, y4, num_segments=50)
        
        for i in range(len(bezier_points) - 1):
            px1, py1 = bezier_points[i]
            px2, py2 = bezier_points[i + 1]
            
            if dash_pattern:
                tk_dash = tuple(int(x) for x in dash_pattern.split())
                self.create_line(px1, py1, px2, py2, fill=tk_color, width=line_width, dash=tk_dash)
            else:
                self.create_line(px1, py1, px2, py2, fill=tk_color, width=line_width)
        
        # Draw on PDF using PyMuPDF - NATIVE bezier support
        if self.pdf_mode and hasattr(self, 'page') and self.page and self.page:
            shape = self.page.new_shape()
            shape.draw_bezier(
                fitz.Point(x1, y1),  # Start point
                fitz.Point(x2, y2),  # Control point 1
                fitz.Point(x3, y3),  # Control point 2
                fitz.Point(x4, y4)   # End point
            )
            
            # Build finish parameters using explicit parameters
            finish_params = {
                'color': self._color_to_fitz_rgb(bezier_color),
                'width': line_width,
                'fill': None,        # Curves should not be filled
                'closePath': False,  # Curves should not close path
                'lineCap': 1,        # Round line caps for better dash appearance
                'lineJoin': 1        # Round line joins
            }
            
            # Only add dashes parameter if we have a dash pattern
            if dash_pattern is not None:
                finish_params['dashes'] = dash_pattern
                
            shape.finish(**finish_params)
            shape.commit()
        
        return self
    
    def _draw_pdf_text(self, x, y, text, size, color, font, anchor):
        '''
        Draw text to PDF with proper alignment and positioning.
        
        This method handles the complex text positioning in PyMuPDF, accounting for:
        - Font metrics and baseline positioning
        - Text bounding box calculations
        - Anchor point alignment
        - Coordinate system differences between tkinter and PyMuPDF
        '''
        if not self.pdf_mode or not self.page:
            return
        
        # Map font names to PyMuPDF built-in fonts
        font_map = {
            'Arial': 'helv',
            'Helvetica': 'helv', 
            'Times': 'times',
            'Times-Roman': 'times',
            'Courier': 'cour',
            'Courier New': 'cour',  # Map Courier New to cour
            'Symbol': 'symb',
            'ZapfDingbats': 'zadb'
        }
        
        # Use built-in font or default to Helvetica
        fontname = font_map.get(font, 'helv')
        
        # Calculate text dimensions using corrected formula to match tkinter exactly
        font_obj = fitz.Font(fontname)
        
        # For multi-line text, split and measure properly
        lines = text.split('\n')
        raw_width = max(font_obj.text_length(line, fontsize=size) for line in lines)
        
        # Apply corrections to match tkinter bounding boxes exactly
        corrected_width = raw_width + 3.0  # Empirical correction for width
        line_height = size + 2  # tkinter uses font_size + 2 for line height
        corrected_height = len(lines) * line_height
        
        # Calculate text positioning based on tkinter anchor behavior
        # tkinter anchors work relative to the text's bounding box
        offset_x, offset_y = self._calculate_tkinter_like_offset(corrected_width, corrected_height, size, anchor)
        
        # Final position - PyMuPDF uses baseline positioning
        # Use font ascender instead of font size for accurate baseline positioning
        ascender = font_obj.ascender * size
        final_x = x + offset_x
        final_y = y + offset_y + ascender  # Use ascender for proper baseline positioning
        
        # Insert each line of text
        for i, line in enumerate(lines):
            line_y = final_y + (i * size * 1.2)  # Position each line
            line_x = final_x
            
            # For center and right anchors, adjust each line individually
            if anchor in ['center', 'n', 's']:
                line_width = font_obj.text_length(line, fontsize=size)
                line_x = x - line_width / 2
            elif anchor in ['ne', 'e', 'se']:
                line_width = font_obj.text_length(line, fontsize=size)
                line_x = x - line_width
            
            try:
                self.page.insert_text(
                    fitz.Point(line_x, line_y),
                    line,
                    fontsize=size,
                    fontname=fontname,
                    color=self._color_to_fitz_rgb(color)
                )
            except Exception as e:
                log(f'Error inserting text: {e}')
                # Fallback: use default font
                self.page.insert_text(
                    fitz.Point(line_x, line_y),
                    line,
                    fontsize=size,
                    color=self._color_to_fitz_rgb(color)
                )
    
    def _calculate_tkinter_like_offset(self, text_width, text_height, font_size, anchor):
        '''
        Calculate text position offset to mimic tkinter's anchor behavior.
        
        Args:
            text_width (float): Width of the text bounding box
            text_height (float): Height of the text bounding box  
            font_size (float): Font size in points
            anchor (str): Anchor specification
            
        Returns:
            tuple: (offset_x, offset_y) to adjust text position
        '''
        offset_x = 0
        offset_y = 0
        
        # Horizontal alignment - matches tkinter behavior exactly
        if anchor in ['center', 'n', 's']:
            offset_x = -text_width / 2
        elif anchor in ['ne', 'e', 'se']:
            offset_x = -text_width
        elif anchor in ['nw', 'w', 'sw']:
            offset_x = 0
        
        # Vertical alignment - adjusted to match tkinter's text box positioning
        if anchor in ['center', 'w', 'e']:
            # Center vertically around the anchor point
            offset_y = -text_height / 2
        elif anchor in ['nw', 'n', 'ne']:
            # Top of text at anchor point
            offset_y = 0
        elif anchor in ['sw', 's', 'se']:
            # Bottom of text at anchor point
            offset_y = -text_height
        
        # Apply empirical Y-axis correction: -1.5px for all anchors
        offset_y -= 1.5
        
        return offset_x, offset_y

    def _calculate_text_offset(self, text_width, text_height, ascender, anchor):
        '''
        Calculate text position offset based on anchor point.
        
        Args:
            text_width (float): Width of the text bounding box
            text_height (float): Height of the text bounding box  
            ascender (float): Font ascender height
            anchor (str): Anchor specification
            
        Returns:
            tuple: (offset_x, offset_y) to adjust text position
        '''
        offset_x = 0
        offset_y = 0
        
        # Horizontal alignment
        if anchor in ['center', 'n', 's']:
            offset_x = -text_width / 2
        elif anchor in ['ne', 'e', 'se']:
            offset_x = -text_width
        elif anchor in ['nw', 'w', 'sw']:
            offset_x = 0
        
        # Vertical alignment - adjusted for baseline positioning
        if anchor in ['center', 'w', 'e']:
            offset_y = -text_height / 2
        elif anchor in ['nw', 'n', 'ne']:
            offset_y = -ascender  # Top of text should be at anchor point
        elif anchor in ['sw', 's', 'se']:
            offset_y = text_height - ascender  # Bottom of text should be at anchor point
        
        return offset_x, offset_y

    def _bezier_to_points(self, x1, y1, x2, y2, x3, y3, x4, y4, num_segments=50):
        '''Convert bezier curve to line segments for tkinter approximation'''
        points = []
        for i in range(num_segments + 1):
            t = i / num_segments
            
            # Cubic Bezier formula: B(t) = (1-t)³P₁ + 3(1-t)²tP₂ + 3(1-t)t²P₃ + t³P₄
            x = (1-t)**3 * x1 + 3*(1-t)**2*t * x2 + 3*(1-t)*t**2 * x3 + t**3 * x4
            y = (1-t)**3 * y1 + 3*(1-t)**2*t * y2 + 3*(1-t)*t**2 * y3 + t**3 * y4
            
            points.append((x, y))
        
        return points
    
    def _update_scrollregion(self):
        '''Update the scrollregion based on the scaled content.'''
        # Calculate the scaled content dimensions
        scaled_width = self.original_width * self.current_scale
        scaled_height = self.original_height * self.current_scale

        # Calculate the offsets for centering
        x_offset = self.content_offset_x
        y_offset = self.content_offset_y

        # Define the scrollregion based on the scaled content and offsets
        x_min = x_offset
        y_min = y_offset
        x_max = x_offset + scaled_width
        y_max = y_offset + scaled_height

        # Update the scrollregion
        self.configure(scrollregion=(x_min, y_min, x_max, y_max))
        log(f"Updated scrollregion: {x_min}, {y_min}, {x_max}, {y_max}")
    
    def _on_canvas_resize(self, event):
        '''Handle canvas resize events and scale content to fit'''
        # Only handle resize events for the canvas itself, not child widgets
        if event.widget != self:
            return
            
        # Get new canvas dimensions
        new_width = event.width
        new_height = event.height
        
        # Skip if dimensions are too small
        if new_width < 10 or new_height < 10:
            return
        
        # Calculate scale factors to fit content while maintaining aspect ratio
        scale_x = new_width / self.original_width
        scale_y = new_height / self.original_height
        
        # Use uniform scaling to maintain aspect ratio (fit to smallest dimension)
        new_scale = min(scale_x, scale_y)
        
        # Calculate scaling transformation needed
        scale_factor = new_scale / self.current_scale if self.current_scale != 0 else new_scale
        
        # Apply scaling transformation
        if abs(scale_factor - 1.0) > 0.0001:  # Only scale if significant change
            self.scale('all', 0, 0, scale_factor, scale_factor)
            self.current_scale = new_scale
        
        # Center the content in the canvas
        self._center_content(new_width, new_height)

        self._update_scrollregion()
    
    def _center_content(self, canvas_width, canvas_height):
        '''Center the scaled content in the canvas'''
        # Calculate the actual size of scaled content
        scaled_width = self.original_width * self.current_scale
        scaled_height = self.original_height * self.current_scale
        
        # Calculate offset to center content
        new_offset_x = (canvas_width - scaled_width) / 2
        new_offset_y = (canvas_height - scaled_height) / 2
        
        # Calculate movement needed
        move_x = new_offset_x - self.content_offset_x
        move_y = new_offset_y - self.content_offset_y
        
        # Move all items to center
        if abs(move_x) > 0.1 or abs(move_y) > 0.1:  # Only move if significant change
            self.move('all', move_x, move_y)
            self.content_offset_x = new_offset_x
            self.content_offset_y = new_offset_y
    
    def get_scale_info(self):
        '''Get current scaling information for debugging'''
        return {
            'current_scale': self.current_scale,
            'original_size': (self.original_width, self.original_height),
            'current_size': (self.winfo_width(), self.winfo_height()),
            'content_offset': (self.content_offset_x, self.content_offset_y)
        }
    
    def add_rectangle(self, x1, y1, x2, y2, color=None, fill=True, outline=None, outline_width=None):
        '''
        Draw rectangle on both tkinter canvas and PDF.
        
        Args:
            x1, y1 (float): Top-left corner position
            x2, y2 (float): Bottom-right corner position
            color (str|tuple): Fill color as hex '#FF0000' or RGB tuple (1,0,0)
            fill (bool): Whether to fill the rectangle (default: True)
            outline (str|tuple): Outline color, disabled if '' or None
            outline_width (int): Outline width, disabled if 0 (default: 1)
        '''
        # Calculate width and height from coordinates
        width = x2 - x1
        height = y2 - y1

        # Store command for potential PDF replay
        cmd = ('rectangle', x1, y1, width, height, color, fill, outline, outline_width)
        self._store_command(cmd)
        
        # Use explicit parameters with defaults
        rect_color = self._parse_color(color) if color is not None else (0, 0, 0)
        
        # Handle outline parameters
        draw_outline = outline is not None and outline != '' and outline_width != 0
        outline_color = self._parse_color(outline) if draw_outline else rect_color
        line_width = outline_width if outline_width is not None and outline_width > 0 else 1
        
        # Draw on tkinter canvas
        tk_fill = self._rgb_to_hex(rect_color) if fill else ''
        tk_outline = self._rgb_to_hex(outline_color) if draw_outline else ''
        
        self.create_rectangle(x1, y1, x1 + width, y1 + height, 
                            fill=tk_fill, outline=tk_outline, width=line_width)
        
        # CONDITIONALLY draw to PDF
        if self.pdf_mode and hasattr(self, 'page') and self.page:
            self._execute_pdf_command(cmd)
        
        return self
    
    def get_performance_stats(self):
        '''Get performance statistics'''
        return {
            'pdf_mode': self.pdf_mode,
            'drawing_commands': len(self.current_page_commands),
            'total_pages': self.get_page_count(),
            'has_pdf_doc': self.doc is not None
        }
    
    def _parse_color(self, color):
        '''Parse hex color string to RGB tuple (0-1 range)'''
        if isinstance(color, str) and color.startswith('#'):
            # Hex color
            hex_color = color[1:]
            if len(hex_color) == 6:
                r = int(hex_color[0:2], 16) / 255.0
                g = int(hex_color[2:4], 16) / 255.0
                b = int(hex_color[4:6], 16) / 255.0
                return (r, g, b)
        elif isinstance(color, (tuple, list)) and len(color) == 3:
            # Direct RGB tuple (0-1 range)
            return tuple(color)
        
        # Default to black for any unrecognized color
        return (0, 0, 0)
    
    def _rgb_to_hex(self, rgb):
        '''Convert RGB tuple (0-1 range) to hex color'''
        if rgb is None:
            rgb = (0, 0, 0)  # Default to black
        return f'#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}'
    
    def _color_to_fitz_rgb(self, color):
        '''Convert color to fitz RGB tuple (0-1 range)'''
        if isinstance(color, (tuple, list)) and len(color) == 3:
            return color
        else:
            return self._parse_color(color)
