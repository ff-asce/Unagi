"""Startup screen for Unagi TUI."""
from textual.screen import Screen
from textual.widgets import Static
from textual.containers import Container, Vertical
from rich.text import Text
from rich.panel import Panel
import asyncio


class StartupScreen(Screen):
    """Startup screen with mascot and loading animation."""
    
    MASCOT = """
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣀⣀⣀⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⣠⣴⣾⣿⣿⣿⣿⣿⣿⣿⣿⣷⣦⣄⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⣠⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣄⠀⠀⠀⠀
    ⠀⠀⠀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⠀⠀⠀
    ⠀⠀⢰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡆⠀⠀
    ⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀
    ⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀
    ⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀
    ⠀⠘⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠃⠀
    ⠀⠀⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⠀⠀
    ⠀⠀⠀⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⠀⠀⠀
    ⠀⠀⠀⠀⠙⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠋⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠉⠛⠿⢿⣿⣿⣿⣿⣿⣿⡿⠿⠛⠉⠀⠀⠀⠀⠀⠀
    """
    
    def compose(self):
        """Compose the startup screen."""
        with Container(id="startup-container"):
            with Vertical(id="startup-content"):
                # Mascot
                mascot_text = Text(self.MASCOT, style="#bc8cff", justify="center")
                yield Static(mascot_text, id="mascot")
                
                # Title
                title = Text("UNAGI", style="bold #bc8cff", justify="center")
                yield Static(title, id="title")
                
                # Tagline
                tagline = Text("Total Food Awareness", style="dim italic", justify="center")
                yield Static(tagline, id="tagline")
                
                # Loading message
                loading = Text("Loading...", style="dim", justify="center")
                yield Static(loading, id="loading")
    
    async def on_mount(self):
        """Start loading animation when mounted."""
        self.loading_task = asyncio.create_task(self._animate_loading())
    
    async def _animate_loading(self):
        """Animate the loading message."""
        loading_widget = self.query_one("#loading", Static)
        frames = ["Loading.", "Loading..", "Loading..."]
        i = 0
        
        while True:
            loading_widget.update(Text(frames[i % len(frames)], style="dim", justify="center"))
            i += 1
            await asyncio.sleep(0.5)
    
    def on_unmount(self):
        """Cancel loading animation when unmounted."""
        if hasattr(self, 'loading_task'):
            self.loading_task.cancel()


class StartupLoadingWidget(Static):
    """Loading widget with animation."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.frame = 0
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    def on_mount(self):
        """Start animation when mounted."""
        self.set_interval(0.1, self.advance_frame)
    
    def advance_frame(self):
        """Advance to next animation frame."""
        self.frame = (self.frame + 1) % len(self.frames)
        spinner = self.frames[self.frame]
        text = Text(f"{spinner} Loading...", style="dim", justify="center")
        self.update(text)


# Made with Bob