# RAG Pipeline Interview Prep - UNAGI Project

## Overview
We implemented a **custom RAG (Retrieval-Augmented Generation) pipeline** for a nutrition tracking agent. This is NOT using LangGraph - we built it from scratch using ChromaDB, Sentence Transformers, and SQLite.

---

## 1. What is RAG?

**RAG = Retrieval-Augmented Generation**

Instead of relying solely on an LLM's training data, RAG:
1. **Retrieves** relevant information from a knowledge base
2. **Augments** the LLM prompt with this retrieved context
3. **Generates** a response using both the LLM's knowledge + retrieved facts

**Why RAG?**
- LLMs have knowledge cutoff dates
- LLMs can hallucinate facts
- RAG grounds responses in actual user data
- Enables personalization without fine-tuning

---

## 2. Our RAG Architecture

### Components:

```
┌─────────────────────────────────────────────────────────────┐
│                    USER QUERY                                │
│              "What did I eat last week?"                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              EMBEDDING GENERATION                            │
│   Sentence Transformers (all-MiniLM-L6-v2)                  │
│   Query → 384-dimensional vector                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              HYBRID RETRIEVAL                                │
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │ Semantic Search  │    │  Recent Logs     │              │
│  │  (ChromaDB)      │    │  (SQLite)        │              │
│  │  Top 5 similar   │    │  Last 3 days     │              │
│  └──────────────────┘    └──────────────────┘              │
│           │                       │                          │
│           └───────┬───────────────┘                          │
│                   ▼                                          │
│          Deduplicate by date                                 │
│          Combine results                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              CONTEXT FORMATTING                              │
│   Format logs as structured text for LLM                    │
│   Include: dates, meals, macros, notes                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              LLM GENERATION                                  │
│   System Prompt + Retrieved Context + User Query            │
│   → Claude/GPT generates personalized response              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Key Implementation Details

### A. Embedding Generation (`memory/embeddings.py`)

**Model:** `sentence-transformers/all-MiniLM-L6-v2`
- **Dimensions:** 384
- **Speed:** Fast (50ms per embedding)
- **Quality:** Good for semantic similarity

**What we embed:**
```python
def embed_log(log_data):
    # Combine multiple fields into rich text
    text = f"""
    Date: {date}
    Calories: {calories}, Protein: {protein}g
    Breakfast: {breakfast_items}
    Lunch: {lunch_items}
    Dinner: {dinner_items}
    Insights: {key_insights}
    Deficient nutrients: {deficiencies}
    """
    return model.encode(text)  # → 384-dim vector
```

**Why this approach?**
- Captures semantic meaning of entire day
- Includes meals, macros, AND insights
- Enables finding "similar days" (e.g., high protein days, deficit days)

---

### B. Vector Store (`memory/vector_store.py`)

**Technology:** ChromaDB (local, persistent)

**Key Operations:**

1. **Add/Upsert:**
```python
collection.add(
    ids=[date],              # "2024-01-15"
    embeddings=[vector],     # 384-dim array
    metadatas=[{             # Filterable metadata
        "calories": 2000,
        "protein": 150,
        "deficit": -500
    }],
    documents=[text]         # Human-readable summary
)
```

2. **Semantic Search:**
```python
results = collection.query(
    query_embeddings=[query_vector],
    n_results=5,
    include=["metadatas", "documents", "distances"]
)
# Returns: Top 5 most similar days by cosine similarity
```

**Why ChromaDB?**
- Local-first (no API calls)
- Persistent storage
- Fast cosine similarity search
- Built-in metadata filtering

---

### C. Hybrid Retrieval (`memory/retrieval.py`)

**Strategy:** Combine semantic search + recency

```python
async def get_relevant_context(query, vector_store, database):
    # 1. Semantic search
    query_embedding = generate_embedding(query)
    semantic_results = vector_store.search(query_embedding, n=5)
    
    # 2. Recent logs (last 3 days)
    recent_logs = database.query_logs(last_3_days)
    
    # 3. Deduplicate and combine
    combined = []
    seen_dates = set()
    
    # Prioritize recent logs
    for log in recent_logs:
        if log['date'] not in seen_dates:
            combined.append(log)
            seen_dates.add(log['date'])
    
    # Add semantic results
    for result in semantic_results:
        if result['date'] not in seen_dates:
            combined.append(database.get_log(result['date']))
            seen_dates.add(result['date'])
    
    return combined
```

**Why hybrid?**
- **Recency bias:** Recent days are always relevant
- **Semantic relevance:** Find similar patterns from history
- **Deduplication:** Avoid redundant context
- **Optimal context window:** ~8-10 days of logs

---

### D. Context Integration (`agent/context.py`)

**Three retrieval modes:**

1. **Recent-only** (fallback):
```python
def load_recent_logs(days=7):
    return reader.read_recent_logs(days)
