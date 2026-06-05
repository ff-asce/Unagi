"""Input bar widget for Unagi TUI."""
from textual.widgets import Input
from textual.message import Message


class InputBar(Input):
    """Input bar for user messages."""
    
    class Submitted(Message):
        """Message sent when user submits input."""
        
        def __init__(self, value: str):
            super().__init__()
            self.value = value
    
    def __init__(self, **kwargs):
        super().__init__(
            placeholder="Type your message... (e.g., 'log breakfast' or 'show today')",
            **kwargs
        )
    
    def on_input_submitted(self, event: Input.Submitted):
        """Handle input submission."""
        value = event.value.strip()
        if value:
            # Post custom message
            self.post_message(self.Submitted(value))
            # Clear input
            self.value = ""
    
    def focus_input(self):
        """Focus the input bar."""
        self.focus()
    
    def set_placeholder(self, text: str):
        """Update placeholder text."""
        self.placeholder = text


# Made with Bob