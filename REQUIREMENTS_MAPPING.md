# 📑 ARCNICAL - REQUIREMENTS MAPPING INDEX
**From: Arcnical Prototype Requirements Document v2.0**  
**Status:** Extracted & mapped  
**Last Updated:** April 10, 2026

---

## 🎯 KEY FACTS AT A GLANCE

| Item | Value |
|------|-------|
| **Project Name** | Arcnical (CLI binary: `arcnical`) |
| **Working Directory** | `.arcnical/` |
| **Package Name** | `arcnical` |
| **Target Delivery** | 15 April 2026 (7 calendar days / 5 working days) |
| **Team Size** | 2 engineers (Backend A, Surface B) |
| **Total Budget** | 87 engineer-hours (80h + 5h buffer) |
| **Tooling** | Cursor + Claude (Sonnet 4.6 default, Opus 4.6 for deep mode) |
| **Python Version** | 3.11+ |
| **Schema Version** | 2.0 (bumped from v1.0) |
| **Tool Version** | 0.2.0 |

---

## 📊 REQUIREMENTS SUMMARY BY CATEGORY

| Category | Count | P0 | P1 | P2 | Est. Hours | Owner |
|----------|-------|----|----|----|-----------:|-------|
| **FR-QUAL** (Target Qualification) | 3 | 2 | 1 | 0 | 3 | A |
| **FR-ING** (Ingestion) | 6 | 4 | 1 | 1 | 4 | A |
| **FR-STR** (Structural Analysis) | 7 | 5 | 0 | 2 | 17 | A |
| **FR-HEU** (Heuristics) | 7 | 4 | 1 | 2 | 10 | A |
| **FR-LAY** (Layered Execution) | 6 | 4 | 2 | 0 | 3 | A+B |
| **FR-SEC** (Security) | 4 | 2 | 0 | 2 | 2 | A |
| **FR-ARCH** (Architecture Detection) | 7 | 0 | 4 | 3 | 4 | B |
| **FR-REV** (Review Agent / L4) | 8 | 6 | 2 | 0 | 9 | A |
| **FR-REP** (Reporting) | 7 | 4 | 2 | 1 | 4 | B |
| **FR-CLI** (CLI Tool) | 9 | 6 | 1 | 2 | 4 | B |
| **FR-UI** (Streamlit Viewer) | 8 | 4 | 2 | 2 | 4 | B |
| **FR-EVA** (Evaluation Harness) | 4 | 2 | 2 | 0 | 4 | B |
| **Docs** | N/A | 1 | 0 | 0 | 2 | B |
| **Project Setup** | N/A | 1 | 0 | 0 | 3 | A+B |
| **Integration & Buffer** | N/A | 1 | 0 | 0 | 9 | A+B |
| **---** | **---** | **---** | **---** | **---** | **---** | **---** |
| **TOTAL** | **87** | **72h (83%)** | **7h (8%)** | **8h (9%)** | **87h** | — |

---

## 🚀 NEXT STEPS: SESSION #2 PLAN

**Goal:** Create project structure + freeze schema

**Tasks:**
1. [ ] Create GitHub repository structure
2. [ ] Setup Python project skeleton (pyproject.toml, uv.lock)
3. [ ] Create Pydantic schema v2.0 (JSON output) - **FROZEN BY EOD**
4. [ ] Create layer config files (arcnical/layers/)
5. [ ] Setup typing + linting (ruff + mypy)
6. [ ] Create first test file (schema validation)

**Deliverable:** Ready-to-code repository; schema locked so parallel work can begin

---

**Document Status:** Ready for session-based work  
**Memory System:** Active (Claude Memory + this tracker + session templates)  
