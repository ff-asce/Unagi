# 🐍 UNAGI — Architecture Specification
### `specs/v1/ARCH_SPEC_v1.md`
**Version:** 1.0
**Status:** Ready for implementation
**Last Updated:** 2026-05-26
**Applies To:** Codebase after `FIX_SPEC_v1.md` is fully implemented
**Companion Specs:** `FIX_SPEC_v1.md`, `UI_SPEC_v1.md` (forthcoming)

---

## Overview

This spec defines the architectural improvements to make before the codebase grows further. The goal is not to rewrite what works — the infrastructure layer (`vault/`, `git_manager/`, `config/`) is clean and should be left largely intact. The changes are targeted at three layers:

1. **The agent layer** — break `ChatAgent` apart into an `AgentOrchestrator` with discrete pipeline steps
2. **The dependency layer** — replace implicit singleton coupling with explicit dependency injection
3. **The infrastructure layer** — add context caching, an event/callback system, and LangGraph-ready seams

None of these changes alter external behaviour. The app runs identically before and after. The payoff is that Phase 2 (RAG, SQLite memory), Phase 3 (multi-agent with LangGraph), and Phase 5 (web UI) become surgical additions rather than rewrites.

---

## Guiding Principles

**1. Design for the next phase, not the final phase**
Every decision is evaluated against: *does this make Phase 2 easier without over-engineering for Phase 3?* If yes, do it. If it only pays off in Phase 4+, defer it.

**2. No frameworks until they earn their place**
LangChain and LangGraph are not introduced in this spec. The architecture is designed to make their eventual introduction a drop-in replacement, not a refactor. The seams are drawn now; the framework slots in later.

**3. The `.md` files are always the source of truth**
All architectural additions (caching, SQLite in Phase 2, vector store in Phase 2) are secondary indexes. The Obsidian vault files are never replaced as the primary store. Any index can be rebuilt from the files.

**4. Keep the CLI as the reference implementation**
The web UI is a future wrapper. Every architectural decision is validated by asking: *does this work cleanly for the CLI today, and does it cleanly support a web UI tomorrow?*

---

## Current Architecture — What's Wrong

```
main.py
  └── CLI
        └── ChatAgent  ←  does everything
              ├── detect_intent()         # language understanding
              ├── parse_date_reference()  # date parsing
              ├── handle_chat()           # LLM call (chat mode)
              ├── handle_log()            # LLM call (log mode) + file write + git
              ├── complete_pending_log()  # file write + git
              └── get_context_loader()    # reads vault
```

**Problems with this structure:**

- **One class, five responsibilities.** Intent detection, date parsing, LLM orchestration, file writing, and git commits all live in `ChatAgent`. Each is hard to test in isolation, and changes in one area risk breaking others.

- **Two separate LLM call paths.** `handle_chat()` and `handle_log()` build the system prompt differently, call the LLM differently, and manage conversation history inconsistently. This is why F-06 (history loss) exists.

- **No pipeline concept.** A log request is a multi-step process: classify intent → resolve date → build context → call LLM → parse response → validate → write file → commit. Currently this is one tangled function. There's no way to insert a step (e.g. a USDA lookup in Phase 3) without touching the core logic.

- **Tight coupling via singletons.** Every module calls `get_settings()`, `get_vault_reader()`, etc. directly. This makes testing hard (shared global state between test cases), and makes the web UI hard to add (no way to have per-request instances).

- **No event system.** The CLI has no way to show real-time progress during a log operation ("Parsing food... Calculating macros... Writing file...") because everything happens synchronously in one function with no callbacks.

---

## Target Architecture

```
main.py
  └── CLI / Web UI (future)
        └── AgentOrchestrator          ← coordinates the pipeline
              ├── IntentClassifier     ← single responsibility: log or chat?
              ├── DateResolver         ← single responsibility: what date?
              ├── ContextManager       ← single responsibility: build LLM context (cached)
              ├── NutritionPipeline    ← single responsibility: LLM call + parse response
              │     ├── step: build_prompt()
              │     ├── step: call_llm()
              │     ├── step: parse_response()
              │     └── step: validate_output()
              ├── VaultWriter          ← unchanged from current (already good)
              └── GitManager           ← unchanged from current (already good)
```

