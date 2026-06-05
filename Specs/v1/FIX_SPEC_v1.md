# 🐍 UNAGI — Fix Specification
### `specs/v1/FIX_SPEC_v1.md`
**Version:** 1.0
**Status:** Ready for implementation
**Last Updated:** 2026-05-26
**Applies To:** Codebase as of commit history at `ff-asce/Unagi` (main branch, May 2026)
**Companion Specs:** `ARCH_SPEC_v1.md`, `UI_SPEC_v1.md` (forthcoming)

---

## Overview

This document catalogues all identified bugs, logic errors, missing functionality, and structural issues in the current v1 codebase. Each issue is described with its root cause, impact, and exact fix instructions for Claude Code.

Issues are ordered by **priority**:
- 🔴 **Critical** — will crash or silently corrupt data
- 🟡 **High** — degrades core functionality significantly
- 🟢 **Medium** — quality/reliability issue, doesn't block core use
- 🔵 **Low** — polish, consistency, or future-proofing

---

## Issue Index

| # | Priority | File | Issue |
|---|---|---|---|
| F-01 | 🔴 | `ui/mascot.py` | Binary file — will crash on import |
| F-02 | 🔴 | `config/settings.py` | Vault path validation blocks first-run |
| F-03 | 🔴 | `agent/prompts.py` | Notes suppression breaks core output |
| F-04 | 🔴 | `agent/chat.py` | Fragile JSON parsing with regex |
| F-05 | 🟡 | `agent/chat.py` | Intent detection too naive — misroutes chat as log |
| F-06 | 🟡 | `agent/chat.py` | Context lost across chat/log mode switches |
| F-07 | 🟡 | `agent/chat.py` | `handle_log()` ignores LLM-resolved date — uses client-side parse only |
| F-08 | 🟡 | `vault/parser.py` | Merge logic silently drops existing meal data |
| F-09 | 🟡 | `git_manager/commits.py` | Git push blocks main thread |
| F-10 | 🟡 | `agent/prompts.py` | User age not calculated from DOB — passed as unknown |
| F-11 | 🟢 | `requirements.txt` | Missing `python-dateutil` dependency |
| F-12 | 🟢 | `config/settings.py` | Config key mismatch — spec says `root`, code uses `root_path` |
| F-13 | 🟢 | `git_manager/commits.py` | Git root tied to vault root — no independent config |
| F-14 | 🟢 | `agent/chat.py` | Conversation history not passed during log mode |
| F-15 | 🟢 | `vault/writer.py` | Dashboard created at wrong path when vault has `Unagi/` subfolder |
| F-16 | 🟢 | `onboarding/setup.py` | DOB stored as Jan 1 approximation — loses real birthday |
| F-17 | 🔵 | `agent/chat.py` | Pending log state not cleared on session reset |
| F-18 | 🔵 | `vault/parser.py` | `format_log_data()` doesn't handle date objects — only strings |
| F-19 | 🔵 | `config/settings.py` | No `git_root` setting — needed for independent git repo config |
| F-20 | 🔵 | All modules | Singleton reload doesn't propagate to dependent singletons |

---

## Detailed Fix Instructions

---

### F-01 🔴 — `ui/mascot.py` is a binary file

**File:** `ui/mascot.py`

**Root Cause:**
The file was either saved incorrectly, compiled accidentally, or corrupted during a Claude Code session. It shows as `[Binary file]` in the repository dump, meaning Python cannot import it. Since `ui/__init__.py` imports from `ui/mascot.py` directly, and `main.py` imports from `ui`, the entire application will crash with an `ImportError` before any code runs.

**Impact:** 🔴 Application cannot start. All imports fail.

**Fix:**
Delete the existing `ui/mascot.py` and recreate it as a clean Python file. The file must export these exact functions (as expected by `ui/__init__.py` and `ui/cli.py`):

