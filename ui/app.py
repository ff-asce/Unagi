"""Main Textual application for Unagi TUI."""
from textual.app import App
from textual.binding import Binding
from .screens.startup import StartupScreen
from .screens.onboarding import OnboardingScreen
from .screens.main import MainScreen
import asyncio
from pathlib import Path


class UnagiApp(App):
    """Unagi TUI application."""
    
    CSS_PATH = "styles/app.tcss"
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+r", "refresh", "Refresh", show=False),
        Binding("ctrl+l", "clear_chat", "Clear Chat", show=False),
    ]
    
    def __init__(self, container: 'Container', **kwargs):
        super().__init__(**kwargs)
        self.container = container
        self.startup_complete = False
    
    async def on_mount(self):
        """Initialize app when mounted."""
        # Show startup screen
        await self.push_screen(StartupScreen())
        
        # Initialize container components
        await self._initialize_container()
        
        # Check if onboarding needed
        if self._needs_onboarding():
            await self.push_screen(OnboardingScreen(self.container))
        
        # Show main screen
        await self.push_screen(MainScreen(self.container))
        
        # Mark startup complete
        self.startup_complete = True
    
    async def _initialize_container(self):
        """Initialize container components."""
        # Ensure vault structure exists
        await asyncio.to_thread(self.container.vault_writer._ensure_vault_structure)
        
        # Pre-warm the context cache (loads profile and recent logs)
        await asyncio.to_thread(self.container.context_manager.get_context)
        
        # Container components are already initialized
        # Orchestrator is ready to process messages
        
        # Small delay for startup screen
        await asyncio.sleep(1.5)
    
    def _needs_onboarding(self) -> bool:
        """Check if user needs onboarding."""
        context = self.container.context_manager.get_context()
        profile = context.profile
        
        # Check if profile has required fields
        if not profile:
            return True
        
        required_fields = ['current_weight', 'height', 'age', 'activity_level', 'goal', 'protein_target_per_kg']
        for field in required_fields:
            if field not in profile:
                return True
        
        return False
    
    def action_quit(self):
        """Quit the application."""
        self.exit()
    
    def action_refresh(self):
        """Refresh data in current screen."""
        if hasattr(self.screen, 'action_refresh'):
            self.screen.action_refresh()
    
    def action_clear_chat(self):
        """Clear chat in current screen."""
        if hasattr(self.screen, 'action_clear_chat'):
            self.screen.action_clear_chat()


class UnagiTUI:
    """Wrapper class for running the Unagi TUI."""
    
    def __init__(self, container: 'Container'):
        self.container = container
        self.app = None
    
    def run(self):
        """Run the TUI application."""
        self.app = UnagiApp(self.container)
        self.app.run()
    
    async def run_async(self):
        """Run the TUI application asynchronously."""
        self.app = UnagiApp(self.container)
        await self.app.run_async()


def create_tui(container: 'Container') -> UnagiTUI:
    """Create a new TUI instance."""
    return UnagiTUI(container)


# Made with Bob