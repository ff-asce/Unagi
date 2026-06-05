"""Main screen for Unagi TUI."""
from textual.screen import Screen
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header as TextualHeader, Footer
from ..widgets.header import UnagiHeader
from ..widgets.stats_bar import StatsBar
from ..widgets.chat_panel import ChatPanel
from ..widgets.today_panel import TodayPanel
from ..widgets.input_bar import InputBar
from ..widgets.status_bar import StatusBar


class MainScreen(Screen):
    """Main application screen with chat and today panel."""
    
    CSS = """
    #main-container {
        height: 100%;
    }
    
    #header-section {
        height: 3;
        dock: top;
    }
    
    #stats-section {
        height: 3;
        dock: top;
    }
    
    #content-section {
        height: 1fr;
    }
    
    #chat-today-container {
        height: 100%;
    }
    
    #chat-panel {
        width: 70%;
    }
    
    #today-panel {
        width: 30%;
        border-left: solid $primary;
    }
    
    #input-section {
        height: 3;
        dock: bottom;
    }
    
    #status-section {
        height: 1;
        dock: bottom;
    }
    
    /* Note: Textual CSS doesn't support @media queries yet */
    /* Responsive behavior would need to be handled in Python code */
    """
    
    def __init__(self, container: 'Container', **kwargs):
        super().__init__(**kwargs)
        self.container = container
    
    def compose(self):
        """Compose the main screen layout."""
        with Container(id="main-container"):
            # Header section
            with Container(id="header-section"):
                yield UnagiHeader(self.container)
            
            # Stats section
            with Container(id="stats-section"):
                yield StatsBar(self.container)
            
            # Content section (chat + today)
            with Container(id="content-section"):
                with Horizontal(id="chat-today-container"):
                    # Chat panel (70%)
                    yield ChatPanel(self.container, id="chat-panel")
                    
                    # Today panel (30%)
                    yield TodayPanel(self.container, id="today-panel")
            
            # Input section
            with Container(id="input-section"):
                yield InputBar(id="input-bar")
            
            # Status section
            with Container(id="status-section"):
                yield StatusBar(self.container)
    
    def on_mount(self):
        """Initialize screen when mounted."""
        # Focus input bar
        input_bar = self.query_one("#input-bar", InputBar)
        input_bar.focus()
        
        # Subscribe to EventBus for real-time updates
        self._subscribe_to_events()
    
    def _subscribe_to_events(self):
        """Subscribe to EventBus events."""
        event_bus = self.container.event_bus
        
        # Subscribe to pipeline events
        event_bus.subscribe('pipeline.started', self._on_pipeline_started)
        event_bus.subscribe('pipeline.completed', self._on_pipeline_completed)
        event_bus.subscribe('pipeline.error', self._on_pipeline_error)
        
        # Subscribe to context updates
        event_bus.subscribe('context.updated', self._on_context_updated)
    
    def _on_pipeline_started(self, event_data):
        """Handle pipeline started event."""
        # Show thinking indicator in chat
        chat_panel = self.query_one("#chat-panel", ChatPanel)
        chat_panel.show_thinking()
        
        # Update status bar
        status_bar = self.query_one(StatusBar)
        status_bar.set_message("Processing...")
    
    def _on_pipeline_completed(self, event_data):
        """Handle pipeline completed event."""
        # Remove thinking indicator
        chat_panel = self.query_one("#chat-panel", ChatPanel)
        chat_panel.remove_thinking()
        
        # Add agent response to chat
        response = event_data.get('response', '')
        chat_panel.add_message('assistant', response)
        
        # Update status bar
        status_bar = self.query_one(StatusBar)
        status_bar.set_message("Ready")
        
        # Refresh stats and today panel
        self._refresh_data()
    
    def _on_pipeline_error(self, event_data):
        """Handle pipeline error event."""
        # Remove thinking indicator
        chat_panel = self.query_one("#chat-panel", ChatPanel)
        chat_panel.remove_thinking()
        
        # Show error in chat
        error = event_data.get('error', 'Unknown error')
        chat_panel.add_message('assistant', f'[ERROR] {error}')
        
        # Update status bar
        status_bar = self.query_one(StatusBar)
        status_bar.set_message("Error occurred")
    
    def _on_context_updated(self, event_data):
        """Handle context updated event."""
        self._refresh_data()
    
    def _refresh_data(self):
        """Refresh all data displays."""
        # Refresh stats bar
        stats_bar = self.query_one(StatsBar)
        stats_bar.refresh_data()
        
        # Refresh today panel
        today_panel = self.query_one("#today-panel", TodayPanel)
        today_panel.refresh_data()
        
        # Update header status
        header = self.query_one(UnagiHeader)
        header.update_status()
    
    async def on_input_bar_submitted(self, event: InputBar.Submitted):
        """Handle input submission."""
        user_input = event.value
        
        # Add user message to chat
        chat_panel = self.query_one("#chat-panel", ChatPanel)
        chat_panel.add_message('user', user_input)
        
        # Process through orchestrator
        await self._process_user_input(user_input)
    
    async def _process_user_input(self, user_input: str):
        """Process user input through the orchestrator."""
        try:
            # Emit pipeline started event
            self.container.event_bus.emit('pipeline.started', {})
            
            # Process through orchestrator
            response = await self.container.orchestrator.process_message(user_input)
            
            # Emit pipeline completed event
            self.container.event_bus.emit('pipeline.completed', {'response': response})
            
        except Exception as e:
            # Emit pipeline error event
            self.container.event_bus.emit('pipeline.error', {'error': str(e)})
    
    def action_quit(self):
        """Quit the application."""
        self.app.exit()
    
    def action_refresh(self):
        """Refresh all data."""
        self._refresh_data()
    
    def action_clear_chat(self):
        """Clear chat history."""
        chat_panel = self.query_one("#chat-panel", ChatPanel)
        chat_panel.clear_messages()


# Made with Bob