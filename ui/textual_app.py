"""Modern Textual UI for UNAGI with 8-bit retro aesthetic."""
import asyncio
import json
from pathlib import Path
from typing import Optional, Dict, Any
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Input, Static
from textual.binding import Binding
from config import get_settings
from agent.chat import ChatAgent, ChatError
from vault import get_vault_writer
from .components.eel_mascot import EelMascot
from .components.chat_panel import ChatPanel
from .components.stats_dashboard import StatsDashboard


class UnagiApp(App):
    """UNAGI Modern Terminal UI Application."""
    
    CSS_PATH = Path(__file__).parent / "styles" / "app.tcss"
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+s", "toggle_stats", "Toggle Stats", show=True),
        Binding("ctrl+slash", "show_help", "Help", show=False),
        Binding("escape", "cancel", "Cancel", show=False),
    ]
    
    def __init__(self):
        """Initialize the Unagi app."""
        super().__init__()
        settings = get_settings()
        
        # Initialize chat agent
        self.agent = ChatAgent()
        
        # Load user goals for stats
        self.goals = {
            "calories": 2000,
            "protein": 150,
            "carbs": 200,
            "fat": 65
        }
        
        self.is_processing = False
        self.pending_confirmation: Optional[Dict[str, Any]] = None
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        with Container(id="main-container"):
            with Vertical(id="left-panel"):
                yield EelMascot()
                yield ChatPanel()
            with Vertical(id="right-panel"):
                yield StatsDashboard(self.goals)
        yield Input(placeholder="Type your message...", id="input-bar")
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when app starts."""
        chat_panel = self.query_one(ChatPanel)
        chat_panel.add_system_message("🐍 Welcome to UNAGI! Type /help for commands.")
        
        # Focus input
        self.query_one(Input).focus()
    
    def action_toggle_stats(self) -> None:
        """Toggle stats panel visibility."""
        right_panel = self.query_one("#right-panel")
        right_panel.display = not right_panel.display
        
        # Adjust left panel width when stats are hidden
        left_panel = self.query_one("#left-panel")
        if right_panel.display:
            left_panel.styles.width = "60%"
        else:
            left_panel.styles.width = "100%"
    
    def action_show_help(self) -> None:
        """Show help message."""
        chat_panel = self.query_one(ChatPanel)
        chat_panel.add_system_message("Keyboard Shortcuts:")
        chat_panel.add_system_message("  Ctrl+C - Quit")
        chat_panel.add_system_message("  Ctrl+S - Toggle Stats")
        chat_panel.add_system_message("  Ctrl+/ - Show Help")
    
    def action_cancel(self) -> None:
        """Cancel current operation."""
        if self.pending_confirmation:
            self.pending_confirmation = None
            chat_panel = self.query_one(ChatPanel)
            chat_panel.add_system_message("✗ Operation cancelled")
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        message = event.value.strip()
        if not message:
            return
        
        # Clear input
        event.input.value = ""
        
        # Handle commands
        if message.startswith("/"):
            await self._handle_command(message)
            return
        
        # Handle confirmation responses
        if self.pending_confirmation:
            await self._handle_confirmation(message)
            return
        
        # Regular message - send to agent
        await self._process_message(message)
    
    async def _handle_command(self, command: str) -> None:
        """Handle special commands.
        
        Args:
            command: Command string starting with /
        """
        chat_panel = self.query_one(ChatPanel)
        
        if command == "/help":
            chat_panel.add_system_message("Available commands:")
            chat_panel.add_system_message("/help - Show this help")
            chat_panel.add_system_message("/stats - Toggle stats panel")
            chat_panel.add_system_message("/clear - Clear chat history")
            chat_panel.add_system_message("/exit - Quit application")
        
        elif command == "/stats":
            self.action_toggle_stats()
        
        elif command == "/clear":
            chat_panel.clear_messages()
            chat_panel.add_system_message("Chat cleared")
        
        elif command == "/exit":
            await self.action_quit()
        
        else:
            chat_panel.add_system_message(f"Unknown command: {command}")
    
    async def _process_message(self, message: str) -> None:
        """Process user message with agent.
        
        Args:
            message: User message
        """
        if self.is_processing:
            return
        
        self.is_processing = True
        chat_panel = self.query_one(ChatPanel)
        eel = self.query_one(EelMascot)
        
        # Show user message
        chat_panel.add_user_message(message)
        
        # Set eel to thinking mode
        eel.set_mood("thinking")
        
        try:
            # Detect intent
            intent = self.agent.detect_intent(message)
            
            if intent == "log":
                # Handle food logging
                response = await self._handle_food_log(message)
            else:
                # Handle general chat
                response = await self._handle_chat(message)
            
            chat_panel.add_assistant_message(response)
            
            # Reset eel mood
            eel.set_mood("happy")
        
        except ChatError as e:
            chat_panel.add_system_message(f"Chat error: {str(e)}")
            eel.set_mood("happy")
        except Exception as e:
            chat_panel.add_system_message(f"Unexpected error: {str(e)}")
            eel.set_mood("happy")
        
        finally:
            self.is_processing = False
    
    async def _handle_chat(self, message: str) -> str:
        """Handle general chat message.
        
        Args:
            message: User message
            
        Returns:
            Agent response
        """
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            self.agent.handle_chat,
            message
        )
        return response
    
    async def _handle_food_log(self, message: str) -> str:
        """Handle food logging request.
        
        Args:
            message: User message with food info
            
        Returns:
            Agent response with confirmation request
        """
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            self.agent.handle_log,
            message
        )
        
        # Check if we need confirmation
        if self.agent.pending_log:
            self.pending_confirmation = self.agent.pending_log
            
            # Show confirmation widget
            chat_panel = self.query_one(ChatPanel)
            chat_panel.show_confirmation(
                f"Log this entry?\n{json.dumps(self.agent.pending_log, indent=2)}"
            )
        
        return response
    
    async def _handle_confirmation(self, response: str) -> None:
        """Handle confirmation response.
        
        Args:
            response: User's yes/no response
        """
        chat_panel = self.query_one(ChatPanel)
        eel = self.query_one(EelMascot)
        
        if response.lower() in ['yes', 'y', 'confirm']:
            # Confirmed - write to vault
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    self.agent.confirm_log
                )
                
                chat_panel.add_system_message("✓ Log confirmed and saved!")
                eel.set_mood("celebrating")
                
                # Reset after celebration
                await asyncio.sleep(2)
                eel.set_mood("happy")
                
                # Update stats
                self._update_stats()
            
            except Exception as e:
                chat_panel.add_system_message(f"Error saving log: {str(e)}")
        
        else:
            # Cancelled
            self.agent.cancel_log()
            chat_panel.add_system_message("✗ Log cancelled")
        
        self.pending_confirmation = None
    
    def _update_stats(self) -> None:
        """Update stats dashboard with latest data."""
        # Reload stats from vault
        stats = self.query_one(StatsDashboard)
        # TODO: Implement stats refresh from vault data
        pass


if __name__ == "__main__":
    app = UnagiApp()
    app.run()

# Made with Bob
