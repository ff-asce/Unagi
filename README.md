# 🐍 UNAGI — Total Food Awareness

**Version:** 1.0 (v1 CLI Agent)  
**Status:** 🚧 In Development - Core Infrastructure Complete

A local-first, AI-powered nutrition agent that acts as your personalized nutritionist and food log manager. Named after Ross Geller's concept of "Unagi" — total awareness.

---

## 📋 Project Overview

Unagi is a CLI-based nutrition tracking agent that:
- Lives entirely on your machine (no cloud storage)
- Manages an Obsidian-based food journal with perfect markdown formatting
- Commits every change to Git with descriptive messages
- Uses conversational AI for natural language food logging
- Calculates macros and tracks 29 micronutrients
- Provides personalized nutrition advice based on your history

---

## 🏗️ Current Implementation Status

### ✅ Completed Modules

#### 1. **Project Structure** (`/Users/parthjindal/Parth Projects/unagi/`)
```
unagi/
├── agent/              # AI agent logic
├── vault/              # Obsidian file management
├── git_manager/        # Git operations
├── migration/          # Vault migration utilities
├── onboarding/         # First-run setup
├── config/             # Configuration management
├── ui/                 # CLI interface
├── main.py             # Entry point
├── requirements.txt    # Dependencies
├── config.yaml         # Non-secret settings
├── .env.example        # Environment template
└── .gitignore          # Git exclusions
```

#### 2. **Configuration System** (`config/`)
- ✅ `settings.py` - Loads and validates `.env` and `config.yaml`
- ✅ Supports multiple LLM backends (Gemini, Claude, Groq, Ollama)
- ✅ Git configuration with optional remote push
- ✅ Vault path management
- ✅ Clear error messages for missing configuration

#### 3. **Agent Intelligence** (`agent/`)
- ✅ `prompts.py` - System prompt with dynamic context injection
  - Personality definition
  - Nutritional reasoning rules
  - Output format specifications
  - Micronutrient tracking (29 nutrients in exact order)
- ✅ `llm.py` - OpenAI-compatible LLM client
  - Supports Gemini 2.0 Flash (recommended free tier)
  - Rate limiting with exponential backoff
  - Error handling and retries
  - Streaming support

#### 4. **Vault Management** (`vault/`)
- ✅ `parser.py` - YAML frontmatter parsing and validation
  - Parse daily log files
  - Parse user profile
  - Validate data types and formats
  - Format log data as markdown
  - Merge logic for updating existing files
- ✅ `reader.py` - Read vault files
  - Read user profile
  - Read daily logs by date
  - Read last N days of logs
  - List all logs
  - Date parsing from filenames
- ✅ `writer.py` - Write vault files
  - Create/update daily logs
  - Merge with existing data
  - Write user profile
  - Update profile fields
  - Create vault directory structure
  - Auto-create Nutrition Dashboard template

#### 5. **Git Integration** (`git_manager/`)
- ✅ `commits.py` - Git operations
  - Initialize repository
  - Commit file changes with descriptive messages
  - Push to remote (optional)
  - Status checking
  - Error handling

#### 5.5. **Vault Migration** (`migration/`)
- ✅ `migrator.py` - Migrate from old Nutrition/ structure to new Unagi/ structure
  - Detect old vault structure automatically
  - Validate all log files before migration
  - Copy files safely (never deletes originals without confirmation)
  - Patch Dataview dashboard queries
  - Git integration for migration commits
  - Incremental migration (finds new files)
  - `/migrate` command for manual migration
  - `/migrate --cleanup` for safe deletion of originals

#### 6. **Onboarding** (`onboarding/`)
- ✅ `setup.py` - First-run flow
  - Interactive user profile creation
  - TDEE calculation (Mifflin-St Jeor equation)
  - Vault initialization
  - Profile file creation

### 🚧 Pending Modules

#### 7. **Agent Context** (`agent/context.py`) - NOT YET CREATED
**Purpose:** Load user profile and recent logs into context for LLM
**Key Functions:**
- `load_context()` - Combine profile + last 7 days
- `format_context_for_llm()` - Format for system prompt injection

#### 8. **Agent Chat Loop** (`agent/chat.py`) - NOT YET CREATED
**Purpose:** Main conversation loop with intent detection
**Key Functions:**
- `detect_intent()` - Determine if user wants to log food or chat
- `parse_log_request()` - Extract date and food data from user input
- `handle_chat()` - Answer questions about nutrition/history
- `handle_log()` - Process food logging requests

#### 9. **UI - Mascot** (`ui/mascot.py`) - NOT YET CREATED
**Purpose:** ASCII/ANSI pixel art for startup screen
**Content:**
- Ross doing Unagi pose
- Cute eel mascot
- Startup banner

#### 10. **UI - CLI** (`ui/cli.py`) - NOT YET CREATED
**Purpose:** Rich-based CLI interface
**Key Functions:**
- Startup screen with mascot
- Formatted output (panels, tables)
- Special commands (`/help`, `/today`, `/week`, `/profile`, `/exit`)
- Input handling with history
- Color-coded responses

#### 11. **Main Entry Point** (`main.py`) - NOT YET CREATED
**Purpose:** Wire everything together
**Flow:**
1. Load configuration
2. Check if onboarding needed
3. Initialize vault, git, LLM
4. Show startup screen
5. Enter chat loop
6. Handle graceful shutdown

---

## 🔧 Setup Instructions