```python
"""ASCII art mascot and startup banner for Unagi."""
from datetime import datetime
import sys
import os


def supports_ansi() -> bool:
    """Check if the terminal supports ANSI escape codes."""
    return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()


def get_ross_unagi_art() -> str:
    """Get the Unagi startup logo."""
    return r"""
  ██  ██ ███  █  █  ████  ████  ██
  ██  ██ ██ █ █  █  ██ ██ ██ ██ ██
  ██  ██ ██  ██  █  ████  ████  ██
  ██  ██ ██   █  █  ██ ██ ██ ██ ██
   ████  ██   █ ███ ████  ██  █ ██
       Total Food Awareness  🐍
"""


def get_startup_banner(user_name: str = None, last_log: str = None) -> str:
    """Get formatted startup banner."""
    today = datetime.now().strftime("%A, %d %B %Y")
    lines = []
    lines.append("━" * 60)
    lines.append(get_ross_unagi_art())
    lines.append("━" * 60)
    lines.append(f"  Today: {today}")
    if user_name:
        lines.append(f"  Welcome back, {user_name}! 👋")
    if last_log:
        lines.append(f"  {last_log}")
    lines.append("")
    lines.append("  Type your food log or ask me anything.")
    lines.append("  Commands: /help /today /week /profile /config /exit")
    lines.append("━" * 60)
    return "\n".join(lines)


def get_help_text() -> str:
    """Get help text."""
    return """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  UNAGI HELP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LOGGING FOOD — just talk naturally:
  "I had breakfast at 1 PM: 10 almonds, 200ml green tea..."
  "Log today's dinner: 450g chicken breast, 150g yogurt"
  "Update yesterday — I forgot to add 2 boiled eggs"

ASKING QUESTIONS:
  "How have I been doing this week?"
  "Am I hitting my protein goal?"
  "What should I eat to fix my Vitamin D deficit?"

COMMANDS:
  /help      This screen
  /today     Today's log summary
  /week      Last 7 days summary
  /profile   Your profile
  /config    Current configuration
  /exit      Quit

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


def get_goodbye_message() -> str:
    """Get goodbye message."""
    return """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Thanks for using UNAGI 🐍
  Stay aware. Stay healthy. Stay strong.
  Your logs are saved and committed to Git.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


def get_error_banner(error_type: str) -> str:
    """Get error banner."""
    return f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ⚠️  {error_type.upper()} ERROR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
```

**Verification:** `python3 -c "from ui.mascot import get_startup_banner; print('OK')"` should print `OK`.

---

### F-02 🔴 — Vault path validation blocks first-run onboarding

**File:** `config/settings.py`, method `_validate()`

**Root Cause:**
```python
# CURRENT (BROKEN)
if self.vault_root and not Path(self.vault_root).exists():
    errors.append(f"Vault root path does not exist: {self.vault_root}...")
```
On a first-run or new machine, `config.yaml` may have the vault path set, but the vault directory hasn't been created yet — `_ensure_vault_structure()` in `writer.py` creates it. The validation runs before onboarding, so it raises `ConfigError` and exits before the vault is ever created. The app can never bootstrap on a fresh install.

**Impact:** 🔴 First-run always fails if vault path doesn't exist yet.

**Fix:**
Change the validation from a hard error to a warning. The vault path existence check should be deferred to the moment the vault is actually accessed, not at settings load time.

```python
# FIXED
def _validate(self):
    errors = []
    
    # LLM API key is required — hard error
    if not self.llm_api_key:
        errors.append(
            "LLM_API_KEY is missing. Please add it to your .env file.\n"
            "Get your API key from: https://aistudio.google.com/app/apikey"
        )
    
    # Vault root: only warn if set AND missing — do not block startup
    # The vault directory will be created by the writer on first use
    if self.vault_root and not Path(self.vault_root).exists():
        print(f"⚠️  Warning: Vault path does not exist yet: {self.vault_root}")
        print("   It will be created automatically on first log.")
    
    if errors:
        raise ConfigError("\n\n".join(errors))
```

**Verification:** Set `vault_root` to a non-existent path in `config.yaml`, run `python3 main.py` — should show warning but continue to onboarding.

---

### F-03 🔴 — System prompt suppresses coaching notes — breaks core output

**File:** `agent/prompts.py`, `get_system_prompt()`

**Root Cause:**
The current prompt contains these conflicting instructions:
```
# CURRENT (BROKEN) — in get_system_prompt()
"Do NOT add suggestions or insights in notes - ONLY macros and micronutrients data"
"Notes format example: '●Macros: P18 C42 F25 Fiber4 ●Micros: ...'"
```

This directly contradicts the spec and the actual log format. Your existing log files contain rich coaching sections (`● INTENSITY DEFICIT:`, `● PROTEIN ANCHOR:`, `● TRENDS & EFFECTS:`, `● CORRECTIONS:`) which are the most valuable part of the output. The current prompt actively prevents the LLM from generating them.

This appears to have been written during an intermediate iteration and never corrected against the spec.

**Impact:** 🔴 The generated notes will be stripped of all coaching content — the core value of the product is missing.

**Fix:**
Replace the notes instruction block in `get_system_prompt()` entirely. The correct instructions are:

```python
# FIXED — replace the notes output rules section with:
"""
Output rules for log files:
- YAML frontmatter fields are bare integers for numbers, quoted strings for text, bare — for empty
- Food descriptions use brand names when known from the user's ingredient list
- Raw weight is always noted as (r) e.g. "450g Chicken Breast (r)"
- The file always ends with: Main View: [[Nutrition Dashboard]]

Notes field rules (CRITICAL):
- The notes field is ONE continuous quoted string — no line breaks inside it
- Use ● as the section separator between sections
- Always include these sections in this order when relevant:
  ● INSIGHTS: Key observations about today's intake and eating pattern
  ● TRENDS & EFFECTS: How today fits into the user's recent history (reference last 7 days)
  ● CORRECTIONS: Specific, actionable instructions for tomorrow based on today's gaps
  ● MICRONUTRIENT STATUS TRACKER: All 29 nutrients in exact order with ✅ ⚠️ ❌
- Write coaching notes like a knowledgeable, direct sports nutritionist
- Reference the user's specific goals, history, and known ingredients
- Be precise — use exact gram amounts and percentages, not vague language
- The MICRONUTRIENT STATUS TRACKER must always be the last section

Micronutrient status indicators:
- ✅ = Daily requirement adequately met by today's intake
- ⚠️ = Partially met or borderline (50-80% of requirement)
- ❌ = Not met / significantly deficient (<50% of requirement)
"""
```

Also update the JSON schema instruction in `get_system_prompt()` to remove the conflicting note:
```python
# REMOVE this line from the JSON schema section:
# "Do NOT add suggestions or insights in notes - ONLY macros and micronutrients data"
```

**Verification:** Run the sample input from spec Section 15 and verify the output notes contain `● INSIGHTS:`, `● TRENDS & EFFECTS:`, `● CORRECTIONS:`, and `● MICRONUTRIENT STATUS TRACKER:` sections.

---

### F-04 🔴 — Fragile JSON parsing with regex

**File:** `agent/chat.py`, `handle_log()`

**Root Cause:**
```python
# CURRENT (FRAGILE)
json_match = re.search(r'\{.*\}', response, re.DOTALL)
log_data = json.loads(json_match.group())
```
This regex matches the first `{` to the last `}` in the response. It breaks on:
- Any response that has text before or after the JSON
- JSON with escaped characters in strings (`\"`, `\\`)
- Nested objects where the outer `}` doesn't close the top-level object cleanly
- Model responses that wrap JSON in markdown code fences (` ```json ... ``` `)

When this fails, the user gets a silent "Could not parse" error with no indication of what the LLM actually returned, making debugging very difficult.

**Impact:** 🔴 Log creation fails silently on any non-clean JSON response. Unreliable in production.

**Fix — Two-part:**

**Part 1:** Use JSON mode on the LLM call for log requests (Gemini supports this):
```python
# In agent/llm.py — add response_format parameter support
def chat(
    self,
    messages,
    temperature=0.7,
    max_tokens=None,
    stream=False,
    json_mode=False       # ADD THIS
) -> str:
    kwargs = {
        "model": self.model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens:
        kwargs["max_tokens"] = max_tokens
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}  # ADD THIS
    
    response = self.client.chat.completions.create(**kwargs, stream=stream)
    # ... rest of method unchanged
```

**Part 2:** Replace the regex parser with a robust extractor and better error reporting:
```python
# In agent/chat.py — replace the JSON extraction block
def _extract_json(self, response: str) -> dict:
    """Robustly extract JSON from LLM response."""
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
                    raise ChatError(f"Malformed JSON from LLM: {e}\nRaw: {response[start:i+1][:300]}")
    
    raise ChatError(f"Could not find valid JSON in response: {response[:500]}")
```

Then in `handle_log()`:
```python
# Replace:
json_match = re.search(r'\{.*\}', response, re.DOTALL)
if not json_match:
    return False, "Could not parse food information..."
try:
    log_data = json.loads(json_match.group())
except json.JSONDecodeError:
    return False, "Could not parse food information..."

# With:
try:
    log_data = self._extract_json(response)
except ChatError as e:
    return False, str(e)
```

**Verification:** Test with a response that has text before/after the JSON, and one wrapped in ```json fences.

---

### F-05 🟡 — Intent detection misroutes conversational messages as log requests

**File:** `agent/chat.py`, `detect_intent()`

**Root Cause:**
The current keyword-based approach:
```python
log_keywords = ['log', 'ate', 'had', 'consumed', 'food', 'meal',
                'breakfast', 'lunch', 'dinner', 'snack', 'today', 'yesterday', 'update']
