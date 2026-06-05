# UNAGI Modern UI Plan
**Branch:** `feature/modern-ui`
**Goal:** Transform UNAGI from basic CLI to modern animated terminal UI with 8-bit retro pixel art aesthetic

**Design Philosophy:** 8-bit retro videogame/pixel art style inspired by classic games
**Color Scheme:** Claude orange (#FF6B35) and Obsidian purple (#7C3AED)
**Focus:** Terminal UI first, web UI later

---

## 1. Framework Analysis & Recommendation

### Option A: **Textual** ⭐ RECOMMENDED
**Why Textual is perfect for UNAGI:**
- **React-like component model** - Similar to Ink (what Claude uses)
- **CSS-like styling** - Modern, declarative UI design
- **Built-in animations** - Smooth transitions, loading spinners, animated widgets
- **Rich integration** - Works seamlessly with our existing Rich library
- **Async/await support** - Non-blocking UI updates while LLM processes
- **Mouse support** - Click buttons, scroll panels, interactive elements
- **Web-ready** - Can export to web with `textual-web` (future-proof)
- **Active development** - Created by Will McGugan (Rich author), well-maintained

**Example capabilities:**
```python
# Animated swimming eel mascot
class EelWidget(Widget):
    def on_mount(self):
        self.set_interval(0.1, self.animate_swim)
    
    def animate_swim(self):
        # Update eel position/frame
        self.refresh()

# Live-updating stats dashboard
class StatsPanel(Static):
    def update_macros(self, data):
        # Real-time macro tracking
        self.update(render_macros(data))
```

### Option B: Asciimatics
- **Pros:** Already installed, good for animations
- **Cons:** More for games/demos, not modern UIs, no component model
- **Verdict:** Not suitable for production app

### Option C: Urwid
- **Pros:** Mature, stable
- **Cons:** Older API, less modern than Textual, no animations
- **Verdict:** Outdated compared to Textual

### Option D: Blessed
- **Pros:** Simple, lightweight
- **Cons:** Low-level, no component model, manual positioning
- **Verdict:** Too basic for our needs

---

## 2. Proposed UI Architecture

### Current Architecture (v1)
```
main.py
  └─> ui/cli.py (Rich-based)
       ├─> ui/mascot.py (static ASCII art)
       ├─> agent/chat.py (conversation loop)
       └─> prompt_toolkit (input handling)
```

### New Architecture (v2 - Textual)
```
main.py
  └─> ui/textual_app.py (Textual App)
       ├─> ui/components/
       │    ├─> eel_mascot.py (animated widget)
       │    ├─> chat_panel.py (conversation display)
       │    ├─> stats_dashboard.py (live macro/micro tracking)
       │    ├─> input_bar.py (message input)
       │    └─> command_palette.py (special commands)
       ├─> ui/screens/
       │    ├─> main_screen.py (split layout)
       │    ├─> onboarding_screen.py (first-run setup)
       │    └─> help_screen.py (interactive help)
       └─> agent/chat.py (async conversation loop)
```

---

## 3. UI Layout Design

### Main Screen Layout
```
┌─────────────────────────────────────────────────────────────┐
│  UNAGI - Total Food Awareness                    [?] [⚙️] [X] │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────┐  ┌──────────────────────────────┐ │
│  │                      │  │  📊 TODAY'S STATS             │ │
│  │   🐍 [Animated Eel]  │  │  ─────────────────────────    │ │
│  │      Swimming...     │  │  Calories: 1,847 / 2,200     │ │
│  │                      │  │  Protein:  145g / 165g  ✅   │ │
│  │  💬 CHAT             │  │  Carbs:    180g / 220g  ⚠️   │ │
│  │  ─────────────       │  │  Fat:      65g / 73g    ✅   │ │
│  │                      │  │                               │ │
│  │  You: I had break... │  │  🔬 MICRONUTRIENTS           │ │
│  │                      │  │  ─────────────────────────    │ │
│  │  Unagi: Great! I'll  │  │  Vitamin D:  45% ❌          │ │
│  │  log that for you... │  │  Calcium:    78% ⚠️          │ │
│  │                      │  │  Iron:       92% ✅          │ │
│  │  [Confirmation]      │  │  Zinc:       88% ✅          │ │
│  │  ✅ Confirm          │  │  ... (scroll for more)       │ │
│  │  ❌ Cancel           │  │                               │ │
│  │                      │  │  📈 WEEKLY TREND             │ │
│  │                      │  │  ─────────────────────────    │ │
│  │                      │  │  ▁▃▅▇█▇▅ Calories            │ │
│  │                      │  │  ▃▅▇█▇▅▃ Protein             │ │
│  └──────────────────────┘  └──────────────────────────────┘ │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│  💬 Type your message... (Ctrl+/ for commands)               │
└─────────────────────────────────────────────────────────────┘
```

### Key Features
1. **Left Panel (60% width)**
   - Animated eel mascot at top (swims, blinks, shows bubbles)
   - Scrollable chat history
   - Interactive confirmation buttons
   - Command palette (Ctrl+/)

2. **Right Panel (40% width)**
   - Live-updating stats dashboard
   - Today's macro progress bars
   - Micronutrient status with emojis
   - Weekly trend sparklines
   - Scrollable for all 29 micronutrients

3. **Bottom Bar**
   - Input field with autocomplete
   - Keyboard shortcuts hint
   - Status indicators (Git sync, LLM processing)

---

## 4. Component Specifications

### 4.1 Animated Eel Mascot (`ui/components/eel_mascot.py`)

**Features:**
- **Swimming animation** - 4-frame cycle, tail wag
- **Blinking** - Random blinks every 3-5 seconds
- **Bubbles** - Rising bubble particles
- **Mood states** - Happy (default), thinking (LLM processing), celebrating (log confirmed)
- **Smooth transitions** - CSS-like animations

**Implementation:**
```python
from textual.widget import Widget
from textual.reactive import reactive

class EelMascot(Widget):
    """Animated eel mascot widget."""
    
    frame = reactive(0)  # Current animation frame
    mood = reactive("happy")  # happy, thinking, celebrating
    
    FRAMES = {
        "happy": [
            "  🐍  ",
            " 🐍   ",
            "🐍    ",
            " 🐍   "
        ],
        "thinking": ["🤔🐍"],
        "celebrating": ["🎉🐍✨"]
    }
    
    def on_mount(self):
        self.set_interval(0.2, self.next_frame)
        self.set_interval(3.0, self.maybe_blink)
    
    def next_frame(self):
        self.frame = (self.frame + 1) % 4
    
    def render(self):
        # Render current frame with bubbles
        return self.FRAMES[self.mood][self.frame]
```

### 4.2 Chat Panel (`ui/components/chat_panel.py`)

**Features:**
- Scrollable message history
- User messages (right-aligned, blue)
- Unagi responses (left-aligned, green)
- System messages (centered, gray)
- Markdown rendering for rich text
- Code blocks with syntax highlighting
- Interactive confirmation buttons

**Implementation:**
```python
from textual.widgets import Static, Button
from textual.containers import Vertical, Horizontal

class ChatPanel(Vertical):
    """Chat conversation display."""
    
    def add_user_message(self, text: str):
        self.mount(UserMessage(text))
        self.scroll_end()
    
    def add_unagi_message(self, text: str):
        self.mount(UnagiMessage(text))
        self.scroll_end()
    
    def show_confirmation(self, data: dict):
        self.mount(ConfirmationWidget(data))
```

### 4.3 Stats Dashboard (`ui/components/stats_dashboard.py`)

**Features:**
- Real-time macro tracking with progress bars
- Color-coded status (green ✅, yellow ⚠️, red ❌)
- Micronutrient grid (scrollable)
- Weekly trend sparklines
- Animated updates (smooth transitions)

**Implementation:**
```python
from textual.widgets import Static, ProgressBar
from textual.reactive import reactive

class StatsDashboard(Static):
    """Live nutrition stats display."""
    
    calories = reactive(0)
    protein = reactive(0)
    
    def watch_calories(self, value: int):
        # Animate progress bar update
        self.query_one("#calories-bar").update(value)
    
    def render(self):
        return self.build_stats_view()
```

### 4.4 Input Bar (`ui/components/input_bar.py`)

**Features:**
- Multi-line input support
- Autocomplete for common foods
- Command palette (Ctrl+/)
- Keyboard shortcuts
- Send on Enter, newline on Shift+Enter

---

## 5. Animation Specifications

### Eel Swimming Animation
- **Frame rate:** 5 FPS (200ms per frame)
- **Frames:** 4 frames showing tail wag
- **Loop:** Continuous
- **Bubbles:** 3-5 bubbles rising at random intervals

### Mood Transitions
- **Happy → Thinking:** When user sends message
- **Thinking → Happy:** When LLM responds
- **Happy → Celebrating:** When log confirmed
- **Duration:** 300ms smooth transition

### Stats Updates
- **Progress bars:** Animate from old to new value (500ms)
- **Color changes:** Fade between states (300ms)
- **New data:** Slide in from right (400ms)

---

## 6. Integration Strategy

### Phase 1: Parallel Development
- Keep existing `ui/cli.py` functional
- Build new Textual UI in `ui/textual_app.py`
- Add feature flag in `config.yaml`:
  ```yaml
  ui:
    mode: "classic"  # or "modern"
  ```

### Phase 2: Adapter Pattern
```python
# main.py
if settings.ui_mode == "modern":
    from ui.textual_app import run_textual_ui
    run_textual_ui()
else:
    from ui.cli import run_cli
    run_cli()
```

### Phase 3: Shared Logic
- Keep `agent/chat.py` unchanged (business logic)
- Both UIs call same agent methods
- Stats calculation in separate module

## 11. Configuration Options

### config.yaml Updates
```yaml
ui:
  mode: "classic"              # "classic" or "modern"
  show_mascot: true
  
  # Modern UI specific settings
  modern:
    animation_level: "full"    # "full" or "minimal"
    stats_panel: true          # Show stats panel by default
    color_scheme: "retro"      # "retro" (orange/purple) or "classic" (cyan/green)
    pixel_art_style: true      # Use 8-bit pixel art aesthetic
```

### Animation Levels
**Full Animation:**
- Swimming eel with tail wag (5 FPS)
- Blinking every 3-5 seconds
- Rising bubbles
- Smooth progress bar transitions
- Color fade effects
- Slide-in animations

**Minimal Animation:**
- Static eel with occasional blink
- No bubbles
- Instant progress bar updates
- No color transitions
- No slide animations

### Stats Panel Toggle
- **Keyboard shortcut:** `Ctrl+S` to toggle stats panel
- **Command:** `/stats` to toggle
- **Persistent:** Saves preference to config
- **Responsive:** Layout adjusts when toggled

---

## 12. 8-Bit Retro Pixel Art Design

### Color Palette
```python
# Primary colors
ORANGE = "#FF6B35"      # Claude orange - primary accent
PURPLE = "#7C3AED"      # Obsidian purple - secondary accent
DARK_BG = "#1A1A2E"     # Dark background
LIGHT_TEXT = "#E8E8E8"  # Light text

# Status colors (8-bit style)
SUCCESS = "#00FF00"     # Bright green (retro success)
WARNING = "#FFFF00"     # Bright yellow (retro warning)
ERROR = "#FF0000"       # Bright red (retro error)
INFO = "#00FFFF"        # Bright cyan (retro info)
```

### Pixel Art Elements
**Eel Mascot (8-bit style):**
```
Frame 1:    Frame 2:    Frame 3:    Frame 4:
  ▓▓▓         ▓▓▓         ▓▓▓         ▓▓▓
 ▓▓▓▓▓       ▓▓▓▓▓       ▓▓▓▓▓       ▓▓▓▓▓
▓▓░░▓▓      ▓▓░░▓▓      ▓▓░░▓▓      ▓▓░░▓▓
▓▓▓▓▓▓      ▓▓▓▓▓▓      ▓▓▓▓▓▓      ▓▓▓▓▓▓
 ▓▓▓▓        ▓▓▓▓        ▓▓▓▓        ▓▓▓▓
  ▓▓          ▓▓▓        ▓▓▓▓        ▓▓▓
   ▓           ▓▓         ▓▓▓        ▓▓
```

**Bubbles (8-bit style):**
```
○  ○○  ○○○
```

**Progress Bars (8-bit style):**
```
[████████░░] 80%  ✓
[██████░░░░] 60%  ⚠
[███░░░░░░░] 30%  ✗
```

**UI Borders (8-bit style):**
```
╔═══════════════════════════════════╗
║  8-BIT RETRO STYLE BORDER         ║
╚═══════════════════════════════════╝
```

### Typography
- **Monospace font:** Required for pixel art alignment
- **Box drawing characters:** For retro borders
- **Block elements:** ▓▒░ for shading
- **Geometric shapes:** ■□▪▫ for icons

---

---

## 7. Dependencies Update

### New Dependencies
```txt
# Add to requirements.txt
textual>=0.47.0          # Modern TUI framework
textual-dev>=1.3.0       # Development tools
```

### Optional (Future)
```txt
textual-web>=0.1.0       # Web export capability
```

---

## 8. File Structure

### New Files to Create
```
ui/
├── textual_app.py              # Main Textual app
├── components/
│   ├── __init__.py
│   ├── eel_mascot.py           # Animated eel widget
│   ├── chat_panel.py           # Conversation display
│   ├── stats_dashboard.py      # Live stats
│   ├── input_bar.py            # Message input
│   └── command_palette.py      # Special commands
├── screens/
│   ├── __init__.py
│   ├── main_screen.py          # Main split layout
│   ├── onboarding_screen.py    # First-run setup
│   └── help_screen.py          # Interactive help
└── styles/
    └── app.tcss                # Textual CSS styling
```

### Files to Modify
```
config/settings.py              # Add ui_mode setting
main.py                         # Add UI mode switch
requirements.txt                # Add textual
README.md                       # Document new UI
```

---

## 9. Development Phases

### Phase 1: Foundation (Days 1-2)
- [ ] Install Textual and dependencies
- [ ] Create basic Textual app structure
- [ ] Build simple eel mascot (static first)
- [ ] Create split-pane layout
- [ ] Test basic rendering

### Phase 2: Components (Days 3-4)
- [ ] Implement animated eel mascot
- [ ] Build chat panel with message history
- [ ] Create stats dashboard with progress bars
- [ ] Add input bar with keyboard handling
- [ ] Style with Textual CSS

### Phase 3: Integration (Days 5-6)
- [ ] Connect to existing agent logic
- [ ] Implement async message handling
- [ ] Add confirmation flow
- [ ] Integrate stats calculation
- [ ] Test end-to-end flow

### Phase 4: Polish (Days 7-8)
- [ ] Add animations and transitions
- [ ] Implement command palette
- [ ] Create help screen
- [ ] Add keyboard shortcuts
- [ ] Performance optimization

### Phase 5: Testing & Documentation (Days 9-10)
- [ ] Test on different terminals
- [ ] Fix bugs and edge cases
- [ ] Write documentation
- [ ] Create demo video
- [ ] Merge to main

---

## 10. Future Enhancements

### Web UI Migration
**Option A: Textual Web**
- Export Textual app to web with `textual-web`
- Same Python code, runs in browser
- WebSocket connection to backend

**Option B: Separate Web Frontend**
- FastAPI backend (reuse agent logic)
- React/Vue frontend
- WebSocket for real-time updates
- Shared data models

### Mobile App
- React Native or Flutter
- Same backend API
- Push notifications for reminders
- Camera for food photo logging

### Advanced Features
- Voice input (Whisper API)
- Food photo recognition (GPT-4 Vision)
- Meal planning assistant
- Recipe suggestions
- Social features (share logs)

---

## 11. Technical Considerations

### Performance
- **Async operations:** Use `asyncio` for non-blocking LLM calls
- **Lazy loading:** Load stats on demand
- **Caching:** Cache recent logs in memory
- **Debouncing:** Limit animation frame rate

### Compatibility
- **Terminal support:** Test on iTerm2, Terminal.app, Windows Terminal
- **Color support:** Graceful degradation for 256-color terminals
- **Size adaptation:** Responsive layout for different terminal sizes

### Accessibility
- **Keyboard navigation:** Full keyboard support
- **Screen readers:** ARIA-like labels for widgets
- **High contrast:** Option for high-contrast theme

---

## 12. Success Metrics

### User Experience
- ✅ Startup time < 2 seconds
- ✅ Smooth animations (no lag)
- ✅ Intuitive navigation
- ✅ Clear visual feedback

### Technical
- ✅ No breaking changes to existing features
- ✅ Backward compatible with classic UI
- ✅ Test coverage > 80%
- ✅ Documentation complete

---

## 13. Risk Mitigation

### Risk 1: Textual Learning Curve
- **Mitigation:** Start with simple components, iterate
- **Fallback:** Keep classic UI as default

### Risk 2: Terminal Compatibility
- **Mitigation:** Test on multiple terminals early
- **Fallback:** Detect terminal capabilities, adapt UI

### Risk 3: Performance Issues
- **Mitigation:** Profile early, optimize animations
- **Fallback:** Reduce animation complexity

---

## 14. Next Steps

1. **Review this plan** - Get user approval
2. **Create branch** - `git checkout -b feature/modern-ui`
3. **Install Textual** - `pip install textual textual-dev`
4. **Start Phase 1** - Build foundation
5. **Iterate** - Get feedback, improve

---

## 15. User Requirements ✅

**Confirmed decisions:**

1. ✅ **UI Mode:** Classic as default, modern opt-in via config
2. ✅ **Animation Level:** Configurable (full/minimal) in config.yaml
3. ✅ **Stats Panel:** Togglable with Ctrl+S or /stats command
4. ✅ **Color Scheme:** Claude orange (#FF6B35) + Obsidian purple (#7C3AED)
5. ✅ **Design Aesthetic:** 8-bit retro videogame/pixel art style
6. ✅ **Priority:** Terminal UI first, web UI later

---

## 16. Implementation Roadmap

### Phase 1: Configuration & Setup (Day 1)
- [ ] Update config.yaml with ui.mode and ui.modern settings
- [ ] Update config/settings.py to load new settings
- [ ] Install Textual framework
- [ ] Create feature/modern-ui branch
- [ ] Set up basic Textual app structure

### Phase 2: 8-Bit Pixel Art Components (Days 2-3)
- [ ] Design 8-bit eel mascot frames (4 frames)
- [ ] Create pixel art bubbles and effects
- [ ] Build retro-styled borders and UI elements
- [ ] Implement color scheme (orange/purple)
- [ ] Create Textual CSS with retro styling

### Phase 3: Core UI Components (Days 4-5)
- [ ] Build animated eel mascot widget (full/minimal modes)
- [ ] Create chat panel with retro styling
- [ ] Implement togglable stats dashboard
- [ ] Add input bar with keyboard shortcuts
- [ ] Style all components with 8-bit aesthetic

### Phase 4: Integration & Polish (Days 6-7)
- [ ] Connect to existing agent logic
- [ ] Implement Ctrl+S stats panel toggle
- [ ] Add animation level switching
- [ ] Test on multiple terminals
- [ ] Performance optimization

### Phase 5: Documentation & Testing (Day 8)
- [ ] Update README with modern UI instructions
- [ ] Document keyboard shortcuts
- [ ] Create demo screenshots/video
- [ ] Test edge cases
- [ ] Merge to main

---

**Ready to build the 8-bit retro UNAGI! 🐍✨🎮**