Each component has one job. The `AgentOrchestrator` wires them together and emits events at each step. The CLI listens to events to show progress. The future web UI listens to the same events to push status updates to the browser.

---

## Component Specifications

---

### 1. `AgentOrchestrator` — replaces `ChatAgent`

**File:** `agent/orchestrator.py` (new file)
**Replaces:** `agent/chat.py`

**Responsibility:** Receive a user message, route it through the correct pipeline, return a response. Does not implement any pipeline step itself — only coordinates.

```python
"""Agent orchestrator — coordinates the pipeline steps."""
from typing import Callable, Optional, Dict, Any
from datetime import datetime


class AgentOrchestrator:
    """
    Coordinates the agent pipeline.
    
    All dependencies are injected — no singletons inside this class.
    This makes it testable and reusable across CLI and web UI.
    
    Event callbacks allow the UI to show real-time progress without
    the orchestrator knowing anything about the UI layer.
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
        on_event: Optional[Callable] = None   # event callback for UI
    ):
        self.intent_classifier = intent_classifier
        self.date_resolver = date_resolver
        self.context_manager = context_manager
        self.nutrition_pipeline = nutrition_pipeline
        self.vault_writer = vault_writer
        self.git_manager = git_manager
        self.settings = settings
        self.on_event = on_event or (lambda event, data: None)
        
        self.conversation_history = []
        self.pending_confirmation = None
    
    def process(self, user_input: str) -> str:
        """
        Process a user message end-to-end.
        Single entry point for all user input.
        """
        if not user_input.strip():
            return "Tell me what you ate or ask me anything."
        
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
            return f"I couldn't parse that. {result.error}"
        
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
        error: str = ""
    ):
        self.success = success
        self.log_data = log_data or {}
        self.summary = summary
        self.action = action
        self.error = error
```

---

### 2. `IntentClassifier` — extracted from `ChatAgent`

**File:** `agent/intent.py` (new file)

**Responsibility:** Given a user message and conversation history, return `"log"` or `"chat"`. Nothing else.

```python
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
```

---

### 3. `DateResolver` — extracted from `ChatAgent`

**File:** `agent/date_resolver.py` (new file)

**Responsibility:** Given a user message, return the target `datetime` for the log entry.

```python
"""Date resolution for log entries."""
import re
from typing import Optional, List, Dict
from datetime import datetime, timedelta


class DateResolver:
    """
    Resolves natural language date references to datetime objects.
    
    Two-stage: fast regex for common cases, LLM for complex cases.
    The LLM's date in the JSON response is always treated as the 
    primary source of truth (see FIX_SPEC F-07).
    
    In Phase 3, this can be enriched with history context from SQLite
    (e.g. "when I had the big workout" requires knowing workout dates).
    """
    
    def __init__(self, llm_client: Optional['LLMClient'] = None):
        self.llm = llm_client  # Optional — only used for complex cases
    
    def resolve(
        self, 
        user_input: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> datetime:
        """Resolve date reference. Returns today if none found."""
        text = user_input.lower()
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Today
        if 'today' in text or not self._has_date_reference(text):
            return today
        
        # Yesterday
        if 'yesterday' in text:
            return today - timedelta(days=1)
        
        # N days ago
        m = re.search(r'(\d+)\s+days?\s+ago', text)
        if m:
            return today - timedelta(days=int(m.group(1)))
        
        # Day of week
        weekdays = ['monday','tuesday','wednesday','thursday',
                    'friday','saturday','sunday']
        for i, day in enumerate(weekdays):
            if day in text:
                current_wd = today.weekday()
                days_back = (current_wd - i) % 7
                if days_back == 0:
                    days_back = 7  # "last Monday" when today is Monday
                return today - timedelta(days=days_back)
        
        # Explicit date (May 19, 19th May, 2026-05-19, etc.)
        explicit = self._parse_explicit_date(user_input)
        if explicit:
            return explicit
        
        return today
    
    def override_from_llm_response(
        self, 
        llm_date_str: Optional[str],
        fallback: datetime
    ) -> datetime:
        """
        Override client-side resolved date with LLM-resolved date.
        Called after the LLM returns its JSON response.
        The LLM's date is primary (see FIX_SPEC F-07).
        """
        if not llm_date_str:
            return fallback
        try:
            return datetime.strptime(llm_date_str[:10], "%Y-%m-%d")
        except (ValueError, TypeError):
            return fallback
    
    def _has_date_reference(self, text: str) -> bool:
        """Check if text contains any date reference."""
        date_words = ['yesterday', 'today', 'ago', 'last', 'monday',
                      'tuesday', 'wednesday', 'thursday', 'friday',
                      'saturday', 'sunday', 'january', 'february',
                      'march', 'april', 'may', 'june', 'july', 'august',
                      'september', 'october', 'november', 'december']
        return any(w in text for w in date_words) or bool(
            re.search(r'\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}', text)
        )
    
    def _parse_explicit_date(self, text: str) -> Optional[datetime]:
        """Try to parse an explicit date from text."""
        patterns = [
            ("%Y-%m-%d", r'\d{4}-\d{2}-\d{2}'),
            ("%d/%m/%Y", r'\d{1,2}/\d{1,2}/\d{4}'),
            ("%d-%m-%Y", r'\d{1,2}-\d{1,2}-\d{4}'),
        ]
        for fmt, pattern in patterns:
            m = re.search(pattern, text)
            if m:
                try:
                    return datetime.strptime(m.group(), fmt)
                except ValueError:
                    continue
        return None
```