question_words = ['how', 'what', 'when', 'where', 'why', 'should', 'can', 'will', '?']
```
This misroutes many legitimate chat messages:
- *"I crushed it today"* → `today` in keywords, no question word → incorrectly routed to log
- *"How did yesterday go?"* → `yesterday` in keywords, `how` in question words → correctly routed to chat, but only by luck
- *"What did I have for breakfast last week?"* → `breakfast` in keywords, `what` in question words → correct
- *"Update me on my progress"* → `update` in keywords, no question word → incorrectly routed to log

The fundamental problem is that keyword matching cannot distinguish "I had chicken" (log intent) from "I had a good week" (chat intent). This is a language understanding problem, not a pattern matching problem.

**Impact:** 🟡 Users asking questions or making statements get unexpected log prompts. Frustrating UX that undermines trust in the agent.

**Fix:**
Replace keyword matching with LLM-based intent classification using a lightweight, cheap call. The prompt should be small and temperature 0 so it's fast and deterministic:

```python
def detect_intent(self, user_input: str) -> str:
    """Use LLM to classify intent as 'log' or 'chat'."""
    
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
```

**Note:** This adds one small LLM call per message. On Gemini free tier this is negligible. When the RAG pipeline and SQLite memory layer are added in Phase 2, intent classification can be enriched with history context at no extra cost.

**Verification:** Test these inputs and verify routing:
- "I had chicken for dinner" → log ✓
- "How have I been doing?" → chat ✓
- "I crushed it today" → chat ✓
- "Update yesterday: forgot eggs" → log ✓
- "What did I eat yesterday?" → chat ✓

---

### F-06 🟡 — Conversation history lost across chat/log mode switches

**File:** `agent/chat.py`, `handle_chat()` and `handle_log()`

**Root Cause:**
`handle_chat()` passes `conversation_history` to the LLM:
```python
response = self.llm.chat_with_system(
    system_prompt=system_prompt,
    user_message=user_input,
    conversation_history=self.conversation_history,  # ✓ history included
)
self.conversation_history.append(...)  # ✓ history updated
```

But `handle_log()` does NOT pass conversation history:
```python
response = self.llm.chat_with_system(
    system_prompt=full_prompt,
    user_message=user_input,
    # ✗ conversation_history not passed — agent has no memory of prior chat
)
# ✗ conversation_history not updated after logging
```

This means if a user chats about their goals, then logs a meal, the agent has no context of what was just discussed. More critically, if the agent asked a clarifying question ("did you mean raw or cooked weight?") and the user answers, then logs — the answer context is lost.

**Impact:** 🟡 Agent feels amnesiac. Multi-turn conversations around logging don't work correctly.

**Fix:**
Pass conversation history in `handle_log()` and update it after the call:

```python
def handle_log(self, user_input: str) -> Tuple[bool, str]:
    # ... existing date parsing and prompt building ...
    
    # FIXED: pass conversation history
    response = self.llm.chat_with_system(
        system_prompt=full_prompt,
        user_message=user_input,
        conversation_history=self.conversation_history,  # ADD THIS
        temperature=0.3
    )
    
    # ... existing JSON extraction ...
    
    # FIXED: update conversation history after logging
    self.conversation_history.append({"role": "user", "content": user_input})
    self.conversation_history.append({
        "role": "assistant", 
        "content": f"Logged successfully: {summary}"
    })
    
    # Trim history to last 20 messages
    if len(self.conversation_history) > 20:
        self.conversation_history = self.conversation_history[-20:]
```

**Verification:** Start a conversation: "My goal is to hit 140g protein today." Then log a meal. The logged notes should reference the protein goal context from the conversation.

---

### F-07 🟡 — Date resolution uses client-side parse only — ignores LLM understanding

**File:** `agent/chat.py`, `handle_log()`

**Root Cause:**
```python
# CURRENT
target_date = self.parse_date_reference(user_input)  # client-side regex
# ...
response = self.llm.chat_with_system(full_prompt, user_input)
log_data = self._extract_json(response)
# target_date from regex is used, NOT the date in log_data['date']
```

`parse_date_reference()` handles simple cases (today, yesterday, "last Monday") but not:
- "the day before my birthday" 
- "when I had that big workout" (requires history)
- "last week Thursday"
- Explicit dates like "May 19th"
- Dates in non-English formats

Meanwhile, the LLM understands all of these perfectly and puts the correct date in `log_data['date']`. But the code ignores `log_data['date']` and uses the client-side parsed date, which may be wrong.

**Impact:** 🟡 Logs can be written to wrong dates silently. Past log entries may be misplaced.

**Fix:**
Trust the LLM's date in the JSON response as the primary source of truth. Use client-side parsing only as a fallback and for pre-flight validation:

```python
def handle_log(self, user_input: str) -> Tuple[bool, str]:
    # Client-side parse as fallback hint only
    fallback_date = self.parse_date_reference(user_input)
    
    # ... LLM call ...
    
    log_data = self._extract_json(response)
    
    # PRIMARY: use LLM-resolved date from JSON
    llm_date_str = log_data.get('date') or log_data.get('data', {}).get('date')
    
    if llm_date_str:
        try:
            target_date = datetime.strptime(llm_date_str, "%Y-%m-%d")
        except ValueError:
            target_date = fallback_date  # fallback if LLM gives bad format
    else:
        target_date = fallback_date
    
    # Sanity check: warn if LLM date and client parse differ by more than 1 day
    if abs((target_date - fallback_date).days) > 1:
        print(f"Note: Using date {target_date.date()} (from your message context)")
