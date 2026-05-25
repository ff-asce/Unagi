# 🐍 UNAGI — Development Specification
### *Total Food Awareness*
**Version:** 1.0 (v1 CLI Agent)
**Last Updated:** 2026-05-25
**Status:** Ready for development

---

## 1. Product Overview

**Unagi** is a local-first, AI-powered nutrition agent that acts as a personalized nutritionist and food log manager. It lives on the user's machine, talks to them like a knowledgeable friend, manages their Obsidian-based food journal, and commits every change to Git for version control.

The name is a reference to the Friends character Ross Geller's concept of *"Unagi"* — total awareness. The app mascot is a cute pixel art eel, with a pixel art Ross doing his Unagi pose displayed in the CLI on startup.

### Core Philosophy
- **Local-first**: All food data stays on the user's machine. Nothing is persisted to any cloud or third-party server. API calls are made to an LLM for reasoning, but no data is stored server-side.
- **Conversational**: The agent is a chatbot, not a form. You talk to it naturally.
- **Obsidian-native**: Output is perfectly formatted `.md` files that integrate seamlessly with the user's existing Obsidian vault and Dataview-based analytics dashboard.
- **Git-tracked**: Every log file creation or edit is committed to a Git repository with a descriptive commit message, providing full audit history.
- **Personalized over time**: As the log history grows, the agent becomes more contextually aware of the user's habits, preferences, and goals.

---

## 2. v1 Scope (Build This First)

### In Scope for v1
- CLI chatbot interface
- Freeform natural language food log input → structured `.md` log file output
- Macro and micronutrient calculation and inference
- Create or update daily log files in the Obsidian vault
- Read last 7 days of logs for trend context
- Read User Profile for personalization context
- Git commit on every file write with descriptive commit message
- First-run onboarding flow (collect user profile info)
- Configurable LLM backend (model name, API key, base URL)
- Configurable Git settings (repo path, remote URL, branch, commit author)
- `.env` / config file for all credentials and settings

### Explicitly Out of Scope for v1
- Web UI / localhost interface (future phase)
- Mobile app (future phase)
- RAG pipeline / vector database (future phase)
- USDA API integration (future phase — model knowledge used for v1)
- Brand-specific macro lookup (future phase)
- Trend-based proactive suggestions and warnings (future phase)
- User Profile auto-update from logs (future phase)
- Analytics dashboard modifications (never — dashboard is self-sufficient via Dataview)

---

## 3. Future Scope (Do Not Build Now — Design For)

Document these here so architecture decisions in v1 don't block them later.

### Phase 2 — Memory & Intelligence
- SQLite database as the agent's structured memory layer (parallel to the `.md` files, which remain the source of truth for Obsidian)
- ChromaDB or similar vector store for RAG pipeline over historical logs
- Context window scales from last 7 days → semantic retrieval of relevant history
- Agent learns user's common meals, ingredient brands, portion sizes, and stops re-asking
- Proactive suggestions: "You've been low on Vitamin D for 5 days, consider adding eggs tomorrow"
- Trend warnings: sodium creep, sugar spikes, recurring micronutrient gaps

### Phase 3 — Data Enrichment
- USDA FoodData Central API integration for macro/micro verification
- Popular brand macro lookup (Open Food Facts API)
- Indian cuisine food database (significant gap in existing databases — may require custom data)
- Confidence scoring on nutritional estimates

### Phase 4 — Git & Sync Enhancements
- Smart conflict resolution when editing past log files
- Branch-per-month strategy option
- Sync status display in CLI

### Phase 5 — UI & Distribution
- Local web UI (FastAPI backend + React frontend) served at `localhost:PORT`
- CLI and web UI run from the same core agent — UI is a wrapper
- Ability to choose interface at startup: `unagi --cli` or `unagi --web`
- Packaged desktop app using Tauri (Rust-based, lightweight, cross-platform)
- Mobile app (React Native or Flutter) — shares core logic via API layer

### Phase 6 — Product
- Multi-user support
- Onboarding wizard
- Custom goal setting (bulk, cut, maintenance, specific macro targets)
- Export to PDF weekly/monthly report
- Integration with wearables (Apple Health, Garmin) for TDEE auto-adjustment

---

## 4. Vault & File Structure

