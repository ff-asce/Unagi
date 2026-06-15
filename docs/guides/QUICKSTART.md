# 🚀 UNAGI - Quick Start Guide

Get Unagi up and running in 5 minutes!

---

## ✅ Prerequisites

- Python 3.11 or higher
- Git
- Obsidian (for viewing your vault)
- A Gemini API key (free tier available)

---

## 📦 Step 1: Install Dependencies

```bash
cd "/Users/parthjindal/Parth Projects/unagi"

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

---

## 🔑 Step 2: Get Your API Key

### Option A: Gemini (Recommended - Free Tier)

1. Visit: https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key

### Option B: Other Providers

- **Claude**: https://console.anthropic.com/
- **Groq**: https://console.groq.com/
- **Ollama**: Run locally (no API key needed)

---

## ⚙️ Step 3: Configure Unagi

### Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and configure:

```env
# LLM Configuration
LLM_API_KEY=your_actual_api_key_here
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_MODEL_NAME=models/gemini-2.5-flash

# Git Configuration
GIT_AUTHOR_NAME=Your Name
GIT_AUTHOR_EMAIL=your.email@example.com
GIT_REMOTE_URL=
GIT_REMOTE_TOKEN=
```

**Required:**
- `LLM_API_KEY`: Your Gemini API key from Step 2
- `GIT_AUTHOR_NAME`: Your name (for Git commits)
- `GIT_AUTHOR_EMAIL`: Your email (for Git commits)

**Optional (for GitHub backup):**
- `GIT_REMOTE_URL`: Your GitHub repository URL (see below)
- `GIT_REMOTE_TOKEN`: GitHub Personal Access Token (see below)

**Optional (for enhanced intelligence features):**
- `USDA_API_KEY`: USDA FoodData Central API key (see below)
- `OPENFOODFACTS_USER_AGENT`: User agent for OpenFoodFacts (default: "Unagi/1.0")

#### Setting up GitHub Backup (Optional)

If you want to automatically backup your vault to GitHub:

1. **Create a private GitHub repository:**
   - Go to https://github.com/new
   - Name it (e.g., `nutrition-vault`)
   - Make it **Private** (your food logs are personal!)
   - Don't initialize with README

2. **Get your repository URL:**
   ```
   https://github.com/yourusername/nutrition-vault.git
   ```

3. **Create a Personal Access Token:**
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token" → "Generate new token (classic)"
   - Give it a name: `Unagi Vault Backup`
   - Select scopes: Check **`repo`** (full control of private repositories)
   - Click "Generate token"
   - **Copy the token immediately** (you won't see it again!)

4. **Add to `.env`:**
   ```env
   GIT_REMOTE_URL=https://github.com/yourusername/nutrition-vault.git
   GIT_REMOTE_TOKEN=ghp_your_token_here
   ```

5. **Enable auto-push in `config.yaml`:**
   ```yaml
   git:
     enabled: true
     auto_push: true  # Push after every commit
   ```

**Note:** If you skip GitHub setup, Unagi will still commit locally to Git for version control.

#### Setting up USDA API (Optional - Enhanced Intelligence)

For access to 400,000+ foods with detailed nutrition data:

1. **Get a free USDA API key:**
   - Go to: https://fdc.nal.usda.gov/api-key-signup.html
   - Fill out the form (takes 1 minute)
   - Check your email for the API key

2. **Add to `.env`:**
   ```env
   USDA_API_KEY=your_usda_api_key_here
   ```

**Benefits:**
- Access to comprehensive USDA FoodData Central database
- More accurate nutrition data for common foods
- Better confidence scores for food estimates

**Note:** UNAGI works great without this - it will use the built-in database and LLM estimates.

### Configure `config.yaml`:

Edit `config.yaml` and set your Obsidian vault path:

```yaml
vault:
  root_path: "/path/to/your/ObsidianVault"  # Change this!
  unagi_folder: Unagi
  logs_subfolder: Daily Logs
  data_subfolder: Data
```

**Example:**
```yaml
vault:
  root_path: "/Users/parthjindal/Documents/MyVault"
```

---

## 🎯 Step 4: Run Unagi

```bash
python main.py
```

On first run, you'll go through onboarding:
- Enter your name
- Age, weight, height
- Gender and fitness goal
- Maintenance calories (or let Unagi calculate it)

---

## 💬 Step 5: Start Logging!

### Log Your Food

Just tell Unagi what you ate naturally:

```
You > I had breakfast at 1 PM: 10 almonds, 200ml green tea, 100g chicken breast (raw weight), 50g yogurt
```

Unagi will:
- Calculate all macros and micros
- Create a perfectly formatted log file
- Commit it to Git
- Show you a summary

### Ask Questions

```
You > How have I been doing this week?
You > Am I hitting my protein goal?
You > What should I eat to fix my Vitamin D deficit?
```

### Use Special Commands

```
/help      Show help
/today     Today's summary
/week      Weekly summary
/profile   Your profile
/exit      Quit
```

---

## 📁 What Gets Created

After your first log, check your Obsidian vault:

```
YourVault/
└── Unagi/
    ├── Nutrition Dashboard.md    ← Open this in Obsidian!
    ├── Daily Logs/
    │   └── 25-05-2026.md        ← Your food logs
    └── Data/
        └── User Profile.md       ← Your profile