---

### 4. `ContextManager` — replaces `ContextLoader` with caching

**File:** `agent/context_manager.py` (new file, replaces `agent/context.py`)

**Responsibility:** Build and cache the LLM context (user profile + recent logs). Invalidate cache when vault files are written.

**Why caching matters:**
Currently, every LLM call reads the user profile and up to 7 log files from disk. For the free Gemini tier with rate limits, reducing unnecessary I/O also reduces the chance of slow responses. More importantly, context loading will become expensive when Phase 2 adds a SQLite lookup and Phase 2 adds vector retrieval — caching becomes essential then, and adding it now costs almost nothing.

```python
"""Context manager with caching for LLM prompts."""
import time
from typing import Optional, Dict, Any, List
from datetime import datetime


class ContextManager:
    """
    Builds and caches context for LLM calls.
    
    Cache invalidation strategy:
    - Cache expires after CACHE_TTL_SECONDS (default 30s)
    - Cache is explicitly invalidated when VaultWriter writes a file
    - Cache is invalidated when user profile changes
    
    In Phase 2, this class grows to include:
    - SQLite query for structured history
    - ChromaDB vector retrieval for relevant past logs
    The interface stays the same — callers don't need to change.
    """
    
    CACHE_TTL_SECONDS = 30
    
    def __init__(
        self,
        vault_reader: 'VaultReader',
        prompt_builder: 'PromptBuilder',
        context_days: int = 7
    ):
        self.reader = vault_reader
        self.prompt_builder = prompt_builder
        self.context_days = context_days
        
        # Cache state
        self._profile_cache: Optional[Dict] = None
        self._logs_cache: Optional[List[Dict]] = None
        self._cache_timestamp: float = 0
        self._cache_valid = False
    
    def get_context(self, target_date: Optional[datetime] = None) -> 'Context':
        """
        Get the full context for an LLM call.
        Returns cached context if fresh, otherwise reloads from disk.
        """
        if not self._is_cache_valid():
            self._reload_cache()
        
        return Context(
            profile=self._profile_cache,
            recent_logs=self._logs_cache,
            target_date=target_date or datetime.now(),
            system_prompt=self.prompt_builder.build(
                self._profile_cache,
                self._logs_cache
            )
        )
    
    def invalidate(self):
        """
        Explicitly invalidate the cache.
        Called by VaultWriter after every file write.
        """
        self._cache_valid = False
        self._profile_cache = None
        self._logs_cache = None
    
    def get_today_summary(self) -> Optional[Dict]:
        """Get today's log if it exists."""
        try:
            return self.reader.read_daily_log(datetime.now())
        except Exception:
            return None
    
    def get_weekly_summary(self) -> Dict[str, Any]:
        """Get aggregated stats for the last 7 days."""
        logs = self._logs_cache or []
        if not logs:
            return {'days': 0, 'avg_calories': 0, 'avg_protein': 0,
                    'avg_deficit': 0, 'total_deficit': 0}
        
        days = len(logs)
        return {
            'days': days,
            'avg_calories': int(sum(l.get('calories', 0) for l in logs) / days),
            'avg_protein': int(sum(l.get('protein', 0) for l in logs) / days),
            'avg_deficit': int(sum(l.get('deficit', 0) for l in logs) / days),
            'total_deficit': sum(l.get('deficit', 0) for l in logs)
        }
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still fresh."""
        if not self._cache_valid:
            return False
        age = time.time() - self._cache_timestamp
        return age < self.CACHE_TTL_SECONDS
    
    def _reload_cache(self):
        """Reload profile and logs from disk."""
        try:
            self._profile_cache = self.reader.read_user_profile()
        except Exception:
            self._profile_cache = None
        
        try:
            self._logs_cache = self.reader.read_recent_logs(self.context_days)
        except Exception:
            self._logs_cache = []
        
        self._cache_timestamp = time.time()
        self._cache_valid = True


class Context:
    """Immutable context snapshot for a single LLM call."""
    
    def __init__(
        self,
        profile: Optional[Dict],
        recent_logs: List[Dict],
        target_date: datetime,
        system_prompt: str
    ):
        self.profile = profile
        self.recent_logs = recent_logs
        self.target_date = target_date
        self.system_prompt = system_prompt
```

