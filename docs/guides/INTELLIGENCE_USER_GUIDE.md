# UNAGI Intelligence System - User Guide

## 🧠 Overview

UNAGI's intelligence system learns from your nutrition history to provide personalized insights, detect trends, and offer proactive suggestions. It combines:

- **Pattern Learning**: Understands your eating habits
- **Trend Detection**: Identifies changes over time
- **Proactive Suggestions**: Recommends actions based on patterns
- **Data Enrichment**: Enhances nutrition data from external sources
- **Semantic Memory**: Finds relevant past logs using AI

## 🚀 Getting Started

### 1. Initial Setup

After installing dependencies (`pip install -r requirements.txt`), the intelligence system is ready to use. No additional configuration required!

### 2. Migrate Existing Logs (One-Time)

If you have existing nutrition logs, migrate them to the intelligence system:

```bash
python migrations/migrate_logs_to_db.py
```

This will:
- Import all your markdown logs into the database
- Generate embeddings for semantic search
- Verify the migration was successful

### 3. Optional: Add API Keys

For enhanced nutrition data, add API keys to your `.env` file:

```bash
# USDA FoodData Central (free, requires signup)
USDA_API_KEY=your_key_here

# Open Food Facts (no key needed, just user agent)
OPENFOODFACTS_USER_AGENT=YourApp/1.0
```

Get USDA API key: https://fdc.nal.usda.gov/api-key-signup.html

**Note**: The system works great without API keys using local data and LLM estimates!

## 📊 Features

### 1. Pattern Learning

UNAGI learns from your history:

**Meal Patterns**
- Average meal times (e.g., "You usually have breakfast at 8:30 AM")
- Meal frequency (e.g., "You have lunch 6.5 times per week")
- Typical meals (e.g., "You often have oats for breakfast")

**Nutrient Patterns**
- Average daily intake for each nutrient
- Typical ranges (min/max)
- Consistency scores (how stable your intake is)

**Ingredient Preferences**
- Most frequently used ingredients
- Common ingredient combinations
- Preferences by meal type

**Goal Progress**
- Achievement rates (% of days you meet goals)
- Average deviation from goals
- Improving/declining trends

### 2. Trend Detection

UNAGI detects changes over time:

**Calorie Trends**
- Direction: increasing, decreasing, or stable
- Percentage change
- Recent vs. overall average

**Nutrient Trends**
- Trends for protein, carbs, fats, fiber
- Identifies significant changes (>5%)

**Meal Timing Drift**
- Detects if meals are shifting earlier or later
- Tracks drift by meal type

**Consistency Changes**
- Monitors if eating patterns are becoming more/less consistent
- Helps identify routine disruptions

**Weekly Patterns**
- Day-of-week analysis
- Weekend vs. weekday differences
- Identifies high/low days

### 3. Proactive Suggestions

UNAGI offers 7 types of suggestions:

**1. Meal Timing Suggestions** (Priority: Medium)
- Reminds you when it's your usual meal time
- Example: "It's around your usual lunch time (12:30). Ready to log your meal?"

**2. Nutrient Balance Suggestions** (Priority: High)
- Alerts on concerning nutrient trends
- Example: "Your protein intake has decreased by 18% recently. Consider adding more protein-rich foods."

**3. Ingredient Variety Suggestions** (Priority: Medium)
- Encourages dietary diversity
- Example: "You tend to use the same ingredients often. Want suggestions for adding variety?"

**4. Meal Prep Suggestions** (Priority: Low)
- Identifies meal prep opportunities
- Example: "You have breakfast 6 times per week with oats. Consider meal prepping to save time!"

**5. Hydration Reminders** (Priority: Medium)
- Time-based water intake reminders
- Example: "Morning hydration is important! Have you had water today?"

**6. Goal Adjustment Suggestions** (Priority: High)
- Recommends goal changes based on achievement
- Example: "Your protein goal might be too aggressive. You're off by 25% on average. Consider adjusting."

**7. Consistency Improvement Tips** (Priority: Medium)
- Helps build healthy routines
- Example: "Your eating patterns have become less consistent recently. Would you like tips for building routine?"

### 4. Data Enrichment

UNAGI enhances nutrition data from multiple sources:

**Source Priority** (highest to lowest confidence):
1. **Your Known Ingredients** (1.0) - From your user profile
2. **Local Indian Foods Database** (0.9) - 10 common items
3. **Open Food Facts** (0.8) - International food database
4. **USDA FoodData Central** (0.7) - US government database
5. **LLM Estimation** (0.3-0.5) - AI-powered estimates

**How It Works**:
- When you log food, UNAGI searches all sources
- Uses fuzzy matching to find best matches
- Caches results for 90 days to reduce API calls
- Falls back gracefully if APIs are unavailable

### 5. Semantic Memory

UNAGI uses AI to find relevant past logs:

**Semantic Search**:
- Understands meaning, not just keywords
- Example: "high protein days" finds logs with lots of protein, even if those words aren't used
- Combines with recent logs for best context