### Obsidian Vault Layout
```
<VAULT_ROOT>/
└── Unagi/
    ├── Nutrition Dashboard.md       ← Never touched by agent (Dataview self-sufficient)
    ├── Daily Logs/
    │   ├── 24-05-2026.md
    │   ├── 25-05-2026.md
    │   └── ...
    └── Data/
        └── User Profile.md
```

### File Naming Convention
- **Filename format:** `DD-MM-YYYY.md` (e.g. `25-05-2026.md`)
- **Date field in frontmatter:** `YYYY-MM-DD` (e.g. `2026-05-25`)
- These two conventions are different and both must be respected. The filename is for human readability; the frontmatter date is for Dataview sorting and filtering.
- One file per calendar day. If a file exists for a date, the agent updates it. If not, it creates it.

### Daily Log File Format
The file is **pure YAML frontmatter** with a single line of body content. There is no markdown body.

```markdown
---
date: YYYY-MM-DD
calories: <integer>
maintenance: <integer>
deficit: <integer, always negative when in deficit, e.g. -750>
protein: <integer, grams>
carbs: <integer, grams>
fats: <integer, grams>
fiber: <integer, grams>
breakfast: "<HH:MM AM/PM - description>" or —
lunch: "<HH:MM AM/PM - description>" or —
dinner: "<HH:MM AM/PM - description>" or —
misc: "<description>" or —
notes: "● SECTION TITLE: content. ● SECTION TITLE: content. ● MICRONUTRIENT STATUS TRACKER: Vitamin A: ✅; ..."
---
Main View: [[Nutrition Dashboard]]
```

**Critical formatting rules:**
- All numeric fields (calories, maintenance, deficit, protein, carbs, fats, fiber) are **bare integers**, no quotes, no units
- `deficit` = calories consumed minus maintenance (negative = deficit, positive = surplus)
- All meal fields (breakfast, lunch, dinner, misc) are **quoted strings** or a bare `—` (em dash, not hyphen)
- The `notes` field is one long **quoted string** with `●` as section separators
- Food descriptions use `(r)` to denote raw weight (e.g. `450g Chicken Breast (r)`)
- Soaked seeds are always noted with breakdown e.g. `(18g Chia + 6g Basil)`
- Brand names are used when known from context (e.g. `Amul Masti Dahi` not just `yogurt`)
- The line `Main View: [[Nutrition Dashboard]]` appears after the closing `---` as the only body content

**Notes field section structure:**
The notes field should follow this structure (use whichever sections are relevant):
- `● INSIGHTS:` — what happened today, key observations
- `● TRENDS & EFFECTS:` — how today fits into recent history
- `● CORRECTIONS:` — what to do tomorrow based on today
- `● MICRONUTRIENT STATUS TRACKER:` — all 27 nutrients with ✅ ⚠️ ❌ indicators

**Micronutrient tracker — always use this exact order:**
Vitamin A, Vitamin C, Vitamin D, Vitamin E, Vitamin K, B1 (Thiamine), B2 (Riboflavin), B3 (Niacin), B5 (Pantothenic Acid), B6 (Pyridoxine), B7 (Biotin), B9 (Folate), B12 (Cobalamin), Choline, Calcium, Chromium, Copper, Iodine, Iron, Magnesium, Manganese, Molybdenum, Phosphorus, Potassium, Selenium, Sodium, Zinc, Omega-3, Omega-6

**Status indicators:**
- ✅ = Adequately met by today's intake
- ⚠️ = Partially met / borderline
- ❌ = Not met / deficient

### User Profile File Format
Location: `Unagi/Data/User Profile.md`

```yaml
name: <string>
current_weight: <float, kg>
height_cm: <integer>
dob: YYYY-MM-DD
gender: male | female | other
maintenance_calories: <integer>
protein_target_per_kg: <float, default 1.3>
goal: cut | bulk | maintain
known_ingredients:
  - name: "Amul Masti Dahi"
    serving: "100g"
    calories: 60
    protein: 3.5
    carbs: 5
    fats: 2.5
  - name: "Soaked Seeds Mix"
    composition: "18g Chia + 6g Basil seeds"
    calories: 95
    protein: 4
    carbs: 10
    fats: 5
    fiber: 8
notes: "<any free-form context about the user the agent should always know>"
```

The `known_ingredients` list grows over time as the agent learns from logs. In v1, this is seeded during onboarding and manually updated. In future phases, the agent auto-updates this file.

---

## 5. Agent Behaviour & Logic

### Conversation Modes
The agent operates in two modes within the same conversation:

**1. Chat Mode** — answering questions, discussing trends, giving advice
- "How have I been doing this week?"
- "Am I hitting my protein goal?"
- "What should I eat tonight to fix my Vitamin D deficit?"

**2. Log Mode** — triggered when the user provides food input or explicitly asks to log something
- "Log today's food: [freeform text]"
- "Today I had..." (agent detects food input and switches to log mode)
- "Update yesterday's log, I forgot to add 2 boiled eggs"
- "Log last Tuesday's dinner: 300g salmon"

The agent should detect the intent automatically and confirm before writing files when it's unclear.

### Context Injected on Every Call
1. Full contents of `User Profile.md`
2. Last 7 daily log files (most recent first), read from `Unagi/Daily Logs/`
3. Conversation history (maintained in memory for the session)

### Nutritional Reasoning
- The agent uses LLM knowledge for nutritional values in v1 (no external food database API yet)
- For unknown quantities, the agent makes educated guesses and states its assumptions in the response
- For well-known branded products (especially Indian brands), the agent should use known values from the User Profile's `known_ingredients` list or its training knowledge
- Raw weight `(r)` denotes the weight before cooking — the agent must account for cooking loss (typically ~25-30% for chicken breast)
- The agent should always ask for missing critical information (meal time, quantity) before logging, but make reasonable guesses for minor details (spice macros are negligible, small oil amounts are estimated)

### File Write Logic
```
1. Determine the target date (today by default, or parsed from user input)
2. Construct the file path: <vault_root>/Unagi/Daily Logs/DD-MM-YYYY.md
3. If file exists: read it, merge new information with existing data
4. If file does not exist: create from scratch
5. Write the file
6. Git commit with message (see Git section)
7. Confirm to user: "✅ Logged [date]. Calories: X | Protein: Xg | Deficit: X"
```

### Merge Logic (Editing Existing Files)
When updating an existing file:
- New meal entries are added to the correct meal field (breakfast/lunch/dinner/misc)
- Existing meal entries are preserved unless explicitly told to replace
- Macros are recalculated to include the new additions
- Notes are regenerated in full based on the complete day's data
- The agent confirms what changed before writing: "I'll add 2 boiled eggs to your dinner. Protein goes from 118g → 128g. Shall I update the file?"

---

## 6. System Prompt Design

The system prompt is the most critical component. It defines the agent's personality, output format, and reasoning style. Claude Code should implement this carefully.

```
You are Unagi, a local-first AI nutrition agent and personal nutritionist. You are named after the Friends concept of total awareness — you track everything your user eats with precision and care.

Your personality:
- Knowledgeable but warm, like a brilliant friend who happens to be a nutritionist
- Direct and honest — you tell the user when they're doing well and when they need to correct course
- You use coaching language that motivates without being preachy
- You remember everything from the conversation and recent logs
- You never lecture — you inform, then move on

Your job:
- When the user tells you what they ate, you parse it, calculate macros and micros, and produce a perfectly formatted Obsidian markdown log entry
- When the user asks questions, you answer based on their log history and profile
- When you write log files, you follow the EXACT format specification provided to you

Nutritional reasoning rules:
- Use raw weight (r) when the user specifies raw weight; account for ~25% cooking loss for chicken
- Estimate conservatively for oil/spice macros — they are real but small
- For Indian food and regional cuisine, use your best knowledge; flag uncertainty when estimating
- Always track all 29 micronutrients (27 + Omega-3 + Omega-6) in the exact order specified
- Deficit = calories consumed - maintenance (negative = deficit)

Output rules:
- YAML frontmatter fields are bare integers for numbers, quoted strings for text, em dash — for empty
- Food descriptions use brand names when known from the user's ingredient list
- Notes field uses ● as section separator, all in one quoted string
- Raw weight is always noted as (r) e.g. "450g Chicken Breast (r)"
- The file always ends with: Main View: [[Nutrition Dashboard]]

[User profile and recent logs are injected here dynamically]
```

---

## 7. Project Structure