```

**Verification:** Say "Log last Wednesday's dinner: 300g salmon" — verify the file is written to the correct Wednesday, not today.

---

### F-08 🟡 — Merge logic silently drops existing meal data

**File:** `vault/parser.py`, `merge_log_data()`

**Root Cause:**
```python
# CURRENT — when both existing and new meal have values:
else:
    merged[field] = new_value  # new silently overwrites existing
```

The comment in the code says *"prefer new value"* but this is wrong for additive updates. If the existing dinner is `"08:30 PM - 450g Chicken Breast"` and the user says "add 2 boiled eggs to my dinner", the LLM returns a new dinner string that includes the eggs — but only if the LLM was given the existing meal content as context.

The problem: `handle_log()` doesn't pass the existing file content to the LLM. The LLM only sees the user's new input. So the "new value" from the LLM will only contain the eggs, not the original chicken. The original chicken entry is silently dropped.

**Impact:** 🟡 Updating existing logs can silently delete previously logged meal data. This is data loss.

**Fix — Two-part:**

**Part 1:** When the target date's file already exists, read it and include the existing meal data in the LLM prompt so the model can produce a complete merged meal string:

```python
# In agent/chat.py, handle_log() — before the LLM call:
existing_log = None
if self.reader.log_exists(target_date):
    existing_log = self.reader.read_daily_log(target_date)

# Add to the system prompt if existing log found:
if existing_log:
    existing_context = f"""
EXISTING LOG FOR {target_date.strftime('%Y-%m-%d')} (already written):
Breakfast: {existing_log.get('breakfast', '—')}
Lunch: {existing_log.get('lunch', '—')}
Dinner: {existing_log.get('dinner', '—')}
Misc: {existing_log.get('misc', '—')}
Calories so far: {existing_log.get('calories', 0)}
Protein so far: {existing_log.get('protein', 0)}g

The user is ADDING TO or UPDATING this log. Preserve existing meal entries unless explicitly told to replace them. 
When updating a meal field, include BOTH the existing content and the new addition in the same field string.
Recalculate all macros to reflect the complete day.
"""
    full_prompt = system_prompt + existing_context + "\n\n" + log_instruction
```

**Part 2:** Update `merge_log_data()` to concatenate meal strings when both have values, as a safety net:

```python
# In vault/parser.py, merge_log_data():
# When both existing and new meal fields have non-empty values
else:
    # If new value looks like a complete replacement (contains time), use new
    # If new value looks like an addition (no time marker), append
    if re.match(r'\d{2}:\d{2}', new_value):
        merged[field] = new_value  # Complete new entry with time
    else:
        merged[field] = f"{existing_value}; {new_value}"  # Append addition
```

**Verification:** Log a breakfast, then say "add a banana to my breakfast." Verify both the original breakfast and the banana appear in the file.

---

### F-09 🟡 — Git push blocks main thread

**File:** `git_manager/commits.py`, `commit_file()` and `push()`

**Root Cause:**
```python
# CURRENT — synchronous, blocks CLI
if self.settings.git_auto_push and self.settings.git_remote_url:
    self.push()  # Can take 3-10 seconds on slow network
```

`git push` is a network operation that blocks the main thread. During a push, the entire CLI is frozen — no input, no output, no feedback. On a slow network or a large repo, this can take 10+ seconds, making the app feel broken.

**Impact:** 🟡 CLI freezes after every log write when auto-push is enabled.

**Fix:**
Run push in a background thread. Commit stays synchronous (it's local and fast), only push is async:

```python
# In git_manager/commits.py
import threading

def commit_file(self, file_path, action, date, summary) -> bool:
    # ... existing commit logic (synchronous — local and fast) ...
    self.repo.index.commit(commit_msg, author=author)
    
    # Push asynchronously — don't block
    if self.settings.git_auto_push and self.settings.git_remote_url:
        push_thread = threading.Thread(
            target=self._push_with_feedback,
            daemon=True  # Dies with main process if app exits
        )
        push_thread.start()
    
    return True

def _push_with_feedback(self):
    """Push to remote in background thread."""
    try:
        self.push()
        # Signal success (will be picked up by CLI status bar in future Textual UI)
        print("\r  📤 Pushed to remote ✓", end="", flush=True)
    except Exception as e:
        print(f"\r  ⚠️  Push failed: {str(e)}", end="", flush=True)
