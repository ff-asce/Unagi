# 🐍 UNAGI — UI Specification
### `specs/v1/UI_SPEC_v1.md`
**Version:** 1.0
**Status:** Ready for implementation
**Last Updated:** 2026-05-26
**Applies To:** Codebase after `FIX_SPEC_v1.md` and `ARCH_SPEC_v1.md` are implemented
**Companion Specs:** `FIX_SPEC_v1.md`, `ARCH_SPEC_v1.md`

---

## Overview

This spec defines the terminal UI for Unagi using **Textual** — the same framework that powers Claude Code's interface. The goal is a CLI that feels like a real application: fixed layout, live updates, keyboard-driven, and visually distinctive — not a scrolling print statement.

The v1 CLI built with `rich` + `prompt_toolkit` is kept as a fallback (`--simple` flag) for environments where Textual doesn't render correctly. The Textual UI is the default and the primary design target.

---

## Why Textual

The current `rich` + `prompt_toolkit` approach gives a chat-like scrolling terminal. It works but has hard limits:

- No fixed layout — the header and status bar scroll away
- No real-time updates during LLM calls — the terminal just freezes
- No panels that update independently (e.g. today's stats updating after a log)
- No keyboard shortcuts beyond what `prompt_toolkit` natively supports
- No path to the future web UI — Textual and web share a mental model; `rich` does not

Textual solves all of these. It renders a proper app layout in the terminal using the same event-driven, component-based model that will be used for the web UI. The CLI and the web UI are the same app with different renderers.

---

## Design Direction

**Aesthetic:** Dark terminal, dense information, surgical precision. Think Bloomberg terminal meets a nutrition tracker. Not cute, not minimal — *purposeful and data-rich*.

**Tone:** The interface communicates that Unagi knows what it's doing. Every pixel has a reason. The mascot provides personality; the data panels provide authority.

**Reference:** Claude Code's interface — fixed header, scrollable content area, persistent input bar, real-time status updates. That's the baseline. Unagi adds nutrition-specific panels and a mascot.

**Color palette:**
```
Background:     #0d1117   (deep GitHub dark)
Surface:        #161b22   (card/panel background)
Border:         #30363d   (subtle borders)
Text primary:   #e6edf3   (near white)
Text muted:     #7d8590   (secondary info)
Accent green:   #3fb950   (success, macros met, positive deficit)
Accent yellow:  #d29922   (warning, borderline)
Accent red:     #f85149   (error, surplus, missed targets)
Accent blue:    #58a6ff   (interactive elements, links)
Accent purple:  #bc8cff   (Unagi brand, mascot accent)
```

**Typography:**
Textual uses the terminal's monospace font — we can't change this. But we can use Unicode box-drawing characters, block elements, and carefully chosen spacing to create a refined, structured layout that doesn't feel like `print()` output.

---

## Layout Specification

```
┌─────────────────────────────────────────────────────────────┐
│  HEADER BAR (fixed, 3 lines)                                │
│  🐍 UNAGI  ·  Total Food Awareness  ·  Wednesday 27 May     │
│  [model: gemini-2.0-flash]  [vault: ✓]  [git: ✓ synced]    │
└─────────────────────────────────────────────────────────────┘
│                                                             │
│  STATS BAR (fixed, 2 lines, updates after each log)        │
│  Today: 1025 kcal  ·  P: 140g ✅  ·  Deficit: -975  ✅    │
│  Protein 140/130g  ████████████░  7-day avg deficit: -820  │
│                                                             │
├───────────────────────────────────┬─────────────────────────┤
│                                   │                         │
│  CHAT PANEL                       │  TODAY PANEL            │
│  (scrollable, ~70% width)         │  (fixed, ~30% width)    │
│                                   │                         │
│  Unagi: Hey Parth! Last log was   │  📅 27 May 2026         │
│  yesterday. You hit 140g protein  │  ─────────────────────  │
│  and a -975 deficit. Strong day.  │  Calories    1025 kcal  │
│                                   │  Protein     140g  ✅   │
│  You > I had 450g chicken...      │  Carbs        37g       │
│                                   │  Fats         32g       │
│  Unagi: ✅ Logged 27 May          │  Fiber        17g       │
│  ┌────────────────────────────┐   │  Deficit     -975  ✅   │
│  │ Cal: 1025 · P: 140g        │   │  ─────────────────────  │
│  │ Deficit: -975 · Fiber: 17g │   │  Breakfast   01:00 PM  │
│  └────────────────────────────┘   │  Lunch       —         │
│                                   │  Dinner      08:30 PM  │
│                                   │  ─────────────────────  │
│                                   │  7-day avg             │
│                                   │  Cal:   1180/day       │
│                                   │  P:     128g/day       │
│                                   │  Def:   -820/day       │
│                                   │                         │
├───────────────────────────────────┴─────────────────────────┤
│  INPUT BAR (fixed, 3 lines)                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ You >                                               │    │
│  └─────────────────────────────────────────────────────┘    │
│  [/help] [/today] [/week] [/profile] [/config] [Tab: cmds]  │
└─────────────────────────────────────────────────────────────┘
│  STATUS BAR (fixed, 1 line)                                  │
│  ● Calculating nutrition...          Ctrl+C to exit          │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### 1. Header Bar

**Widget:** `Header` (custom, extends `Static`)
**Height:** 3 lines (fixed)

Displays:
- Left: `🐍 UNAGI · Total Food Awareness`
- Centre: Current date and day name
- Right: System status indicators

Status indicators:
```
[model: gemini-2.0-flash]    ← from config, green if connected
[vault: ✓]                   ← green if vault path valid, red if not
[git: ✓ synced]              ← green if up to date, yellow if local-only
```

The header never scrolls. It is always visible.

---

### 2. Stats Bar

**Widget:** `StatsBar` (custom, extends `Static`)
**Height:** 2 lines (fixed)
**Updates:** After every successful log write (via EventBus)

Line 1: Today's key metrics in a compact inline format
```
Today: 1025 kcal  ·  Protein: 140g ✅  ·  Deficit: -975 ✅  ·  Fiber: 17g ✅
```

Line 2: Protein progress bar + 7-day rolling average
```
Protein 140/130g  ████████████░░  107%   ·   7-day avg deficit: -820 kcal
```

Progress bar logic:
- Green filled blocks (`█`) for the achieved amount up to goal
- Empty blocks (`░`) for remaining
- Percentage shown after bar
- Bar turns yellow at 80-99% of goal, green at ≥100%, red if protein target missed by >20%

If no log today, shows:
```
No log today yet.  ·  Yesterday: 1251 kcal · P: 118g · Deficit: -749
```

---

### 3. Chat Panel

**Widget:** `ChatPanel` (custom, extends `ScrollableContainer`)
**Width:** 70% (flexible)
**Height:** Fills remaining space between stats bar and input bar

Renders the conversation history. Each message is styled differently:

**User messages:**
```
  You › I had 450g chicken breast and yogurt for dinner
```
Right-aligned label, muted purple for `You ›`, white text, slight indent.

**Agent text responses:**
```
  🐍 › You've been consistently hitting your protein target this week.
        Yesterday was strong — 140g with a -975 deficit. Keep that
        pattern tonight.
```
Left-aligned, purple `🐍 ›` label, white text, word-wrapped.

**Agent log confirmations (success panel):**
```
  🐍 › ✅ Logged 27 May 2026
       ┌──────────────────────────────────────────┐
       │  Calories  1025 kcal   Deficit  -975      │
       │  Protein   140g   ✅   Carbs    37g        │
       │  Fats      32g        Fiber    17g        │
       └──────────────────────────────────────────┘
       Breakfast + Dinner logged. Git committed.
```
Success panel uses green border. The macro summary is a compact table, not a wall of text.

**Agent notes display (after log confirmation):**
After the success panel, the notes content is rendered in a collapsible section. Collapsed by default, expanded with `n` key or click:
```
  🐍 › [n] Show today's notes ▶
```
Expanded:
```
  🐍 › ▼ Today's Notes
       ● INSIGHTS: Pushed a massive -975 kcal deficit...
       ● TRENDS & EFFECTS: Total protein landed at 140g...
       ● CORRECTIONS: Tomorrow's architecture must distribute...
       ● MICRONUTRIENT STATUS TRACKER:
         Vitamin A ✅  Vitamin C ⚠️  Vitamin D ❌  Vitamin E ✅
         Vitamin K ❌  B1 ✅  B2 ✅  B3 ✅  B5 ✅  B6 ✅
         B7 ✅  B9 ❌  B12 ✅  Choline ✅  Calcium ✅
         [... remaining nutrients ...]
```

Micronutrient display is in a 4-column grid, not a long semicolon-separated string, for readability.

**Pipeline status messages (during LLM call):**
These appear in the chat panel during processing, then are replaced by the actual response:
```
  🐍 › ⠋ Calculating nutrition...
```
Spinner animation using Textual's built-in `LoadingIndicator`.

---

### 4. Today Panel

**Widget:** `TodayPanel` (custom, extends `Static`)
**Width:** 30% (fixed)
**Height:** Fills remaining space
**Updates:** After every log write (via EventBus)

Shows a structured summary of today's log. If no log today, shows the previous day's summary with a "No log today yet" header.

Layout:
```
📅 Wednesday 27 May
──────────────────
Calories    1025
Maintenance 2000
Deficit     -975  ✅

──────────────────
Protein    140g  ✅
Carbs       37g
Fats        32g
Fiber       17g

──────────────────
Breakfast  01:00 PM
Lunch      —
Dinner     08:30 PM
Misc       —

──────────────────
7-DAY AVERAGES
Calories   1180/day
Protein    128g/day
Deficit    -820/day
Days logged  6/7
```

Color coding:
- Deficit: green if ≤ -20% maintenance, yellow if -10% to -20%, red if positive (surplus)
- Protein: green if ≥ target, yellow if 80-99%, red if <80%
- Meal fields: muted if `—`, white if logged

The panel title updates with the date and a subtle indicator of how the day is going:
- `📅 Today · On Track ✅` — if deficit target is being met
- `📅 Today · Needs Dinner ⚠️` — if calories are low and it's past 6pm
- `📅 Today · Surplus ❌` — if currently in caloric surplus

---

### 5. Input Bar

**Widget:** `Input` (Textual built-in, styled)
**Height:** 3 lines (fixed, at bottom)

The input bar is always focused. The user types directly into it.

Features:
- Multi-line input support (Shift+Enter for newline, Enter to submit)
- Command history (Up/Down arrows navigate history)
- Tab completion for special commands (`/h` → `/help`)
- Placeholder text: `Tell me what you ate, or ask me anything...`

Below the input box, a single line of keyboard shortcut hints:
```
[/help] [/today] [/week] [/profile] [/config] [↑↓ history] [Shift+Enter newline]
```
These are styled as muted pills, not interactive buttons.

---

### 6. Status Bar

**Widget:** `StatusBar` (custom, extends `Static`)
**Height:** 1 line (fixed, at very bottom)
**Updates:** Driven by EventBus pipeline events

Left: Current pipeline status message
Right: Keyboard hint

```
● Calculating nutrition...                              Ctrl+C to exit
```

Status messages come from `EVENT_MESSAGES` in `agent/events.py`:
```python
EVENT_MESSAGES = {
    "classifying":           "Understanding your message...",
    "resolving_date":        "Figuring out the date...",
    "loading_context":       "Loading your history...",
    "calculating_nutrition": "Calculating nutrition...",
    "writing_file":          "Writing to vault...",
    "committing":            "Committing to Git...",
    "pushing":               "Pushing to remote...",
    "done":                  "",   # Clear status bar when done
    "error":                 "Something went wrong",
}
```

The `●` indicator is animated (cycles through `◐◓◑◒`) during active processing. When idle it disappears.

---

### 7. Mascot — Startup Screen

**Triggered:** On app launch, before the main layout renders. Displays for 2-3 seconds then transitions to the main layout.

The startup screen is a full-terminal takeover — not part of the main layout. It plays once, then dismisses.

```
                         ___
                   ___  /   \  ___
                  /   \/     \/   \
                 (  ·  )  🐍  (  ·  )
                  \___/       \___/

         ██╗   ██╗███╗  ██╗ █████╗  ██████╗ ██╗
         ██║   ██║████╗ ██║██╔══██╗██╔════╝ ██║
         ██║   ██║██╔██╗██║███████║██║  ███╗██║
         ██║   ██║██║╚████║██╔══██║██║   ██║██║
         ╚██████╔╝██║ ╚███║██║  ██║╚██████╔╝██║
          ╚═════╝ ╚═╝  ╚══╝╚═╝  ╚═╝ ╚═════╝ ╚═╝

              T O T A L   F O O D   A W A R E N E S S

         ─────────────────────────────────────────────
         Welcome back, Parth  ·  Wednesday 27 May 2026
         Last log: Yesterday  ·  1251 kcal  ·  -749 deficit
         ─────────────────────────────────────────────

                      Loading your vault...
```

The `Loading your vault...` line animates through the pipeline events as context loads.

**Transition:** The startup screen fades out (terminal clear) and the main layout fades in over 300ms using Textual's animation support.

**First-run variant:** If no user profile exists, the startup screen is replaced by the onboarding screen (separate spec in the onboarding section below).

---

### 8. Onboarding Screen

**Triggered:** When `User Profile.md` does not exist (first run).

Replaces the startup screen entirely. Uses the same full-terminal layout.

```
         ██╗   ██╗███╗  ██╗ █████╗  ██████╗ ██╗
         ...

              T O T A L   F O O D   A W A R E N E S S

         ─────────────────────────────────────────────
              Hey! I'm Unagi, your nutrition agent.
           Looks like this is your first time here.
            Let me ask a few quick questions first.
         ─────────────────────────────────────────────

         What's your name?
         ›  _
```

Each question appears one at a time as the previous is answered. The interface feels conversational, not form-like.

Questions are rendered as:
```
         What's your name?
         ›  Parth

         How old are you? (or enter your date of birth as YYYY-MM-DD)
         ›  _
```

After all questions are answered:
```
         ─────────────────────────────────────────────
         ✅ Profile created. Here's what I've got:

            Name          Parth
            Weight        105 kg
            Height        180 cm
            Goal          Cut
            Maintenance   2000 kcal/day (estimated)
            Protein goal  136g/day (1.3g × 105kg)

         Looks right? Press Enter to continue or 'e' to edit.
         ─────────────────────────────────────────────
```

---

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `Enter` | Submit message |
| `Shift+Enter` | New line in input |
| `↑` / `↓` | Navigate message history |
| `Tab` | Autocomplete command |
| `n` | Toggle notes panel on last log response |
| `Ctrl+T` | Show today's summary |
| `Ctrl+W` | Show weekly summary |
| `Ctrl+P` | Show profile |
| `Ctrl+C` | Exit |
| `Esc` | Clear input / dismiss modal |
| `F1` | Show help |

---

## Special Commands

Commands are entered in the input bar with a `/` prefix:

| Command | Action |
|---|---|
| `/help` | Show help modal |
| `/today` | Show today's log in chat panel |
| `/week` | Show 7-day summary in chat panel |
| `/profile` | Show user profile in chat panel |
| `/config` | Show current config (keys masked) |
| `/clear` | Clear chat history (not vault files) |
| `/reset` | Reset conversation context |
| `/exit` | Quit |

---

## Responsive Behaviour

Textual handles terminal resize automatically. Define minimum sizes:

- **Minimum width:** 100 columns — below this, hide the Today Panel and show only the Chat Panel at full width
- **Minimum height:** 30 rows — below this, show a "Terminal too small" message
- **Narrow mode** (< 100 cols): Single column layout, Today Panel hidden, accessible via `/today` command

---

## Implementation Specification

### File Structure

```
ui/
├── __init__.py              ← updated exports
├── app.py                   ← NEW: Textual App class (main entry point)
├── screens/
│   ├── __init__.py
│   ├── startup.py           ← NEW: Startup/splash screen
│   ├── onboarding.py        ← NEW: First-run onboarding screen
│   └── main.py              ← NEW: Main app screen
├── widgets/
│   ├── __init__.py
│   ├── header.py            ← NEW: Header bar widget
│   ├── stats_bar.py         ← NEW: Stats bar widget
│   ├── chat_panel.py        ← NEW: Chat panel widget
│   ├── today_panel.py       ← NEW: Today summary panel
│   ├── input_bar.py         ← NEW: Input bar widget
│   └── status_bar.py        ← NEW: Status bar widget
├── cli.py                   ← KEPT: Simple fallback (--simple flag)
└── mascot.py                ← KEPT: Text art functions (used by startup screen)
```

### `app.py` — Textual App Root

```python
"""Unagi Textual application."""
from textual.app import App, ComposeResult
from textual.binding import Binding
from ui.screens.startup import StartupScreen
from ui.screens.main import MainScreen
from ui.screens.onboarding import OnboardingScreen
from agent.container import Container
from agent.events import PipelineEvent


class UnagiApp(App):
    """The Unagi terminal application."""
    
    CSS_PATH = "styles/app.tcss"  # Textual CSS file
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Exit", priority=True),
        Binding("ctrl+t", "today", "Today"),
        Binding("ctrl+w", "week", "Week"),
        Binding("ctrl+p", "profile", "Profile"),
        Binding("f1", "help", "Help"),
    ]
    
    def __init__(self, container: Container):
        super().__init__()
        self.container = container
        
        # Subscribe to pipeline events for status bar updates
        self.container.event_bus.subscribe(self._on_pipeline_event)
    
    def on_mount(self) -> None:
        """Show startup screen on launch."""
        from onboarding import needs_onboarding
        if needs_onboarding(self.container.settings):
            self.push_screen(OnboardingScreen(self.container))
        else:
            self.push_screen(StartupScreen(self.container))
    
    def _on_pipeline_event(self, event) -> None:
        """Forward pipeline events to the main screen's status bar."""
        try:
            main_screen = self.get_screen("main")
            main_screen.update_status(event.name, event.data)
        except Exception:
            pass
    
    def action_today(self) -> None:
        self._send_command("/today")
    
    def action_week(self) -> None:
        self._send_command("/week")
    
    def action_profile(self) -> None:
        self._send_command("/profile")
    
    def _send_command(self, command: str) -> None:
        try:
            main_screen = self.get_screen("main")
            main_screen.handle_command(command)
        except Exception:
            pass


