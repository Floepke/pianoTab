# Engraver Usage Guide

## Overview

The Engraver is a multi-threaded system that handles complex score layout calculations and rendering. It automatically manages task queuing and discards outdated render requests to keep the UI responsive.

## Architecture

```
┌─────────────────┐
│  Tool (UI)      │  ← User interaction
│  modifies SCORE │
└────────┬────────┘
         │ calls trigger_engrave()
         ▼
┌─────────────────┐
│  BaseTool       │
│  .trigger_      │
│   engrave()     │
└────────┬────────┘
         │ submits task
         ▼
┌─────────────────┐
│  Engraver       │  ← Singleton instance
│  Queue          │
└────────┬────────┘
         │ discards old tasks
         │ processes newest task
         ▼
┌─────────────────┐
│  Worker Thread  │  ← Background thread
│  - Deep copy    │
│  - Calculate    │
│    layout       │
└────────┬────────┘
         │ schedules on main thread
         ▼
┌─────────────────┐
│  Canvas Drawing │  ← Main/UI thread (Kivy)
│  - Draw to      │
│    canvas       │
└─────────────────┘
```

## Integration in Tools

### Step 1: Import and Use in BaseTool Subclasses

After modifying the SCORE, call `self.trigger_engrave()`:

```python
# In any tool (e.g., note_tool.py, beam_tool.py, etc.)

def on_left_click(self, x: float, y: float) -> bool:
    """Add a note to the score."""
    
    # 1. Modify the SCORE
    note = Note(pitch=pitch, time_ticks=time_ticks, duration=duration)
    self.score.stave[stave_idx].event.note.append(note)
    
    # 2. Trigger engraving (automatic layout + rendering)
    self.trigger_engrave()
    
    return True
```

### Step 2: Replace Manual Redraw Calls

**Before (old approach):**
```python
# After modifying score
self.editor.canvas._redraw_all()  # Blocks UI thread
```

**After (new approach):**
```python
# After modifying score
self.trigger_engrave()  # Non-blocking, threaded
```

## Task Queue Behavior

The engraver maintains an intelligent queue:

1. **Current Task**: One task is actively processing in the background thread
2. **Queued Task**: At most ONE pending task is held in the queue
3. **New Tasks**: When submitted:
   - If queue is empty → task is queued
   - If queue has a task → old task is **discarded**, new task replaces it
4. **Task Skipping**: When current task completes:
   - Checks if there's a newer task in the queue
   - Processes the **newest** task
   - Skips any intermediate tasks

### Example Timeline

```
Time  User Action           Queue State              Thread State
────  ───────────────────   ──────────────────────   ─────────────────
0ms   Edit note A           [A]                      Processing A
10ms  Edit note B           [B] (A discarded)        Processing A
20ms  Edit note C           [C] (B discarded)        Processing A
100ms A completes           [C]                      Starting C
110ms Edit note D           [D] (C interrupted)      Processing C
200ms C completes           [D]                      Starting D
300ms D completes           []                       Idle
```

Result: Only A, C, and D are actually rendered. B was never processed because it was immediately superseded.

## Implementing the Engraver Logic

The engraver template provides three key methods to implement:

### 1. `_calculate_layout(score: SCORE) -> dict`

Runs in **background thread** - CPU-intensive work happens here.

```python
def _calculate_layout(self, score: SCORE) -> dict:
    """Calculate layout for all score elements.
    
    This runs in a background thread - safe to do heavy computation.
    """
    layout_data = {
        'notes': [],
        'beams': [],
        'slurs': [],
        # ... etc
    }
    
    # Example: Calculate note positions
    for stave in score.stave:
        for note in stave.event.note:
            x_mm = self._pitch_to_x(note.pitch)
            y_mm = self._time_to_y(note.time_ticks)
            layout_data['notes'].append({
                'x': x_mm,
                'y': y_mm,
                'width': note_width,
                'height': note_height,
                'color': note.color,
                # ... other properties
            })
    
    return layout_data
```

### 2. `_draw_to_canvas(canvas: Canvas, layout_data: dict)`

Runs on **main thread** - Kivy drawing happens here.

```python
def _draw_to_canvas(self, canvas: Canvas, layout_data: dict):
    """Draw layout data to canvas.
    
    MUST run on main thread (Kivy requirement).
    Called via Clock.schedule_once automatically.
    """
    # Clear canvas
    canvas.delete_all()
    
    # Draw notes
    for note_data in layout_data['notes']:
        canvas.add_oval(
            x=note_data['x'],
            y=note_data['y'],
            width=note_data['width'],
            height=note_data['height'],
            fill=note_data['color'],
            tags=['note', f"note_{note_data['id']}"]
        )
    
    # Draw beams, slurs, etc.
    # ...
```

### 3. `_safe_copy_score(score: SCORE) -> SCORE`

Deep copies the score for thread safety.

Already implemented, but you may need to customize if your SCORE has special requirements:

```python
def _safe_copy_score(self, score: SCORE) -> SCORE:
    """Deep copy the score for thread-safe processing."""
    try:
        return deepcopy(score)
    except Exception as e:
        # Handle special cases if deepcopy fails
        print(f"Deep copy failed: {e}")
        return score  # Fallback (not thread-safe!)
```

## Monitoring and Debugging

### Get Statistics

```python
from engraver import get_engraver_instance

engraver = get_engraver_instance()
stats = engraver.get_stats()

print(f"Submitted: {stats['submitted']}")
print(f"Completed: {stats['completed']}")
print(f"Skipped: {stats['skipped']}")
print(f"Queue size: {stats['queue_size']}")
print(f"Current task: {stats['current_task_id']}")
```

### Console Logging

The engraver automatically logs:
- Task submission: `"Engraver: Task X submitted (queue size: Y)"`
- Task skipping: `"Engraver: Skipping task X, jumping to newer task Y"`
- Task processing: `"Engraver: Processing task X"`
- Task completion: `"Engraver: Task X completed (success=True, stats: ...)"`

## Migration Checklist

To migrate existing tools to use the engraver:

- [ ] Import engraver at module level (already in `base_tool.py`)
- [ ] Replace `canvas._redraw_all()` with `self.trigger_engrave()`
- [ ] Remove manual layout calculations from tools
- [ ] Implement `_calculate_layout()` in `engraver.py`
- [ ] Implement `_draw_to_canvas()` in `engraver.py`
- [ ] Test with rapid score modifications
- [ ] Verify task skipping works (check console logs)
- [ ] Monitor statistics during heavy use

## Best Practices

1. **Always call `trigger_engrave()` after modifying SCORE**
   - Even for small changes
   - The queue will handle batching automatically

2. **Don't worry about calling too often**
   - The engraver discards old tasks
   - Only the latest change gets processed

3. **Keep `_calculate_layout()` pure**
   - No Kivy widget operations
   - No canvas drawing
   - Only data transformation

4. **Keep `_draw_to_canvas()` fast**
   - Pre-calculated data from layout phase
   - Simple drawing operations only

5. **Handle errors gracefully**
   - Layout errors are logged but don't crash the app
   - Canvas drawing errors are caught and reported

## Shutdown

The engraver automatically shuts down when the app closes. To manually shutdown:

```python
from engraver import get_engraver_instance

engraver = get_engraver_instance()
engraver.shutdown()
```

This waits for the current task to complete before stopping the worker thread.
