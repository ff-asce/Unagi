"""
NutritionPipeline — handles all LLM interactions for the agent.

Two modes:
- process(): For food logging, returns structured PipelineResult
- chat(): For conversation, returns plain text response

This class draws the seams for future multi-agent architecture (Phase 3).
In Phase 3, process() will delegate to specialized agents (meal parser,
macro calculator, etc.) orchestrated by LangGraph.
"""
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from agent.llm import LLMClient
    from agent.context_manager import Context
    from agent.orchestrator import PipelineResult


class NutritionPipeline:
    """
    Handles all LLM interactions for the agent.
    
    Two modes:
    - process(): For food logging, returns structured PipelineResult
    - chat(): For conversation, returns plain text response
    
    This class draws the seams for future multi-agent architecture.
    In Phase 3, process() will delegate to specialized agents
    (meal parser, macro calculator, etc.) orchestrated by LangGraph.
    """
    
    def __init__(self, llm_client: 'LLMClient'):
        self.llm = llm_client
    
    def process(
        self,
        user_input: str,
        context: 'Context',
        target_date: datetime,
        conversation_history: Optional[List[Dict]] = None
    ) -> 'PipelineResult':
        """
        Process a food log request.
        Returns a PipelineResult with structured log data.
        """
        from agent.orchestrator import PipelineResult
        
        prompt = self._build_log_prompt(context, target_date)
        
        try:
            response = self.llm.chat_with_system(
                system_prompt=prompt,
                user_message=user_input,
                conversation_history=conversation_history or [],
                temperature=0.3,
                json_mode=True      # Use JSON mode for reliable parsing
            )
            
            log_data = self._parse_response(response)
            
            # Override date with LLM's resolved date (FIX F-07)
            llm_date = log_data.get('date') or log_data.get('data', {}).get('date')
            from agent.date_resolver import DateResolver
            resolver = DateResolver(self.llm)
            resolved_date = resolver.override_from_llm_response(llm_date, target_date)
            
            data = log_data.get('data', log_data)
            summary = log_data.get('summary', self._auto_summary(data))
            action = log_data.get('action', 'create')
            
            return PipelineResult(
                success=True,
                log_data=data,
                summary=summary,
                action=action,
                resolved_date=resolved_date
            )
            
        except Exception as e:
            return PipelineResult(
                success=False,
                error=str(e)
            )
    
    def chat(
        self,
        user_input: str,
        context: 'Context',
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Process a conversational message.
        Returns plain text response.
        """
        return self.llm.chat_with_system(
            system_prompt=context.system_prompt,
            user_message=user_input,
            conversation_history=conversation_history or [],
            temperature=0.7
        )
    
    def _build_log_prompt(self, context: 'Context', target_date: datetime) -> str:
        """Build the system prompt for a log request."""
        date_str = target_date.strftime("%Y-%m-%d")
        
        # Load existing log for merge context (FIX F-08)
        existing_context = ""
        existing_log = None
        try:
            from vault.reader import get_vault_reader
            reader = get_vault_reader()
            existing_log = reader.read_daily_log(target_date)
        except Exception:
            pass
        
        if existing_log:
            existing_context = f"""
EXISTING LOG FOR {date_str} — preserve these entries unless told to change them:
Breakfast: {existing_log.get('breakfast', '—')}
Lunch: {existing_log.get('lunch', '—')}
Dinner: {existing_log.get('dinner', '—')}
Misc: {existing_log.get('misc', '—')}
Current totals: {existing_log.get('calories', 0)} kcal | 
P: {existing_log.get('protein', 0)}g | 
C: {existing_log.get('carbs', 0)}g | 
F: {existing_log.get('fats', 0)}g

When updating, include BOTH existing and new content in meal fields.
Recalculate all macros to reflect the complete day.
"""
        
        log_schema = """
Respond with ONLY valid JSON in this exact structure:
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
    "breakfast": "<HH:MM AM/PM - description>" or "—",
    "lunch": "<HH:MM AM/PM - description>" or "—",
    "dinner": "<HH:MM AM/PM - description>" or "—",
    "misc": "<description>" or "—",
    "notes": "<full notes string with ● section separators>"
  },
  "summary": "<one line: what was logged and key macros>"
}
"""
        
        return context.system_prompt + existing_context + "\n\n" + log_schema
    
    def _parse_response(self, response: str) -> Dict:
        """Robustly parse JSON from LLM response (FIX F-04)."""
        # Direct parse (JSON mode should give clean JSON)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Strip markdown fences
        clean = re.sub(r'```(?:json)?\s*', '', response).strip()
        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            pass
        
        # Balanced brace extraction
        start = response.find('{')
        if start == -1:
            raise ValueError(
                f"No JSON found in response.\nResponse was:\n{response[:400]}"
            )
        depth = 0
        for i, char in enumerate(response[start:], start):
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    return json.loads(response[start:i+1])
        
        raise ValueError(f"Malformed JSON in response: {response[:400]}")
    
    def _auto_summary(self, data: Dict) -> str:
        """Generate a summary if the LLM didn't provide one."""
        return (
            f"Cal: {data.get('calories', 0)} | "
            f"P: {data.get('protein', 0)}g | "
            f"C: {data.get('carbs', 0)}g | "
            f"F: {data.get('fats', 0)}g | "
            f"Deficit: {data.get('deficit', 0)}"
        )

# Made with Bob
