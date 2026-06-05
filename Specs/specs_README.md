# 🐍 UNAGI — Specification Directory
### `specs/README.md`
**Last Updated:** 2026-05-26

This directory contains all technical specifications for Unagi. Every significant decision, fix, design, and architectural choice is documented here before it is built.

Specs are versioned alongside the product. When a new version introduces breaking changes or a major new direction, a new version folder is created. Old specs are never deleted — they are the audit trail of every decision made.

---

## Directory Structure

```
specs/
├── README.md              ← This file
├── v1/
│   ├── FIX_SPEC_v1.md     ← Bug fixes and code issues
│   ├── ARCH_SPEC_v1.md    ← Architectural improvements
│   └── UI_SPEC_v1.md      ← Textual UI design and implementation
└── (future versions)
    ├── v2/
    └── v3/
```

---

## Spec Types

As the product grows, new spec types will be added. Each type has a defined scope and purpose.

| Type | Prefix | Purpose |
|---|---|---|
| Fix Spec | `FIX_SPEC` | Catalogues bugs, logic errors, and issues in existing code. Each issue has root cause, impact, and exact fix instructions. |
| Architecture Spec | `ARCH_SPEC` | Defines structural changes to the codebase — new patterns, new modules, dependency changes. Never breaks external behaviour. |
| UI Spec | `UI_SPEC` | Defines the user interface — layout, components, interactions, styling, and implementation order. |
| Feature Spec | `FEAT_SPEC` | Defines new features to build. Includes user stories, acceptance criteria, and technical design. *(forthcoming)* |
| Test Spec | `TEST_SPEC` | Defines what to test, how to test it, and what passing looks like. Unit tests, integration tests, end-to-end scenarios. *(forthcoming)* |
| Performance Spec | `PERF_SPEC` | Defines performance targets, profiling approach, and optimization strategies. *(forthcoming)* |
| Security Spec | `SEC_SPEC` | Defines security requirements, threat model, and mitigations. Critical for the local-first, sensitive data model. *(forthcoming)* |
| Ideation Spec | `IDEA_SPEC` | Captures half-formed ideas, experiments, and explorations that aren't ready to build. A holding area, not a commitment. *(forthcoming)* |
| Migration Spec | `MIG_SPEC` | Defines how to migrate data, config, or file formats between versions. Required whenever a change breaks backward compatibility. *(forthcoming)* |

---

## v1 Specs

### `FIX_SPEC_v1.md` — Bug Fixes and Code Issues
**Status:** Ready for implementation
**Priority:** Implement before ARCH_SPEC

Catalogues 20 issues found in the initial codebase, ranging from a binary `mascot.py` file that crashes on import (🔴 critical) to singleton propagation issues (🔵 low). Each issue has:
- Root cause explanation
- Impact assessment (🔴🟡🟢🔵)
- Exact Python code to fix it
- Verification step

**Implement in this order:**
1. Group 1 (critical — get it running): F-01, F-02, F-11
2. Group 2 (core output quality): F-03, F-10, F-16
3. Group 3 (reliability): F-04, F-18, F-08
4. Group 4 (conversation quality): F-05, F-06, F-07
5. Group 5 (infrastructure): F-09, F-13
6. Group 6 (polish): F-12, F-15, F-17, F-20

**Key issues:**
- `ui/mascot.py` is a binary file — app cannot start
- System prompt suppresses coaching notes — core value prop is broken
- Vault path validation blocks first-run onboarding
- JSON parsing uses fragile regex — breaks on any non-clean LLM response
- Intent detection misroutes chat as log for many natural phrases

---

### `ARCH_SPEC_v1.md` — Architectural Improvements
**Status:** Ready for implementation
**Prerequisite:** `FIX_SPEC_v1.md` Group 1-3 complete

Defines the architectural refactor that transforms `ChatAgent` (one class doing five things) into a proper pipeline with single-responsibility components. Introduces dependency injection, a context cache, and an event system.

