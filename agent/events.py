"""
Event system for agent pipeline.
Enables UI to show real-time progress without tight coupling.
"""
from typing import Callable, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class PipelineEvent(str, Enum):
    """Events emitted during pipeline execution."""
    CLASSIFYING     = "classifying"           # Determining intent
    RESOLVING_DATE  = "resolving_date"        # Parsing date reference
    LOADING_CONTEXT = "loading_context"       # Reading vault files
    CALCULATING     = "calculating_nutrition" # LLM call in progress
    WRITING_FILE    = "writing_file"          # Writing .md to vault
    COMMITTING      = "committing"            # Git commit in progress
    PUSHING         = "pushing"               # Git push in progress
    DONE            = "done"                  # Pipeline complete
    ERROR           = "error"                 # Something failed


@dataclass
class Event:
    """Event data structure."""
    name: str
    data: Dict[str, Any]


class EventBus:
    """
    Simple synchronous event bus.
    
    Usage:
        bus = EventBus()
        bus.subscribe(lambda e: print(f"Event: {e.name}"))
        bus.emit("calculating", {"step": "macros"})
    
    In Phase 5 (web UI), this becomes async and emits to WebSocket
    connections. The interface stays the same.
    """
    
    def __init__(self):
        self._subscribers: List[Callable] = []
    
    def subscribe(self, callback: Callable[[Event], None]):
        """Subscribe to all events."""
        self._subscribers.append(callback)
    
    def emit(self, event_name: str, data: Dict[str, Any] = None):
        """Emit an event to all subscribers."""
        event = Event(name=event_name, data=data or {})
        for subscriber in self._subscribers:
            try:
                subscriber(event)
            except Exception:
                pass  # Never let UI errors crash the pipeline


# Human-readable status messages for each event
# Used by CLI and future web UI to show progress
EVENT_MESSAGES = {
    PipelineEvent.CLASSIFYING:     "Understanding your message...",
    PipelineEvent.RESOLVING_DATE:  "Figuring out the date...",
    PipelineEvent.LOADING_CONTEXT: "Loading your history...",
    PipelineEvent.CALCULATING:     "Calculating nutrition...",
    PipelineEvent.WRITING_FILE:    "Writing to vault...",
    PipelineEvent.COMMITTING:      "Committing to Git...",
    PipelineEvent.PUSHING:         "Pushing to remote...",
    PipelineEvent.DONE:            "Done ✓",
    PipelineEvent.ERROR:           "Something went wrong",
}


# Made with Bob