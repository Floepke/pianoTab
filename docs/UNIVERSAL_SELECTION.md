# Universal Selection Feature

## Overview

Selection is now a **universal feature** that works across all tools in the piano roll editor. It's activated by holding the **Shift** key, similar to selection in Adobe Photoshop, Illustrator, and other professional design tools.

## How to Use

### Creating a Selection

1. **Hold Shift** and **drag** with the left mouse button to create a selection rectangle
2. The rectangle will be drawn with a blue dashed outline
3. All notes whose noteheads fall within the rectangle will be selected
4. Selected notes are highlighted in the accent color

### Selection Behavior

- **Shift released during drag**: If you release Shift while dragging, the rectangle continues until you release the mouse button
- **Shift+click on empty space**: Clears the current selection
- **Works in any tool**: Selection works whether you're in Note tool, Beam tool, or any other tool mode
- **Persists across tool switches**: Your selection remains active when you switch between tools

### Keyboard Shortcuts (When Selection is Active)

| Key | Action |
|-----|--------|
| **Ctrl+C** | Copy selected elements to clipboard |
| **Ctrl+X** | Cut selected elements (copy + delete) |
| **Ctrl+V** | Paste clipboard at cursor position |
| **Delete** or **Backspace** | Delete selected elements |
| **Escape** | Clear selection |
| **Up Arrow** | Move selection earlier in time (by grid step) |
| **Down Arrow** | Move selection later in time (by grid step) |
| **Left Arrow** | Transpose selection down by 1 semitone |
| **Right Arrow** | Transpose selection up by 1 semitone |

### Paste Behavior

- Paste uses the **cursor position** (not mouse position) for timing
- Pasted notes maintain their **original pitch relationships**
- The pasted notes become the new selection
- Each pasted note gets a **unique ID** automatically

## Technical Details

### Architecture

The selection system is implemented as a **SelectionManager** that integrates into the Editor:

```
Editor
  ├── ToolManager (manages active tool)
  └── SelectionManager (universal selection)
```

### Event Flow

1. **Mouse down** (with Shift held):
   - SelectionManager intercepts the event
   - Starts drawing selection rectangle
   - Tool doesn't receive the event

2. **Mouse drag** (during rectangle drawing):
   - SelectionManager updates rectangle
   - Tool doesn't receive drag events

3. **Mouse up** (finishes selection):
   - SelectionManager finds all elements in rectangle
   - Highlights selected elements
   - Returns control to active tool

4. **Keyboard events**:
   - SelectionManager checks for selection-related keys first
   - If not handled, passes to active tool

### Selection Detection

Selection uses **direct coordinate checking**:
- Gets notehead position using `editor.pitch_to_x(note.pitch)` and `editor.time_to_y(note.time)`
- Checks if position falls within rectangle bounds
- Only the **notehead** needs to be in the rectangle (not the entire note stem/tail)

### Drawing Modes

Notes can be drawn in different modes:
- `'note'`: Regular note (black)
- `'cursor'`: Preview note (accent color)
- `'select/edit'`: Note being edited (accent color)
- `'selected'`: Selected note (accent color) ← Used by SelectionManager

## Implementation Files

- **`editor/selection_manager.py`**: Core selection logic
- **`editor/editor.py`**: Integration into Editor class
- **`utils/canvas.py`**: Shift key detection and forwarding
- **`editor/drawer/note_drawer.py`**: `_draw_single_note()` with `draw_mode` support

## Removed Components

The old **Selection tool** (separate tool mode) has been removed:
- ~~`editor/tool/selection_tool.py`~~ (deprecated)
- ~~Selection from tool selector~~ (removed from UI)
- ~~Temporary tool switching on Shift~~ (replaced with universal selection)

Selection is now always available via Shift key, regardless of active tool.

## Future Enhancements

Possible improvements:
- [ ] Support for selecting other element types (beams, slurs, text, etc.)
- [ ] Multi-selection (add to selection with Shift+Ctrl+drag)
- [ ] Select all (Ctrl+A)
- [ ] Invert selection
- [ ] Select by criteria (pitch range, time range, etc.)
- [ ] Selection groups/save selection states