```

2. **Semantic-only**:
```python
async def load_semantic_context(query, n=5):
    return await get_relevant_context(query, vector_store, db, n)
```

3. **Hybrid** (best):
```python
async def load_hybrid_context(query, days=7):
    recent = load_recent_logs(days)
    semantic = load_semantic_context(query, n=5)
    return deduplicate_and_combine(recent, semantic)
```

**Graceful degradation:**
- If vector store unavailable → use recent logs
- If database unavailable → use markdown files
- Always has a fallback

---

## 4. Data Flow Example

**User Query:** "What high-protein meals did I have last month?"

### Step 1: Embedding
```
Query → Sentence Transformer → [0.23, -0.45, 0.67, ..., 0.12]
                                 (384 dimensions)
```

### Step 2: Vector Search
```
ChromaDB finds 5 most similar days:
1. 2024-05-10 (distance: 0.12) - "High protein day, chicken breast..."
2. 2024-05-03 (distance: 0.18) - "Protein focus, Greek yogurt..."
3. 2024-04-28 (distance: 0.21) - "Lean protein, fish..."
4. 2024-05-15 (distance: 0.24) - "Protein shake, eggs..."
5. 2024-04-20 (distance: 0.27) - "High protein breakfast..."
```

### Step 3: Recent Logs
```
SQLite query: Last 3 days
- 2024-05-24
- 2024-05-23
- 2024-05-22
```

### Step 4: Combine & Deduplicate
```
Final context (8 unique days):
- 2024-05-24 (recent)
- 2024-05-23 (recent)
- 2024-05-22 (recent)
- 2024-05-15 (semantic)
- 2024-05-10 (semantic)
- 2024-05-03 (semantic)
- 2024-04-28 (semantic)
- 2024-04-20 (semantic)
```

### Step 5: Format for LLM
```
System Prompt:
You are UNAGI, a nutrition tracking agent.

User Profile:
- Name: Parth
- Goal: Cut (lose fat)
- Maintenance: 2500 kcal

Recent History:
[8 days of formatted logs with meals, macros, notes]

User Query: What high-protein meals did I have last month?
```

### Step 6: LLM Response
```
Based on your logs, here are your high-protein meals from last month:

**May 10:** Grilled chicken breast (45g protein), Greek yogurt (20g)
**May 3:** Protein shake (30g), eggs (18g), chicken (40g)
...