**New components introduced:**
- `AgentOrchestrator` — replaces `ChatAgent`, coordinates the pipeline
- `IntentClassifier` — single responsibility: log or chat?
- `DateResolver` — single responsibility: which date?
- `ContextManager` — replaces `ContextLoader`, adds caching and cache invalidation
- `NutritionPipeline` — all LLM interaction in one place
- `PromptBuilder` — class wrapper for prompts.py
- `EventBus` — decouples pipeline from UI for real-time updates
- `Container` — dependency injection wiring, replaces scattered `get_*()` singletons

**Why this matters:**
- Makes each component unit-testable in isolation
- Enables real-time progress updates in the Textual UI
- Draws the exact seams where LangGraph agents will slot in at Phase 3
- Makes the web UI (Phase 5) addable without touching agent code

**LangGraph migration path:**
`NutritionPipeline.process()` is the only method that changes in Phase 3. The orchestrator, CLI, and all infrastructure stay the same.

---

### `UI_SPEC_v1.md` — Textual UI Design
**Status:** Ready for implementation
**Prerequisite:** `ARCH_SPEC_v1.md` complete (EventBus required for status bar)

Replaces the `rich` + `prompt_toolkit` CLI with a proper Textual application. Layout is inspired by Claude Code — fixed header, scrollable chat, persistent input bar, real-time status updates.

**Layout:**
```
┌─────────────────────────────────────────────┐
│  Header: name · date · system status        │
│  Stats: today's calories · protein · deficit│
├──────────────────────────┬──────────────────┤
│  Chat Panel (70%)        │  Today Panel     │
│  Scrollable conversation │  Live stats      │
├──────────────────────────┴──────────────────┤
│  Input bar (always focused)                 │
│  Status bar (pipeline events)               │
└─────────────────────────────────────────────┘
```

