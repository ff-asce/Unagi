# UNAGI Architecture Diagrams

This document contains all architecture diagrams for the UNAGI project using Mermaid syntax. GitHub will automatically render these as images.

---

## 1. Overall System Architecture

```mermaid
graph TB
    subgraph "User Interface"
        CLI[CLI Interface<br/>Rich Terminal UI]
    end
    
    subgraph "Agent Layer"
        Orchestrator[Agent Orchestrator<br/>Main Controller]
        Intent[Intent Classifier<br/>Chat vs Log]
        DateResolver[Date Resolver<br/>Natural Language Dates]
        Context[Context Manager<br/>Load History]
        Pipeline[Nutrition Pipeline<br/>Extract Nutrition Data]
    end
    
    subgraph "Intelligence System"
        Memory[Memory Layer<br/>Database + Vector Store]
        DataEnrich[Data Enrichment<br/>USDA + OpenFoodFacts]
        Intelligence[Intelligence Layer<br/>Learning + Trends + Suggestions]
    end
    
    subgraph "Storage Layer"
        Vault[Vault Writer/Reader<br/>Markdown Files]
        Git[Git Manager<br/>Version Control]
        DB[(SQLite Database<br/>Structured Memory)]
        Vector[(ChromaDB<br/>Vector Store)]
    end
    
    subgraph "External Services"
        LLM[LLM API<br/>Gemini/Claude/Groq]
        USDA[USDA FoodData<br/>400K+ Foods]
        OFF[OpenFoodFacts<br/>Products DB]
    end
    
    CLI --> Orchestrator
    Orchestrator --> Intent
    Orchestrator --> DateResolver
    Orchestrator --> Context
    Orchestrator --> Pipeline
    
    Context --> Memory
    Pipeline --> DataEnrich
    Pipeline --> Intelligence
    
    Memory --> DB
    Memory --> Vector
    DataEnrich --> USDA
    DataEnrich --> OFF
    
    Orchestrator --> Vault
    Vault --> Git
    Vault --> DB
    Vault --> Vector
    
    Pipeline --> LLM
    Intent --> LLM
    
    style Intelligence fill:#e1f5ff
    style Memory fill:#e1f5ff
    style DataEnrich fill:#e1f5ff
```

---

## 2. Intelligence System Architecture

```mermaid
graph TB
    subgraph "Memory Layer"
        DB[(SQLite Database<br/>7 Tables)]
        Vector[(ChromaDB<br/>Vector Store)]
        Embeddings[Sentence Transformers<br/>all-MiniLM-L6-v2]
        Retrieval[Hybrid Retrieval<br/>Semantic + Recency]
    end
    
    subgraph "Data Enrichment Layer"
        USDA[USDA Client<br/>FoodData Central]
        OFF[OpenFoodFacts Client<br/>International Products]
        Indian[Indian Foods DB<br/>10 Common Dishes]
        Confidence[Confidence Scorer<br/>Multi-factor 0.0-1.0]
        Cache[Smart Cache<br/>30-day TTL]
    end
    
    subgraph "Intelligence Layer"
        Learning[Pattern Learner<br/>Habits + Preferences]
        Trends[Trend Detector<br/>7-day + 30-day]
        Suggestions[Suggestion Engine<br/>7 Types]
    end
    
    subgraph "Integration"
        Context[Context Manager<br/>Semantic Context]
        Writer[Vault Writer<br/>Dual-Write System]
    end
    
    Writer --> DB
    Writer --> Vector
    Writer --> Embeddings
    
    Context --> Retrieval
    Retrieval --> DB
    Retrieval --> Vector
    Retrieval --> Embeddings
    
    Learning --> DB
    Trends --> DB
    Suggestions --> Learning
    Suggestions --> Trends
    
    USDA --> Cache
    OFF --> Cache
    Cache --> DB
    
    USDA --> Confidence
    OFF --> Confidence
    Indian --> Confidence
    
    style Learning fill:#ffe1e1
    style Trends fill:#ffe1e1
    style Suggestions fill:#ffe1e1
    style DB fill:#e1ffe1
    style Vector fill:#e1ffe1
```

---

## 3. Data Flow - Food Logging

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Orchestrator
    participant Intent
    participant Pipeline
    participant DataEnrich
    participant LLM
    participant Writer
    participant Memory
    participant Git
    
    User->>CLI: "I had 2 eggs for breakfast"
    CLI->>Orchestrator: process(input)
    Orchestrator->>Intent: classify(input)
    Intent->>LLM: Classify intent
    LLM-->>Intent: "LOG_FOOD"
    Intent-->>Orchestrator: Intent result
    
    Orchestrator->>Pipeline: extract_nutrition(input)
    Pipeline->>DataEnrich: enrich_food_data("eggs")
    DataEnrich->>LLM: Get nutrition estimate
    LLM-->>DataEnrich: Nutrition data
    DataEnrich-->>Pipeline: Enriched data + confidence
    Pipeline-->>Orchestrator: Structured log data
    
    Orchestrator->>Writer: write_daily_log(data)
    Writer->>Writer: Write markdown file
    Writer->>Memory: Store in database
    Writer->>Memory: Generate embedding
    Writer->>Memory: Store in vector store
    Writer->>Git: Commit changes
    Git-->>Writer: Commit successful
    Writer-->>Orchestrator: Write successful
    
    Orchestrator-->>CLI: Success message
    CLI-->>User: "✅ Logged 2 eggs..."