---

### 5. `NutritionPipeline` — replaces the LLM call logic in `ChatAgent`

**File:** `agent/nutrition_pipeline.py` (new file)

**Responsibility:** Given context and user input, call the LLM and parse the response into a structured result. This is the core reasoning step. In Phase 3, each sub-step here becomes a specialized agent.

```python
"""Nutrition reasoning pipeline — the core LLM interaction layer."""
import json
import re
from typing import Optional, List, Dict
from datetime import datetime


class NutritionPipeline:
    """
    Handles all LLM interactions for the agent.
    
    Two modes:
    - process(): food logging — returns structured PipelineResult
    - chat(): conversational — returns plain text response
    
    This class draws the seams for future multi-agent architecture:
    
    Current (v1): One LLM call does everything
    
    Phase 3 (LangGraph):
      ParserAgent    → extracts food items and quantities
      NutritionAgent → calculates macros/micros
      WriterAgent    → formats the .md output
      CoachAgent     → generates insights and notes
    
    The interface (process() and chat()) stays the same.
    The orchestrator doesn't change. Only this class is replaced.
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
            resolver = DateResolver()
            resolved_date = resolver.override_from_llm_response(llm_date, target_date)
            
            data = log_data.get('data', log_data)
            summary = log_data.get('summary', self._auto_summary(data))
            action = log_data.get('action', 'create')
            
            return PipelineResult(
                success=True,
                log_data=data,
                summary=summary,
                action=action
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
```

---

### 6. `PromptBuilder` — extracted from `prompts.py`

**File:** `agent/prompt_builder.py` (new file, wraps `prompts.py`)

**Responsibility:** Build the system prompt from a user profile and recent logs. Thin wrapper around the existing `get_system_prompt()` function, adding a class interface for dependency injection.

```python
"""Prompt builder — thin class wrapper around prompts.py."""
from typing import Optional, List, Dict
from .prompts import get_system_prompt


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
```

---

### 7. Event System — `EventBus`

**File:** `agent/events.py` (new file)

**Responsibility:** Decouple the pipeline from the UI. The orchestrator emits events; the UI subscribes to them to show progress indicators, status updates, and real-time feedback.

This is the bridge between the agent layer and the UI layer. Without it, adding real-time progress to the Textual UI (or the future web UI) requires touching agent code. With it, the UI just subscribes to events.

```python
"""Event system for decoupling pipeline from UI."""
from typing import Callable, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class PipelineEvent(str, Enum):
    """Events emitted during pipeline execution."""
    CLASSIFYING     = "classifying"       # Determining intent
    RESOLVING_DATE  = "resolving_date"    # Parsing date reference
    LOADING_CONTEXT = "loading_context"  # Reading vault files
    CALCULATING     = "calculating_nutrition"  # LLM call in progress
    WRITING_FILE    = "writing_file"      # Writing .md to vault
    COMMITTING      = "committing"        # Git commit in progress
    PUSHING         = "pushing"           # Git push in progress
    DONE            = "done"              # Pipeline complete
    ERROR           = "error"             # Something failed


@dataclass
class Event:
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
```

