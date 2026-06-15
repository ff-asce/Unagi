# UNAGI v2.0 Release Notes

**Release Date:** June 16, 2026  
**Branch:** `unagi-spec-v1-intelligence`  
**Status:** ✅ Production Ready

---

## 🎉 What's New in v2.0

### 🧠 Intelligence System (Complete)

The biggest update to UNAGI yet! A complete intelligence system that learns from your eating habits and provides personalized insights.

#### Memory Layer
- **SQLite Database**: Structured storage with 7 tables for efficient querying
- **ChromaDB Vector Store**: Semantic search across your entire nutrition history
- **Sentence Transformers**: 384-dimensional embeddings using all-MiniLM-L6-v2
- **Hybrid Retrieval**: Combines semantic similarity with recency for optimal context

#### Data Enrichment
- **USDA FoodData Central**: Access to 400,000+ foods with detailed nutrition data
- **OpenFoodFacts**: International product database for packaged foods
- **Indian Foods Database**: Curated collection of 10 common Indian dishes
- **Confidence Scoring**: Multi-factor accuracy assessment (0.0-1.0 scale)
- **Smart Caching**: 30-day TTL with database persistence

#### Intelligence Layer
- **Pattern Learning**: Automatically learns your eating habits, preferences, and goals
  - Meal patterns (timing, frequency, composition)
  - Nutrient patterns (protein intake, calorie trends)
  - Ingredient preferences (favorite foods, portions)
  - Goal patterns (deficit consistency, macro targets)

- **Trend Detection**: Identifies patterns over 7-day and 30-day windows
  - Calorie trends (increasing, decreasing, stable)
  - Macro trends (protein, carbs, fats)
  - Timing trends (meal schedule consistency)
  - Consistency trends (logging frequency)

- **Proactive Suggestions**: 7 types of personalized recommendations
  - Meal suggestions based on patterns
  - Nutrient recommendations for deficiencies
  - Goal reminders and progress updates
  - Timing suggestions for optimal nutrition
  - Variety suggestions to diversify diet
  - Hydration reminders
  - General nutrition tips

### 🔧 Technical Improvements

#### Architecture
- **Dependency Injection**: Clean container-based architecture
- **Dual-Write System**: Markdown remains source of truth, database supplementary
- **Graceful Degradation**: System works without memory/APIs if unavailable
- **Custom RAG Pipeline**: No LangChain dependencies, built from scratch

#### Bug Fixes
- Fixed CLI orchestrator interface to handle string responses
- Added memory path helpers to Settings class
- Initialized memory components in container
- Resolved async/sync operation mismatches
- Fixed database schema issues (missing columns, SQL syntax)
- Fixed VaultWriter initialization parameters

#### Testing
- ✅ Memory layer tests (database, embeddings, vector store)
- ✅ Data enrichment tests (USDA, OpenFoodFacts, confidence scoring)
- ✅ Intelligence layer tests (learning, trends, suggestions)
- ✅ Integration tests (application startup, component initialization)

### 📚 Documentation Overhaul

#### New Structure
```
docs/
├── README.md           # Documentation index
├── guides/             # User guides
│   ├── QUICKSTART.md
│   ├── GEMINI_SETUP.md
│   └── INTELLIGENCE_USER_GUIDE.md
├── implementation/     # Development docs
│   └── INTELLIGENCE_IMPLEMENTATION_STATUS.md
└── archive/           # Historical documents
    ├── ARCH_REFACTOR_PROGRESS.md
    ├── BUILD_STATUS.md
    └── RAG_INTERVIEW_PREP.md
```

#### Updated Documentation
- Comprehensive README.md with quick start
- Complete intelligence user guide
- Implementation status tracking
- API setup guides
- Testing documentation

---

## 📊 Statistics

### Code Changes
- **Files Added**: 20 new files (memory, data, intelligence layers)
- **Files Modified**: 7 core files (context, writer, settings, container, CLI)
- **Lines of Code**: 2,492+ lines across intelligence system
- **Tests**: 3 test suites, all passing
- **Commits**: 10 commits in this release

### Implementation Breakdown
- Memory Layer: 4 files, ~800 lines
- Data Enrichment: 6 files, ~900 lines
- Intelligence Layer: 3 files, ~1,036 lines
- Tests: 3 files, ~400 lines
- Documentation: 4 files, ~1,500 lines

---

## 🚀 Getting Started

### For New Users
1. Follow the [Quick Start Guide](docs/guides/QUICKSTART.md)
2. Set up your [Gemini API key](docs/guides/GEMINI_SETUP.md)
3. Run `python3 main.py` and complete onboarding
4. Start logging your meals!

### For Existing Users
1. Pull the latest changes: `git pull origin unagi-spec-v1-intelligence`
2. Install new dependencies: `pip install -r requirements.txt`
3. (Optional) Run migration script to populate database from existing logs
4. Continue using UNAGI as normal - intelligence features activate automatically!

### Optional: API Keys for Enhanced Features
- **USDA API Key**: Get from https://fdc.nal.usda.gov/api-key-signup.html
- Add to `.env`: `USDA_API_KEY=your_key_here`
- Enables access to 400K+ foods with detailed nutrition data

---

## 🔮 What's Next

### Planned for v2.1
- [ ] Display suggestions in chat UI
- [ ] Additional unit tests for edge cases
- [ ] Performance optimizations for large datasets
- [ ] Export/import functionality for data portability

### Future Enhancements
- [ ] Web UI for visualization
- [ ] Mobile app integration
- [ ] Recipe database and meal planning
- [ ] Integration with fitness trackers
- [ ] Multi-user support for families

---

## 🙏 Acknowledgments

This release represents a major milestone in UNAGI's development. Special thanks to:
- **Gemini 2.0 Flash** for LLM capabilities
- **ChromaDB** for vector storage
- **Sentence Transformers** for embeddings
- **USDA FoodData Central** for nutrition data
- **Open Food Facts** for product database

---

## 📝 Migration Notes

### Breaking Changes
None! This release is fully backward compatible.

### Database Migration
If you have existing logs, run the migration script to populate the database:
```bash
python3 -c "from migration.migrate_logs import migrate_existing_logs; migrate_existing_logs()"
```

### Configuration Changes
New optional settings in `config.yaml`:
```yaml
intelligence:
  enabled: true
  memory_enabled: true
  suggestions_enabled: true
  data_enrichment_enabled: true
  semantic_search_results: 5
  pattern_learning_days: 30
  trend_detection_days: 30
```

---

## 🐛 Known Issues

None at this time! All tests passing, application stable.

---

## 📄 License

Private project - All rights reserved.

---

**Built with 🐍 total food awareness.**

*"Unagi is a state of total awareness. Only by achieving true Unagi can you be prepared for any danger that may befall you."* — Ross Geller