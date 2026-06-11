# 🧠 UNAGI Intelligence & Data Enrichment Specification
### *Phase 2+3 Combined: RAG, Memory, and External Data*
**Version:** 1.0
**Last Updated:** 2026-06-11
**Status:** Ready for implementation

---

## 1. Overview

This specification combines Phase 2 (Memory & Intelligence) and Phase 3 (Data Enrichment) into a single cohesive upgrade that transforms Unagi from a simple logging agent into an intelligent nutrition assistant with:

- **Semantic memory** via RAG pipeline
- **External data validation** via USDA and Open Food Facts APIs
- **Learning system** that remembers user patterns
- **Proactive intelligence** with suggestions and warnings
- **Confidence scoring** on all nutritional estimates

### Why Combine These Phases?

1. **Synergy**: RAG retrieval benefits from API-enriched data
2. **Efficiency**: Single migration of existing logs to database
3. **Coherent UX**: User sees one upgrade, not two separate changes
4. **Reduced complexity**: One architectural change instead of two

---

## 2. Architecture Overview

### Current (Phase 1) Architecture
```
User Input → LLM (with 7-day context) → .md file → Git commit
                ↑
         User Profile + Last 7 logs
```

### New (Phase 2+3) Architecture
```
User Input → Intent Detection
              ↓
         ┌────────────────────────────────────┐
         │  Context Assembly                  │
         │  - Semantic retrieval (RAG)        │
         │  - User profile                    │
         │  - Learned patterns                │
         └────────────────────────────────────┘
              ↓
         ┌────────────────────────────────────┐
         │  Data Enrichment                   │
         │  - USDA API lookup                 │
         │  - Open Food Facts API             │
         │  - Confidence scoring              │
         └────────────────────────────────────┘
              ↓
         LLM Reasoning → Structured Output
              ↓
         ┌────────────────────────────────────┐
         │  Dual Write                        │
         │  - .md file (source of truth)      │
         │  - SQLite (structured memory)      │
         │  - Vector store (embeddings)       │
         └────────────────────────────────────┘
              ↓
         Git Commit
              ↓
         ┌────────────────────────────────────┐
         │  Post-Processing                   │
         │  - Pattern learning                │
         │  - Trend analysis                  │
         │  - Proactive suggestions           │
         └────────────────────────────────────┘
```

---

## 3. Component Specifications

### 3.1 SQLite Memory Database

**Purpose**: Structured queryable memory parallel to .md files

**Schema**:
```sql
-- Daily logs table
CREATE TABLE daily_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE UNIQUE NOT NULL,
    calories INTEGER,
    maintenance INTEGER,
    deficit INTEGER,
    protein INTEGER,
    carbs INTEGER,
    fats INTEGER,
    fiber INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Meals table (normalized)
CREATE TABLE meals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_id INTEGER NOT NULL,
    meal_type TEXT NOT NULL, -- breakfast, lunch, dinner, misc
    time TEXT,
    description TEXT NOT NULL,
    FOREIGN KEY (log_id) REFERENCES daily_logs(id)
);

-- Food items table (for learning)
CREATE TABLE food_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    brand TEXT,
    serving_size TEXT,
    calories REAL,
    protein REAL,
    carbs REAL,
    fats REAL,
    fiber REAL,
    confidence_score REAL, -- 0.0 to 1.0
    source TEXT, -- 'llm', 'usda', 'openfoodfacts', 'user'
    usda_fdc_id TEXT,
    last_used DATE,
    use_count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Micronutrients table
CREATE TABLE micronutrients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_id INTEGER NOT NULL,
    nutrient_name TEXT NOT NULL,
    amount REAL,
    unit TEXT,
    status TEXT, -- 'met', 'partial', 'deficient'
    FOREIGN KEY (log_id) REFERENCES daily_logs(id)
);

-- User patterns table (learned behaviors)
CREATE TABLE user_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_type TEXT NOT NULL, -- 'common_meal', 'brand_preference', 'portion_size'
    pattern_key TEXT NOT NULL,
    pattern_value TEXT NOT NULL,
    confidence REAL,
    occurrences INTEGER DEFAULT 1,
    last_seen DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(pattern_type, pattern_key)
);

-- Trends table (for warnings)
CREATE TABLE trends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trend_type TEXT NOT NULL, -- 'sodium_creep', 'sugar_spike', 'micronutrient_gap'
    metric TEXT NOT NULL,
    start_date DATE,
    end_date DATE,
    severity TEXT, -- 'info', 'warning', 'critical'
    description TEXT,
    acknowledged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_daily_logs_date ON daily_logs(date);
CREATE INDEX idx_meals_log_id ON meals(log_id);
CREATE INDEX idx_food_items_name ON food_items(name);
CREATE INDEX idx_food_items_last_used ON food_items(last_used);
CREATE INDEX idx_micronutrients_log_id ON micronutrients(log_id);
CREATE INDEX idx_user_patterns_type_key ON user_patterns(pattern_type, pattern_key);
CREATE INDEX idx_trends_type ON trends(trend_type);
```

