"""Chat panel widget for Unagi TUI."""
from textual.widgets import Static
from textual.containers import VerticalScroll
from rich.console import RenderableType
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from typing import List, Dict, Any


class ChatPanel(VerticalScroll):
    """Scrollable chat panel showing conversation history."""
    
    def __init__(self, container: 'Container', **kwargs):
        super().__init__(**kwargs)
        self.container = container
        self.messages: List[Dict[str, Any]] = []
    
    def on_mount(self):
        """Load initial messages when mounted."""
        self.load_messages()
    
    def load_messages(self):
        """Load messages from context manager."""
        # For now, start with empty messages
        # TODO: Add conversation history to Context in Phase 3
        self.messages = []
        self._render_messages()
    
    def add_message(self, role: str, content: str):
        """Add a new message to the chat."""
        self.messages.append({'role': role, 'content': content})
        self._render_messages()
        # Auto-scroll to bottom
        self.scroll_end(animate=False)
    
    def _render_messages(self):
        """Render all messages to the panel."""
        # Clear existing content
        self.remove_children()
        
        # Add each message
        for msg in self.messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            if role == 'user':
                widget = self._render_user_message(content)
            elif role == 'assistant':
                widget = self._render_agent_message(content)
            elif role == 'system':
                widget = self._render_system_message(content)
            else:
                widget = self._render_user_message(content)
            
            self.mount(widget)
    
    def _render_user_message(self, content: str) -> Static:
        """Render a user message."""
        text = Text()
        text.append("You: ", style="bold cyan")
        text.append(content)
        
        widget = Static(text)
        widget.add_class("message-user")
        return widget
    
    def _render_agent_message(self, content: str) -> Static:
        """Render an agent message with markdown support."""
        # Check if content contains special panels
        if content.startswith('[SUCCESS]'):
            return self._render_success_panel(content[9:].strip())
        elif content.startswith('[WARNING]'):
            return self._render_warning_panel(content[9:].strip())
        elif content.startswith('[ERROR]'):
            return self._render_error_panel(content[7:].strip())
        
        # Regular markdown message
        text = Text()
        text.append("🐍 Unagi: ", style="bold #bc8cff")
        
        # Simple markdown rendering (bold, italic, code)
        rendered = self._simple_markdown(content)
        text.append(rendered)
        
        widget = Static(text)
        widget.add_class("message-agent")
        return widget
    
    def _render_system_message(self, content: str) -> Static:
        """Render a system message."""
        text = Text(content, style="dim italic")
        widget = Static(text)
        widget.add_class("message-system")
        return widget
    
    def _render_success_panel(self, content: str) -> Static:
        """Render a success panel."""
        panel = Panel(
            content,
            title="✅ Success",
            border_style="green",
            padding=(0, 1)
        )
        widget = Static(panel)
        widget.add_class("panel-success")
        return widget
    
    def _render_warning_panel(self, content: str) -> Static:
        """Render a warning panel."""
        panel = Panel(
            content,
            title="⚠️  Warning",
            border_style="yellow",
            padding=(0, 1)
        )
        widget = Static(panel)
        widget.add_class("panel-warning")
        return widget
    
    def _render_error_panel(self, content: str) -> Static:
        """Render an error panel."""
        panel = Panel(
            content,
            title="❌ Error",
            border_style="red",
            padding=(0, 1)
        )
        widget = Static(panel)
        widget.add_class("panel-error")
        return widget
    
    def _simple_markdown(self, text: str) -> Text:
        """Simple markdown rendering for inline formatting."""
        result = Text()
        i = 0
        while i < len(text):
            # Bold: **text**
            if text[i:i+2] == '**':
                end = text.find('**', i+2)
                if end != -1:
                    result.append(text[i+2:end], style="bold")
                    i = end + 2
                    continue
            
            # Italic: *text*
            if text[i] == '*' and (i == 0 or text[i-1] != '*'):
                end = text.find('*', i+1)
                if end != -1 and (end == len(text)-1 or text[end+1] != '*'):
                    result.append(text[i+1:end], style="italic")
                    i = end + 1
                    continue
            
            # Code: `text`
            if text[i] == '`':
                end = text.find('`', i+1)
                if end != -1:
                    result.append(text[i+1:end], style="bold cyan on #1c1c1c")
                    i = end + 1
                    continue
            
            # Regular character
            result.append(text[i])
            i += 1
        
        return result
    
    def clear_messages(self):
        """Clear all messages from the chat."""
        self.messages = []
        self.remove_children()
    
    def show_thinking(self):
        """Show a thinking indicator."""
        text = Text("🐍 Unagi is thinking...", style="dim italic #bc8cff")
        widget = Static(text)
        widget.add_class("message-thinking")
        self.mount(widget)
        self.scroll_end(animate=False)
    
    def remove_thinking(self):
        """Remove the thinking indicator."""
        # Remove last widget if it's a thinking indicator
        children = list(self.children)
        if children and hasattr(children[-1], 'has_class') and children[-1].has_class("message-thinking"):
            children[-1].remove()


class MessageWidget(Static):
    """Individual message widget."""
    
    def __init__(self, role: str, content: str, **kwargs):
        super().__init__(**kwargs)
        self.role = role
        self.content = content
    
    def render(self) -> RenderableType:
        """Render the message."""
        if self.role == 'user':
            text = Text()
            text.append("You: ", style="bold cyan")
            text.append(self.content)
            return text
        elif self.role == 'assistant':
            text = Text()
            text.append("🐍 Unagi: ", style="bold #bc8cff")
            text.append(self.content)
            return text
        else:
            return Text(self.content, style="dim italic")


# Made with Bob