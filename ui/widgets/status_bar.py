"""Status bar widget for Unagi TUI."""
from textual.widgets import Static


class StatusBar(Static):
    """Status bar showing pipeline status and keyboard hints."""
    
    def __init__(self, container: 'Container' = None, **kwargs):
        super().__init__(**kwargs)
        self.container = container
        self.current_message = ""
        self.is_processing = False
        self.spinner_state = 0
        self.spinner_chars = "◐◓◑◒"
    
    def set_message(self, message: str):
        """Set the status message."""
        self.current_message = message
        self.is_processing = bool(message)
        self._update_display()
    
    def _update_display(self):
        """Update the status bar display."""
        if self.is_processing:
            spinner = self.spinner_chars[self.spinner_state % len(self.spinner_chars)]
            left = f"{spinner} {self.current_message}"
        else:
            left = ""
        
        right = "Ctrl+C to exit"
        
        # Calculate spacing to right-align
        total_width = 100  # Will be dynamic based on terminal width
        spacing = " " * max(0, total_width - len(left) - len(right))
        
        self.update(f"{left}{spacing}{right}")
    
    def advance_spinner(self):
        """Advance the spinner animation."""
        if self.is_processing:
            self.spinner_state += 1
            self._update_display()


# Made with Bob