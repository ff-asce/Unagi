"""Intent classification for the agent pipeline."""
import re
from typing import List, Dict, Optional


class IntentClassifier:
    """
    Classifies user intent as 'log' (food logging) or 'chat' (conversation).
    
    Uses a two-stage approach:
    1. Fast-path rules for unambiguous cases (no LLM call needed)
    2. LLM classification for ambiguous cases
    
    This class is deliberately thin — it has one job and one method.
    In Phase 3, this can be replaced by a LangGraph node with no changes
    to the orchestrator.
    """
    
    FAST_PATH_LOG = [
        r'^log ',                          # Explicit log command
        r'\d+\s*g\b',                      # Has gram measurements
        r'\d+\s*ml\b',                     # Has ml measurements  
        r'\d+\s*kg\b',                     # Has kg measurements
    ]
    
    FAST_PATH_CHAT = [
        r'\?$',                            # Ends with question mark
        r'^(how|what|when|where|why|am i|are|is my|do i|did i|should)',
    ]
    
    def __init__(self, llm_client: 'LLMClient'):
        self.llm = llm_client
    
    def classify(
        self, 
        user_input: str, 
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Classify intent as 'log' or 'chat'.
        Returns 'chat' on any error — safer than accidentally logging.
        """
        text = user_input.strip().lower()
        
        # Fast path: explicit log trigger
        for pattern in self.FAST_PATH_LOG:
            if re.search(pattern, text):
                return 'log'
        
        # Fast path: clear chat trigger
        for pattern in self.FAST_PATH_CHAT:
            if re.search(pattern, text):
                return 'chat'
        
        # LLM classification for ambiguous cases
        return self._llm_classify(user_input)
    
    def _llm_classify(self, user_input: str) -> str:
        """Use LLM for ambiguous intent classification."""
        prompt = """Classify the user message as exactly one of: log or chat

"log" = user is describing food they ate or want to record
"chat" = user is asking a question, requesting advice, or making a statement

Reply with ONLY the word: log or chat

Examples:
"I had 200g chicken" → log
"10 almonds and green tea for breakfast" → log  
"How am I doing this week?" → chat
"What should I eat?" → chat
"I crushed it today" → chat
"Update yesterday, forgot eggs" → log
"Am I hitting protein?" → chat"""

        try:
            response = self.llm.chat(
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0,
                max_tokens=5
            )
            return 'log' if 'log' in response.strip().lower() else 'chat'
        except Exception:
            return 'chat'  # Safe default


# Made with Bob