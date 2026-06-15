# 🐍 UNAGI — Total Food Awareness

**Version:** 2.0 (Intelligence System Complete)  
**Status:** ✅ Production Ready

A local-first, AI-powered nutrition agent that acts as your personalized nutritionist and food log manager. Named after Ross Geller's concept of "Unagi" — total awareness.

**NEW in v2.0:** 🧠 Complete intelligence system with semantic memory, pattern learning, trend detection, and proactive suggestions!

---

## 🚀 Quick Start

```bash
# 1. Clone and setup
git clone <your-repo-url>
cd unagi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Add your LLM_API_KEY to .env

# 3. Run
python3 main.py
```

**📖 Full Guide:** See [docs/guides/QUICKSTART.md](docs/guides/QUICKSTART.md)

---

## ✨ Key Features

### 🧠 Intelligence System (NEW in v2.0)
- **Semantic Memory**: ChromaDB vector store for contextual search across your entire history
- **Pattern Learning**: Automatically learns your eating habits, preferences, and goals
- **Trend Detection**: Identifies nutrition trends and patterns over time
- **Smart Suggestions**: Proactive recommendations based on your data and goals
- **Data Enrichment**: USDA FoodData Central (400K+ foods) + OpenFoodFacts + Indian foods database

### 🎯 Core Features
- **Natural Language Logging**: Just describe what you ate in plain English
- **Obsidian Integration**: Markdown-first, vault-native with perfect formatting
- **Git Sync**: Automatic version control with descriptive commit messages
- **Privacy-First**: All data stays local on your machine
- **29 Micronutrients**: Comprehensive nutrition tracking beyond just macros
- **TDEE Calculation**: Personalized calorie targets based on your profile

---

## 📁 Project Structure

```
unagi/
├── agent/              # AI agent logic (orchestrator, intent, context)
├── vault/              # Obsidian file management (reader, writer, parser)
├── git_manager/        # Git operations (commits, push)
├── onboarding/         # First-run setup and ingredient seeding
├── config/             # Configuration management
├── memory/             # 🧠 Database & vector store (SQLite + ChromaDB)
├── data/               # 🧠 Data enrichment (USDA, OpenFoodFacts, Indian foods)
├── intelligence/       # 🧠 Learning, trends, suggestions
├── migration/          # Migration scripts for existing logs
├── ui/                 # CLI interface (Rich-based)
├── tests/              # Unit tests
├── docs/               # 📚 Documentation
│   ├── guides/         # User guides and tutorials
│   ├── implementation/ # Implementation status and notes
│   └── archive/        # Historical documents
├── Specs/              # Technical specifications
├── main.py             # Entry point
├── requirements.txt    # Dependencies
├── config.yaml         # Non-secret settings
└── .env.example        # Environment template
```

---

## 📚 Documentation

### For Users
- **[Quick Start Guide](docs/guides/QUICKSTART.md)** - Get up and running in 5 minutes
- **[Intelligence User Guide](docs/guides/INTELLIGENCE_USER_GUIDE.md)** - Complete feature walkthrough
- **[Gemini API Setup](docs/guides/GEMINI_SETUP.md)** - Configure your LLM API key

### For Developers
- **[Architecture Specification](Specs/v1/ARCH_SPEC_v1.md)** - Overall system design
- **[Intelligence Specification](Specs/v1/INTELLIGENCE_SPEC_v1.md)** - Intelligence system architecture
- **[Implementation Status](docs/implementation/INTELLIGENCE_IMPLEMENTATION_STATUS.md)** - Current progress
- **[Testing Guide](tests/README.md)** - Running tests

**📖 Full Documentation Index:** [docs/README.md](docs/README.md)

---

## 🔧 Setup Instructions

### Prerequisites
- Python 3.11+
- Git
- Obsidian (for viewing the vault)

### Installation

1. **Clone the repository:**
```bash
git clone <your-repo-url>
cd unagi
```

2. **Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or on Windows: venv\Scripts\activate
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
  root_path: "/path/to/your/ObsidianVault"
