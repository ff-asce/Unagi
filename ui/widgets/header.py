"""Header bar widget for Unagi TUI."""
from textual.widgets import Static
from textual.app import ComposeResult
from datetime import datetime


class UnagiHeader(Static):
    """Header bar showing app title, date, and system status."""
    
    def __init__(self, container: 'Container' = None, **kwargs):
        super().__init__(**kwargs)
        self.container = container
        self.model_name = "gemini-2.0-flash"
        self.vault_status = "✓"
        self.git_status = "✓ synced"
    
    def compose(self) -> ComposeResult:
        """Compose the header content."""
        yield Static(self._build_header_text())
    
    def _build_header_text(self) -> str:
        """Build the header text with status indicators."""
        now = datetime.now()
        date_str = now.strftime("%A, %d %B %Y")
        
        line1 = "🐍 UNAGI  ·  Total Food Awareness"
        line2 = f"[model: {self.model_name}]  [vault: {self.vault_status}]  [git: {self.git_status}]"
        line3 = f"Today: {date_str}"
        
        return f"{line1}\n{line2}\n{line3}"
    
    def update_status(self, vault_ok: bool = True, git_ok: bool = True, git_synced: bool = True):
        """Update system status indicators."""
        self.vault_status = "✓" if vault_ok else "✗"
        if not git_ok:
            self.git_status = "✗"
        elif not git_synced:
            self.git_status = "⚠ local only"
        else:
            self.git_status = "✓ synced"
        
        self.update(self._build_header_text())


# Made with Bob