```

Open `Nutrition Dashboard.md` in Obsidian to see your analytics!

---

## 🎨 Example Session

```
╔═══════════════════════════════════════════════════════════╗
║         🐍 Total Food Awareness 🐍                        ║
╚═══════════════════════════════════════════════════════════╝

Today: Sunday, 25 May 2026
Welcome back, Parth! 👋

Type your food log or ask me anything.
────────────────────────────────────────────────────────────

You > Today I had breakfast at 1 PM: 10 almonds, 200ml cold brew green tea, 100g chicken breast (raw weight), 50g Amul Masti Dahi

Unagi: ✅ Logged 2026-05-25
Breakfast logged at 01:00 PM
Calories: 245 | Protein: 28g | Carbs: 8g | Fats: 11g | Deficit: -1755

You > /today

┌─────────────────────────────────────┐
│        Today's Summary              │
├──────────────┬──────────────────────┤
│ Metric       │ Value                │
├──────────────┼──────────────────────┤
│ Date         │ 2026-05-25           │
│ Calories     │ 245 kcal             │
│ Protein      │ 28g                  │
│ Carbs        │ 8g                   │
│ Fats         │ 11g                  │
│ Fiber        │ 3g                   │
│ Deficit      │ -1755                │
└──────────────┴──────────────────────┘

You > /exit

╔═══════════════════════════════════════════════════════════╗
║              Thanks for using UNAGI! 🐍                   ║
║         Stay aware. Stay healthy. Stay strong.           ║
╚═══════════════════════════════════════════════════════════╝
```

---

## 🐛 Troubleshooting

### "LLM_API_KEY is missing"
- Check your `.env` file exists
- Make sure you copied `.env.example` to `.env`
- Verify the API key is correct (no extra spaces)

### "Vault root does not exist"
- Check the path in `config.yaml`
- Make sure the directory exists
- Use absolute paths (not `~` or `$HOME`)

### "Import errors" when running
- Make sure you activated the virtual environment
- Run `pip install -r requirements.txt` again

### "Operation not permitted" Git errors (macOS)

This is a macOS security feature. You need to grant Full Disk Access:

**Option 1: Grant Terminal Full Disk Access (Recommended)**
1. Open **System Settings** → **Privacy & Security** → **Full Disk Access**
2. Click the **+** button
3. Navigate to `/Applications/Utilities/` and select **Terminal.app**
4. Toggle it ON
5. **Restart Terminal** and try again

**Option 2: Disable Git temporarily**
If you don't need Git right now:
```yaml
# In config.yaml
git:
  enabled: false
```

**Option 3: Use a different vault location**
Move your vault to a location that doesn't require Full Disk Access:
```yaml
# In config.yaml
vault:
  root_path: "/Users/parthjindal/unagi-vault"  # In your home directory
```

### "Write access to repository not granted" (GitHub)

This means either the repository doesn't exist or your token lacks permissions:

**Check 1: Does the repository exist?**
- Visit your repository URL in a browser
- If it shows 404, create the repository first (see Step 3 above)

**Check 2: Token permissions**
Your Personal Access Token needs the `repo` scope:
1. Go to: https://github.com/settings/tokens
2. Click on your token or create a new one
3. Ensure **`repo`** (Full control of private repositories) is checked
4. If you made changes, regenerate the token
5. Update the token in `.env`

**Quick Fix: Disable auto-push**
If you don't need GitHub backup right now:
```yaml
# In config.yaml
git:
  auto_push: false  # Still commits locally
```

### Stale Git lock file
If you see `HEAD.lock` errors:
```bash
rm "/path/to/your/vault/.git/HEAD.lock"
rm "/path/to/your/vault/.git/index.lock"
```

---

## 📚 Next Steps

1. **Customize your dashboard**: Edit `Nutrition Dashboard.md` in Obsidian
2. **Add known ingredients**: Update `User Profile.md` with your common foods
3. **Set up Git remote**: Add your GitHub repo URL to `.env`
4. **Explore Dataview**: Learn Dataview queries to create custom analytics

---

## 🆘 Need Help?

- **README.md**: Full documentation
- **BUILD_STATUS.md**: Technical details
- **UNAGI_DEV_SPEC.md**: Complete specification

---

**Built with 🐍 total food awareness.**
# 🚀 UNAGI - Quick Start Guide

Get Unagi up and running in 5 minutes!

---

## 📦 For Users with Existing Logs

**If you already have nutrition logs in `Nutrition/Daily Logs/`:**

Unagi will automatically detect your existing logs on first run and offer to migrate them to the new `Unagi/` folder structure. This process is:
- ✅ **Safe**: Original files are never deleted without your confirmation
- ✅ **Validated**: Malformed files are flagged but don't block migration
- ✅ **Automatic**: Dashboard queries are updated automatically
- ✅ **Git-tracked**: All changes are committed with descriptive messages

**Migration Commands:**
- `/migrate` - Migrate logs from old structure (or find new files)
- `/migrate --cleanup` - Delete originals after you've verified everything

---