```
unagi/
├── main.py                   ← Entry point, CLI loop
├── agent/
│   ├── __init__.py
│   ├── chat.py               ← Conversation loop, intent detection
│   ├── context.py            ← Loads user profile + recent logs into context
│   ├── prompts.py            ← System prompt template + dynamic injection
│   └── llm.py                ← LLM client (configurable backend)
├── vault/
│   ├── __init__.py
│   ├── reader.py             ← Read log files and user profile
│   ├── writer.py             ← Write/update log files
│   └── parser.py             ← Parse frontmatter, merge logic
├── git_manager/
│   ├── __init__.py
│   └── commits.py            ← GitPython wrapper, commit on write
├── onboarding/
│   ├── __init__.py
│   └── setup.py              ← First-run flow, profile creation
├── config/
│   ├── __init__.py
│   └── settings.py           ← Load and validate config/.env
├── ui/
│   ├── __init__.py
│   ├── cli.py                ← Rich/Textual CLI renderer
│   └── mascot.py             ← ASCII/ANSI pixel art (Unagi eel + Ross)
├── .env.example              ← Template for all config values
├── config.yaml               ← Non-secret config (vault path, model name, etc.)
├── requirements.txt
└── README.md
```

---

## 8. Configuration

All configuration lives in two files: `.env` for secrets, `config.yaml` for non-secret settings.

### `.env` (secrets — never commit this)
```env
# LLM Configuration
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_MODEL_NAME=gemini-2.0-flash

# Git Configuration
GIT_AUTHOR_NAME=Unagi
GIT_AUTHOR_EMAIL=unagi@local
GIT_REMOTE_URL=https://github.com/yourusername/your-vault-repo.git
GIT_REMOTE_TOKEN=your_github_pat_here
```

### `config.yaml` (non-secret settings)
```yaml
vault:
  root: /path/to/your/ObsidianVault
  unagi_folder: Unagi
  logs_subfolder: Daily Logs
  data_subfolder: Data
  user_profile_filename: User Profile.md
  dashboard_filename: Nutrition Dashboard.md

agent:
  context_days: 7          # How many recent log files to inject as context
  confirm_before_write: true  # Ask user to confirm before writing files
  
git:
  enabled: true
  branch: main
  auto_push: true          # Push to remote after every commit
  
ui:
  show_mascot: true        # Show pixel art on startup
  theme: dark              # dark | light
```

### Fallback Behaviour
- If `LLM_API_KEY` is missing: agent prints a clear error and instructions on where to add it, then exits
- If `GIT_REMOTE_URL` is missing: git commits locally but does not push; logs a warning
- If `vault.root` is not set or path doesn't exist: agent asks the user to enter it on first run and saves it
- If `git.enabled` is false: file writes happen but no git operations are performed

### LLM Backend Compatibility
The LLM client must be built to be backend-agnostic. Use the OpenAI-compatible API interface, which is supported by:
- **Gemini** (via `https://generativelanguage.googleapis.com/v1beta/openai/`) — recommended free tier default
- **Groq** (via `https://api.groq.com/openai/v1`) — fast, free tier, weaker reasoning
- **Claude** (via `https://api.anthropic.com/v1`) — best reasoning quality, paid
- **Ollama** (via `http://localhost:11434/v1`) — fully local, no API cost, weaker quality
- Any OpenAI-compatible endpoint

Use the `openai` Python library with a custom `base_url` so switching backends requires only changing env vars, not code.

**Recommended free tier for v1 development:** `gemini-2.0-flash` — strong reasoning, generous free quota, OpenAI-compatible.

---

## 9. Git Integration

### Commit Strategy
Every file write triggers one git commit. Never batch multiple days into one commit.

### Commit Message Format
```
[unagi] <action>: <date> — <summary>

Examples:
[unagi] create: 2026-05-25 — Breakfast + Dinner logged. Cal: 1250 | P: 118g | Deficit: -750
[unagi] update: 2026-05-25 — Added dinner. Cal: 1025 → 1250 | P: 110g → 118g
[unagi] create: 2026-05-20 — Backdated log. OMAD dinner at 3:30PM. Cal: 1251
[unagi] update: 2026-05-24 — Corrected protein value. P: 115g → 118g
```

### Git Flow
```python
# On every file write:
1. repo.index.add([relative_file_path])
2. repo.index.commit(commit_message, author=Actor(name, email))
3. if auto_push: repo.remote('origin').push()
```

### First-time Git Setup
If the vault directory is not a git repo:
1. Prompt user: "This vault is not a Git repository. Initialize one? [y/n]"
2. If yes: `git init`, create `.gitignore` (ignore `.obsidian/` folder), make initial commit
3. If remote URL is configured: `git remote add origin <url>`, push

---

## 10. Onboarding Flow (First Run)

