"""UI module for Unagi CLI interface."""
from .cli import CLI, run_cli
from .mascot import (
    get_ross_unagi_art,
    get_startup_banner,
    get_help_text,
    get_goodbye_message,
    get_error_banner
)

__all__ = [
    "CLI",
    "run_cli",
    "get_ross_unagi_art",
    "get_startup_banner",
    "get_help_text",
    "get_goodbye_message",
    "get_error_banner",
]

# Made with Bob
