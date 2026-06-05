"""
PromptBuilder — thin class wrapper around prompts.py.

Builds system prompts for LLM calls. This gives prompts.py a class interface,
enabling dependency injection and easy testing.

In Phase 2, this class gains a method for RAG-enhanced prompts:
build_with_retrieval(profile, logs, retrieved_context)
The interface stays the same for callers that don't need retrieval.
"""
from typing import Optional, List, Dict
from agent.prompts import get_system_prompt


class PromptBuilder:
    """
    Builds system prompts for LLM calls.
    
    Thin wrapper that gives prompts.py a class interface,
    enabling dependency injection and easy testing.
    
    In Phase 2, this class gains a method for RAG-enhanced prompts:
    build_with_retrieval(profile, logs, retrieved_context)
    The interface stays the same for callers that don't need retrieval.
    """
    
    def build(
        self,
        user_profile: Optional[Dict] = None,
        recent_logs: Optional[List[Dict]] = None
    ) -> str:
        """Build the system prompt with context."""
        return get_system_prompt(
            user_profile=user_profile,
            recent_logs=recent_logs
        )

# Made with Bob