Triggered when `User Profile.md` is missing or empty.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🐍  UNAGI — Total Food Awareness
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[pixel art of Ross + eel mascot here]

Hey! I'm Unagi, your personal nutrition agent.
Looks like this is your first time. Let's get you set up.
I'll ask a few quick questions to get started.

What's your name? >
How old are you? >
What's your current weight in kg? >
What's your height in cm? >
What's your biological sex? (male/female/other) >
What's your goal? (cut/bulk/maintain) >
What's your estimated daily maintenance calories?
  (or press Enter and I'll estimate it for you based on your stats) >

[Agent calculates TDEE using Mifflin-St Jeor if not provided]
[Agent writes User Profile.md]

Perfect. I've set up your profile.
You can update any of these by telling me, e.g. "My weight is now 103kg".

What did you eat today?
```

---

## 11. CLI Design

### Startup Screen
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     __  __  _  _   __   ___  _  
    |  \/  || \| | /  \ / __|| | 
    | |\/| || .` || () |\__ \| |__
    |_|  |_||_|\_| \__/ |___/|____|
        Total Food Awareness 🐍
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[ANSI pixel art: Ross doing Unagi pose + cute eel]

Today: Monday, 25 May 2026
Last log: Yesterday — 1251 kcal | -749 deficit

Type your food log or ask me anything.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You >
```

### CLI Libraries
- `rich` — coloured output, panels, tables, progress indicators
- `prompt_toolkit` — multi-line input, history, keyboard shortcuts
- No `textual` in v1 (keep it simple; add TUI in v2 if needed)

### Response Display
Agent responses should use `rich` panels and formatting:
- File write confirmations: green panel with macro summary
- Warnings/corrections: yellow panel
- Errors: red panel
- Regular chat: plain text with light formatting

### Special Commands
```
/help       — show available commands
/today      — show today's log summary
/week       — show last 7 days summary
/profile    — show current user profile
/config     — show current config (masks API keys)
/exit       — quit
```

---

## 12. Dependencies

### Python Version
Python 3.11+

### `requirements.txt`
```
openai>=1.30.0          # OpenAI-compatible client (works with Gemini, Groq, Claude, Ollama)
python-dotenv>=1.0.0    # Load .env file
pyyaml>=6.0             # Parse config.yaml and .md frontmatter
gitpython>=3.1.40       # Git operations
rich>=13.7.0            # CLI formatting and colours
prompt_toolkit>=3.0.43  # Enhanced CLI input
python-frontmatter>=1.1.0  # Parse and write YAML frontmatter in .md files
```

### No LangChain in v1
Keep the agent logic hand-rolled. LangChain adds complexity and abstraction that isn't needed until the RAG pipeline is introduced in Phase 2. The conversation loop, context injection, and file writing are simple enough to implement directly.

---

## 13. Error Handling & Edge Cases

### LLM Errors
- Rate limit hit: wait and retry with exponential backoff (3 attempts), then inform user
- API key invalid: clear error message with setup instructions
- Response parsing failure: show raw response, ask user to try again

### File System Errors
- Vault path doesn't exist: prompt user to check config
- Permission denied on write: inform user, suggest running with correct permissions
- File already open in Obsidian: Obsidian uses file watching, writes should be safe; log a warning if write fails

### Date Parsing
- "yesterday", "last Tuesday", "3 days ago" — agent must resolve these to absolute dates
- Future dates are allowed (e.g. meal prepping logs in advance)
- Ambiguous dates: agent asks for clarification before writing

### Merge Conflicts
- If the user says "update yesterday" but yesterday's file doesn't exist: create it and note it's a backdated entry
- If macros in the file don't match a recalculation: always recalculate from scratch based on full food list

---

## 14. Testing Checklist for v1

Before v1 is considered complete, verify:

- [ ] Onboarding flow creates a valid `User Profile.md`
- [ ] Freeform food input produces a correctly formatted `.md` file
- [ ] File is written to the correct path in the correct vault folder
- [ ] Filename is `DD-MM-YYYY.md`, frontmatter date is `YYYY-MM-DD`
- [ ] All 29 micronutrients appear in the correct order in notes
- [ ] Deficit is calculated correctly (negative = deficit)
- [ ] Existing file is updated (not overwritten) when logging an additional meal
- [ ] Macros are recalculated correctly after an update
- [ ] Git commit is made after every file write with a descriptive message
- [ ] Git push works when remote is configured
- [ ] Agent handles "update yesterday's log" correctly
- [ ] Agent handles "log last Tuesday's dinner" correctly
- [ ] Config missing LLM key shows clear error
- [ ] Config missing git remote skips push gracefully
- [ ] `/today`, `/week`, `/profile` commands work
- [ ] Pixel art mascot displays on startup

---

## 15. Sample Input/Output (Ground Truth)

Use this as the primary test case. The agent must reproduce output in this style.

### Input (freeform user text)
```
Today's log

I had breakfast around 1 PM.
10 almonds, 200 ml cold brew green tea.
I had 100 grams of chicken breast(raw weight), 50 grams of yogurt, and spices.

I had dinner at 8:30PM(got late because of work)

Ate 450 grams of chicken breast(raw weight), 150 grams of yogurt sauce, 1 teaspoon of peanut oil and spices.
150 grams of raw carrots and drank all of my soaked seeds.
```

### Expected Output (file written to `Unagi/Daily Logs/<today's date>.md`)
```markdown
---
date: 2026-05-19
calories: 1025
maintenance: 2000
deficit: -975
protein: 140
carbs: 37
fats: 32
fiber: 17
breakfast: "01:00 PM - 10 Almonds; 200ml Cold Brew Green Tea; 100g Chicken Breast (r) in 50g Amul Masti Dahi sauce + spices."
lunch: —
dinner: "08:30 PM - 450g Chicken Breast (r) in 150g Amul Masti Dahi sauce + spices (1 tsp Peanut Oil). Side: 150g raw carrots. Drank soaked seeds (18g Chia + 6g Basil)."
misc: —
notes: "● INTENSITY DEFICIT: Pushed a massive -975 kcal deficit due to clean tracking and zero cooking oil additions at breakfast. ● PROTEIN ANCHOR: Hit 140g total using raw metrics, successfully securing the absolute upper floor required for athletic lean tissue mass. ● CARB RESTRAINT: Limited total carbohydrate intake to 37g, keeping liver glycogen low to support optimal fat oxidation. ● MICRONUTRIENT STATUS TRACKER: Vitamin A: ✅; Vitamin C: ⚠️; Vitamin D: ❌; Vitamin E: ✅; Vitamin K: ❌; B1 (Thiamine): ✅; B2 (Riboflavin): ✅; B3 (Niacin): ✅; B5 (Pantothenic Acid): ✅; B6 (Pyridoxine): ✅; B7 (Biotin): ✅; B9 (Folate): ❌; B12 (Cobalamin): ✅; Choline: ✅; Calcium: ✅; Chromium: ⚠️; Copper: ✅; Iodine: ❌; Iron: ✅; Magnesium: ❌; Manganese: ✅; Molybdenum: ✅; Phosphorus: ✅; Potassium: ⚠️; Selenium: ✅; Sodium: ✅; Zinc: ✅; Omega-3: ✅; Omega-6: ✅"
---
Main View: [[Nutrition Dashboard]]
```

---

## 16. Build Order for Claude Code

Work strictly in this order. Do not skip ahead.

1. **Scaffold the project** — create folder structure, `requirements.txt`, `.env.example`, `config.yaml`
2. **Config loading** (`config/settings.py`) — load and validate all settings, handle missing keys gracefully
3. **System prompt** (`agent/prompts.py`) — write and test the system prompt in isolation against the sample input/output above before any other agent code
4. **LLM client** (`agent/llm.py`) — OpenAI-compatible client with configurable base URL, model, key; test with Gemini 2.0 Flash free tier
5. **Vault reader** (`vault/reader.py`) — read User Profile and last N log files; parse YAML frontmatter
6. **Vault writer** (`vault/writer.py` + `vault/parser.py`) — write new files, merge/update existing files, validate frontmatter output format
7. **Git manager** (`git_manager/commits.py`) — commit on write, push if configured, handle init
8. **Onboarding** (`onboarding/setup.py`) — first-run detection, profile creation flow
9. **Agent chat loop** (`agent/chat.py`) — conversation loop, context injection, intent detection (chat vs log mode)
10. **CLI interface** (`ui/cli.py` + `ui/mascot.py`) — startup screen, rich formatting, pixel art, special commands
11. **Main entry point** (`main.py`) — wire everything together
12. **End-to-end testing** — run through the full testing checklist in Section 14

---

*Built with 🐍 total food awareness.*