---

### 8. Dependency Injection — `Container`

**File:** `agent/container.py` (new file)

**Responsibility:** Wire all dependencies together. One place where all instances are created and connected. This replaces the scattered `get_*()` singleton calls with a single assembly point.

The Container is not a framework — it's just a function that creates instances and injects them. It keeps singletons where they make sense (one LLM client, one vault reader), while making the wiring explicit and testable.

```python
"""
Dependency injection container.
Creates and wires all agent components.

This is the ONLY place where singletons are created.
All other code receives dependencies via __init__ parameters.

Testing: create a Container with mock dependencies.
Web UI: create a Container per request (or share where safe).
"""
from config.settings import Settings
from agent.intent import IntentClassifier
from agent.date_resolver import DateResolver
from agent.context_manager import ContextManager
from agent.prompt_builder import PromptBuilder
from agent.nutrition_pipeline import NutritionPipeline
from agent.orchestrator import AgentOrchestrator
from agent.events import EventBus
from agent.llm import LLMClient
from vault.reader import VaultReader
from vault.writer import VaultWriter
from git_manager.commits import GitManager


class Container:
    """
    Dependency injection container.
    
    Creates all instances once and wires them together.
    Pass this container to main.py and the CLI — they 
    pull what they need from it.
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        
        # Infrastructure layer (unchanged from current)
        self.llm_client = LLMClient(settings)
        self.vault_reader = VaultReader(settings)
        self.vault_writer = VaultWriter(settings, self.vault_reader)
        self.git_manager = GitManager(settings)
        
        # Agent layer (new)
        self.event_bus = EventBus()
        self.prompt_builder = PromptBuilder()
        self.intent_classifier = IntentClassifier(self.llm_client)
        self.date_resolver = DateResolver(self.llm_client)
        self.context_manager = ContextManager(
            vault_reader=self.vault_reader,
            prompt_builder=self.prompt_builder,
            context_days=settings.agent_context_days
        )
        self.nutrition_pipeline = NutritionPipeline(self.llm_client)
        
        # Wire cache invalidation:
        # When writer writes a file, context cache is invalidated
        # This is the event system in action — writer doesn't know
        # about context_manager; the container wires them together
        original_write = self.vault_writer.write_daily_log
        def write_and_invalidate(*args, **kwargs):
            result = original_write(*args, **kwargs)
            self.context_manager.invalidate()
            return result
        self.vault_writer.write_daily_log = write_and_invalidate
        
        # Orchestrator gets everything injected
        self.orchestrator = AgentOrchestrator(
            intent_classifier=self.intent_classifier,
            date_resolver=self.date_resolver,
            context_manager=self.context_manager,
            nutrition_pipeline=self.nutrition_pipeline,
            vault_writer=self.vault_writer,
            git_manager=self.git_manager,
            settings=settings,
            on_event=self.event_bus.emit
        )


def create_container() -> Container:
    """Create the production container. Called once from main.py."""
    from config.settings import get_settings
    return Container(get_settings())
```

---

### 9. Updated `main.py`

The new `main.py` is significantly cleaner — it just creates the container and passes it to the CLI:

```python
#!/usr/bin/env python3
"""UNAGI - Total Food Awareness"""
import sys
from pathlib import Path


def main():
    try:
        from config import get_settings, ConfigError
        from agent.container import create_container
        from onboarding import needs_onboarding, run_onboarding_flow
        from ui import run_cli
        from ui.mascot import get_error_banner
        
        # Load config
        try:
            settings = get_settings()
        except ConfigError as e:
            print(get_error_banner("Configuration"))
            print(f"\n{str(e)}\n")
            sys.exit(1)
        
        # Validate vault path (warn, don't block — FIX F-02)
        vault_path = Path(settings.vault_root) if settings.vault_root else None
        if not vault_path:
            print(get_error_banner("Configuration"))
            print("\nVault root is not configured in config.yaml\n")
            sys.exit(1)
        
        # Onboarding check
        if needs_onboarding(settings):
            try:
                if not run_onboarding_flow(settings):
                    sys.exit(0)
            except KeyboardInterrupt:
                print("\nOnboarding cancelled.\n")
                sys.exit(0)
        
        # Create dependency container
        container = create_container()
        
        # Ensure vault structure
        container.vault_writer._ensure_vault_structure()
        container.vault_writer.create_dashboard_if_missing()
        
        # Run CLI
        run_cli(container)
        
    except KeyboardInterrupt:
        print("\n\nGoodbye! 🐍\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
```