```

**Verification:** Enable `auto_push: true` with a valid remote. After logging, the CLI should return immediately and show push confirmation asynchronously.

---

### F-10 🟡 — User age not calculated from DOB — injected as "Unknown"

**File:** `agent/prompts.py`, `get_system_prompt()`

**Root Cause:**
```python
# CURRENT
base_prompt += f"Age: {user_profile.get('age', 'Unknown')} years\n"
```

The User Profile does not store `age` as a field — it stores `dob` (date of birth) as `YYYY-MM-DD`. The code looks for `age` which doesn't exist, so it always injects `"Age: Unknown years"` into the system prompt. The LLM then cannot calculate the correct protein target (which is `weight_kg * protein_target_per_kg`) and cannot give age-appropriate nutritional advice.

The Dataview charts in Obsidian correctly calculate age dynamically from `dob` — the agent should do the same.

**Impact:** 🟡 Agent cannot give age-appropriate nutritional advice. Protein targets and TDEE reasoning are wrong.

**Fix:**
Calculate age from DOB before building the prompt:

```python
# In agent/prompts.py, get_system_prompt():
if user_profile:
    # Calculate age from DOB
    dob_str = user_profile.get('dob')
    age = 'Unknown'
    if dob_str:
        try:
            dob = datetime.strptime(str(dob_str), "%Y-%m-%d")
            today = datetime.now()
            age = today.year - dob.year - (
                (today.month, today.day) < (dob.month, dob.day)
            )
        except (ValueError, AttributeError):
            age = 'Unknown'
    
    # Calculate protein target
    weight = user_profile.get('current_weight', 0)
    protein_per_kg = user_profile.get('protein_target_per_kg', 1.3)
    protein_target = round(weight * protein_per_kg) if weight else 'Unknown'
    
    base_prompt += f"Age: {age} years\n"
    base_prompt += f"Daily Protein Target: {protein_target}g "
    base_prompt += f"({protein_per_kg}g × {weight}kg)\n"
```

**Verification:** Check that the system prompt injected to the LLM contains the correct calculated age and protein target.

---

### F-11 🟢 — Missing `python-dateutil` dependency

**File:** `requirements.txt`

**Root Cause:**
`pre_flight_check.py` checks for `dateutil` as a required dependency:
```python
'python-dateutil': 'dateutil'
```
But `requirements.txt` does not include `python-dateutil`. The pre-flight check will always fail on the dependency check, and any code that imports `dateutil` will crash.

**Impact:** 🟢 Pre-flight check always reports a missing dependency. Will crash if `dateutil` is used anywhere.

**Fix:**
Add to `requirements.txt`:
```
python-dateutil>=2.8.2
```

---

### F-12 🟢 — Config key name inconsistency

**File:** `config/settings.py`, `config.yaml`, `UNAGI_DEV_SPEC.md`

**Root Cause:**
The spec (`UNAGI_DEV_SPEC.md`) defines the config key as `root` under `vault:`. The actual `config.yaml` and `settings.py` use `root_path`. While the code is internally consistent, this diverges from the spec and will cause confusion when new developers or Claude Code sessions reference the spec and write `root` instead of `root_path`.

**Impact:** 🟢 Documentation/code mismatch. Will cause confusion during future development.

**Fix:**
Choose one and be consistent. `root_path` is more explicit and less likely to conflict with Python's `Path.root` attribute. Update the spec:

In `UNAGI_DEV_SPEC.md`, Section 8, change:
```yaml
vault:
  root: /path/to/your/ObsidianVault  # OLD
```
To:
```yaml
vault:
  root_path: /path/to/your/ObsidianVault  # CORRECT
```

Also update `QUICKSTART.md` to use `root_path` consistently.

---

### F-13 🟢 — Git repo always initialized at vault root — no independent config

**File:** `git_manager/commits.py`, `config/settings.py`

**Root Cause:**
The git manager always uses `vault_root` as the git repository root. This has two problems:

1. If the user's Obsidian vault is already a git repo for other purposes (tracking all notes, not just nutrition), initializing a new git repo at `vault_root` will conflict with it.
2. The user might want to track only the `Unagi/` subfolder as a separate repo, not the entire vault.

**Impact:** 🟢 Will conflict with existing vault git repos. No flexibility in git setup.

**Fix — Two-part:**

**Part 1:** Add `git_root` to `config.yaml` and `.env.example`:
```yaml
# config.yaml
git:
  enabled: true
  branch: main
  auto_push: true
  git_root: ""  # Leave empty to use vault_root. Set to override (e.g. path to Unagi/ subfolder)