### Prerequisites
- Python 3.11+
- Git
- Obsidian (for viewing the vault)

### Installation

1. **Clone or navigate to the project:**
```bash
cd "/Users/parthjindal/Parth Projects/unagi"
```

2. **Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment:**
```bash
cp .env.example .env
# Edit .env and add your LLM_API_KEY
```

5. **Configure vault path:**
Edit `config.yaml` and set your Obsidian vault path:
```yaml
vault:
  root: "/path/to/your/ObsidianVault"
```

### Get API Key (Gemini - Free Tier)
1. Visit: https://aistudio.google.com/app/apikey
2. Create an API key
3. Add to `.env`: `LLM_API_KEY=your_key_here`

---

## 📝 Next Steps to Complete v1

### Immediate Tasks (Required for MVP)

1. **Create `agent/context.py`**
   - Load user profile from vault
   - Load last 7 days of logs
   - Format for LLM system prompt injection

2. **Create `agent/chat.py`**
   - Main conversation loop
   - Intent detection (chat vs log mode)
   - Parse food input and extract structured data
   - Call LLM with proper context
   - Handle JSON responses for log creation

3. **Create `ui/mascot.py`**
   - ASCII art for Ross + eel
   - Startup banner

4. **Create `ui/cli.py`**
   - Rich-based interface
   - Startup screen
   - Input/output formatting
   - Special commands
   - Error display

5. **Create `main.py`**
   - Entry point
   - Initialize all components
   - Run onboarding if needed
   - Start chat loop
   - Handle Ctrl+C gracefully

6. **Create `agent/__init__.py`**
   - Export agent modules

7. **Create `ui/__init__.py`**
   - Export UI modules

### Testing Tasks

8. **Test with sample input** (from spec Section 15)
   - Verify freeform input → correct `.md` output
   - Check all 29 micronutrients in correct order
   - Verify deficit calculation
   - Test merge logic for updates

9. **Run through testing checklist** (spec Section 14)
   - [ ] Onboarding creates valid User Profile
   - [ ] Freeform input produces correctly formatted file
   - [ ] Filename is `DD-MM-YYYY.md`, frontmatter date is `YYYY-MM-DD`
   - [ ] All 29 micronutrients in correct order
   - [ ] Deficit calculated correctly
   - [ ] Existing file updated (not overwritten)
   - [ ] Macros recalculated after update
   - [ ] Git commit after every write
   - [ ] Git push works when configured
   - [ ] "update yesterday" works
   - [ ] "log last Tuesday" works
   - [ ] Missing LLM key shows clear error
   - [ ] Missing git remote skips push gracefully
   - [ ] Special commands work
   - [ ] Mascot displays on startup

---

## 🎯 Key Design Decisions

### File Format
Daily logs use YAML frontmatter with specific formatting:
- Numeric fields are bare integers (no quotes)
- Meal fields are quoted strings or em dash `—`
- Notes field uses `●` as section separator
- Raw weight noted as `(r)` e.g., `450g Chicken Breast (r)`
- File ends with: `Main View: [[Nutrition Dashboard]]`

### Micronutrient Order (Always This Exact Order)
Vitamin A, Vitamin C, Vitamin D, Vitamin E, Vitamin K, B1 (Thiamine), B2 (Riboflavin), B3 (Niacin), B5 (Pantothenic Acid), B6 (Pyridoxine), B7 (Biotin), B9 (Folate), B12 (Cobalamin), Choline, Calcium, Chromium, Copper, Iodine, Iron, Magnesium, Manganese, Molybdenum, Phosphorus, Potassium, Selenium, Sodium, Zinc, Omega-3, Omega-6

### Git Commit Format
```
[unagi] <action>: <date> — <summary>

Examples:
[unagi] create: 2026-05-25 — Breakfast + Dinner logged. Cal: 1250 | P: 118g | Deficit: -750
[unagi] update: 2026-05-25 — Added dinner. Cal: 1025 → 1250 | P: 110g → 118g
```

---

## 🔍 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     CLI Interface                       │
│  (Rich formatting, pixel art mascot, special commands)  │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│                   Agent Chat Loop                       │
│  • Intent detection (chat vs log mode)                  │
│  • Context injection (profile + last 7 days)            │
│  • Conversation history management                      │
└────┬──────────────────────────────────────────┬─────────┘
     │                                          │
┌────▼─────────────┐                  ┌─────────▼─────────┐
│   LLM Client     │                  │  Context Loader   │
│  (OpenAI API)    │                  │  (Profile + Logs) │
└──────────────────┘                  └───────────────────┘
                                                │
                 ┌──────────────────────────────┴─────────┐
                 │                                        │
        ┌────────▼─────────┐                   ┌──────────▼────────┐
        │  Vault Reader    │                   │   Vault Writer    │
        │  (Parse YAML)    │                   │  (Create/Update)  │
        └──────────────────┘                   └──────────┬────────┘
                                                          │
                                               ┌──────────▼────────┐
                                               │   Git Manager     │
                                               │ (Commit & Push)   │
                                               └───────────────────┘
```

---

## 📚 Reference

- **Specification:** `/Users/parthjindal/Downloads/UNAGI_DEV_SPEC.md`
- **Sample Input/Output:** See spec Section 15
- **Testing Checklist:** See spec Section 14

---

## 🤝 Contributing

This is a personal project. The implementation follows the detailed specification document.

---

## 📄 License

Private project - All rights reserved.

---

**Built with 🐍 total food awareness.**
