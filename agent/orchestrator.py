"""
AgentOrchestrator — the main pipeline coordinator.

Replaces ChatAgent with a cleaner, more testable architecture.
Coordinates all pipeline steps: intent classification, date resolution,
context loading, LLM calls, file writes, and git commits.

This is the "brain" of the agent — it knows the sequence of steps
but delegates all actual work to specialized components.
"""
from typing import Dict, List, Optional, Any, Callable, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from agent.intent import IntentClassifier
    from agent.date_resolver import DateResolver
    from agent.context_manager import ContextManager
    from agent.nutrition_pipeline import NutritionPipeline
    from vault.writer import VaultWriter
    from git_manager.commits import GitManager
    from config.settings import Settings


class AgentOrchestrator:
    """
    Main pipeline coordinator.
    
    Replaces ChatAgent with a cleaner, more testable architecture.
    Coordinates all pipeline steps but delegates work to specialized components.
    
    The orchestrator is stateful (conversation history, pending confirmations)
    but all other components are stateless or have explicit cache invalidation.
    """
    
    def __init__(
        self,
        intent_classifier: 'IntentClassifier',
        date_resolver: 'DateResolver',
        context_manager: 'ContextManager',
        nutrition_pipeline: 'NutritionPipeline',
        vault_writer: 'VaultWriter',
        git_manager: 'GitManager',
        settings: 'Settings',
        on_event: Callable[[str, Dict[str, Any]], None]
    ):
        self.intent_classifier = intent_classifier
        self.date_resolver = date_resolver
        self.context_manager = context_manager
        self.nutrition_pipeline = nutrition_pipeline
        self.vault_writer = vault_writer
        self.git_manager = git_manager
        self.settings = settings
        self.on_event = on_event
        
        # State
        self.conversation_history: List[Dict] = []
        self.pending_confirmation: Optional[Dict] = None
    
    def process(self, user_input: str) -> str:
        """
        Main entry point for processing user input.
        Returns a response string to display to the user.
        """
        if not user_input.strip():
            return "What would you like to log or ask?"
        
        # Handle pending confirmation
        if self.pending_confirmation:
            return self._handle_confirmation(user_input)
        
        # Classify intent
        self._emit("classifying", {"input": user_input})
        intent = self.intent_classifier.classify(
            user_input, 
            self.conversation_history
        )
        
        if intent == "log":
            return self._run_log_pipeline(user_input)
        else:
            return self._run_chat_pipeline(user_input)
    
    def _run_log_pipeline(self, user_input: str) -> str:
        """Run the food logging pipeline."""
        
        # Step 1: Resolve date
        self._emit("resolving_date", {})
        target_date = self.date_resolver.resolve(
            user_input, 
            self.conversation_history
        )
        
        # Step 2: Load context (cached)
        self._emit("loading_context", {})
        context = self.context_manager.get_context(target_date)
        
        # Step 3: Call nutrition pipeline
        self._emit("calculating_nutrition", {})
        result = self.nutrition_pipeline.process(
            user_input=user_input,
            context=context,
            target_date=target_date,
            conversation_history=self.conversation_history
        )
        
        if not result.success:
            self._emit("error", {"error": result.error})
            return f"I couldn't parse that. {result.error}"
        
        # Use LLM's resolved date if available (FIX F-07)
        if hasattr(result, 'resolved_date') and result.resolved_date:
            target_date = result.resolved_date
        
        # Step 4: Confirm before write (if configured)
        if self.settings.agent_confirm_before_write:
            self.pending_confirmation = {
                "date": target_date,
                "data": result.log_data,
                "summary": result.summary,
                "action": result.action
            }
            self._update_history(user_input, f"Ready to log: {result.summary}")
            return f"Ready to log:\n{result.summary}\n\nConfirm? (yes/no)"
        
        # Step 5: Write file
        return self._commit_log(target_date, result)
    
    def _run_chat_pipeline(self, user_input: str) -> str:
        """Run the conversational chat pipeline."""
        self._emit("thinking", {})
        context = self.context_manager.get_context()
        
        response = self.nutrition_pipeline.chat(
            user_input=user_input,
            context=context,
            conversation_history=self.conversation_history
        )
        
        self._update_history(user_input, response)
        return response
    
    def _commit_log(self, target_date: datetime, result: 'PipelineResult') -> str:
        """Write log file and commit to git."""
        self._emit("writing_file", {"date": str(target_date.date())})
        log_path = self.vault_writer.write_daily_log(
            date=target_date,
            data=result.log_data,
            merge=(result.action == "update")
        )
        
        self._emit("committing", {})
        if self.settings.git_enabled:
            commit_summary = (
                f"Cal: {result.log_data.get('calories')} | "
                f"P: {result.log_data.get('protein')}g | "
                f"Deficit: {result.log_data.get('deficit')}"
            )
            self.git_manager.commit_file(
                file_path=log_path,
                action=result.action,
                date=target_date,
                summary=commit_summary
            )
        
        # Push if enabled (FIX F-11)
        if self.settings.git_enabled and self.settings.git_auto_push:
            self._emit("pushing", {})
            try:
                self.git_manager.push()
            except Exception as e:
                # Don't fail the whole operation if push fails
                self._emit("error", {"error": f"Push failed: {str(e)}"})
        
        self._emit("done", {"summary": result.summary})
        date_str = target_date.strftime("%Y-%m-%d")
        success_msg = f"✅ Logged {date_str}\n{result.summary}"
        self._update_history("", success_msg)
        return success_msg
    
    def _handle_confirmation(self, user_input: str) -> str:
        """Handle yes/no confirmation for pending log."""
        text = user_input.strip().lower()
        
        if text in ['yes', 'y', 'confirm', 'ok']:
            pending = self.pending_confirmation
            self.pending_confirmation = None
            result = PipelineResult(
                success=True,
                log_data=pending['data'],
                summary=pending['summary'],
                action=pending['action']
            )
            return self._commit_log(pending['date'], result)
        
        elif text in ['no', 'n', 'cancel']:
            self.pending_confirmation = None
            return "Cancelled. What would you like to do?"
        
        else:
            # User is providing a correction — clear pending and reprocess
            self.pending_confirmation = None
            return self.process(user_input)
    
    def _emit(self, event: str, data: Dict[str, Any]):
        """Emit a pipeline event to the UI callback."""
        self.on_event(event, data)
    
    def _update_history(self, user_input: str, response: str):
        """Update conversation history."""
        if user_input:
            self.conversation_history.append(
                {"role": "user", "content": user_input}
            )
        self.conversation_history.append(
            {"role": "assistant", "content": response}
        )
        # Keep last 20 messages
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    def reset(self):
        """Reset conversation state."""
        self.conversation_history = []
        self.pending_confirmation = None


class PipelineResult:
    """Result from the nutrition pipeline."""
    def __init__(
        self,
        success: bool,
        log_data: Optional[Dict] = None,
        summary: str = "",
        action: str = "create",
        error: str = "",
        resolved_date: Optional[datetime] = None
    ):
        self.success = success
        self.log_data = log_data or {}
        self.summary = summary
        self.action = action
        self.error = error
        self.resolved_date = resolved_date

# Made with Bob