---

## Updated Infrastructure — Minor Changes

### `VaultWriter` — accept `VaultReader` via injection

```python
# CURRENT
class VaultWriter:
    def __init__(self):
        self.settings = get_settings()        # singleton
        self.reader = get_vault_reader()      # singleton

# FIXED — accept dependencies
class VaultWriter:
    def __init__(self, settings: Settings, reader: VaultReader):
        self.settings = settings
        self.reader = reader
```

Keep `get_vault_writer()` as a convenience wrapper for backward compatibility during transition:
```python
def get_vault_writer(reload=False) -> VaultWriter:
    global _vault_writer
    if _vault_writer is None or reload:
        _vault_writer = VaultWriter(get_settings(), get_vault_reader())
    return _vault_writer
```

### `VaultReader` — accept `Settings` via injection

```python
# CURRENT
class VaultReader:
    def __init__(self):
        self.settings = get_settings()  # singleton

# FIXED
class VaultReader:
    def __init__(self, settings: Settings):
        self.settings = settings
```

### `LLMClient` — accept `Settings` via injection, add `json_mode`

```python
# CURRENT
class LLMClient:
    def __init__(self):
        settings = get_settings()  # singleton

# FIXED
class LLMClient:
    def __init__(self, settings: Settings):
        self.client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url
        )
        self.model = settings.llm_model_name
    
    def chat(self, messages, temperature=0.7, max_tokens=None, 
             stream=False, json_mode=False) -> str:  # ADD json_mode
        kwargs = {"model": self.model, "messages": messages, 
                  "temperature": temperature}
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        # ... rest unchanged
```

### `GitManager` — accept `Settings` via injection, async push

```python
# CURRENT
class GitManager:
    def __init__(self):
        self.settings = get_settings()  # singleton

# FIXED  
class GitManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        # ... rest unchanged, push is already made async in FIX F-09
```

---

## New File Structure

```
unagi/
├── main.py                          ← simplified (uses container)
├── agent/
│   ├── __init__.py                  ← update exports
│   ├── container.py                 ← NEW: dependency injection
│   ├── orchestrator.py              ← NEW: replaces chat.py
│   ├── intent.py                    ← NEW: extracted from chat.py
│   ├── date_resolver.py             ← NEW: extracted from chat.py
│   ├── context_manager.py           ← NEW: replaces context.py (adds caching)
│   ├── nutrition_pipeline.py        ← NEW: extracted from chat.py
│   ├── prompt_builder.py            ← NEW: class wrapper for prompts.py
│   ├── events.py                    ← NEW: event bus
│   ├── chat.py                      ← DEPRECATED (keep for transition)
│   ├── context.py                   ← DEPRECATED (keep for transition)
│   ├── llm.py                       ← MODIFIED (injection + json_mode)
│   └── prompts.py                   ← UNCHANGED (fixed by FIX_SPEC F-03)
├── vault/
│   ├── reader.py                    ← MODIFIED (injection)
│   ├── writer.py                    ← MODIFIED (injection)
│   └── parser.py                    ← UNCHANGED (fixed by FIX_SPEC F-08, F-18)
├── git_manager/
│   └── commits.py                   ← MODIFIED (injection, async push)
├── config/
│   └── settings.py                  ← MODIFIED (fixed by FIX_SPEC F-02, F-13, F-20)
├── onboarding/
│   └── setup.py                     ← MODIFIED (fixed by FIX_SPEC F-16)
└── ui/
    ├── cli.py                        ← MODIFIED (use container, subscribe to events)
    └── mascot.py                     ← RECREATED (FIX_SPEC F-01)
```