**Hybrid Retrieval**:
- Balances relevance with recency
- Deduplicates results
- Prioritizes recent logs when equally relevant

## 🎯 Using Intelligence Features

### In Chat Interface

**View Suggestions**:
Suggestions appear automatically at conversation start and are prioritized by importance.

**Ask About Trends**:
```
"What are my nutrition trends?"
"How has my protein intake changed?"
"Am I getting more consistent?"
```

**Ask About Patterns**:
```
"What are my eating patterns?"
"When do I usually eat breakfast?"
"What ingredients do I use most?"
```

**Request Insights**:
```
"Give me insights on my progress"
"How am I doing with my goals?"
"What should I focus on?"
```

### Understanding Confidence Scores

When UNAGI provides nutrition data, it includes a confidence score:

- **0.9-1.0**: Very High - Your known ingredients or verified local data
- **0.7-0.9**: High - External API data (USDA, OpenFoodFacts)
- **0.5-0.7**: Medium - LLM estimates with good context
- **0.3-0.5**: Low - LLM estimates with limited context
- **0.0-0.3**: Very Low - Rough estimates

Higher confidence = more accurate data.

## ⚙️ Configuration

### Enable/Disable Features

Edit `config.yaml`:

```yaml
intelligence:
  enabled: true  # Master switch
  memory_enabled: true  # Database + vector store
  suggestions_enabled: true  # Proactive suggestions
  data_enrichment_enabled: true  # External APIs
  semantic_search_results: 5  # Number of semantic results
  pattern_learning_days: 30  # Days for pattern analysis
  trend_detection_days: 30  # Days for trend analysis
```

### Adjust Thresholds

You can modify thresholds in the code:

**Trend Detection** (`intelligence/trends.py`):
- Significant change: >5% (line 67)
- Timing drift: >30 minutes (line 186)
- Consistency change: 20% (line 227)

**Suggestions** (`intelligence/suggestions.py`):
- Meal timing window: 30 minutes (line 42)
- Nutrient trend threshold: 15% (line 82)
- Ingredient repetition: 70% (line 137)

## 🔧 Troubleshooting

### "Memory components not available"

**Cause**: Missing dependencies or import errors

**Solution**:
```bash
pip install -r requirements.txt
```

### "Semantic search failed, falling back to recent logs"

**Cause**: Vector store or database issue

**Solution**:
1. Check if migration was run: `python migrations/migrate_logs_to_db.py`
2. Verify database exists: `ls -la <vault_path>/memory.db`
3. Check vector store: `ls -la <vault_path>/vector_store/`

### "API request failed"

**Cause**: Network issue or invalid API key

**Solution**:
- System automatically falls back to other sources
- Check API key in `.env` if using USDA
- Verify internet connection

### Suggestions not appearing

**Cause**: Insufficient data or suggestions disabled

**Solution**:
1. Ensure you have at least 7 days of logs
2. Check `config.yaml`: `suggestions_enabled: true`
3. Run migration if you have existing logs

## 📈 Best Practices

### 1. Consistent Logging
- Log meals regularly for better pattern learning
- Include meal times for timing analysis
- Add notes for context

### 2. Set Realistic Goals
- UNAGI will suggest adjustments if goals are too aggressive
- Aim for 80%+ achievement rate

### 3. Review Trends Weekly
- Ask about trends every week
- Act on high-priority suggestions
- Adjust goals based on progress

### 4. Use Semantic Search
- Ask specific questions about past logs
- Example: "Find days when I felt energetic"
- Helps identify what works for you

### 5. Maintain Variety
- Follow variety suggestions
- Try new ingredients
- Prevents nutritional gaps

## 🎓 Advanced Usage

### Custom Queries

You can query the database directly:

```python
from memory.database import MemoryDatabase
from config import get_settings

settings = get_settings()
db = MemoryDatabase(settings.vault_path / "memory.db")

# Get all logs with >2000 calories
async with db.get_connection() as conn:
    cursor = await conn.execute(
        "SELECT date, calories FROM daily_logs WHERE calories > 2000"
    )
    results = await cursor.fetchall()
```

### Export Intelligence Data

```python
from intelligence import PatternLearner, TrendDetector
from memory.database import MemoryDatabase

db = MemoryDatabase("path/to/memory.db")
learner = PatternLearner(db)

# Get all patterns
patterns = await learner.get_all_patterns()

# Export to JSON
import json
with open('my_patterns.json', 'w') as f:
    json.dump(patterns, f, indent=2)
```

## 🆘 Support

For issues or questions:
1. Check this guide
2. Review `INTELLIGENCE_IMPLEMENTATION_STATUS.md`
3. Check the code comments in `intelligence/`, `memory/`, and `data/` directories

## 🔮 Future Enhancements

Planned features:
- Recipe suggestions based on preferences
- Meal planning assistance
- Integration with fitness trackers
- Social features (compare with friends)
- Advanced visualizations

---

**Made with 🐍 by Bob**