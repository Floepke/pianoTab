'''
Engraver: Multi-threaded Klavarskribo/PianoScript notation layout and rendering engine.

Architecture:
- Phase 1 (Background Thread): Calculate complete layout structure (DOC)
  - Generate structural events (barlines, gridlines, time signatures)
  - Process notes (split on barlines/linebreaks, add decorations)
  - Calculate staff dimensions and pagination
  
- Phase 2 (Main Thread): Draw to canvas in chunks (maintain 60fps)
  - Chunked drawing prevents UI freezing
  - Each chunk draws ~150 operations per frame

Threading Model:
- Single worker thread processes layout calculations
- Queue holds at most ONE pending task (the newest)
- Old tasks are automatically discarded when new ones arrive
- Main thread callbacks for Kivy canvas updates

Usage:
    from engraver import get_engraver_instance
    
    engraver = get_engraver_instance()
    engraver.do_engrave(score, canvas, callback)
'''

from __future__ import annotations

import threading
import queue
import time
import math
from typing import Optional, Callable, Any, List, Dict, Tuple
from dataclasses import dataclass
from copy import deepcopy

from kivy.clock import Clock

from file.SCORE import SCORE


@dataclass
class LayoutData:
    '''Pre-calculated layout data structure (DOC).
    
    Organized as: pages → lines → events
    Each event has type, time, pitch, and pre-calculated drawing coordinates.
    '''
    DOC: List[List[List[Dict]]]  # [page][line][event]
    leftover_page_space: List[float]  # Extra horizontal space per page to distribute
    staff_dimensions: List[List[Dict]]  # Width/margins per staff per line
    staff_ranges: List[List[Tuple[int, int]]]  # (min_pitch, max_pitch) per staff per line
    barline_times: List[float]  # All barline tick positions
    total_pages: int
    current_page: int


@dataclass
class EngraveTask:
    '''Represents a single engraving task.'''
    
    score: SCORE  # Will be deep copied for thread safety
    canvas: Any  # Canvas widget reference
    callback: Optional[Callable[[bool, Optional[str]], None]] = None
    task_id: int = 0
    timestamp: float = 0.0