**Location**: `<vault_root>/Unagi/.unagi/memory.db`

**Key Operations**:
- `insert_log()` - Add new daily log
- `update_log()` - Update existing log
- `get_log(date)` - Retrieve log by date
- `query_logs(start_date, end_date)` - Range query
- `learn_food_item()` - Add/update food item knowledge
- `get_similar_foods(name)` - Fuzzy search for learned foods
- `record_pattern()` - Update user pattern
- `get_patterns(pattern_type)` - Retrieve learned patterns
- `detect_trends()` - Analyze recent data for trends

---

### 3.2 Vector Store (ChromaDB)

**Purpose**: Semantic search over historical logs for intelligent context retrieval

**Collection Schema**:
```python
{
    "id": "2026-05-25",  # Date as ID
    "embedding": [0.123, 0.456, ...],  # 384-dim vector
    "metadata": {
        "date": "2026-05-25",
        "calories": 1025,
        "protein": 140,
        "deficit": -975,
        "meal_summary": "Chicken breast, yogurt, almonds, carrots, soaked seeds",
        "notes_summary": "High protein, low carb, massive deficit",
        "micronutrient_gaps": ["Vitamin D", "Folate", "Magnesium"]
    },
    "document": "Full text of the day's log for retrieval"
}
```

**Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions, fast, good quality)

**Location**: `<vault_root>/Unagi/.unagi/chroma_db/`

**Key Operations**:
- `embed_log(log_data)` - Generate embedding for a log
- `add_to_collection(log_data)` - Add log to vector store
- `semantic_search(query, n_results=5)` - Find similar logs
- `get_relevant_context(user_query)` - Retrieve context for current query

**Retrieval Strategy**:
```python
def get_relevant_context(user_query: str, n_results: int = 5) -> List[Dict]:
    """
    Retrieve most relevant historical logs based on semantic similarity.
    
    Examples:
    - "How have I been doing with protein?" → retrieves high/low protein days
    - "What should I eat tonight?" → retrieves similar dinner patterns
    - "Am I getting enough Vitamin D?" → retrieves logs with Vitamin D data
    """
    # Embed the query
    query_embedding = embed_text(user_query)
    
    # Search vector store
    results = chroma_collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["metadatas", "documents", "distances"]
    )
    
    # Also include last 3 days for recency
    recent_logs = get_last_n_logs(3)
    
    # Combine and deduplicate
    return merge_contexts(results, recent_logs)
```

---

### 3.3 External API Integration

#### 3.3.1 USDA FoodData Central API

**Purpose**: Validate and enrich nutritional data with authoritative source

**API Endpoint**: `https://api.nal.usda.gov/fdc/v1/`

**Key Endpoints**:
- `/foods/search` - Search for foods
- `/food/{fdcId}` - Get detailed nutrition for a food

**Usage Flow**:
```python
async def lookup_usda(food_name: str, amount: str) -> Optional[Dict]:
    """
    Look up food in USDA database.
    
    Returns:
        {
            "fdc_id": "123456",
            "description": "Chicken, broilers or fryers, breast, meat only, raw",
            "nutrients": {
                "protein": 23.09,  # per 100g
                "carbs": 0.0,
                "fats": 2.59,
                "fiber": 0.0,
                # ... all micronutrients
            },
            "confidence": 0.95
        }
    """
    # Search USDA database
    search_results = await usda_client.search(food_name)
    
    # Find best match (fuzzy matching + category filtering)
    best_match = find_best_match(search_results, food_name)
    
    if best_match:
        # Get detailed nutrition
        details = await usda_client.get_food(best_match['fdcId'])
        return parse_usda_response(details, amount)
    
    return None
```