```

---

## 4. Data Flow - Intelligence & Suggestions

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Orchestrator
    participant Context
    participant Memory
    participant Intelligence
    participant Suggestions
    
    User->>CLI: "What should I eat?"
    CLI->>Orchestrator: process(input)
    Orchestrator->>Context: load_context()
    
    Context->>Memory: get_recent_logs(7 days)
    Memory-->>Context: Recent logs
    Context->>Memory: semantic_search(query)
    Memory-->>Context: Similar logs
    Context-->>Orchestrator: Combined context
    
    Orchestrator->>Intelligence: analyze_patterns()
    Intelligence->>Memory: Query eating patterns
    Memory-->>Intelligence: Pattern data
    Intelligence-->>Orchestrator: Learned patterns
    
    Orchestrator->>Intelligence: detect_trends()
    Intelligence->>Memory: Query nutrition trends
    Memory-->>Intelligence: Trend data
    Intelligence-->>Orchestrator: Detected trends
    
    Orchestrator->>Suggestions: generate_suggestions(patterns, trends)
    Suggestions-->>Orchestrator: Prioritized suggestions
    
    Orchestrator-->>CLI: Response with suggestions
    CLI-->>User: "Based on your patterns..."
```

---

## 5. Database Schema

```mermaid
erDiagram
    DAILY_LOGS ||--o{ MEALS : contains
    MEALS ||--o{ MEAL_INGREDIENTS : has
    MEAL_INGREDIENTS }o--|| FOOD_ITEMS : references
    
    DAILY_LOGS {
        int id PK
        date date UK
        int calories
        int maintenance
        int deficit
        int protein
        int carbs
        int fats
        int fiber
        int water_ml
        real weight_kg
        timestamp created_at
        timestamp updated_at
    }
    
    MEALS {
        int id PK
        int log_id FK
        string meal_type
        string time
        text description
    }
    
    FOOD_ITEMS {
        int id PK
        string name
        string brand
        string serving_size
        real calories
        real protein
        real carbs
        real fats
        real fiber
        real confidence_score
        string source
        string usda_fdc_id
        date last_used
        int use_count
        timestamp created_at
    }
    
    MEAL_INGREDIENTS {
        int id PK
        int meal_id FK
        int food_item_id FK
        real quantity
        string unit
    }
    
    LEARNED_PATTERNS {
        int id PK
        string pattern_type
        json pattern_data
        real confidence
        timestamp learned_at
        timestamp last_seen
    }
    
    USER_PREFERENCES {
        int id PK
        string key UK
        json value
        timestamp updated_at
    }
    
    API_CACHE {
        int id PK
        string cache_key UK
        json response_data
        timestamp cached_at
        timestamp expires_at
    }
```

---

## 6. Component Dependencies

```mermaid
graph LR
    subgraph "Core"
        Config[Config/Settings]
        Container[DI Container]
    end
    
    subgraph "Agent"
        Orchestrator[Orchestrator]
        Intent[Intent Classifier]
        DateResolver[Date Resolver]
        Context[Context Manager]
        Pipeline[Nutrition Pipeline]
    end
    
    subgraph "Intelligence"
        Memory[Memory Layer]
        DataEnrich[Data Enrichment]
        Intelligence[Intelligence Layer]
    end
    
    subgraph "Storage"
        Vault[Vault Reader/Writer]
        Git[Git Manager]
    end
    
    subgraph "UI"
        CLI[CLI Interface]
    end
    
    subgraph "External"
        LLM[LLM Client]
    end
    
    Container --> Config
    Container --> Orchestrator
    Container --> Memory
    Container --> Vault
    Container --> Git
    Container --> LLM
    
    Orchestrator --> Intent
    Orchestrator --> DateResolver
    Orchestrator --> Context
    Orchestrator --> Pipeline
    Orchestrator --> Vault
    Orchestrator --> Git
    
    Context --> Memory
    Context --> Vault
    
    Pipeline --> DataEnrich
    Pipeline --> Intelligence
    Pipeline --> LLM
    
    Vault --> Memory
    
    CLI --> Container
    
    style Container fill:#ffe1e1
    style Memory fill:#e1f5ff
    style Intelligence fill:#e1f5ff
```

---

## 7. Deployment Architecture

```mermaid
graph TB
    subgraph "User's Machine"
        subgraph "UNAGI Application"
            App[Python Application<br/>main.py]
            Venv[Virtual Environment<br/>Python 3.11+]
        end
        
        subgraph "Local Storage"
            Vault[Obsidian Vault<br/>Markdown Files]
            DB[(SQLite Database<br/>memory.db)]
            Vector[(ChromaDB<br/>vector_store/)]
            Git[Git Repository<br/>.git/]
        end
        
        subgraph "Obsidian"
            Obsidian[Obsidian App<br/>Vault Viewer]
        end
    end
    
    subgraph "External Services"
        LLM[LLM API<br/>Gemini/Claude]
        USDA[USDA API<br/>Optional]
        OFF[OpenFoodFacts<br/>Optional]
        GitHub[GitHub<br/>Optional Backup]
    end
    
    App --> Venv
    App --> Vault
    App --> DB
    App --> Vector
    App --> Git
    
    Obsidian --> Vault
    
    App -.->|API Calls| LLM
    App -.->|Optional| USDA
    App -.->|Optional| OFF
    Git -.->|Optional Push| GitHub
    
    style App fill:#e1f5ff
    style Vault fill:#ffe1e1
    style DB fill:#e1ffe1
    style Vector fill:#e1ffe1
```

---

## Notes

- All diagrams use Mermaid syntax and will render automatically on GitHub
- Blue boxes indicate intelligence system components
- Green boxes indicate storage components
- Red boxes indicate core application components
- Dotted lines indicate optional connections
- Solid lines indicate required connections