**Key design decisions:**
- Dark theme (#0d1117 background, GitHub dark palette)
- Purple accent (#bc8cff) for Unagi brand and mascot
- Today Panel updates in real-time after each log write
- Notes section in chat is collapsible (hidden by default, `n` to expand)
- `--simple` flag preserves the old rich CLI as a fallback
- Startup screen shows mascot art + loading sequence before main layout

---

## Versioning Policy

### When to create a new version folder

Create `specs/v2/` when any of these are true:
- A change breaks backward compatibility with existing vault files
- A change requires migrating user data or config format
- A major new phase begins (Phase 2: RAG + SQLite, Phase 3: multi-agent, Phase 5: web UI)
- The product is distributed to users beyond the original developer

### Within a version

Within a version, specs are updated in place with a changelog section at the top. Old content is never deleted — it is moved to a `## History` section at the bottom of the file.

### Spec status values

| Status | Meaning |
|---|---|
| `Draft` | Being written, not ready for implementation |
| `Ready for implementation` | Complete, reviewed, ready to hand to Claude Code |
| `In progress` | Currently being implemented |
| `Complete` | Implemented and verified |
| `Superseded` | Replaced by a newer spec in a later version |

---

## Planned Specs

These specs are planned but not yet written. They will be created when their phase begins.

### v1 (remaining)

| Spec | Type | Trigger |
|---|---|---|
| `TEST_SPEC_v1.md` | Test | After ARCH_SPEC is implemented |
| `FEAT_SPEC_v1_git_workflow.md` | Feature | Git branch strategy, conflict resolution |

### v2 — Memory & Intelligence Phase

| Spec | Type | Description |
|---|---|---|
| `ARCH_SPEC_v2.md` | Architecture | SQLite memory layer, ChromaDB RAG pipeline |
| `FEAT_SPEC_v2_rag.md` | Feature | Semantic retrieval from log history |
| `FEAT_SPEC_v2_suggestions.md` | Feature | Proactive micronutrient suggestions, trend warnings |
| `FEAT_SPEC_v2_brand_lookup.md` | Feature | Open Food Facts API integration for brand macros |
| `PERF_SPEC_v2.md` | Performance | Context window token budgets, RAG retrieval latency |
| `MIG_SPEC_v2.md` | Migration | Migrating from flat file context to SQLite index |

### v3 — Multi-Agent Phase

| Spec | Type | Description |
|---|---|---|
| `ARCH_SPEC_v3.md` | Architecture | LangGraph introduction, agent graph design |
| `FEAT_SPEC_v3_agents.md` | Feature | ParserAgent, NutritionAgent, CoachAgent, WriterAgent |
| `FEAT_SPEC_v3_usda.md` | Feature | USDA FoodData Central API integration |
| `PERF_SPEC_v3.md` | Performance | Multi-agent latency, parallel execution strategy |

### v4 — Git & Sync Phase

| Spec | Type | Description |
|---|---|---|
| `FEAT_SPEC_v4_git.md` | Feature | Branch-per-month, conflict resolution, sync status |
| `SEC_SPEC_v4.md` | Security | PAT handling, vault encryption at rest, git history privacy |

### v5 — Web UI & Distribution Phase

| Spec | Type | Description |
|---|---|---|
| `ARCH_SPEC_v5.md` | Architecture | FastAPI backend, React frontend, shared agent core |
| `UI_SPEC_v5_web.md` | UI | Localhost web interface design |
| `FEAT_SPEC_v5_tauri.md` | Feature | Tauri desktop app packaging |
| `FEAT_SPEC_v5_mobile.md` | Feature | React Native / Flutter mobile app |
| `SEC_SPEC_v5.md` | Security | Multi-user isolation, local-first data guarantees |

### v6 — Product Phase

| Spec | Type | Description |
|---|---|---|
| `FEAT_SPEC_v6_multiuser.md` | Feature | Multi-user support, profile switching |
| `FEAT_SPEC_v6_wearables.md` | Feature | Apple Health, Garmin TDEE auto-adjustment |
| `FEAT_SPEC_v6_export.md` | Feature | PDF weekly/monthly report generation |
| `IDEA_SPEC_v6.md` | Ideation | Half-formed ideas for v6+ |

---

## How to Use This Directory

**When starting a new Claude Code session:**
1. Share the relevant spec file(s) with Claude Code
2. Tell it which step in the implementation order to start from
3. Tell it to stop and verify after each step before proceeding

**When a new issue is found:**
1. Add it to the relevant `FIX_SPEC` file with the standard format
2. Assign it a priority and ID
3. Add it to the implementation order in the correct group

**When planning a new feature:**
1. Create a `FEAT_SPEC` file in the current version folder
2. Define user story, acceptance criteria, and technical design
3. Only then hand it to Claude Code

**Golden rule:** Nothing gets built without a spec. The spec is the single source of truth. Claude Code sessions start with the spec, not with a verbal description.

---

## Quick Reference — Current Implementation Status

| Component | Spec | Status |
|---|---|---|
| Config system | — | ✅ Built (needs F-02, F-12, F-13 fixes) |
| Vault reader/writer/parser | — | ✅ Built (needs F-08, F-18 fixes) |
| LLM client | — | ✅ Built (needs F-04 json_mode addition) |
| Git manager | — | ✅ Built (needs F-09, F-13 fixes) |
| Onboarding | — | ✅ Built (needs F-16 fix) |
| System prompt | — | ✅ Built (needs F-03, F-10 fixes) |
| Intent classification | FIX F-05 | 🔴 Needs fix (keyword-based, broken) |
| Chat agent | ARCH_SPEC | 🟡 Works but needs architectural refactor |
| mascot.py | FIX F-01 | 🔴 Binary file, needs recreation |
| cli.py (rich) | — | ✅ Built |
| Textual UI | UI_SPEC_v1 | ⬜ Not started |
| AgentOrchestrator | ARCH_SPEC | ⬜ Not started |
| ContextManager (cached) | ARCH_SPEC | ⬜ Not started |
| NutritionPipeline | ARCH_SPEC | ⬜ Not started |
| EventBus | ARCH_SPEC | ⬜ Not started |
| Container (DI) | ARCH_SPEC | ⬜ Not started |

**Legend:** ✅ Complete · 🔴 Broken · 🟡 Needs refactor · ⬜ Not started

---

*Unagi Specs — Built with 🐍 total food awareness.*
