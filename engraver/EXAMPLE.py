"""
Example: Integrating Engraver into a Tool

This file demonstrates how to modify existing tools to use the 
threaded engraver system instead of manual canvas redraws.
"""

from editor.tool.base_tool import BaseTool


class ExampleNoteTool(BaseTool):
    """Example tool showing engraver integration."""
    
    @property
    def name(self) -> str:
        return "Note"
    
    def on_left_click(self, x: float, y: float) -> bool:
        """Add a note at the clicked position."""
        
        # === OLD APPROACH (blocking, slow) ===
        # 1. Modify score
        # note = Note(...)
        # self.score.stave[0].event.note.append(note)
        # 
        # 2. Manually redraw (blocks UI thread)
        # self.editor.canvas._redraw_all()
        
        
        # === NEW APPROACH (non-blocking, fast) ===
        # 1. Modify score (same as before)
        pitch = int(self.x_to_pitch(x))
        time_ticks = self.get_snapped_time_from_y(y)
        duration = self.editor.get_grid_step_ticks()
        
        from file.note import Note
        note = Note(
            pitch=pitch,
            time_ticks=time_ticks,
            duration=duration,
            color='#000000'
        )
        
        # Find stave (simplified - use actual stave detection)
        stave_idx = 0
        self.score.stave[stave_idx].event.note.append(note)
        
        # 2. Trigger engraving (non-blocking, queued, automatic)
        self.trigger_engrave()
        
        return True
    
    def on_right_click(self, x: float, y: float) -> bool:
        """Delete note at position."""
        
        # 1. Find and delete note
        element = self.get_element_at_position(x, y, element_types=['note'])
        if element is None:
            return False
        
        # Remove from score
        stave_idx = self.find_stave_for_element(element)
        if stave_idx is not None:
            stave = self.score.stave[stave_idx]
            if element in stave.event.note:
                stave.event.note.remove(element)
                
                # 2. Trigger engraving to update display
                self.trigger_engrave()
                
                return True
        
        return False
    
    def on_drag_end(self, x: float, y: float) -> bool:
        """Move note via drag."""
        
        # 1. Update note position in score
        # (simplified - actual implementation would track dragged note)
        selected_note = self.get_selected_note()
        if selected_note:
            selected_note.pitch = int(self.x_to_pitch(x))
            selected_note.time_ticks = self.get_snapped_time_from_y(y)
            
            # 2. Trigger engraving
            self.trigger_engrave()
            
            return True
        
        return False
    
    def get_selected_note(self):
        """Helper method (placeholder)."""
        return None


# === Migration Pattern ===

def migrate_tool_to_engraver():
    """
    Step-by-step migration guide:
    
    1. Find all places where SCORE is modified:
       - Adding elements: score.stave[i].event.note.append(...)
       - Removing elements: score.stave[i].event.note.remove(...)
       - Modifying elements: note.pitch = new_pitch
    
    2. After each modification, replace:
       OLD: self.editor.canvas._redraw_all()
       NEW: self.trigger_engrave()
    
    3. Remove any manual layout calculations from the tool:
       - Time-to-Y conversions for drawing
       - Pitch-to-X conversions for drawing
       - These will move to engraver._calculate_layout()
    
    4. Test the tool:
       - Make rapid changes (click many times quickly)
       - Check console for task skipping messages
       - Verify UI stays responsive
    
    That's it! The engraver handles everything else automatically.
    """
    pass


# === Common Patterns ===

class EngravingPatterns:
    """Common patterns for working with the engraver."""
    
    @staticmethod
    def pattern_single_modification(tool):
        """Pattern: Single score modification."""
        # Modify
        tool.score.some_property = new_value
        # Trigger
        tool.trigger_engrave()
    
    @staticmethod
    def pattern_multiple_modifications(tool):
        """Pattern: Multiple related modifications."""
        # Make ALL modifications first
        tool.score.property1 = value1
        tool.score.property2 = value2
        tool.score.stave[0].event.note.append(note)
        
        # THEN trigger once
        # The engraver will process the complete state
        tool.trigger_engrave()
    
    @staticmethod
    def pattern_conditional_modification(tool, condition):
        """Pattern: Modification only if condition met."""
        if condition:
            tool.score.some_property = new_value
            tool.trigger_engrave()
        # If no modification, don't trigger engraving
    
    @staticmethod
    def pattern_with_callback(tool):
        """Pattern: Custom callback for engraving completion."""
        # You can override _on_engrave_complete in your tool
        # to add custom behavior when engraving finishes
        
        def custom_callback(success, error):
            if success:
                print("Engraving done! Update UI...")
            else:
                print(f"Engraving failed: {error}")
        
        # Or modify the engraver call directly (advanced):
        from engraver import get_engraver_instance
        engraver = get_engraver_instance()
        engraver.do_engrave(
            score=tool.score,
            canvas=tool.canvas,
            callback=custom_callback
        )


if __name__ == '__main__':
    print(__doc__)
    print("\nSee USAGE.md for complete documentation.")