---

## LangGraph Seams — Phase 3 Migration Path

The architecture is designed so that Phase 3 (multi-agent with LangGraph) requires changing only `NutritionPipeline` and the `Container`. Everything else stays the same.

**Current `NutritionPipeline.process()` — one LLM call:**
```
user_input → LLM → JSON → PipelineResult
```

**Phase 3 `NutritionPipeline.process()` — LangGraph graph:**
```
user_input
  → ParserAgent    (extracts food items, quantities, times)
  → NutritionAgent (calculates macros, looks up USDA, estimates micros)
  → CoachAgent     (generates insights, trends, corrections)
  → WriterAgent    (formats the final .md frontmatter)
  → PipelineResult
```

The `AgentOrchestrator` calls `nutrition_pipeline.process()` in both cases. The orchestrator doesn't change. The CLI doesn't change. The container wires in the new `LangGraphNutritionPipeline` instead of `NutritionPipeline`. That's the entire migration.

**Phase 2 `ContextManager.get_context()` — adds RAG:**
```
# Current: reads 7 log files from disk
profile + last_7_logs → Context

# Phase 2: semantic retrieval from SQLite + ChromaDB
profile + last_7_logs + retrieved_relevant_logs → Context
```

The `AgentOrchestrator` calls `context_manager.get_context()` in both cases. Same interface, richer data.

---

## Implementation Order

**Do not implement everything at once.** Work in this order, test between each step:

**Step 1 — Add events (no behaviour change, 20 lines):**
Create `agent/events.py`. Wire `EventBus` into `main.py`. Subscribe a simple print callback in CLI. Verify events print to console during a log operation.

**Step 2 — Extract `IntentClassifier` and `DateResolver` (refactor only):**
Create `agent/intent.py` and `agent/date_resolver.py`. Move logic from `chat.py` into them. Update `chat.py` to call the new classes. No behaviour change — this is pure extraction. Run tests after.

**Step 3 — Create `PromptBuilder` and `ContextManager` (adds caching):**
Create `agent/prompt_builder.py` and `agent/context_manager.py`. Wire cache invalidation via the vault writer. Verify that context is not reloaded from disk on every message.

**Step 4 — Create `NutritionPipeline` (refactor only):**
Move LLM call logic from `chat.py` into `nutrition_pipeline.py`. Add JSON mode. Update `chat.py` to delegate to it. No behaviour change.

**Step 5 — Create `AgentOrchestrator` (replaces ChatAgent):**
Create `agent/orchestrator.py`. Wire all the extracted components through it. Update CLI to call `orchestrator.process()` instead of `agent.process_message()`.

**Step 6 — Create `Container` (wires everything):**
Create `agent/container.py`. Update `main.py` to use `create_container()`. Update CLI to accept `container` parameter. Remove direct singleton calls from CLI.

**Step 7 — Update infrastructure layer (injection):**
Update `VaultReader`, `VaultWriter`, `LLMClient`, `GitManager` to accept Settings in `__init__`. Keep `get_*()` convenience wrappers for backward compatibility.

**Step 8 — Deprecate old files:**
Mark `agent/chat.py` and `agent/context.py` as deprecated. They still work but are no longer the primary path. Remove in v2.

---

## What This Unlocks

| Capability | Without this arch | With this arch |
|---|---|---|
| Unit test intent classifier | Can't — tangled in ChatAgent | `classifier.classify("I had chicken")` |
| Unit test date resolver | Can't — mixed with LLM calls | `resolver.resolve("last Tuesday")` |
| Show real-time progress in UI | Can't — synchronous black box | Subscribe to EventBus |
| Swap LLM backend per call | Can't — one global client | Pass different LLMClient to pipeline |
| Add Phase 2 RAG | Major refactor to ContextLoader | Add retrieval in ContextManager.get_context() |
| Add Phase 3 LangGraph | Complete rewrite of ChatAgent | Replace NutritionPipeline only |
| Add web UI | Impossible without shared state | Container is web-request-safe |
| Test without hitting LLM API | Can't — singletons everywhere | Inject mock LLMClient |

---

*Unagi Architecture Spec v1 — Built with 🐍 total food awareness.*