**Caching Strategy**:
- Cache USDA responses locally in SQLite `food_items` table
- TTL: 90 days (nutritional data doesn't change often)
- Cache key: `usda:{food_name}:{serving_size}`

**Rate Limiting**:
- Free tier: 1000 requests/hour
- Implement exponential backoff on rate limit errors
- Batch requests when possible

#### 3.3.2 Open Food Facts API

**Purpose**: Look up branded products (especially Indian brands)

**API Endpoint**: `https://world.openfoodfacts.org/api/v2/`

**Key Endpoints**:
- `/search` - Search products by name/barcode
- `/product/{barcode}` - Get product details

**Usage Flow**:
```python
async def lookup_openfoodfacts(product_name: str) -> Optional[Dict]:
    """
    Look up branded product in Open Food Facts.
    
    Prioritizes Indian products when user profile indicates Indian context.
    """
    # Search with country filter if applicable
    search_params = {
        "search_terms": product_name,
        "countries": "India",  # from user profile
        "fields": "product_name,nutriments,brands"
    }
    
    results = await off_client.search(**search_params)
    
    if results:
        best_match = find_best_match(results, product_name)
        return parse_off_response(best_match)
    
    return None
```

**Caching Strategy**:
- Same as USDA (90-day TTL in `food_items` table)
- Cache key: `off:{product_name}`

#### 3.3.3 Indian Food Database (Custom)

**Purpose**: Fill gaps in USDA/OFF for Indian cuisine

**Implementation**: JSON file with common Indian foods

**Location**: `data/indian_foods.json`

**Structure**:
```json
{
  "foods": [
    {
      "name": "Amul Masti Dahi",
      "brand": "Amul",
      "category": "dairy",
      "serving_size": "100g",
      "nutrients": {
        "calories": 60,
        "protein": 3.5,
        "carbs": 5.0,
        "fats": 2.5,
        "fiber": 0.0
      },
      "confidence": 0.9,
      "source": "manufacturer_label"
    },
    {
      "name": "Soaked Chia Seeds",
      "category": "seeds",
      "serving_size": "18g",
      "nutrients": {
        "calories": 70,
        "protein": 3.0,
        "carbs": 6.0,
        "fats": 4.5,
        "fiber": 6.0,
        "omega3": 3.5
      },
      "confidence": 0.85,
      "source": "usda_derived"
    }
  ]
}
```

**Lookup Priority**:
1. User's `known_ingredients` (highest confidence)
2. Indian foods database
3. Open Food Facts (branded products)
4. USDA (generic foods)
5. LLM inference (lowest confidence)

---

### 3.4 Confidence Scoring System

**Purpose**: Quantify reliability of nutritional estimates

**Confidence Levels**:
```python
CONFIDENCE_LEVELS = {
    "user_provided": 1.0,      # User explicitly provided values
    "usda_exact": 0.95,        # Exact USDA match
    "off_exact": 0.90,         # Exact Open Food Facts match
    "indian_db": 0.85,         # Indian foods database
    "usda_similar": 0.75,      # Similar USDA food
    "off_similar": 0.70,       # Similar branded product
    "llm_known": 0.60,         # LLM with high certainty
    "llm_estimated": 0.40,     # LLM estimation
    "llm_guessed": 0.20        # LLM low confidence guess
}
```

**Confidence Display**:
```markdown
notes: "● CONFIDENCE: Overall 0.82 (High). Chicken: 0.95 (USDA), Yogurt: 0.90 (Amul label), Almonds: 0.75 (USDA similar). ● ..."
```

**Confidence-Based Behavior**:
- **High (>0.8)**: No warnings, proceed normally
- **Medium (0.5-0.8)**: Note uncertainty in response
- **Low (<0.5)**: Warn user, suggest providing more details

---

### 3.5 Learning System

**Purpose**: Remember user patterns to reduce friction over time

**Pattern Types**:

#### 3.5.1 Common Meals
```python
# After 3+ occurrences of similar meal description
pattern = {
    "pattern_type": "common_meal",
    "pattern_key": "breakfast_chicken_yogurt",
    "pattern_value": {
        "description": "100g Chicken Breast (r) in 50g Amul Masti Dahi",
        "typical_time": "01:00 PM",
        "avg_calories": 180,
        "avg_protein": 28
    },
    "confidence": 0.85,
    "occurrences": 5
}
```

**Usage**: When user says "had my usual breakfast", agent retrieves this pattern

#### 3.5.2 Brand Preferences
```python
# Track which brands user consistently uses
pattern = {
    "pattern_type": "brand_preference",
    "pattern_key": "yogurt",
    "pattern_value": "Amul Masti Dahi",
    "confidence": 0.90,
    "occurrences": 12
}
```

**Usage**: When user says "yogurt", agent assumes Amul Masti Dahi

#### 3.5.3 Portion Sizes
```python
# Learn typical portion sizes
pattern = {
    "pattern_type": "portion_size",
    "pattern_key": "chicken_breast",
    "pattern_value": "450g (r)",
    "confidence": 0.75,
    "occurrences": 8
}
```

**Usage**: When user says "chicken breast" without quantity, agent suggests 450g

**Learning Trigger**:
```python
def update_patterns(log_data: Dict):
    """Called after every successful log write."""
    # Extract patterns from log
    meals = extract_meals(log_data)
    
    for meal in meals:
        # Check if this meal is similar to existing patterns
        similar_pattern = find_similar_pattern(meal)
        
        if similar_pattern:
            # Increment occurrence count
            increment_pattern(similar_pattern)
        else:
            # Create new pattern if this is 3rd occurrence
            if count_similar_meals(meal) >= 3:
                create_pattern(meal)
```

---

### 3.6 Proactive Intelligence

#### 3.6.1 Trend Detection

**Trends to Detect**:

1. **Sodium Creep**
   - Trigger: Sodium >2300mg for 3+ consecutive days
   - Severity: Warning
   - Message: "Your sodium has been elevated for 3 days (avg 2450mg). Consider reducing processed foods."

2. **Sugar Spikes**
   - Trigger: Carbs >100g with low fiber (<10g) for 2+ days
   - Severity: Info
   - Message: "Carb intake has been higher than usual. Fiber is low. Consider adding vegetables."

3. **Micronutrient Gaps**
   - Trigger: Same micronutrient marked ❌ for 5+ consecutive days
   - Severity: Warning
   - Message: "You've been low on Vitamin D for 5 days. Consider adding eggs, fatty fish, or supplementation."

4. **Protein Consistency**
   - Trigger: Protein <target for 3+ days
   - Severity: Info
   - Message: "Protein has been below target (avg 95g vs 130g goal). Tomorrow aim for an extra 35g."

5. **Calorie Drift**
   - Trigger: Actual deficit differs from target by >200 kcal for 5+ days
   - Severity: Warning
   - Message: "Your deficit has been -1100 kcal (target -750). Consider increasing intake to avoid metabolic adaptation."

**Detection Frequency**: Run after every log write, check last 7 days

**Trend Storage**: Store in `trends` table, mark as acknowledged when user responds

#### 3.6.2 Proactive Suggestions

**Suggestion Types**:

1. **Meal Recommendations**
   ```python
   # Based on current day's intake + trends
   if current_protein < target_protein * 0.7:
       suggest("You're at 80g protein with dinner left. Consider 200g chicken breast to hit your 130g target.")
   ```

2. **Micronutrient Corrections**
   ```python
   # Based on recent deficiencies
   if vitamin_d_deficient_for_days >= 5:
       suggest("To address Vitamin D: Add 2 whole eggs (20% DV) or 100g salmon (50% DV) tomorrow.")
   ```

3. **Pattern-Based Suggestions**
   ```python
   # Based on learned patterns
   if time_is("evening") and no_dinner_logged:
       common_dinner = get_pattern("common_meal", "dinner")
       suggest(f"It's 8 PM. Your usual dinner is {common_dinner}. Logging that?")
   ```

**Suggestion Timing**:
- After log write (immediate feedback)
- On chat mode queries (e.g., "What should I eat tonight?")
- Daily summary (if enabled in config)

---

## 4. Implementation Plan

### 4.1 File Structure (New Files)

```
unagi/
├── memory/
│   ├── __init__.py
│   ├── database.py          ← SQLite operations
│   ├── embeddings.py        ← Text embedding generation
│   ├── vector_store.py      ← ChromaDB wrapper
│   └── retrieval.py         ← Semantic search logic
├── data/
│   ├── __init__.py
│   ├── usda_client.py       ← USDA API wrapper
│   ├── openfoodfacts_client.py  ← Open Food Facts API
│   ├── indian_foods.py      ← Indian food database loader
│   ├── confidence.py        ← Confidence scoring
│   └── cache.py             ← API response caching
├── intelligence/
│   ├── __init__.py
│   ├── learning.py          ← Pattern learning system
│   ├── trends.py            ← Trend detection
│   └── suggestions.py       ← Proactive suggestions
├── data/
│   └── indian_foods.json    ← Indian food database
└── migrations/
    ├── __init__.py
    └── migrate_logs_to_db.py  ← One-time migration script
```

### 4.2 Modified Files

```
agent/
├── context.py               ← Replace fixed 7-day with semantic retrieval
├── chat.py                  ← Add suggestion/warning display
└── llm.py                   ← Add API lookup before LLM call

vault/
├── writer.py                ← Dual-write to .md + database
└── parser.py                ← Extract data for database

config/
└── settings.py              ← Add database, API, vector store config
```

### 4.3 New Dependencies

```txt
# Add to requirements.txt
chromadb>=0.4.22            # Vector database
sentence-transformers>=2.3.1  # Embedding model
aiohttp>=3.9.0              # Async HTTP for APIs
cachetools>=5.3.2           # In-memory caching
fuzzywuzzy>=0.18.0          # Fuzzy string matching
python-levenshtein>=0.23.0  # Fast fuzzy matching
```

### 4.4 Configuration Updates

**Add to `config.yaml`**:
```yaml
memory:
  database_path: .unagi/memory.db
  vector_store_path: .unagi/chroma_db
  embedding_model: sentence-transformers/all-MiniLM-L6-v2
  context_retrieval_count: 5  # Number of similar logs to retrieve

apis:
  usda:
    enabled: true
    api_key: ${USDA_API_KEY}  # Optional, higher rate limit with key
    cache_ttl_days: 90
  openfoodfacts:
    enabled: true
    cache_ttl_days: 90
  indian_foods:
    enabled: true
    database_path: data/indian_foods.json

intelligence:
  learning:
    enabled: true
    min_occurrences_for_pattern: 3
  trends:
    enabled: true
    detection_window_days: 7
  suggestions:
    enabled: true
    proactive_mode: true  # Show suggestions without being asked
```

**Add to `.env`**:
```env
# Optional: USDA API key for higher rate limits
USDA_API_KEY=your_key_here
```

---

## 5. Migration Strategy

### 5.1 Backward Compatibility

**Critical**: Existing .md files remain the source of truth. Database is supplementary.

**Migration Script**: `migrations/migrate_logs_to_db.py`

```python
async def migrate_existing_logs():
    """
    One-time migration of all existing .md logs to database and vector store.
    
    Safe to run multiple times (idempotent).
    """
    # Get all log files
    log_files = list_all_log_files()
    
    print(f"Found {len(log_files)} log files to migrate...")
    
    for log_file in log_files:
        # Parse .md file
        log_data = parse_log_file(log_file)
        
        # Insert into database
        await db.insert_log(log_data)
        
        # Generate embedding and add to vector store
        embedding = generate_embedding(log_data)
        await vector_store.add(log_data, embedding)
        
        # Extract and learn patterns
        await learning.extract_patterns(log_data)
    
    print("✅ Migration complete!")
```

**Run Migration**:
```bash
python -m migrations.migrate_logs_to_db
```

### 5.2 Dual-Write Strategy

**On Every Log Write**:
```python
async def write_log(log_data: Dict):
    """Write log to both .md file and database."""
    # 1. Write .md file (source of truth)
    md_path = write_markdown_file(log_data)
    
    # 2. Write to database
    await db.insert_or_update_log(log_data)
    
    # 3. Update vector store
    embedding = generate_embedding(log_data)
    await vector_store.upsert(log_data, embedding)
    
    # 4. Learn patterns
    await learning.update_patterns(log_data)
    
    # 5. Detect trends
    trends = await trends.detect(log_data)
    
    # 6. Git commit (as before)
    git_commit(md_path, log_data)
    
    return md_path, trends
```

### 5.3 Graceful Degradation

**If database is corrupted/missing**:
- Agent falls back to reading .md files directly
- Logs warning but continues to function
- Offers to rebuild database from .md files

**If vector store is corrupted/missing**:
- Agent falls back to last N days context (Phase 1 behavior)
- Logs warning
- Offers to rebuild embeddings

**If APIs are down**:
- Agent falls back to LLM inference
- Logs lower confidence scores
- Continues to function normally

---

## 6. Testing Strategy

### 6.1 Unit Tests

```python
# tests/test_memory.py
def test_database_insert_log()
def test_database_query_logs()
def test_vector_store_semantic_search()
def test_embedding_generation()

# tests/test_data.py
def test_usda_api_lookup()
def test_openfoodfacts_lookup()
def test_indian_foods_lookup()
def test_confidence_scoring()

# tests/test_intelligence.py
def test_pattern_learning()
def test_trend_detection()
def test_suggestion_generation()
```

### 6.2 Integration Tests

```python
# tests/test_integration.py
async def test_full_log_write_with_intelligence():
    """Test complete flow: input → APIs → LLM → dual write → learning."""
    
async def test_semantic_retrieval():
    """Test that relevant logs are retrieved for queries."""
    
async def test_migration():
    """Test migration of existing logs to database."""
```

### 6.3 Manual Testing Checklist

- [ ] Migration script successfully imports all existing logs
- [ ] Semantic search returns relevant logs for various queries
- [ ] USDA API lookup works for common foods
- [ ] Open Food Facts lookup works for branded products
- [ ] Confidence scores are calculated correctly
- [ ] Patterns are learned after 3+ occurrences
- [ ] Trends are detected correctly (sodium, protein, micronutrients)
- [ ] Suggestions are relevant and helpful
- [ ] Graceful degradation works when APIs are down
- [ ] Database corruption recovery works
- [ ] Performance is acceptable (log write <2 seconds)

---

## 7. Performance Considerations

### 7.1 Embedding Generation

- **Model**: `all-MiniLM-L6-v2` (fast, 384 dims)
- **Time**: ~50ms per log on CPU
- **Strategy**: Generate embeddings async, don't block log write

### 7.2 API Calls

- **Caching**: Aggressive caching (90-day TTL)
- **Batching**: Batch multiple food lookups when possible
- **Timeout**: 5-second timeout per API call
- **Fallback**: Always have LLM fallback

### 7.3 Database Queries

- **Indexes**: All critical queries have indexes
- **Connection pooling**: Use SQLite connection pool
- **Async**: All database operations are async

### 7.4 Vector Search

- **ChromaDB**: In-memory for speed
- **Query time**: <100ms for 5 results
- **Collection size**: ~1000 logs = ~50MB

**Expected Performance**:
- Log write: <2 seconds (including all intelligence)
- Semantic search: <200ms
- API lookup (cached): <50ms
- API lookup (uncached): <2 seconds

---

## 8. User Experience Changes

### 8.1 Enhanced Responses

**Before (Phase 1)**:
```
You: Log today's food: 450g chicken breast, 150g yogurt, carrots

Unagi: ✅ Logged 2026-05-25. Calories: 1025 | Protein: 140g | Deficit: -975
```

**After (Phase 2+3)**:
```
You: Log today's food: 450g chicken breast, 150g yogurt, carrots

Unagi: 🔍 Looking up nutritional data...
       ✅ Chicken breast: USDA verified (95% confidence)
       ✅ Yogurt: Amul Masti Dahi (your usual brand)
       ✅ Carrots: USDA verified (90% confidence)
       
       ✅ Logged 2026-05-25. Calories: 1025 | Protein: 140g | Deficit: -975
       
       💡 Insight: You've been low on Vitamin D for 5 days. Consider adding 
       2 eggs tomorrow (20% DV) or 100g salmon (50% DV).
       
       📊 Pattern learned: This is your 4th time having chicken + yogurt for 
       dinner. I'll remember this as a common meal.
```

### 8.2 Intelligent Context

**Before (Phase 1)**:
```
You: How have I been doing with protein?

Unagi: [Analyzes last 7 days]
       Your protein average is 125g over the last week. Target is 130g.
       You're slightly below target.
```

**After (Phase 2+3)**:
```
You: How have I been doing with protein?

Unagi: [Semantic search finds all protein-related logs]
       Your protein average is 125g over the last 30 days. Target is 130g.
       
       📈 Trend: You hit target on 18/30 days (60%).
       📉 Low days: Usually when you skip breakfast (8 occurrences).
       💡 Suggestion: Your breakfast typically adds 30g protein. When you 
       skip it, you rarely recover. Consider a quick protein source like 
       2 boiled eggs (12g) on busy mornings.
```

### 8.3 Proactive Warnings

**New Feature**:
```
You: Log today's food: [high sodium meal]

Unagi: ✅ Logged 2026-05-25. Calories: 1200 | Protein: 110g | Deficit: -800
       
       ⚠️  Sodium Alert: Today's sodium is 2650mg. This is your 3rd consecutive 
       day above 2300mg (avg 2550mg). Consider reducing processed foods or 
       adding more fresh vegetables tomorrow.
```

---

## 9. Success Metrics

### 9.1 Quantitative Metrics

- **Confidence Score**: Average confidence >0.75 for all logs
- **API Hit Rate**: >60% of foods found in USDA/OFF
- **Pattern Learning**: >80% of common meals learned after 3 occurrences
- **Trend Detection**: 100% of 5+ day trends detected
- **Performance**: Log write <2 seconds, search <200ms

### 9.2 Qualitative Metrics

- User reports fewer clarifying questions from agent
- User finds suggestions helpful and actionable
- User trusts nutritional data more (due to confidence scores)
- User appreciates proactive warnings

---

## 10. Implementation Steps

### Step 1: Database & Memory (Week 1)
1. Create SQLite schema
2. Implement database operations
3. Write migration script
4. Test migration with existing logs

### Step 2: Vector Store & RAG (Week 1-2)
1. Set up ChromaDB
2. Implement embedding generation
3. Implement semantic search
4. Replace fixed 7-day context with semantic retrieval
5. Test retrieval quality

### Step 3: API Integration (Week 2)
1. Implement USDA client
2. Implement Open Food Facts client
3. Create Indian foods database
4. Implement caching layer
5. Test API lookups

### Step 4: Confidence Scoring (Week 2)
1. Implement confidence calculation
2. Update log format to include confidence
3. Test confidence accuracy

### Step 5: Learning System (Week 3)
1. Implement pattern extraction
2. Implement pattern storage
3. Implement pattern retrieval
4. Test pattern learning

### Step 6: Intelligence (Week 3)
1. Implement trend detection
2. Implement suggestion generation
3. Update chat responses to include insights
4. Test intelligence features

### Step 7: Integration & Testing (Week 4)
1. Wire all components together
2. Update agent/context.py
3. Update vault/writer.py for dual-write
4. Run full integration tests
5. Performance optimization
6. Documentation

**Total Estimated Time**: 4 weeks (part-time) or 2 weeks (full-time)

---

## 11. Rollout Strategy

### Phase A: Silent Mode (Week 1)
- Deploy database and vector store
- Run migration
- Dual-write enabled but intelligence features disabled
- Monitor for issues

### Phase B: Intelligence Beta (Week 2)
- Enable learning and trend detection
- Show insights in responses
- Collect user feedback

### Phase C: Full Rollout (Week 3)
- Enable all features
- Update documentation
- Announce to users

### Phase D: Optimization (Week 4)
- Performance tuning based on real usage
- Fix edge cases
- Improve suggestion quality

---

## 12. Future Enhancements (Post-v1)

- **Multi-user support**: Separate databases per user
- **Export/import**: Export learned patterns, import from other users
- **Custom trend rules**: User-defined trend detection
- **Meal planning**: Suggest meals for tomorrow based on trends
- **Recipe database**: Learn and suggest full recipes
- **Wearable integration**: Auto-adjust TDEE based on activity data

---

*Built with 🧠 intelligence and 📊 data.*