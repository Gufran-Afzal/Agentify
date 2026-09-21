# Adaptive Content Intelligence

**Adaptive Content Intelligence** is an ecommerce content intelligence and content operations platform. It continuously analyzes an ecommerce store's product catalog, keyword search demand signals, and existing published content to uncover high-converting content opportunities, generate structured briefs and rich drafts, and manage a complete human editorial review, approval, and publishing pipeline.

---

## Complete Editorial Workflow

```text
Store Catalog & Keywords
          ↓
  Research Run (Autonomous Opportunity Engine)
          ↓
Content Opportunities (Evidence & Demand Scoring)
          ↓
  Human Editorial Approval / Rejection
          ↓
Structured Content Brief (Search Intent & Audience Outline)
          ↓
  Draft Generation (Extensible AI / Deterministic Engine)
          ↓
  Human In-Place Editing (Title, Intro, Body, Conclusion)
          ↓
  Human Draft Approval / Rejection
          ↓
  Atomic Publishing Pipeline (Safe Slug Generation & Collision Resolution)
          ↓
  Live Customer-Facing Article (/blog/{slug})
```

---

## Architectural Highlights

- **Modular Backend (`backend/app/`)**:
  - `database/`: Centralized SQLite connection management enforcing `PRAGMA foreign_keys = ON`, automatic schema migration, and seed data initialization.
  - `schemas/`: Comprehensive Pydantic v2 validation models across all resources.
  - `services/`:
    - `content_analysis_service.py`: Reusable text normalization, stopword filtering, and duplicate topic detection.
    - `opportunity_service.py`: Transparent scoring formula:
      $$\text{Score} = \text{Product Relevance} + \text{Search Demand Signal} + \text{Keyword Relevance} - \text{Duplicate Content Penalty}$$
    - `research_service.py`: State-controlled research run execution and persistence.
    - `brief_service.py`: Generation of structured editorial blueprints.
    - `draft_service.py`: In-place draft editing validation and approval/rejection state transitions.
    - `publishing_service.py`: Atomic publishing transactions, unique slug generation with collision handling (`-2`, `-3`), and unpublishing.
    - `generators/`: Pluggable `ContentGenerator` interface with `MockContentGenerator` (production-grade deterministic output) and `AIContentGenerator` (extensible adapter for OpenAI, Anthropic, Gemini, or local LLMs).
  - `api/`: Dedicated FastAPI routers for Products, Keywords, Content/Store Profile, Research, Opportunities, Briefs, Drafts, Publishing, and Dashboard Metrics.
  - `utils/`: Safe slug generator, text tokenizers, and UTC ISO 8601 date formatters.
- **Root Compatibility (`app.py`)**: Re-exports the modular FastAPI `app` so running `uvicorn app:app --reload` functions seamlessly without breaking legacy commands.
- **Modern Frontend (`frontend/`)**:
  - React 19 + TypeScript + Vite with a modern, glassmorphic dark-mode design system.
  - Sidebar navigation, live KPI counters, workflow pipeline visualization, responsive data tables, full in-place markdown draft editor, and public blog viewer.

---

## Project Structure

```text
d:\AI\Agentify\
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI app factory, CORS, lifespan, exception handlers
│   │   ├── config.py                   # Environment settings
│   │   ├── database/
│   │   │   ├── connection.py           # SQLite connection with foreign keys
│   │   │   ├── schema.py               # Schema DDL and non-destructive column migrations
│   │   │   └── seed.py                 # Default seed data for demo store
│   │   ├── schemas/                    # Pydantic validation models
│   │   ├── services/                   # Business logic and opportunity scoring engine
│   │   ├── api/                        # FastAPI endpoint routers
│   │   └── utils/                      # Reusable slug and text utilities
│   └── tests/                          # Pytest automated test suite (11 test suites)
├── frontend/                           # React 19 + TypeScript + Vite dashboard
│   ├── src/
│   │   ├── components/                 # Sidebar, Header, Modal, StatusBadge
│   │   ├── pages/                      # Dashboard, Products, Keywords, Research, Opportunities,
│   │   │                               # Briefs, Drafts, Published, PublicArticle
│   │   ├── api/                        # Typed client for backend communication
│   │   └── index.css                   # Custom CSS design system
│   ├── package.json
│   └── vite.config.ts
├── app.py                              # Backwards-compatible root export
├── .env.example                        # Environment variables template
└── README.md
```

---

## Installation & Setup

### 1. Prerequisites
- **Python 3.10+** (tested on Python 3.14)
- **Node.js 18+** & **npm**

### 2. Backend Setup
```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install backend dependencies (if needed)
pip install -r requirements.txt # or: pip install fastapi uvicorn pydantic pytest httpx
```

### 3. Frontend Setup
```bash
cd frontend
npm install
```

---

## Environment Configuration

Copy `.env.example` to `.env` if custom configuration is needed:

```bash
cp .env.example .env
```

| Variable | Description | Default |
| :--- | :--- | :--- |
| `DATABASE_URL` | SQLite database file path | `adaptive_content.db` |
| `AI_PROVIDER` | AI provider identifier (`mock`, `openai`, `anthropic`, `gemini`) | `mock` |
| `AI_API_KEY` | API key for external LLM generation | `""` |
| `ENVIRONMENT` | Environment name | `development` |