```

### Get API Key (Gemini - Free Tier)
1. Visit: https://aistudio.google.com/app/apikey
2. Create an API key
3. Add to `.env`: `LLM_API_KEY=your_key_here`

**Optional:** Add USDA API key for enhanced food data (see [docs/guides/INTELLIGENCE_USER_GUIDE.md](docs/guides/INTELLIGENCE_USER_GUIDE.md))

---

## 🎯 How It Works

### 1. Natural Language Input
```
You: "I had 2 eggs and toast for breakfast, then chicken and rice for lunch"
```

### 2. AI Processing
- Intent classification (logging vs. chat)
- Date resolution (today, yesterday, last Tuesday, etc.)
- Nutrition extraction using LLM + enrichment APIs
- Confidence scoring for accuracy

### 3. Structured Output
Creates/updates markdown file with YAML frontmatter:
```yaml
---
date: 2026-05-25
calories: 1250
protein: 118
carbs: 95
fats: 35
breakfast: "2 Eggs, 2 Slices Whole Wheat Toast"
lunch: "200g Chicken Breast, 150g White Rice"
---
```

### 4. Intelligence Layer
- Stores in SQLite database for structured queries
- Generates embeddings for semantic search
- Learns patterns from your eating habits
- Detects trends in your nutrition
- Provides proactive suggestions

### 5. Git Sync
```
[unagi] create: 2026-05-25 — Breakfast + Lunch logged. Cal: 1250 | P: 118g | Deficit: -750
```

---

## 🧪 Testing

Run the test suite:
```bash
# All tests
python3 -m pytest tests/ -v

# Specific test modules
python3 -m pytest tests/test_memory.py -v
python3 -m pytest tests/test_data_enrichment.py -v
python3 -m pytest tests/test_intelligence.py -v
```

**Current Status:** ✅ All tests passing (3/3 modules)

---

## 🏗️ Architecture Highlights

### Dependency Injection
- Single `Container` class manages all dependencies
- No global state or singletons outside container
- Easy to test with mock dependencies

### Dual-Write System
- Markdown files remain the source of truth
- Database provides structured queries
- Vector store enables semantic search
- Graceful degradation if memory systems unavailable

### Custom RAG Pipeline
- No LangChain or LangGraph dependencies
- Built from scratch for full control
- Hybrid retrieval (semantic + recency)
- Optimized for nutrition tracking use case

### Privacy-First
- All data stays local on your machine
- No cloud storage or external services (except LLM API)
- Git sync is optional and user-controlled

---

## 📊 What's Tracked

### Macronutrients
- Calories, Protein, Carbs, Fats, Fiber

### 29 Micronutrients (in exact order)
Vitamin A, Vitamin C, Vitamin D, Vitamin E, Vitamin K, B1 (Thiamine), B2 (Riboflavin), B3 (Niacin), B5 (Pantothenic Acid), B6 (Pyridoxine), B7 (Biotin), B9 (Folate), B12 (Cobalamin), Choline, Calcium, Chromium, Copper, Iodine, Iron, Magnesium, Manganese, Molybdenum, Phosphorus, Potassium, Selenium, Sodium, Zinc, Omega-3, Omega-6

### Intelligence Metrics
- Eating patterns (meal timing, frequency)
- Nutrient trends (7-day, 30-day averages)
- Goal progress (calorie deficit, protein targets)
- Ingredient preferences and portions

---

## 🤝 Contributing

This is a personal project, but suggestions and bug reports are welcome! Please open an issue on GitHub.

---

## 📄 License

Private project - All rights reserved.

---

## 🙏 Acknowledgments

- Built with [Gemini 2.0 Flash](https://ai.google.dev/) for LLM capabilities
- Powered by [ChromaDB](https://www.trychroma.com/) for vector storage
- Uses [Sentence Transformers](https://www.sbert.net/) for embeddings
- Nutrition data from [USDA FoodData Central](https://fdc.nal.usda.gov/) and [Open Food Facts](https://world.openfoodfacts.org/)

---

**Built with 🐍 total food awareness.**

*"Unagi is a state of total awareness. Only by achieving true Unagi can you be prepared for any danger that may befall you."* — Ross Geller