def run_app(container: Container) -> None:
    """Launch the Textual UI."""
    app = UnagiApp(container)
    app.run()
```

### `screens/main.py` — Main Screen Layout

```python
"""Main application screen."""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Input
from textual.containers import Horizontal, Vertical

from ui.widgets.header import UnagiHeader
from ui.widgets.stats_bar import StatsBar
from ui.widgets.chat_panel import ChatPanel
from ui.widgets.today_panel import TodayPanel
from ui.widgets.status_bar import StatusBar
from agent.events import EVENT_MESSAGES


class MainScreen(Screen):
    """The main chat interface."""
    
    def compose(self) -> ComposeResult:
        yield UnagiHeader(id="header")
        yield StatsBar(id="stats")
        with Horizontal(id="main-body"):
            yield ChatPanel(id="chat", classes="main-panel")
            yield TodayPanel(id="today", classes="side-panel")
        yield Input(
            placeholder="Tell me what you ate, or ask me anything...",
            id="chat-input"
        )
        yield StatusBar(id="status")
    
    def on_mount(self) -> None:
        self.query_one("#chat-input", Input).focus()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user message submission."""
        text = event.value.strip()
        if not text:
            return
        
        event.input.value = ""  # Clear input
        
        # Check for special commands
        if text.startswith('/'):
            self.handle_command(text)
            return
        
        # Send to orchestrator
        chat = self.query_one("#chat", ChatPanel)
        chat.add_user_message(text)
        
        # Process in background worker to avoid blocking UI
        self.run_worker(
            self._process_message(text),
            exclusive=True,
            name="message-worker"
        )
    
    async def _process_message(self, text: str) -> None:
        """Process message in background worker."""
        orchestrator = self.app.container.orchestrator
        chat = self.query_one("#chat", ChatPanel)
        today = self.query_one("#today", TodayPanel)
        stats = self.query_one("#stats", StatsBar)
        
        # Show thinking indicator
        thinking_id = chat.add_thinking_indicator()
        
        try:
            response = orchestrator.process(text)
        except Exception as e:
            response = f"Something went wrong: {str(e)}"
        finally:
            chat.remove_thinking_indicator(thinking_id)
        
        chat.add_agent_message(response)
        
        # Refresh data panels after any log write
        today.refresh_data()
        stats.refresh_data()
    
    def handle_command(self, command: str) -> None:
        """Handle /commands."""
        chat = self.query_one("#chat", ChatPanel)
        ctx = self.app.container.context_manager
        
        cmd = command.lower().strip()
        if cmd == "/today":
            summary = ctx.get_today_summary()
            chat.add_today_summary(summary)
        elif cmd == "/week":
            summary = ctx.get_weekly_summary()
            chat.add_week_summary(summary)
        elif cmd == "/profile":
            profile = ctx._profile_cache or ctx.load_user_profile()
            chat.add_profile_display(profile)
        elif cmd == "/config":
            chat.add_config_display(self.app.container.settings)
        elif cmd == "/clear":
            chat.clear()
        elif cmd == "/reset":
            self.app.container.orchestrator.reset()
            chat.add_system_message("Conversation reset.")
        elif cmd in ["/exit", "/quit"]:
            self.app.exit()
        elif cmd == "/help":
            chat.add_help_text()
        else:
            chat.add_system_message(f"Unknown command: {command}")
    
    def update_status(self, event_name: str, data: dict) -> None:
        """Update status bar from pipeline event."""
        status = self.query_one("#status", StatusBar)
        message = EVENT_MESSAGES.get(event_name, "")
        status.set_message(message)
```

### Textual CSS — `styles/app.tcss`

```css
/* Unagi Terminal Styles */

Screen {
    background: #0d1117;
}

#header {
    height: 3;
    background: #161b22;
    border-bottom: solid #30363d;
    color: #e6edf3;
}

#stats {
    height: 2;
    background: #0d1117;
    border-bottom: solid #30363d;
    padding: 0 2;
    color: #7d8590;
}

#main-body {
    height: 1fr;
}

#chat {
    width: 2fr;
    border-right: solid #30363d;
    padding: 1 2;
}

#today {
    width: 1fr;
    padding: 1 2;
    color: #e6edf3;
}

#chat-input {
    height: 3;
    border-top: solid #30363d;
    border: solid #30363d;
    background: #161b22;
    color: #e6edf3;
    padding: 0 2;
}

#chat-input:focus {
    border: solid #58a6ff;
}

#status {
    height: 1;
    background: #161b22;
    border-top: solid #30363d;
    color: #7d8590;
    padding: 0 2;
}

/* Message styles */
.user-message {
    color: #e6edf3;
    margin: 1 0;
}

.agent-message {
    color: #e6edf3;
    margin: 1 0;
}

.agent-label {
    color: #bc8cff;
    text-style: bold;
}

.success-panel {
    border: solid #3fb950;
    background: #0d1f0d;
    padding: 1 2;
    margin: 1 0;
    color: #e6edf3;
}

.warning-panel {
    border: solid #d29922;
    background: #1f1a0d;
    padding: 1 2;
    margin: 1 0;
}

.error-panel {
    border: solid #f85149;
    background: #1f0d0d;
    padding: 1 2;
    margin: 1 0;
}

.metric-good {
    color: #3fb950;
}

.metric-warning {
    color: #d29922;
}

.metric-bad {
    color: #f85149;
}

.muted {
    color: #7d8590;
}

.section-divider {
    color: #30363d;
}
```

### Updated `requirements.txt`

Add Textual:
```
textual>=0.52.0
```

The existing `rich` and `prompt_toolkit` dependencies are kept for the `--simple` fallback mode.

---

## Entry Point Changes

Update `main.py` to support both UI modes:

```python
import argparse

def main():
    parser = argparse.ArgumentParser(description='Unagi — Total Food Awareness')
    parser.add_argument(
        '--simple', 
        action='store_true',
        help='Use simple CLI mode (fallback for unsupported terminals)'
    )
    args = parser.parse_args()
    
    # ... config loading, onboarding check, container creation ...
    
    if args.simple:
        from ui.cli import run_cli
        run_cli(container)          # existing rich + prompt_toolkit
    else:
        from ui.app import run_app
        run_app(container)          # new Textual UI (default)
```

---

## Mascot Implementation

The mascot is a pure text art block rendered in the startup screen. No animation library needed — Textual handles the screen transition.

The large UNAGI ASCII lettering uses Unicode block characters for a clean terminal-native look:

```python
# ui/mascot.py — add to existing file

UNAGI_LOGO = r"""
 ██╗   ██╗███╗  ██╗ █████╗  ██████╗ ██╗
 ██║   ██║████╗ ██║██╔══██╗██╔════╝ ██║
 ██║   ██║██╔██╗██║███████║██║  ███╗██║
 ██║   ██║██║╚████║██╔══██║██║   ██║██║
 ╚██████╔╝██║ ╚███║██║  ██║╚██████╔╝██║
  ╚═════╝ ╚═╝  ╚══╝╚═╝  ╚═╝ ╚═════╝ ╚═╝