---

## Running the Application

### Start the Backend
From the project root:
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```
- API root: `http://localhost:8000/`
- Interactive Swagger documentation: `http://localhost:8000/docs`

### Start the Frontend Dashboard
From the `frontend/` directory:
```bash
npm run dev
```
Open `http://localhost:5173/` in your browser.

---

## API Overview

### Products
- `GET /products` — List store products.
- `POST /products` — Add a new product to catalog.
- `GET /products/{id}` — Get single product.
- `PUT /products/{id}` — Update product attributes.
- `DELETE /products/{id}` — Remove product from catalog.

### Keywords (Search Demand Signals)
- `GET /keywords` — List target keywords and estimated monthly search volumes.
- `POST /keywords` — Add a keyword query and search demand.
- `PUT /keywords/{id}` — Update keyword or search volume.
- `DELETE /keywords/{id}` — Remove keyword.

### Store Content & Profile
- `GET /content` (or `/existing-content`) — List existing published articles.
- `POST /existing-content` — Add existing article to catalog audit index.
- `DELETE /existing-content/{id}` — Delete article from audit index.
- `GET /store-profile` — Overview of categories, product counts, and descriptions.

### Research Engine
- `POST /research-runs` — Initialize a new research scan.
- `GET /research-runs` — View history of research scans.
- `GET /research-runs/{run_id}` — Get details of a single research run.
- `POST /research-runs/{run_id}/execute` — Run opportunity discovery engine.
- `GET /research-runs/{run_id}/opportunities` — Get opportunities discovered by a run.

### Content Opportunities
- `GET /opportunities` — List opportunities (supports `?status=pending|approved|rejected`).
- `GET /opportunities/{id}` — Get single opportunity with transparent scoring evidence.
- `POST /opportunities/{id}/approve` — Approve pending opportunity.
- `POST /opportunities/{id}/reject` — Reject pending opportunity.
- `POST /opportunities/{id}/create-brief` — Transform approved opportunity into a Content Brief.

### Content Briefs
- `GET /content-briefs` — List all content briefs.
- `GET /content-briefs/{id}` — Retrieve single brief with search intent, audience, and outline.
- `POST /briefs/{id}/generate-draft` — Generate structured draft from brief.

### Content Drafts & Editor
- `GET /content-drafts` — List all content drafts.
- `GET /content-drafts/{id}` — Get single draft with title, intro, body, conclusion.
- `PUT /content-drafts/{id}` — Edit draft in-place (allowed only for status `'draft'`).
- `POST /content-drafts/{id}/approve` — Approve draft for publication.
- `POST /content-drafts/{id}/reject` — Reject draft.
- `POST /content-drafts/{draft_id}/publish` — Atomically publish approved draft.

### Publishing & Public Articles
- `GET /published-content` — List published content records (supports `?status=published|unpublished`).
- `GET /published-content/{id}` — Get single published content record.
- `POST /published-content/{id}/unpublish` — Unpublish article.
- `GET /blog/{slug}` — Customer-facing public article route (returns 404 for unpublished articles).

### Operations Dashboard
- `GET /dashboard/stats` — High-level KPI aggregations for active products, keywords, runs, opportunities, briefs, drafts, and publications.

---

## Running Automated Tests

Run the full automated pytest suite:
```bash
pytest backend/tests -v
```

### Test Coverage Summary
- `test_products_keywords.py`: Product and keyword CRUD, validation, and collision handling.
- `test_content_analysis.py`: Text normalization, stopword filtering, and duplicate article detection.
- `test_research.py`: Run creation, execution, status transitions, and duplicate execution guards.
- `test_opportunities.py`: Approval/rejection state machines, invalid transition rejection (409).
- `test_briefs.py`: Brief generation from approved opportunities, duplicate brief prevention (409).
- `test_drafts.py`: Draft generation from valid briefs, in-place draft editing, edit locking on approved/rejected drafts.
- `test_publishing.py`: Publish validation, safe slug generation, slug collision resolution (`-2`), public blog view, and unpublishing.
- `test_e2e_workflow.py`: Comprehensive end-to-end integration test simulating the entire workflow.

---

## Verification & Deliverables

All 10 project stages have been implemented, verified, and tested:
1. **Audited and fixed backend**: Foreign keys enabled (`PRAGMA foreign_keys = ON`), connection leaks resolved, transaction safety implemented, state transition validation enforced (409 Conflict), and duplicate handling resolved.
2. **Modular Architecture**: Code refactored into `database`, `schemas`, `services`, `api`, `utils`, and generator abstractions while maintaining root `app.py` backward compatibility.
3. **Database & Schema**: Persistent SQLite tables for `products`, `keywords`, `existing_content`, `research_runs`, `content_opportunities`, `content_briefs`, `content_drafts`, and `published_content`.
4. **Publishing Pipeline**: Safe slug generator with collision resolution, atomic publishing transactions, unpublishing, and public `/blog/{slug}` endpoint.
5. **Modern Dashboard**: React 19 + TypeScript + Vite frontend with glassmorphic dark-mode design system, live stats, and complete workflow management.