```

**Part 2:** In `settings.py`, add:
```python
git_config = config.get("git", {})
self.git_root = git_config.get("git_root", "") or self.vault_root
```

**Part 3:** In `git_manager/commits.py`, replace all `self.settings.vault_root` references with `self.settings.git_root`.

---

### F-14 🟢 — Conversation history not passed during log mode LLM call

**Note:** This is the same root cause as F-06 but specifically about the log instruction prompt. F-06 covers the fix. Listed separately for tracking purposes since it has a slightly different impact — the log instruction prompt gets appended to the system prompt but the conversation history is not passed, making the two issues distinct in the call stack even though they're fixed together.

**Fix:** Covered by F-06 fix.

---

### F-15 🟢 — Dashboard created at wrong path in some vault configurations

**File:** `vault/writer.py`, `create_dashboard_if_missing()`

**Root Cause:**
```python
# CURRENT
vault_path = self.settings.get_vault_path()  # Returns <vault_root>/Unagi/
dashboard_path = vault_path / self.settings.vault_dashboard_filename
```

`get_vault_path()` returns `<vault_root>/Unagi/` — the Unagi subfolder. So the dashboard is created at `<vault_root>/Unagi/Nutrition Dashboard.md`. But the spec says the dashboard should be at `<vault_root>/Unagi/Nutrition Dashboard.md` — which is actually correct.

However, the Dataview queries in the dashboard reference `"Nutrition/Daily Logs"` (the old path from before the `Unagi/` folder rename):
```javascript
const logs = dv.pages('"Nutrition/Daily Logs"')
```

The new path should be `"Unagi/Daily Logs"`. The dashboard template in `writer.py` uses the new path correctly, but if the user has an existing dashboard from before the `Unagi/` folder migration, the queries will return no data.

**Impact:** 🟢 Dashboard shows no data if migrating from old vault structure where logs were in `Nutrition/Daily Logs`.

**Fix:**
Update the dashboard template in `writer.py` to use the correct `Unagi/Daily Logs` path (it already does this correctly). Add a migration note to `QUICKSTART.md`:

```markdown
## Migrating from the old Nutrition/ folder structure

If you have existing logs in `Nutrition/Daily Logs/`, move them to `Unagi/Daily Logs/`
and update any Dataview queries from `"Nutrition/Daily Logs"` to `"Unagi/Daily Logs"`.
```

---

### F-16 🟢 — DOB stored as Jan 1 approximation in onboarding

**File:** `onboarding/setup.py`, `create_user_profile()`

**Root Cause:**
```python
# CURRENT
birth_year = current_year - age
dob = f"{birth_year}-01-01"  # Approximate DOB — always Jan 1
```

The onboarding flow asks for age but not date of birth. It then approximates DOB as January 1 of the birth year. This means age calculations from DOB will be off by up to 11 months. The Dataview protein chart calculates age from `dob` and the agent does the same — so if the user's birthday is December and we're in January, the calculated age will be one year too high.

**Impact:** 🟢 Age-based calculations are inaccurate by up to 11 months.

**Fix:**
Ask for date of birth directly in onboarding instead of age:

```python
# In onboarding/setup.py, run_onboarding_flow():

# REPLACE:
age_str = input("How old are you? ").strip()
age = int(age_str)

# WITH:
dob_str = input("What's your date of birth? (YYYY-MM-DD or DD/MM/YYYY) ").strip()
try:
    # Try multiple formats
    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
        try:
            dob_date = datetime.strptime(dob_str, fmt)
            dob = dob_date.strftime("%Y-%m-%d")
            break
        except ValueError:
            continue
    else:
        raise OnboardingError("Please enter your date of birth as YYYY-MM-DD")
except Exception:
    raise OnboardingError("Invalid date of birth format")
```

Remove the approximate DOB calculation from `create_user_profile()` and accept `dob` directly as a parameter.

---

### F-17 🔵 — Pending log state not cleared on conversation reset

**File:** `agent/chat.py`, `reset_conversation()`

**Root Cause:**
```python
def reset_conversation(self):
    self.conversation_history = []
    # ✗ self.pending_log is NOT cleared
```

If a user has a pending log confirmation and the conversation is reset (e.g. via a future `/reset` command or session restart), `pending_log` retains stale data. On the next `yes` confirmation, it writes stale data to the vault.

**Impact:** 🔵 Edge case — can only occur if a reset command is added. No current code path triggers this. Fix preemptively.

**Fix:**
```python
def reset_conversation(self):
    self.conversation_history = []
    self.pending_log = None  # ADD THIS
```

---

### F-18 🔵 — `format_log_data()` doesn't handle `datetime.date` objects

**File:** `vault/parser.py`, `format_log_data()`

**Root Cause:**
When frontmatter is parsed by the `python-frontmatter` library, YAML date values (e.g. `date: 2026-05-25`) are returned as `datetime.date` objects, not strings. The `validate_log_data()` function converts these via `str(data['date'])`, which works. But when the LLM returns a date in the JSON as a string like `"2026-05-25"`, and it gets passed through `merge_log_data()` and then `format_log_data()`, the date field stays as a string. The two code paths produce different types for the `date` field, which can cause subtle formatting bugs.

**Impact:** 🔵 Intermittent — depends on which code path the data travels. Can produce `date: 2026-05-25 00:00:00` in frontmatter if a `datetime` object slips through.

**Fix:**
Normalize the date field to string at the entry point of `format_log_data()`:

```python
def format_log_data(data: Dict[str, Any]) -> str:
    # Normalize date to string before anything else
    if 'date' in data:
        d = data['date']
        if hasattr(d, 'strftime'):
            data['date'] = d.strftime('%Y-%m-%d')
        else:
            data['date'] = str(d)[:10]  # Take YYYY-MM-DD portion only
    
    # ... rest of function unchanged
