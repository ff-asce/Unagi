"""Animated 8-bit eel mascot widget for modern UI."""
import random
from textual.widget import Widget
from textual.reactive import reactive
from rich.text import Text
from config import get_settings
from .retro_assets import (
    EEL_FRAMES,
    EEL_BLINK,
    EEL_THINKING,
    EEL_CELEBRATING,
    BUBBLES,
    COLORS
)


class EelMascot(Widget):
    """Animated 8-bit eel mascot widget.
    
    Features:
    - Swimming animation (4 frames with tail wag)
    - Random blinking
    - Mood states (happy, thinking, celebrating)
    - Rising bubbles (full animation mode only)
    - Configurable animation level (full/minimal)
    """
    
    # Reactive properties
    frame = reactive(0)
    mood = reactive("happy")
    is_blinking = reactive(False)
    bubble_offset = reactive(0)
    
    def __init__(self, *args, **kwargs):
        """Initialize the eel mascot."""
        super().__init__(*args, **kwargs)
        self.settings = get_settings()
        self.animation_level = self.settings.ui_modern_animation_level
        self.blink_counter = 0
        self.blink_interval = random.randint(30, 50)  # Blink every 3-5 seconds (at 10 FPS)
    
    def on_mount(self) -> None:
        """Set up animation intervals when widget is mounted."""
        if self.animation_level == "full":
            # Full animation: swimming at 5 FPS, bubbles at 10 FPS
            self.set_interval(0.2, self.animate_swim)
            self.set_interval(0.1, self.animate_bubbles)
            self.set_interval(0.1, self.check_blink)
        else:
            # Minimal animation: just occasional blink
            self.set_interval(1.0, self.check_blink)
    
    def animate_swim(self) -> None:
        """Advance to next swimming frame."""
        if self.mood == "happy" and not self.is_blinking:
            self.frame = (self.frame + 1) % len(EEL_FRAMES)
    
    def animate_bubbles(self) -> None:
        """Animate rising bubbles."""
        self.bubble_offset = (self.bubble_offset + 1) % len(BUBBLES)
    
    def check_blink(self) -> None:
        """Check if it's time to blink."""
        self.blink_counter += 1
        
        if self.is_blinking:
            # End blink after 2 frames
            self.is_blinking = False
            self.blink_counter = 0
            self.blink_interval = random.randint(30, 50)
        elif self.blink_counter >= self.blink_interval:
            # Start blink
            self.is_blinking = True
    
    def set_mood(self, mood: str) -> None:
        """Change the eel's mood.
        
        Args:
            mood: One of "happy", "thinking", "celebrating"
        """
        if mood in ["happy", "thinking", "celebrating"]:
            self.mood = mood
            self.frame = 0  # Reset animation
    
    def render(self) -> Text:
        """Render the current eel frame with bubbles."""
        # Select the appropriate frame based on mood and state
        if self.is_blinking and self.mood == "happy":
            eel_art = EEL_BLINK
        elif self.mood == "thinking":
            eel_art = EEL_THINKING
        elif self.mood == "celebrating":
            eel_art = EEL_CELEBRATING
        else:
            # Happy mood - use swimming animation
            eel_art = EEL_FRAMES[self.frame]
        
        # Create rich text with color
        text = Text()
        
        # Add eel art with orange color
        for line in eel_art.strip().split('\n'):
            text.append(line, style=f"bold {COLORS['ORANGE']}")
            text.append("\n")
        
        # Add bubbles if full animation mode
        if self.animation_level == "full" and self.mood == "happy":
            bubble = BUBBLES[self.bubble_offset]
            text.append(f"  {bubble}", style=f"{COLORS['INFO']}")
        
        return text


# Made with Bob