class Engraver:
    '''
    Multi-threaded score engraver with intelligent task queuing.
    
    Ensures only the most recent engraving task is processed,
    automatically discarding outdated requests.
    '''
    
    def __init__(self):
        '''Initialize the engraver with a background worker thread.'''
        
        # Task queue - holds at most 1 pending task (the newest)
        self._task_queue: queue.Queue[Optional[EngraveTask]] = queue.Queue()
        
        # Current task being processed
        self._current_task: Optional[EngraveTask] = None
        self._current_task_lock = threading.Lock()
        
        # Worker thread
        self._worker_thread: Optional[threading.Thread] = None
        self._running = False
        self._shutdown_event = threading.Event()
        
        # Task ID counter for debugging
        self._task_id_counter = 0
        self._task_id_lock = threading.Lock()
        
        # Statistics
        self._tasks_submitted = 0
        self._tasks_completed = 0
        self._tasks_skipped = 0
        
        # Start worker thread
        self._start_worker()
    
    def _start_worker(self):
        '''Start the background worker thread.'''
        if self._worker_thread is not None and self._worker_thread.is_alive():
            return
        
        self._running = True
        self._shutdown_event.clear()
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            name='EngraverWorker',
            daemon=True
        )
        self._worker_thread.start()
        print("Engraver: Worker thread started")
    
    def _worker_loop(self):
        '''Main worker thread loop - processes tasks from the queue.'''
        print("Engraver: Worker loop started")
        
        while self._running:
            try:
                # Wait for next task (blocking, 1 second timeout)
                task = self._task_queue.get(timeout=1.0)
                
                # None task signals shutdown
                if task is None:
                    print("Engraver: Received shutdown signal")
                    break
                
                # Check if there's a newer task already waiting
                # If so, skip this one and process the newer one
                if not self._task_queue.empty():
                    # Discard current task, get the newest one
                    while not self._task_queue.empty():
                        try:
                            newer_task = self._task_queue.get_nowait()
                            if newer_task is not None:
                                print(f"Engraver: Skipping task {task.task_id}, "
                                      f"jumping to newer task {newer_task.task_id}")
                                self._tasks_skipped += 1
                                task = newer_task
                        except queue.Empty:
                            break
                
                # Process the task
                self._process_task(task)
                
            except queue.Empty:
                # No task available, continue waiting
                continue
            except Exception as e:
                print(f"Engraver: Worker loop error: {e}")
                import traceback
                traceback.print_exc()
        
        print("Engraver: Worker loop stopped")
    
    def _process_task(self, task: EngraveTask):
        '''Process a single engraving task.
        
        Args:
            task: The EngraveTask to process
        '''
        with self._current_task_lock:
            self._current_task = task
        
        print(f"Engraver: Processing task {task.task_id}")
        
        success = False
        error_msg = None
        
        try:
            # PHASE 1: Deep copy score for thread-safe access
            score_copy = self._safe_copy_score(task.score)
            
            # PHASE 2: Perform layout calculations (CPU-intensive)
            layout_data = self._calculate_layout(score_copy)
            
            # PHASE 3: Schedule canvas drawing on main thread (Kivy requirement)
            # All Kivy widget operations MUST happen on the main thread
            def draw_on_main_thread(dt):
                try:
                    self._draw_to_canvas(task.canvas, layout_data)
                    # Call success callback if provided
                    if task.callback:
                        task.callback(True, None)
                except Exception as e:
                    print(f"Engraver: Canvas drawing failed: {e}")
                    if task.callback:
                        task.callback(False, str(e))
            
            Clock.schedule_once(draw_on_main_thread, 0)
            
            success = True
            self._tasks_completed += 1
            
        except Exception as e:
            error_msg = str(e)
            print(f"Engraver: Task {task.task_id} failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Call error callback on main thread
            if task.callback:
                def error_callback(dt):
                    task.callback(False, error_msg)
                Clock.schedule_once(error_callback, 0)
        
        finally:
            with self._current_task_lock:
                self._current_task = None
            
            print(f"Engraver: Task {task.task_id} completed "
                  f"(success={success}, stats: {self._tasks_completed} completed, "
                  f"{self._tasks_skipped} skipped)")
    
    def _is_print_preview_canvas(self, canvas: Any) -> bool:
        '''Detect if the given canvas is the print preview canvas.
        
        Args:
            canvas: Canvas widget to check
            
        Returns:
            True if this is the print preview canvas, False otherwise
        '''
        try:
            # Try to get the GUI instance and check if this canvas matches the preview
            from kivy.app import App
            app = App.get_running_app()
            if app and hasattr(app, 'gui') and app.gui:
                preview_canvas = app.gui.get_preview_widget()
                return canvas is preview_canvas
        except Exception:
            pass
        return False
    
    def _safe_copy_score(self, score: SCORE) -> SCORE:
        '''Create a thread-safe deep copy of the score.
        
        Args:
            score: The SCORE object to copy
            
        Returns:
            A deep copy safe for background processing
            
        Raises:
            Exception: If deep copy fails
        '''
        if score is None:
            print("Engraver: WARNING - Cannot copy None score!")
            return None
            
        try:
            score_copy = deepcopy(score)
            if score_copy is None:
                print("Engraver: WARNING - deepcopy returned None!")
            return score_copy
        except Exception as e:
            print(f"Engraver: Error copying score: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _calculate_layout(self, score: SCORE) -> LayoutData:
        '''Calculate complete layout structure (DOC) for Klavarskribo/PianoScript notation.
        
        This is the main pre-calculation phase. All heavy computation happens here.
        Runs in background thread.
        
        Process:
        1. Generate structural events (barlines, gridlines, time signatures)
        2. Process notes (split on barlines/linebreaks, add decorations)
        3. Process beams and slurs
        4. Calculate staff dimensions based on pitch ranges
        5. Organize events into lines (based on linebreaks)
        6. Organize lines into pages (based on page width)
        
        Args:
            score: Deep copy of SCORE (thread-safe)
            
        Returns:
            LayoutData with pre-calculated positions
        '''
        
        print("Engraver: Starting layout calculation...")
        
        # Safety check
        if score is None:
            print("Engraver: ERROR - score is None!")
            return LayoutData(DOC=[[[]]], leftover_page_space=[0.0], staff_dimensions=[], 
                            staff_ranges=[], barline_times=[])
        
        start_time = time.time()
        
        # Initialize DOC structure: [page][line][event]
        DOC = []
        
        # Data to collect
        leftover_page_space = []
        staff_dimensions = []
        staff_ranges = []
        barline_times = []
        
        # ====================================================================
        # STEP 1: Generate structural events (barlines, gridlines, time sigs)
        # ====================================================================
        
        events = self._generate_structural_events(score, barline_times)
        print(f"Engraver: Generated {len(barline_times)} barlines, {len(events)} structural events")
        
        # ====================================================================
        # STEP 2: Process notes (split on barlines/linebreaks, add to events)
        # ====================================================================
        
        events = self._process_notes(score, events, barline_times)
        print(f"Engraver: Processed notes, total events: {len(events)}")
        
        # ====================================================================
        # STEP 3: Add decorations (continuation dots, stop signs, stems)
        # ====================================================================
        
        events = self._add_note_decorations(score, events)
        print(f"Engraver: Added decorations")
        
        # ====================================================================
        # STEP 4: Process beams
        # ====================================================================
        
        events = self._process_beams(score, events)
        print(f"Engraver: Processed beams")
        
        # ====================================================================
        # STEP 5: Add other events (slurs, text, tempo, etc.)
        # ====================================================================
        
        events = self._add_other_events(score, events)
        print(f"Engraver: Added other events, total: {len(events)}")
        
        # ====================================================================
        # STEP 6: Sort events by time
        # ====================================================================
        
        events = sorted(events, key=lambda e: (e.get('time', 0.0), e.get('type', '')))
        
        # ====================================================================
        # STEP 7: Organize into lines (based on linebreaks)
        # ====================================================================
        
        line_docs = self._organize_into_lines(score, events)
        print(f"Engraver: Organized into {len(line_docs)} lines")
        
        # ====================================================================
        # STEP 8: Calculate staff dimensions for each line
        # ====================================================================
        
        staff_dimensions, staff_ranges = self._calculate_staff_dimensions(score, line_docs)
        print(f"Engraver: Calculated staff dimensions")
        
        # ====================================================================
        # STEP 9: Organize lines into pages (pagination)
        # ====================================================================
        
        DOC, leftover_page_space = self._organize_into_pages(
            score, line_docs, staff_dimensions)
        print(f"Engraver: Organized into {len(DOC)} pages")
        
        # ====================================================================
        # STEP 10: Return complete layout data
        # ====================================================================
        
        layout_data = LayoutData(
            DOC=DOC,
            leftover_page_space=leftover_page_space,
            staff_dimensions=staff_dimensions,
            staff_ranges=staff_ranges,
            barline_times=barline_times,
            total_pages=len(DOC),
            current_page=0  # Will be set by caller
        )
        
        calc_time = time.time() - start_time
        total_events = sum(len(event) for page in DOC for line in page for event in line)
        print(f"Engraver: Layout calculated in {calc_time:.3f}s - "
              f"{len(DOC)} pages, {len(line_docs)} lines, {total_events} events")
        
        return layout_data
    
    # ========================================================================
    # Layout Calculation Helper Methods (Background Thread)
    # ========================================================================
    
    def _generate_structural_events(self, score: SCORE, barline_times: List[float]) -> List[Dict]:
        '''Generate barlines, gridlines, time signatures from baseGrid.
        
        Args:
            score: The SCORE object
            barline_times: List to populate with barline tick positions
            
        Returns:
            List of structural events (barlines, gridlines, time sigs)
        '''
        events = []
        time_ticks = 0.0
        FRACTION = 0.01  # Small offset for event ordering
        
        # Process each baseGrid
        for grid in score.baseGrid:
            # Calculate measure duration in ticks
            quarter_note_ticks = getattr(score, 'quarterNoteUnit', 256.0)
            measure_ticks = (grid.numerator / grid.denominator) * 4.0 * quarter_note_ticks
            
            # Generate barlines and gridlines for each measure
            for measure_num in range(grid.measureAmount):
                measure_start = time_ticks + (measure_num * measure_ticks)
                
                # Add barline and double barline (double is slightly before for ordering)
                barline_times.append(measure_start)
                events.append({
                    'type': 'barline',
                    'time': measure_start,
                    'measure_num': measure_num + 1
                })
                events.append({
                    'type': 'barlinedouble',
                    'time': measure_start - FRACTION
                })
                
                # Add time signature indicator at first measure of grid
                if measure_num == 0 and grid.timeSignatureIndicatorVisible:
                    events.append({
                        'type': 'timesignature',
                        'time': time_ticks,
                        'numerator': grid.numerator,
                        'denominator': grid.denominator,
                        'visible': grid.timeSignatureIndicatorVisible
                    })
                
                # Add gridlines within the measure
                for grid_time in grid.gridTimes:
                    gridline_time = measure_start + grid_time
                    if gridline_time < measure_start + measure_ticks:
                        events.append({
                            'type': 'gridline',
                            'time': gridline_time
                        })
                        events.append({
                            'type': 'gridlinedouble',
                            'time': gridline_time - FRACTION
                        })
            
            # Move to next grid's start time
            time_ticks += grid.measureAmount * measure_ticks
        
        # Add final endbarline
        total_ticks = time_ticks
        events.append({
            'type': 'endbarline',
            'time': total_ticks - FRACTION
        })
        
        return events
    
    def _process_notes(self, score: SCORE, events: List[Dict], barline_times: List[float]) -> List[Dict]:
        '''Process notes: split on barlines/linebreaks if needed.
        
        Args:
            score: The SCORE object
            events: Existing events list
            barline_times: Barline positions for splitting
            
        Returns:
            Events list with processed notes
        '''
        
        # TODO: Implement note splitting logic
        # For each stave, for each note:
        # - Check if note crosses a barline
        # - If yes, split into note + notesplit segments
        # - Add all segments to events
        
        for stave_idx, stave in enumerate(score.stave):
            for note in stave.event.note:
                # Simple case: add note as-is (no splitting yet)
                events.append({
                    'type': 'note',
                    'time': note.time,
                    'duration': note.duration,
                    'pitch': note.pitch,
                    'stave_idx': stave_idx,
                    'color': getattr(note, 'color', '#000000'),
                    'hand': getattr(note, 'hand', 'r'),
                    'note_obj': note
                })
        
        return events
    
    def _add_note_decorations(self, score: SCORE, events: List[Dict]) -> List[Dict]:
        '''Add continuation dots, stop signs, connect stems.
        
        Analyzes overlapping notes to add visual indicators.
        
        Args:
            score: The SCORE object
            events: Events list with notes
            
        Returns:
            Events list with decorations added
        '''
        
        # TODO: Implement decoration logic
        # - Analyze overlapping notes
        # - Where note A continues while note B starts → add continuation dot
        # - Where note ends → add stop sign
        # - Where notes at same time/pitch → add connect stem
        
        return events
    
    def _process_beams(self, score: SCORE, events: List[Dict]) -> List[Dict]:
        '''Group rapid notes into beam groups.
        
        Args:
            score: The SCORE object
            events: Events list
            
        Returns:
            Events list with beam events added
        '''
        
        # Add beam events from score
        for stave_idx, stave in enumerate(score.stave):
            for beam in stave.event.beam:
                events.append({
                    'type': 'beam',
                    'time': beam.time,
                    'stave_idx': stave_idx,
                    'beam_obj': beam
                })
        
        return events
    
    def _add_other_events(self, score: SCORE, events: List[Dict]) -> List[Dict]:
        '''Add slurs, text, tempo, grace notes, etc.
        
        Args:
            score: The SCORE object
            events: Events list
            
        Returns:
            Events list with all events
        '''
        
        for stave_idx, stave in enumerate(score.stave):
            # Slurs
            for slur in stave.event.slur:
                events.append({
                    'type': 'slur',
                    'time': slur.time,
                    'stave_idx': stave_idx,
                    'slur_obj': slur
                })
            
            # Text
            for text in stave.event.text:
                events.append({
                    'type': 'text',
                    'time': text.time,
                    'stave_idx': stave_idx,
                    'text_obj': text
                })
            
            # Tempo
            for tempo in stave.event.tempo:
                events.append({
                    'type': 'tempo',
                    'time': tempo.time,
                    'stave_idx': stave_idx,
                    'tempo_obj': tempo
                })
            
            # Grace notes
            for grace in stave.event.graceNote:
                events.append({
                    'type': 'gracenote',
                    'time': grace.time,
                    'stave_idx': stave_idx,
                    'gracenote_obj': grace
                })
            
            # Count lines
            for count in stave.event.countLine:
                events.append({
                    'type': 'countline',
                    'time': count.time,
                    'stave_idx': stave_idx,
                    'countline_obj': count
                })
        
        return events
    
    def _organize_into_lines(self, score: SCORE, events: List[Dict]) -> List[List[Dict]]:
        '''Organize events into lines based on linebreak markers.
        
        Args:
            score: The SCORE object
            events: Sorted events list
            
        Returns:
            List of lines, each line is a list of events
        '''
        
        lines = []
        current_line = []
        
        # Get linebreak times
        linebreak_times = sorted([lb.time for lb in score.lineBreak])
        linebreak_idx = 0
        
        for event in events:
            event_time = event.get('time', 0.0)
            
            # Check if we've crossed a linebreak
            while (linebreak_idx < len(linebreak_times) - 1 and 
                   event_time >= linebreak_times[linebreak_idx + 1]):
                # Start new line
                if current_line:
                    lines.append(current_line)
                    current_line = []
                linebreak_idx += 1
            
            current_line.append(event)
        
        # Add final line
        if current_line:
            lines.append(current_line)
        
        return lines if lines else [[]]
    
    def _calculate_staff_dimensions(
        self, 
        score: SCORE, 
        line_docs: List[List[Dict]]
    ) -> Tuple[List[List[Dict]], List[List[Tuple[int, int]]]]:
        '''Calculate width and margins for each staff in each line.
        
        Args:
            score: The SCORE object
            line_docs: Lines of events
            
        Returns:
            (staff_dimensions, staff_ranges)
            - staff_dimensions: [line][staff] = {staff_width, margin_left, margin_right}
            - staff_ranges: [line][staff] = (min_pitch, max_pitch)
        '''
        
        staff_dimensions = []
        staff_ranges = []
        
        # TODO: Calculate based on pitch ranges in each line
        # For now, return placeholder
        for line in line_docs:
            line_dims = []
            line_ranges = []
            for stave in score.stave:
                line_dims.append({
                    'staff_width': 140.0,  # mm
                    'margin_left': 35.0,
                    'margin_right': 35.0
                })
                line_ranges.append((1, 88))  # Full piano range
            staff_dimensions.append(line_dims)
            staff_ranges.append(line_ranges)
        
        return staff_dimensions, staff_ranges
    
    def _organize_into_pages(
        self,
        score: SCORE,
        line_docs: List[List[Dict]],
        staff_dimensions: List[List[Dict]]
    ) -> Tuple[List[List[List[Dict]]], List[float]]:
        '''Organize lines into pages based on page height.
        
        Args:
            score: The SCORE object
            line_docs: Lines of events
            staff_dimensions: Staff dimensions per line
            
        Returns:
            (DOC, leftover_page_space)
            - DOC: [page][line][event]
            - leftover_page_space: Extra vertical space per page
        '''
        
        DOC = []
        leftover_page_space = []
        
        # For now, simple pagination: all lines on one page
        if line_docs:
            DOC.append(line_docs)
            leftover_page_space.append(0.0)
        
        return DOC if DOC else [[[]]], leftover_page_space if leftover_page_space else [0.0]
    
    def _draw_to_canvas(self, canvas: Any, layout_data: LayoutData):
        '''Draw layout to canvas in chunks to prevent UI freezing.
        
        MUST run on main thread (Kivy requirement).
        Draws in batches of CHUNK_SIZE operations per frame to maintain 60fps.
        
        Args:
            canvas: The Canvas widget to draw on
            layout_data: Pre-calculated layout from _calculate_layout
        '''
        
        print(f"Engraver: Starting chunked canvas drawing for canvas: {canvas}")
        
        # Detect if this is the print preview canvas
        is_print_preview = self._is_print_preview_canvas(canvas)
        print(f"Engraver: Is print preview canvas: {is_print_preview}")
        
        # Clear canvas
        try:
            if hasattr(canvas, 'clear'):
                canvas.clear()
            elif hasattr(canvas, 'delete_all'):
                canvas.delete_all()
        except Exception as e:
            print(f"Engraver: Warning - could not clear canvas: {e}")
        
        # Prepare all drawing operations as a list of callables
        draw_operations = []
        
        # ====================================================================
        # Collect drawing operations (fast, doesn't draw yet)
        # ====================================================================
        
        # Only draw test visualization on print preview
        if is_print_preview:
            # Page boundaries and background
            draw_operations.extend(self._prepare_page_operations(layout_data))
            
            # Header/footer
            draw_operations.extend(self._prepare_header_operations(layout_data))
            draw_operations.extend(self._prepare_footer_operations(layout_data))
            
            # Staff lines and mini-piano
            draw_operations.extend(self._prepare_staff_operations(layout_data))
            
            # Structural elements
            draw_operations.extend(self._prepare_barline_operations(layout_data))
            draw_operations.extend(self._prepare_gridline_operations(layout_data))
            draw_operations.extend(self._prepare_time_signature_operations(layout_data))
            
            # Musical elements
            draw_operations.extend(self._prepare_note_operations(layout_data))
            draw_operations.extend(self._prepare_stem_operations(layout_data))
            draw_operations.extend(self._prepare_beam_operations(layout_data))
            draw_operations.extend(self._prepare_decoration_operations(layout_data))
            draw_operations.extend(self._prepare_slur_operations(layout_data))
            draw_operations.extend(self._prepare_text_operations(layout_data))
            draw_operations.extend(self._prepare_gracenote_operations(layout_data))
            draw_operations.extend(self._prepare_countline_operations(layout_data))
        
        total_operations = len(draw_operations)
        print(f"Engraver: Prepared {total_operations} drawing operations")
        
        if total_operations == 0:
            print("Engraver: WARNING - No drawing operations prepared! Check _prepare_* methods.")
            return
        
        # ====================================================================
        # Draw in chunks to maintain 60fps
        # ====================================================================
        
        CHUNK_SIZE = 150  # Operations per frame (~16ms target at 60fps)
        operation_index = [0]  # Use list for closure modification
        
        def draw_chunk(dt):
            '''Draw a chunk of operations, return True to continue scheduling.'''
            start_idx = operation_index[0]
            end_idx = min(start_idx + CHUNK_SIZE, total_operations)
            
            # Draw this chunk
            for i in range(start_idx, end_idx):
                try:
                    draw_operations[i](canvas)
                except Exception as e:
                    print(f"Engraver: Error in draw operation {i}: {e}")
            
            operation_index[0] = end_idx
            
            # Log progress periodically
            if end_idx % 500 == 0 or end_idx == total_operations:
                progress = (end_idx / total_operations) * 100
                print(f"Engraver: Drawing progress: {progress:.1f}% "
                      f"({end_idx}/{total_operations})")
            
            # Continue or stop
            if end_idx < total_operations:
                return True  # Continue scheduling
            else:
                print(f"Engraver: Drawing complete!")
                return False  # Stop scheduling
        
        # Schedule chunked drawing (runs every frame until complete)
        Clock.schedule_interval(draw_chunk, 0)  # 0 = next frame
    
    # ========================================================================
    # Drawing Operation Preparers (Return lists of callables)
    # ========================================================================
    
    def _prepare_page_operations(self, layout_data: LayoutData) -> List[Callable]:
        '''Prepare page boundary drawing operations.'''
        operations = []
        
        # TODO: Draw page bounds, margins, etc.
        
        # TEMPORARY: Draw a test rectangle to verify engraver is working
        def draw_test_rect(canvas):
            try:
                # Draw a simple test rectangle
                canvas.add_rectangle(
                    x1_mm=10.0,
                    y1_mm=10.0,
                    x2_mm=50.0,
                    y2_mm=50.0,
                    fill=True,
                    fill_color='#FF0000',  # Red hex color
                    outline=False,
                    tags=['test', 'engraver_test']
                )
                # Draw test text showing DOC info
                num_pages = len(layout_data.DOC)
                total_lines = sum(len(page) for page in layout_data.DOC)
                total_events = sum(len(line) for page in layout_data.DOC for line in page)
                
                canvas.add_text(
                    text=f'Engraver: {num_pages} pages, {total_lines} lines, {total_events} events',
                    x_mm=60.0,
                    y_mm=20.0,
                    font_size_pt=12,  # Corrected parameter name
                    color='#000000',  # Black hex color
                    tags=['test', 'engraver_test']
                )
                
                # Draw some barlines as proof
                if layout_data.DOC:
                    y = 70.0
                    barline_count = 0
                    for page in layout_data.DOC:
                        for line in page:
                            for event in line:
                                if event['type'] == 'barline' and barline_count < 20:
                                    canvas.add_line(
                                        x1_mm=20.0,
                                        y1_mm=y,
                                        x2_mm=20.0,
                                        y2_mm=y + 8.0,
                                        color='#000000',  # Black hex color
                                        width_mm=0.3,
                                        tags=['barline', 'test']
                                    )
                                    barline_count += 1
                                    y += 10.0
                    
                    canvas.add_text(
                        text=f'{barline_count} barlines drawn',
                        x_mm=30.0,
                        y_mm=70.0,
                        font_size_pt=10,  # Corrected parameter name
                        color='#0000FF',  # Blue hex color
                        tags=['test']
                    )
            except Exception as e:
                print(f"Engraver: Error drawing test shapes: {e}")
                import traceback
                traceback.print_exc()
        
        operations.append(draw_test_rect)
        
        return operations
    
    def _prepare_header_operations(self, layout_data: LayoutData) -> List[Callable]:
        '''Prepare title/composer/header text operations.'''
        operations = []
        
        # TODO: Title, composer, timestamp
        
        return operations
    
    def _prepare_footer_operations(self, layout_data: LayoutData) -> List[Callable]:
        '''Prepare footer (page numbers, copyright) operations.'''
        operations = []
        
        # TODO: Page numbers, copyright
        
        return operations
    
    def _prepare_staff_operations(self, layout_data: LayoutData) -> List[Callable]:
        '''Prepare staff line drawing operations.'''
        operations = []
        
        # TODO: Vertical staff lines (piano keys), mini-piano keyboard
        
        return operations
    
    def _prepare_barline_operations(self, layout_data: LayoutData) -> List[Callable]:
        '''Prepare barline drawing operations.'''
        operations = []
        
        # TODO: For each barline event, create lambda to draw horizontal line
        # across all staves. Handle endbarline (thicker).
        
        return operations
    
    def _prepare_gridline_operations(self, layout_data: LayoutData) -> List[Callable]:
        '''Prepare gridline (subdivision) drawing operations.'''
        operations = []
        
        # TODO: For each gridline event, create lambda to draw dashed line
        
        return operations
    
    def _prepare_time_signature_operations(self, layout_data: LayoutData) -> List[Callable]:
        '''Prepare time signature drawing operations.'''
        operations = []
        
        # TODO: Draw numerator, divider, denominator
        
        return operations
    
    def _prepare_note_operations(self, layout_data: LayoutData) -> List[Callable]:
        '''Prepare note head and body drawing operations.'''
        operations = []
        
        # TODO: For each note event:
        # - Black key notes: filled oval
        # - White key notes: hollow oval
        # - Left hand indicator dot
        # - Midi-note body (colored rectangle showing duration)
        
        return operations
    
    def _prepare_stem_operations(self, layout_data: LayoutData) -> List[Callable]:
        '''Prepare stem drawing operations.'''
        operations = []
        
        # TODO: Horizontal stems extending from note heads
        # - Right hand: extend right
        # - Left hand: extend left
        # - Connect stems for chords
        
        return operations
    
    def _prepare_beam_operations(self, layout_data: LayoutData) -> List[Callable]:
        '''Prepare beam drawing operations.'''
        operations = []
        
        # TODO: Draw angled beams connecting rapid note sequences
        
        return operations
    
    def _prepare_decoration_operations(self, layout_data: LayoutData) -> List[Callable]:
        '''Prepare continuation dots, stop signs, etc.'''
        operations = []
        
        # TODO: Continuation dots (triangles/dots when note continues)
        # TODO: Stop signs (X or triangle when note ends)
        
        return operations
    
    def _prepare_slur_operations(self, layout_data: LayoutData) -> List[Callable]:
        '''Prepare slur/phrase curve drawing operations.'''
        operations = []
        
        # TODO: Bezier curves for slurs/phrases
        
        return operations
    
    def _prepare_text_operations(self, layout_data: LayoutData) -> List[Callable]:
        '''Prepare text annotation drawing operations.'''
        operations = []
        
        # TODO: Text at specified positions with alignment
        
        return operations
    
    def _prepare_gracenote_operations(self, layout_data: LayoutData) -> List[Callable]:
        '''Prepare grace note drawing operations.'''
        operations = []
        
        # TODO: Smaller note heads for grace notes
        
        return operations
    
    def _prepare_countline_operations(self, layout_data: LayoutData) -> List[Callable]:
        '''Prepare count line (rhythm guide) drawing operations.'''
        operations = []
        
        # TODO: Count lines for rhythm guidance
        
        return operations
    
    def do_engrave(
        self,
        score: Any,
        canvas: Any,
        callback: Optional[Callable[[bool, Optional[str]], None]] = None
    ):
        '''Submit an engraving task.
        
        If a task is currently processing, this new task will be queued.
        If a task is already queued, it will be replaced with this newer task.
        
        Thread-safe. Can be called from any thread (typically main/UI thread).
        
        Args:
            score: The SCORE object to engrave
            canvas: The Canvas widget to draw on
            callback: Optional callback(success: bool, error: Optional[str])
                     Called on main thread when engraving completes
        '''
        # Generate unique task ID
        with self._task_id_lock:
            self._task_id_counter += 1
            task_id = self._task_id_counter
        
        # Create task
        task = EngraveTask(score, canvas, callback, task_id)
        
        # Clear any existing queued task (keep only the newest)
        while not self._task_queue.empty():
            try:
                old_task = self._task_queue.get_nowait()
                if old_task is not None:
                    print(f"Engraver: Discarding old queued task {old_task.task_id}")
                    self._tasks_skipped += 1
            except queue.Empty:
                break
        
        # Queue the new task
        self._task_queue.put(task)
        self._tasks_submitted += 1
        
        print(f"Engraver: Task {task_id} submitted "
              f"(queue size: {self._task_queue.qsize()})")
    
    def shutdown(self):
        '''Shutdown the engraver and stop the worker thread.
        
        Waits for current task to complete before shutting down.
        '''
        print("Engraver: Shutdown requested")
        
        self._running = False
        
        # Send shutdown signal
        self._task_queue.put(None)
        
        # Wait for worker thread to finish
        if self._worker_thread is not None:
            self._worker_thread.join(timeout=5.0)
            if self._worker_thread.is_alive():
                print("Engraver: Worker thread did not stop cleanly")
            else:
                print("Engraver: Worker thread stopped")
        
        print(f"Engraver: Shutdown complete "
              f"(processed {self._tasks_completed}/{self._tasks_submitted} tasks, "
              f"skipped {self._tasks_skipped})")
    
    def get_stats(self) -> dict:
        '''Get engraver statistics.
        
        Returns:
            Dictionary with statistics:
            {
                'submitted': int,
                'completed': int,
                'skipped': int,
                'current_task_id': Optional[int],
                'queue_size': int
            }
        '''
        with self._current_task_lock:
            current_id = self._current_task.task_id if self._current_task else None
        
        return {
            'submitted': self._tasks_submitted,
            'completed': self._tasks_completed,
            'skipped': self._tasks_skipped,
            'current_task_id': current_id,
            'queue_size': self._task_queue.qsize()
        }


# Singleton instance
_engraver_instance: Optional[Engraver] = None
_engraver_lock = threading.Lock()


def get_engraver_instance() -> Engraver:
    '''Get the global Engraver singleton instance.
    
    Thread-safe. Creates the instance on first call.
    
    Returns:
        The global Engraver instance
    '''
    global _engraver_instance
    
    if _engraver_instance is None:
        with _engraver_lock:
            # Double-checked locking
            if _engraver_instance is None:
                _engraver_instance = Engraver()
    
    return _engraver_instance


__all__ = ['Engraver', 'EngraveTask', 'get_engraver_instance']
