"""8-bit retro pixel art assets and color scheme for modern UI."""

# Color Palette - 8-bit Retro Style
COLORS = {
    # Primary colors
    "ORANGE": "#FF6B35",      # Claude orange - primary accent
    "PURPLE": "#7C3AED",      # Obsidian purple - secondary accent
    "DARK_BG": "#1A1A2E",     # Dark background
    "LIGHT_TEXT": "#E8E8E8",  # Light text
    
    # Status colors (8-bit style)
    "SUCCESS": "#00FF00",     # Bright green (retro success)
    "WARNING": "#FFFF00",     # Bright yellow (retro warning)
    "ERROR": "#FF0000",       # Bright red (retro error)
    "INFO": "#00FFFF",        # Bright cyan (retro info)
    
    # UI elements
    "BORDER": "#FF6B35",      # Orange borders
    "PANEL_BG": "#0F0F1E",    # Slightly lighter than dark bg
    "HIGHLIGHT": "#7C3AED",   # Purple highlights
}


# 8-bit Eel Mascot Frames (Swimming Animation)
EEL_FRAMES = [
    # Frame 1 - Tail left
    """
    ▓▓▓▓▓
   ▓▓▓▓▓▓▓
  ▓▓░░▓▓▓▓
  ▓▓▓▓▓▓▓
   ▓▓▓▓▓
    ▓▓▓
     ▓
    """,
    
    # Frame 2 - Tail center
    """
    ▓▓▓▓▓
   ▓▓▓▓▓▓▓
  ▓▓░░▓▓▓▓
  ▓▓▓▓▓▓▓
   ▓▓▓▓▓
    ▓▓▓
     ▓▓
    """,
    
    # Frame 3 - Tail right
    """
    ▓▓▓▓▓
   ▓▓▓▓▓▓▓
  ▓▓░░▓▓▓▓
  ▓▓▓▓▓▓▓
   ▓▓▓▓▓
    ▓▓▓▓
     ▓▓▓
    """,
    
    # Frame 4 - Tail center (return)
    """
    ▓▓▓▓▓
   ▓▓▓▓▓▓▓
  ▓▓░░▓▓▓▓
  ▓▓▓▓▓▓▓
   ▓▓▓▓▓
    ▓▓▓
     ▓▓
    """
]


# Eel Blinking Frame
EEL_BLINK = """
    ▓▓▓▓▓
   ▓▓▓▓▓▓▓
  ▓▓──▓▓▓▓
  ▓▓▓▓▓▓▓
   ▓▓▓▓▓
    ▓▓▓
     ▓▓
"""


# Eel Thinking Frame (when LLM is processing)
EEL_THINKING = """
    ▓▓▓▓▓
   ▓▓▓▓▓▓▓  💭
  ▓▓░░▓▓▓▓
  ▓▓▓▓▓▓▓
   ▓▓▓▓▓
    ▓▓▓
     ▓▓
"""


# Eel Celebrating Frame (when log confirmed)
EEL_CELEBRATING = """
  ✨ ▓▓▓▓▓ ✨
   ▓▓▓▓▓▓▓
  ▓▓^▓^▓▓▓▓
  ▓▓▓▓▓▓▓
   ▓▓▓▓▓
    ▓▓▓
     ▓▓
"""


# Bubble Patterns (for animation)
BUBBLES = [
    "○",
    "○○",
    "○○○",
    " ○○",
    "  ○"
]


# Progress Bar Styles (8-bit)
def get_progress_bar(percentage: int, width: int = 10) -> str:
    """Generate 8-bit style progress bar.
    
    Args:
        percentage: Progress percentage (0-100)
        width: Width of progress bar in characters
        
    Returns:
        Formatted progress bar string
    """
    filled = int(width * percentage / 100)
    empty = width - filled
    
    # Status emoji based on percentage
    if percentage >= 80:
        status = "✓"
        color = "SUCCESS"
    elif percentage >= 50:
        status = "⚠"
        color = "WARNING"
    else:
        status = "✗"
        color = "ERROR"
    
    bar = f"[{'█' * filled}{'░' * empty}] {percentage}% {status}"
    return bar


# Retro Border Styles
BORDERS = {
    "double": {
        "tl": "╔", "tr": "╗", "bl": "╚", "br": "╝",
        "h": "═", "v": "║"
    },
    "single": {
        "tl": "┌", "tr": "┐", "bl": "└", "br": "┘",
        "h": "─", "v": "│"
    },
    "thick": {
        "tl": "┏", "tr": "┓", "bl": "┗", "br": "┛",
        "h": "━", "v": "┃"
    },
    "rounded": {
        "tl": "╭", "tr": "╮", "bl": "╰", "br": "╯",
        "h": "─", "v": "│"
    }
}


def create_border(text: str, width: int, style: str = "double") -> str:
    """Create a bordered text box.
    
    Args:
        text: Text to display
        width: Width of the box
        style: Border style (double, single, thick, rounded)
        
    Returns:
        Bordered text string
    """
    b = BORDERS.get(style, BORDERS["double"])
    
    # Top border
    result = f"{b['tl']}{b['h'] * (width - 2)}{b['tr']}\n"
    
    # Content (centered)
    padding = (width - 2 - len(text)) // 2
    result += f"{b['v']}{' ' * padding}{text}{' ' * (width - 2 - len(text) - padding)}{b['v']}\n"
    
    # Bottom border
    result += f"{b['bl']}{b['h'] * (width - 2)}{b['br']}"
    
    return result


# Pixel Art Icons
ICONS = {
    "food": "🍽️",
    "stats": "📊",
    "check": "✓",
    "cross": "✗",
    "warning": "⚠",
    "info": "ℹ",
    "fire": "🔥",
    "star": "⭐",
    "heart": "❤️",
    "muscle": "💪",
    "brain": "🧠",
    "sparkle": "✨",
    "wave": "〰️",
    "arrow_up": "↑",
    "arrow_down": "↓",
    "bullet": "•",
    "diamond": "◆",
    "square": "■",
    "circle": "●",
}


# Sparkline Characters (for mini charts)
SPARKLINE_CHARS = " ▁▂▃▄▅▆▇█"


def create_sparkline(values: list[int], max_val: int | None = None) -> str:
    """Create a sparkline chart from values.
    
    Args:
        values: List of integer values
        max_val: Maximum value for scaling (auto-detected if None)
        
    Returns:
        Sparkline string
    """
    if not values:
        return ""
    
    if max_val is None:
        max_val = max(values) if values else 1
    
    if max_val == 0:
        max_val = 1
    
    chars = []
    for val in values:
        # Scale to 0-8 range
        scaled = int((val / max_val) * 8)
        scaled = max(0, min(8, scaled))  # Clamp to 0-8
        chars.append(SPARKLINE_CHARS[scaled])
    
    return "".join(chars)


# Retro Loading Animation Frames
LOADING_FRAMES = [
    "⠋",
    "⠙",
    "⠹",
    "⠸",
    "⠼",
    "⠴",
    "⠦",
    "⠧",
    "⠇",
    "⠏"
]


# Made with Bob