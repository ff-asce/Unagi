"""Chat loop and conversation management for Unagi agent."""
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from config import get_settings
from vault import get_vault_writer, get_vault_reader
from git_manager import get_git_manager
from .llm import get_llm_client, LLMError
from .context import get_context_loader


class ChatError(Exception):
    """Raised when chat operations fail."""
    pass


class ChatAgent:
    """Main chat agent for conversation and food logging."""
    
    def __init__(self):
        """Initialize the chat agent."""
        self.settings = get_settings()
        self.llm = get_llm_client()
        self.context_loader = get_context_loader()
        self.writer = get_vault_writer()
        self.reader = get_vault_reader()
        self.git = get_git_manager()
        self.conversation_history: List[Dict[str, str]] = []
        self.pending_log: Optional[Dict[str, Any]] = None  # Store pending log data for confirmation
    
    def detect_intent(self, user_input: str) -> str:
        """Use LLM to classify intent as 'log' or 'chat'.
        
        Args:
            user_input: User's message
            
        Returns:
            'log' or 'chat'
        """
        # Fast path: explicit log command
        if user_input.lower().strip().startswith('log '):
            return 'log'
        
        # Fast path: explicit question punctuation with no food quantities
        if user_input.strip().endswith('?') and not re.search(r'\d+\s*(g|ml|kg|grams|ml)', user_input.lower()):
            return 'chat'
        
        # LLM classification for ambiguous cases
        classification_prompt = """You are a classifier. Determine if the user's message is:
- "log": The user is describing food they ate or want to record (contains food items, quantities, meal times)
- "chat": The user is asking a question, making a statement, or requesting information/advice

Respond with ONLY the single word: log or chat

Examples:
"I had 200g chicken and rice for lunch" → log
"How am I doing this week?" → chat
"Today I ate 10 almonds and green tea" → log
"What should I eat tomorrow?" → chat
"I crushed it today" → chat
"Update yesterday: forgot to add eggs" → log
"Am I hitting my protein goal?" → chat"""

        try:
            response = self.llm.chat(
                messages=[
                    {"role": "system", "content": classification_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0,
                max_tokens=5
            )
            intent = response.strip().lower()
            return 'log' if 'log' in intent else 'chat'
        except Exception:
            # Fallback to chat on any error — safer than accidentally logging
            return 'chat'
    
    def parse_date_reference(self, text: str) -> Optional[datetime]:
        """Parse date references like 'yesterday', 'last Tuesday', etc.
        
        Args:
            text: Text containing date reference
            
        Returns:
            datetime object, or None if no date found
        """
        text_lower = text.lower()
        today = datetime.now()
        
        # Today
        if 'today' in text_lower:
            return today
        
        # Yesterday
        if 'yesterday' in text_lower:
            return today - timedelta(days=1)
        
        # Days ago (e.g., "2 days ago", "3 days ago")
        days_ago_match = re.search(r'(\d+)\s+days?\s+ago', text_lower)
        if days_ago_match:
            days = int(days_ago_match.group(1))
            return today - timedelta(days=days)
        
        # Day of week (e.g., "last Monday", "Monday")
        weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for i, day in enumerate(weekdays):
            if day in text_lower:
                # Find the most recent occurrence of that weekday
                current_weekday = today.weekday()
                target_weekday = i
                days_back = (current_weekday - target_weekday) % 7
                if days_back == 0 and 'last' in text_lower:
                    days_back = 7
                return today - timedelta(days=days_back)
        
        # Default to today
        return today
    
    def handle_chat(self, user_input: str) -> str:
        """Handle general chat (questions, advice, etc.).
        
        Args:
            user_input: User's message
            
        Returns:
            Agent's response
        """
        try:
            # Get system prompt with context
            system_prompt = self.context_loader.format_for_llm()
            
            # Call LLM
            response = self.llm.chat_with_system(
                system_prompt=system_prompt,
                user_message=user_input,
                conversation_history=self.conversation_history,
                temperature=0.7
            )
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": response})
            
            # Keep only last 10 exchanges
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            return response
            
        except LLMError as e:
            raise ChatError(f"Chat failed: {str(e)}")
    
    def _extract_json(self, response: str) -> Dict[str, Any]:
        """Robustly extract JSON from LLM response.
        
        Args:
            response: LLM response text that should contain JSON
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            ChatError: If JSON cannot be extracted or parsed
        """
        # Try direct parse first (JSON mode should give clean JSON)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Strip markdown code fences if present
        clean = re.sub(r'```(?:json)?\s*', '', response).strip()
        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            pass
        
        # Find JSON object by balanced brace matching
        start = response.find('{')
        if start == -1:
            raise ChatError(
                f"LLM did not return JSON. Response was:\n{response[:500]}"
            )
        
        depth = 0
        for i, char in enumerate(response[start:], start):
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(response[start:i+1])
                    except json.JSONDecodeError as e:
                        raise ChatError(
                            f"Malformed JSON from LLM: {e}\nRaw: {response[start:i+1][:300]}"
                        )
        
        raise ChatError(f"Could not find valid JSON in response: {response[:500]}")
    
    def handle_log(self, user_input: str) -> Tuple[bool, str]:
        """Handle food logging request.
        
        Args:
            user_input: User's message with food information
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # F-07: Parse date from input as fallback only
            fallback_date = self.parse_date_reference(user_input)
            
            # Get system prompt with context
            system_prompt = self.context_loader.format_for_llm()
            
            # Add instruction to output JSON
            log_instruction = """
When the user provides food information, you MUST respond with ONLY valid JSON in this exact format:
{
  "action": "create" or "update",
  "date": "YYYY-MM-DD",
  "data": {
    "date": "YYYY-MM-DD",
    "calories": <integer>,
    "maintenance": <integer>,
    "deficit": <integer>,
    "protein": <integer>,
    "carbs": <integer>,
    "fats": <integer>,
    "fiber": <integer>,
    "breakfast": "<time and description>" or "—",
    "lunch": "<time and description>" or "—",
    "dinner": "<time and description>" or "—",
    "misc": "<description>" or "—",
    "notes": "<full notes string with ● separators>"
  },
  "summary": "<brief summary for user confirmation>"
}

Do not include any other text. Only output the JSON.
"""
            
            full_prompt = system_prompt + "\n\n" + log_instruction
            
            # F-06: Build messages with conversation history
            messages = [{"role": "system", "content": full_prompt}]
            if self.conversation_history:
                messages.extend(self.conversation_history)
            messages.append({"role": "user", "content": user_input})
            
            # Call LLM with JSON mode enabled
            response = self.llm.chat(
                messages=messages,
                temperature=0.3,  # Lower temperature for more consistent output
                json_mode=True
            )
            
            # Extract JSON from response
            try:
                log_data = self._extract_json(response)
            except ChatError as e:
                return False, str(e)
            
            # Validate JSON structure
            if 'data' not in log_data or 'summary' not in log_data:
                return False, "Invalid response format. Please try again."
            
            data = log_data['data']
            summary = log_data['summary']
            action = log_data.get('action', 'create')
            
            # F-07: Use LLM-resolved date as primary source
            llm_date_str = log_data.get('date') or data.get('date')
            
            if llm_date_str:
                try:
                    target_date = datetime.strptime(llm_date_str, "%Y-%m-%d")
                except ValueError:
                    target_date = fallback_date  # Fallback if LLM gives bad format
            else:
                target_date = fallback_date
            
            # Sanity check: warn if LLM date and client parse differ by more than 1 day
            if abs((target_date - fallback_date).days) > 1:
                print(f"Note: Using date {target_date.date()} (from your message context)")
            
            # Confirm with user if configured
            if self.settings.agent_confirm_before_write:
                # Store pending log data
                self.pending_log = {
                    'date': target_date,
                    'data': data,
                    'summary': summary,
                    'action': action
                }
                return False, f"Ready to log:\n{summary}\n\nType 'yes' to confirm or provide corrections."
            
            # Write to vault
            log_path = self.writer.write_daily_log(
                date=target_date,
                data=data,
                merge=(action == 'update')
            )
            
            # Git commit
            if self.settings.git_enabled:
                commit_summary = f"Cal: {data['calories']} | P: {data['protein']}g | Deficit: {data['deficit']}"
                self.git.commit_file(
                    file_path=log_path,
                    action=action,
                    date=target_date,
                    summary=commit_summary
                )
            
            # F-06: Update conversation history after logging
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({
                "role": "assistant",
                "content": f"Logged successfully: {summary}"
            })
            
            # Trim history to last 20 messages
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            # Success message
            date_str = target_date.strftime("%Y-%m-%d")
            success_msg = f"✅ Logged {date_str}\n{summary}"
            
            return True, success_msg
            
        except Exception as e:
            return False, f"Failed to log food: {str(e)}"
    
    def complete_pending_log(self) -> Tuple[bool, str]:
        """Complete a pending log confirmation.
        
        Returns:
            Tuple of (success, message)
        """
        if not self.pending_log:
            return False, "No pending log to confirm."
        
        try:
            # Extract pending data
            target_date = self.pending_log['date']
            data = self.pending_log['data']
            summary = self.pending_log['summary']
            action = self.pending_log['action']
            
            # Write to vault
            log_path = self.writer.write_daily_log(
                date=target_date,
                data=data,
                merge=(action == 'update')
            )
            
            # Git commit
            if self.settings.git_enabled:
                commit_summary = f"Cal: {data['calories']} | P: {data['protein']}g | Deficit: {data['deficit']}"
                self.git.commit_file(
                    file_path=log_path,
                    action=action,
                    date=target_date,
                    summary=commit_summary
                )
            
            # Clear pending log
            self.pending_log = None
            
            # Success message
            date_str = target_date.strftime("%Y-%m-%d")
            success_msg = f"✅ Logged {date_str}\n{summary}"
            
            return True, success_msg
            
        except Exception as e:
            self.pending_log = None
            return False, f"Failed to complete log: {str(e)}"
    
    def process_message(self, user_input: str) -> str:
        """Process a user message and return response.
        
        Args:
            user_input: User's message
            
        Returns:
            Agent's response
        """
        if not user_input or not user_input.strip():
            return "Please tell me what you ate or ask me a question."
        
        # Check if user is confirming a pending log
        if self.pending_log and user_input.strip().lower() in ['yes', 'y', 'confirm', 'ok']:
            success, message = self.complete_pending_log()
            return message
        
        # Check if user is canceling a pending log
        if self.pending_log and user_input.strip().lower() in ['no', 'n', 'cancel']:
            self.pending_log = None
            return "Log canceled. What would you like to do instead?"
        
        # If there's a pending log and user provides new input, treat it as a correction
        if self.pending_log:
            self.pending_log = None  # Clear the old pending log
            # Fall through to process the new input
        
        # Detect intent
        intent = self.detect_intent(user_input)
        
        if intent == 'log':
            success, message = self.handle_log(user_input)
            return message
        else:
            return self.handle_chat(user_input)
    
    def reset_conversation(self):
        """Reset conversation history."""
        self.conversation_history = []
        # F-17: Clear pending log state on reset
        self.pending_log = None
    
    def get_conversation_length(self) -> int:
        """Get number of messages in conversation history.
        
        Returns:
            Number of messages
        """
        return len(self.conversation_history)


# Global chat agent instance
_chat_agent: Optional[ChatAgent] = None


def get_chat_agent(reload: bool = False) -> ChatAgent:
    """Get the global chat agent instance.
    
    Args:
        reload: If True, create a new agent instance
        
    Returns:
        ChatAgent instance
    """
    global _chat_agent
    if _chat_agent is None or reload:
        _chat_agent = ChatAgent()
    return _chat_agent

# Made with Bob
