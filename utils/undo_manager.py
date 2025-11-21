"""
Undo/Redo Manager for SCORE objects.

Maintains a history of SCORE snapshots with a configurable maximum size.
Supports undo (Ctrl+Z) and redo (Ctrl+Shift+Z) operations.

Usage:
    undo_manager = UndoManager(max_history=50)
    undo_manager.save_snapshot(score)  # Call after every change
    score = undo_manager.undo(current_score)  # Returns previous state
    score = undo_manager.redo(current_score)  # Returns next state
"""

from typing import Optional, List
from copy import deepcopy


class UndoManager:
    """Manages undo/redo history for SCORE objects."""
    
    def __init__(self, max_history: int = 50):
        """
        Initialize the undo manager.
        
        Args:
            max_history: Maximum number of snapshots to keep in history
        """
        self.max_history = max_history
        self.history: List = []  # List of SCORE snapshots
        self.current_index: int = -1  # Index of current state in history
        self._ignore_next_save = False  # Flag to prevent double-saves during undo/redo
    
    def save_snapshot(self, score) -> None:
        """
        Save a snapshot of the current SCORE state.
        
        This should be called after every modification to the SCORE.
        Creates a deep copy to preserve the state.
        
        Args:
            score: The SCORE object to snapshot
        """
        if self._ignore_next_save:
            self._ignore_next_save = False
            return
        
        if score is None:
            return
        
        try:
            # Create deep copy of the score
            snapshot = deepcopy(score)
            
            # If we're not at the end of history, discard any "future" states
            if self.current_index < len(self.history) - 1:
                self.history = self.history[:self.current_index + 1]
            
            # Add the new snapshot
            self.history.append(snapshot)
            
            # Enforce max history size
            if len(self.history) > self.max_history:
                self.history.pop(0)
            else:
                self.current_index += 1
            
            # Make sure current_index is valid
            self.current_index = min(self.current_index, len(self.history) - 1)
            
        except Exception as e:
            print(f'ERROR: Failed to save undo snapshot: {e}')
            import traceback
            traceback.print_exc()
    
    def undo(self, current_score) -> Optional[object]:
        """
        Undo to the previous state.
        
        Args:
            current_score: The current SCORE object (saved as latest if needed)
            
        Returns:
            The previous SCORE state, or None if no undo available
        """
        if not self.can_undo():
            print('UndoManager: No undo history available')
            return None
        
        try:
            # If current state isn't saved, save it first
            if self.current_index == len(self.history) - 1:
                # We're at the latest state, save current before going back
                if current_score is not None:
                    snapshot = deepcopy(current_score)
                    self.history.append(snapshot)
                    self.current_index += 1
                    if len(self.history) > self.max_history:
                        self.history.pop(0)
                        self.current_index -= 1
            
            # Move back in history
            self.current_index -= 1
            
            # Return deep copy of the previous state
            self._ignore_next_save = True
            return deepcopy(self.history[self.current_index])
            
        except Exception as e:
            print(f'ERROR: Undo failed: {e}')
            import traceback
            traceback.print_exc()
            return None
    
    def redo(self, current_score) -> Optional[object]:
        """
        Redo to the next state.
        
        Args:
            current_score: The current SCORE object (unused but kept for API consistency)
            
        Returns:
            The next SCORE state, or None if no redo available
        """
        if not self.can_redo():
            print('UndoManager: No redo history available')
            return None
        
        try:
            # Move forward in history
            self.current_index += 1
            
            # Return deep copy of the next state
            self._ignore_next_save = True
            return deepcopy(self.history[self.current_index])
            
        except Exception as e:
            print(f'ERROR: Redo failed: {e}')
            import traceback
            traceback.print_exc()
            return None
    
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return self.current_index > 0
    
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return self.current_index < len(self.history) - 1
    
    def clear(self) -> None:
        """Clear all undo/redo history."""
        self.history.clear()
        self.current_index = -1
        self._ignore_next_save = False
    
    def clear_history(self) -> None:
        """Alias for clear(). Clear all undo/redo history."""
        self.clear()
    
    def get_history_info(self) -> dict:
        """
        Get information about the current history state.
        
        Returns:
            Dict with 'count', 'current_index', 'can_undo', 'can_redo'
        """
        return {
            'count': len(self.history),
            'current_index': self.current_index,
            'can_undo': self.can_undo(),
            'can_redo': self.can_redo(),
        }