```

---

### F-19 🔵 — No `git_root` setting in initial config

**Note:** Covered by F-13. Listed separately as a config-layer concern.

**Fix:** Covered by F-13 fix.

---

### F-20 🔵 — Singleton reload doesn't propagate to dependent singletons

**File:** All modules using the singleton pattern.

**Root Cause:**
```python
def get_settings(reload=True) -> Settings:
    global _settings
    _settings = Settings()
    return _settings
```

If `get_settings(reload=True)` is called (e.g. after `update_vault_root()`), a new `Settings` instance is created. But `_llm_client`, `_vault_reader`, `_vault_writer`, etc. still hold references to the old `Settings` instance. So config changes don't propagate to already-initialized singletons.

**Impact:** 🔵 Affects `update_vault_root()` and any future live config update. Not triggered by normal use in v1.

**Fix:**
When reloading settings, also reload all dependent singletons:

```python
# In config/settings.py
def get_settings(reload: bool = False) -> Settings:
    global _settings
    if _settings is None or reload:
        _settings = Settings()
        if reload:
            # Reload all dependent singletons
            _reload_all_singletons()
    return _settings

def _reload_all_singletons():
    """Reload all module singletons after settings change."""
    try:
        from vault.reader import get_vault_reader
        from vault.writer import get_vault_writer
        from agent.llm import get_llm_client
        from agent.context import get_context_loader
        from agent.chat import get_chat_agent
        from git_manager.commits import get_git_manager
        
        get_vault_reader(reload=True)
        get_vault_writer(reload=True)
        get_llm_client(reload=True)
        get_context_loader(reload=True)
        get_chat_agent(reload=True)
        get_git_manager(reload=True)
    except ImportError:
        pass  # Module not yet initialized
```

---

## Implementation Order

Fix these in strict order. Each group should be tested before moving to the next.

**Group 1 — Get it running (do these first, in order):**
1. F-01 — Recreate `mascot.py`
2. F-02 — Fix vault path validation
3. F-11 — Add `python-dateutil` to requirements

**Group 2 — Fix core output quality:**

4. F-03 — Fix system prompt notes suppression
5. F-10 — Fix age calculation from DOB
6. F-16 — Fix DOB collection in onboarding

**Group 3 — Fix reliability:**

7. F-04 — Replace regex JSON parser
8. F-18 — Fix date type normalization
9. F-08 — Fix merge logic data loss

**Group 4 — Fix conversation quality:**

10. F-05 — Replace keyword intent detection with LLM classification
11. F-06 — Pass conversation history in log mode
12. F-07 — Trust LLM date resolution

**Group 5 — Fix infrastructure:**

13. F-09 — Make git push async
14. F-13 — Add `git_root` config
15. F-19 — (Covered by F-13)

**Group 6 — Polish and consistency:**

16. F-12 — Config key consistency
17. F-14 — (Covered by F-06)
18. F-15 — Dashboard path migration note
19. F-17 — Clear pending log on reset
20. F-20 — Singleton propagation

---

## Testing After Fixes

Run through this sequence to verify all fixes:

```
1. Fresh install — run pre_flight_check.py → all checks pass
2. First run — onboarding completes, User Profile.md created with real DOB
3. Log sample input from spec Section 15
4. Verify output .md file matches expected format exactly
5. Verify notes contain ● INSIGHTS, ● TRENDS, ● CORRECTIONS, ● MICRONUTRIENT TRACKER
6. Check micronutrient order matches spec exactly
7. Log a second meal to same day → verify merge preserves first meal
8. Say "Add 2 boiled eggs to my dinner" → verify eggs added, original preserved
9. Ask "How did I do today?" → verify routed to chat, not log
10. Check git log → verify commit message format matches spec
11. Verify git push happens asynchronously (CLI returns immediately)
```

---

## Files Modified by This Spec

| File | Issues Fixed |
|---|---|
| `ui/mascot.py` | F-01 (recreate) |
| `config/settings.py` | F-02, F-19, F-20 |
| `config.yaml` | F-12, F-13 |
| `agent/prompts.py` | F-03, F-10 |
| `agent/chat.py` | F-04, F-05, F-06, F-07, F-08 (partial), F-17 |
| `agent/llm.py` | F-04 (JSON mode) |
| `vault/parser.py` | F-08, F-18 |
| `git_manager/commits.py` | F-09, F-13 |
| `onboarding/setup.py` | F-16 |
| `requirements.txt` | F-11 |
| `UNAGI_DEV_SPEC.md` | F-12 |
| `QUICKSTART.md` | F-12, F-15 |

---

*Unagi v1 Fix Spec — Built with 🐍 total food awareness.*