"""

EEL_ART = r"""
       /\_____/\
      /  ~   ~  \
     ( ^_^ )  🐍
      \  ~~~  /
       \_____/
    ~≋~≋~≋~≋~≋~≋~
"""

def get_startup_art(user_name: str = None, last_log: str = None) -> str:
    """Full startup screen content for Textual startup screen."""
    from datetime import datetime
    today = datetime.now().strftime("%A, %d %B %Y")
    
    lines = [
        "",
        EEL_ART,
        UNAGI_LOGO,
        "         T O T A L   F O O D   A W A R E N E S S",
        "",
        "  " + "─" * 50,
    ]
    if user_name:
        lines.append(f"  Welcome back, {user_name}  ·  {today}")
    else:
        lines.append(f"  {today}")
    if last_log:
        lines.append(f"  {last_log}")
    lines.append("  " + "─" * 50)
    lines.append("")
    lines.append("  Loading your vault...")
    
    return "\n".join(lines)
```

---

## Implementation Order

**Step 1 — Add Textual to requirements, verify it installs:**
```bash
pip install textual>=0.52.0
python3 -c "import textual; print(textual.__version__)"
```

**Step 2 — Create the file structure (empty files):**
Create all files in `ui/screens/` and `ui/widgets/` as empty modules. Verify imports work.

**Step 3 — Build `MainScreen` layout (static, no logic):**
Wire all widgets into `MainScreen`. Hard-code placeholder data. Verify the layout renders correctly at different terminal sizes.

**Step 4 — Wire `ChatPanel` (messages only):**
Implement message rendering in `ChatPanel`. Hard-code a few sample messages. Verify styling matches spec.

**Step 5 — Wire input and orchestrator:**
Connect `Input.Submitted` → `orchestrator.process()` → `ChatPanel.add_agent_message()`. Verify end-to-end: type a message, get a response.

**Step 6 — Wire `TodayPanel` and `StatsBar`:**
Connect to `ContextManager`. Verify they update after a log write (via cache invalidation).

**Step 7 — Wire `StatusBar` to `EventBus`:**
Subscribe to pipeline events. Verify status messages appear and clear correctly.

**Step 8 — Build `StartupScreen`:**
Full-terminal startup screen with mascot art and loading sequence. Verify transition to `MainScreen`.

**Step 9 — Build `OnboardingScreen`:**
Conversational onboarding flow. Verify it writes `User Profile.md` and transitions to `MainScreen`.

**Step 10 — Test responsive behaviour:**
Resize terminal to various widths. Verify narrow mode hides `TodayPanel` correctly.

**Step 11 — Add `--simple` flag to `main.py`:**
Verify both UI modes work end-to-end.

---

## Testing Checklist

- [ ] App launches with startup screen
- [ ] Startup screen transitions to main screen
- [ ] First-run shows onboarding screen, not startup screen
- [ ] Onboarding creates valid `User Profile.md`
- [ ] Layout renders correctly at 120+ column width
- [ ] Layout switches to narrow mode below 100 columns
- [ ] User message appears immediately on Enter
- [ ] Thinking indicator shows during LLM call
- [ ] Success panel shows after log write
- [ ] `TodayPanel` updates after log write
- [ ] `StatsBar` updates after log write
- [ ] Status bar shows pipeline events during processing
- [ ] Status bar clears when pipeline completes
- [ ] All `/commands` work correctly
- [ ] Keyboard shortcuts (`Ctrl+T`, `Ctrl+W`, etc.) work
- [ ] Notes section collapses/expands with `n` key
- [ ] `--simple` flag launches the old rich CLI
- [ ] `Ctrl+C` exits cleanly from both UI modes

---

*Unagi UI Spec v1 — Built with 🐍 total food awareness.*