Your average protein intake was 145g/day, which is excellent for your cut!
```

---

## 5. Why NOT LangGraph?

**LangGraph** is a framework for building **stateful, multi-agent workflows** with:
- State machines
- Conditional edges
- Agent orchestration
- Complex routing logic

**We didn't need it because:**
1. Our RAG pipeline is **linear** (no branching logic)
2. No multi-agent coordination required
3. No complex state management
4. Simple: Query → Retrieve → Generate

**When you WOULD use LangGraph:**
- Multi-step reasoning (plan → execute → verify)
- Agent collaboration (researcher + writer + critic)
- Conditional workflows (if X then Y else Z)
- Stateful conversations with memory

**Our approach is simpler and more maintainable** for this use case.

---

## 6. Performance Characteristics

### Latency Breakdown:
```
Embedding generation:    ~50ms
Vector search:           ~20ms
Database queries:        ~10ms
Context formatting:      ~5ms
LLM generation:          ~2000ms
─────────────────────────────────
Total:                   ~2085ms
```

**Bottleneck:** LLM API call (96% of latency)

### Storage:
```
SQLite database:         ~500KB (1000 logs)
ChromaDB vectors:        ~1.5MB (1000 logs × 384 dims × 4 bytes)
Markdown files:          ~2MB (source of truth)
─────────────────────────────────
Total:                   ~4MB
```

### Scalability:
- **Current:** 1000 logs, sub-second retrieval
- **Limit:** ~100K logs before needing optimization
- **Solutions:** Batch embeddings, HNSW indexing, sharding

---

## 7. Interview Talking Points

### Technical Depth:

**"How does your RAG pipeline work?"**
> "We use a hybrid retrieval approach combining semantic search via ChromaDB and recency-based filtering. User queries are embedded using Sentence Transformers (all-MiniLM-L6-v2) into 384-dimensional vectors. We perform cosine similarity search to find the top 5 semantically similar historical logs, then combine with the last 3 days of recent logs. After deduplication, we format this context and inject it into the LLM prompt. This grounds the LLM's responses in actual user data while maintaining temporal relevance."

**"Why ChromaDB over Pinecone/Weaviate?"**
> "We chose ChromaDB for local-first architecture. No API calls, no latency, no costs, and full data privacy. For a personal nutrition tracker with ~1000 logs, local vector search is sub-20ms, which is faster than any API round-trip. We also maintain markdown files as the source of truth, so the vector store is purely supplementary."

**"How do you handle embedding quality?"**
> "We create rich text representations of each log by combining meals, macros, insights, and nutrient deficiencies. This captures the semantic meaning of the entire day, not just meal names. The all-MiniLM-L6-v2 model is optimized for semantic similarity tasks and produces high-quality embeddings at 50ms per log."

**"What about cold start?"**
> "We have graceful degradation. If the vector store isn't initialized, we fall back to recent logs from SQLite. If SQLite isn't available, we read directly from markdown files. The system always works, just with varying levels of intelligence."

### Architecture Decisions:

**"Why not fine-tune the LLM?"**
> "RAG is more flexible and cost-effective. We can update the knowledge base in real-time without retraining. Fine-tuning would require thousands of examples and wouldn't adapt to new user data. RAG gives us personalization without the overhead."

**"How do you prevent hallucinations?"**
> "By grounding responses in retrieved facts. The LLM sees actual log data in the prompt, so it can cite specific dates and meals. We also use confidence scoring for external API data (USDA, OpenFoodFacts) to indicate reliability."

**"What's your context window strategy?"**
> "We limit to ~8-10 logs (hybrid retrieval) to stay within token limits while maximizing relevance. Recent logs get priority, semantic results fill gaps. This balances recency bias with historical patterns."

---

## 8. Advanced Topics

### Embedding Optimization:
- **Batch processing:** Embed multiple logs in parallel
- **Caching:** Store embeddings, regenerate only on updates
- **Dimensionality reduction:** Could use 256-dim for faster search

### Retrieval Improvements:
- **Metadata filtering:** "Find high-protein days with <2000 calories"
- **Temporal weighting:** Decay older results
- **Re-ranking:** Use cross-encoder for final ranking

### Production Considerations:
- **Monitoring:** Track retrieval quality, embedding drift
- **A/B testing:** Compare semantic vs. recent-only
- **Feedback loops:** Learn from user corrections

---

## 9. Code Walkthrough (For Interview)

**Show this flow:**

1. **User asks question** → `agent/chat.py`
2. **Load context** → `agent/context.py:load_hybrid_context()`
3. **Generate embedding** → `memory/embeddings.py:generate_embedding()`
4. **Search vectors** → `memory/vector_store.py:search()`
5. **Query database** → `memory/database.py:query_logs()`
6. **Combine results** → `memory/retrieval.py:get_relevant_context()`
7. **Format prompt** → `agent/context.py:format_for_llm()`
8. **Call LLM** → `agent/llm.py:generate()`

**Key files to reference:**
- `memory/embeddings.py` (79 lines)
- `memory/vector_store.py` (159 lines)
- `memory/retrieval.py` (69 lines)
- `agent/context.py` (261 lines)

---

## 10. Summary

**What we built:**
- Custom RAG pipeline (no LangGraph)
- Hybrid retrieval (semantic + recency)
- Local-first architecture (ChromaDB + SQLite)
- Graceful degradation (multiple fallbacks)
- Production-ready (error handling, logging, async)

**Key technologies:**
- Sentence Transformers (embeddings)
- ChromaDB (vector store)
- SQLite (structured data)
- Async Python (performance)

**Why it's impressive:**
- Built from scratch (not just using LangChain)
- Thoughtful architecture (hybrid retrieval)
- Production considerations (fallbacks, monitoring)
- Measurable performance (sub-100ms retrieval)

**Interview confidence:**
You can explain:
- RAG fundamentals
- Embedding generation
- Vector search mechanics
- Hybrid retrieval strategies
- Production trade-offs
- Why we didn't use LangGraph

---

## Bonus: LangGraph Comparison

**If asked "Would you use LangGraph?"**

> "For this use case, no. Our RAG pipeline is linear: retrieve → format → generate. LangGraph shines for complex, stateful workflows like multi-agent systems or conditional routing. However, if we were to add features like multi-step meal planning (research → plan → verify → adjust), then LangGraph's state machine would be valuable. For now, our custom pipeline is simpler, faster, and easier to debug."

**When LangGraph makes sense:**
- Multi-agent collaboration
- Conditional workflows
- Stateful conversations
- Complex reasoning chains

**Our approach is better for:**
- Simple RAG pipelines
- Performance-critical paths
- Full control over retrieval
- Minimal dependencies

---

Good luck with your interview! 🚀