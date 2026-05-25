"""Chat panel component for displaying conversation history."""
from textual.widgets import Static
from textual.containers import VerticalScroll
from rich.text import Text
from rich.panel import Panel
from .retro_assets import COLORS, ICONS


class ChatMessage(Static):
    """A single chat message widget."""
    
    def __init__(self, role: str, content: str, *args, **kwargs):
        """Initialize chat message.
        
        Args:
            role: Message role (user, assistant, system)
            content: Message content
        """
        super().__init__(*args, **kwargs)
        self.role = role
        self.content = content
    
    def render(self) -> Text:
        """Render the message with appropriate styling."""
        text = Text()
        
        if self.role == "user":
            # User messages - right-aligned, blue/purple
            text.append(f"{ICONS['diamond']} You: ", style=f"bold {COLORS['PURPLE']}")
            text.append(self.content, style=COLORS['LIGHT_TEXT'])
        elif self.role == "assistant":
            # Unagi messages - left-aligned, orange
            text.append(f"🐍 Unagi: ", style=f"bold {COLORS['ORANGE']}")
            text.append(self.content, style=COLORS['LIGHT_TEXT'])
        elif self.role == "system":
            # System messages - centered, cyan
            text.append(f"{ICONS['info']} ", style=f"bold {COLORS['INFO']}")
            text.append(self.content, style=f"italic {COLORS['INFO']}")
        
        return text


class ConfirmationWidget(Static):
    """Widget for displaying confirmation requests."""
    
    def __init__(self, data: dict, *args, **kwargs):
        """Initialize confirmation widget.
        
        Args:
            data: Log data to confirm
        """
        super().__init__(*args, **kwargs)
        self.data = data
    
    def render(self) -> Text:
        """Render confirmation request."""
        text = Text()
        
        # Header
        text.append(f"\n{ICONS['warning']} Confirmation Required\n", 
                   style=f"bold {COLORS['WARNING']}")
        text.append("─" * 40 + "\n", style=COLORS['BORDER'])
        
        # Data preview
        text.append(f"Date: {self.data.get('date', 'Unknown')}\n", 
                   style=COLORS['LIGHT_TEXT'])
        text.append(f"Calories: {self.data.get('calories', 0)} kcal\n", 
                   style=COLORS['LIGHT_TEXT'])
        text.append(f"Protein: {self.data.get('protein', 0)}g\n", 
                   style=COLORS['LIGHT_TEXT'])
        
        # Buttons
        text.append("\n")
        text.append(f"{ICONS['check']} ", style=f"bold {COLORS['SUCCESS']}")
        text.append("Type 'yes' to confirm  ", style=COLORS['SUCCESS'])
        text.append(f"{ICONS['cross']} ", style=f"bold {COLORS['ERROR']}")
        text.append("Type 'no' to cancel\n", style=COLORS['ERROR'])
        
        return text


class ChatPanel(VerticalScroll):
    """Scrollable chat conversation panel."""
    
    def __init__(self, *args, **kwargs):
        """Initialize chat panel."""
        super().__init__(*args, **kwargs)
        self.message_count = 0
    
    def add_user_message(self, content: str) -> None:
        """Add a user message to the chat.
        
        Args:
            content: Message content
        """
        message = ChatMessage("user", content)
        self.mount(message)
        self.message_count += 1
        self.scroll_end(animate=True)
    
    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message to the chat.
        
        Args:
            content: Message content
        """
        message = ChatMessage("assistant", content)
        self.mount(message)
        self.message_count += 1
        self.scroll_end(animate=True)
    
    def add_system_message(self, content: str) -> None:
        """Add a system message to the chat.
        
        Args:
            content: Message content
        """
        message = ChatMessage("system", content)
        self.mount(message)
        self.message_count += 1
        self.scroll_end(animate=True)
    
    def show_confirmation(self, data: dict) -> None:
        """Show a confirmation request.
        
        Args:
            data: Log data to confirm
        """
        confirmation = ConfirmationWidget(data)
        self.mount(confirmation)
        self.scroll_end(animate=True)
    
    def clear_messages(self) -> None:
        """Clear all messages from the chat."""
        self.remove_children()
        self.message_count = 0


# Made with Bob