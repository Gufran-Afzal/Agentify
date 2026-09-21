# Agentify — Complete System Map

---

## Part 1 — Executive Explanation

### What is Agentify?
Agentify is an internal content intelligence and editorial production platform for ecommerce businesses. It acts like an automated marketing strategist and copywriter working inside your online store.

### Who is it for?
It is built for ecommerce brand owners, marketing managers, and editorial teams who want to generate qualified organic customer traffic by answering shopper questions on search engines.

### What problem does it solve?
Publishing blog content for an online store usually requires manually researching keyword tools, guessing what shoppers want, checking that previous articles do not cover the same topic, writing briefs in spreadsheets, drafting copy in word processors, and copy-pasting into a CMS. Agentify unifies this entire disconnected process into a single, guided operations dashboard.

### What does the user actually do?
Inside Agentify, the user manages their product catalog, triggers automated research scans, reviews proposed topic ideas, approves or rejects them, edits generated article drafts, and clicks to publish approved articles.

### What does the system do automatically?
Agentify automatically:
1. Audits product catalog descriptions against target search queries.
2. Checks existing articles to prevent duplicate topics.
3. Calculates a 100-point opportunity score based on demand signals.
4. Generates structured editorial briefs with search intent and audience outlines.
5. Produces formatted article drafts with section headings and disclaimers.
6. Generates clean web URLs (slugs) and resolves duplicate naming collisions.

### Where does the human make decisions?
The human user makes three mandatory decisions:
1. **Opportunity Approval**: Deciding whether a topic idea matches store strategy.
2. **Draft Editing**: Refining title, introduction, body copy, and conclusion in the editorial studio.
3. **Publication Approval**: Formally approving and publishing the article.

Nothing is published to the public web without explicit human sign-off.

### What is the final output?
The final output is a live, customer-facing, SEO-optimized article published at a clean public web address (such as `/blog/what-is-niacinamide-serum-good-for`) complete with product recommendations and disclaimers.

---

## Part 2 — The Complete User Journey

### Complete Workflow Diagram
```text
  [Products Catalog] + [Search Keywords] + [Existing Content]
                          │
                          ▼
                  [1. Research Run]
                          │ (Engine analyzes demand & checks duplicates)
                          ▼
              [2. Content Opportunities]
                          │
                          ▼
            [3. Human Editorial Approval] ──(Rejected)──▶ [Archived / Stopped]
                          │ (Approved)
                          ▼
                [4. Content Brief]
                          │ (Structured outline & target audience)
                          ▼
               [5. Draft Generation]
                          │ (Article drafted with headings)
                          ▼
                [6. Human In-Place Edit]
                          │ (Title, Intro, Body, Conclusion edited)
                          ▼
             [7. Human Draft Approval] ──(Rejected)──▶ [Locked / Stopped]
                          │ (Approved)
                          ▼
                 [8. Publishing]
                          │ (Slug generated; published_content created)
                          ▼
               [9. Live Public Article] (/blog/{slug})
```

---

### Step-by-Step Stage Breakdown

#### Stage 1: Store Data & Keywords
- **What enters**: Product names, categories, descriptions, target search queries, and existing articles.
- **What happens**: Data is stored and indexed in SQLite.
- **Database records**: `products`, `keywords`, `existing_content`.
- **API endpoints**: `GET/POST /products`, `GET/POST /keywords`, `GET/POST /existing-content`.
- **Frontend screens**: `ProductsPage.tsx`, `KeywordsPage.tsx`.
- **What user sees**: Tables of merchandise and tracked keyword search volumes.
- **What can go wrong**: Empty catalog or zero keywords stops research from discovering topics.
- **What happens next**: User goes to Research page to initiate a scan.

#### Stage 2: Research Run
- **What enters**: Catalog items and search demand signals.
- **What happens**: The research engine creates a run session, normalizes text, strips stopwords, checks for duplicate articles, matches keywords, and computes scores.
- **Database records**: `research_runs` (status: `created` $\rightarrow$ `running` $\rightarrow$ `completed`).
- **API endpoints**: `POST /research-runs`, `POST /research-runs/{id}/execute`.
- **Frontend screen**: `ResearchPage.tsx`.
- **What user sees**: "Run Research" button with spinner, run history cards, and completed execution status.
- **What can go wrong**: Database connection failure or re-executing an already completed run (HTTP 409).
- **What happens next**: System displays discovered opportunities.

#### Stage 3: Opportunity Discovery
- **What enters**: Scored suggestions from the research engine.
- **What happens**: Opportunities are saved to the database with confidence ratings and audit evidence.
- **Database records**: `content_opportunities` (status: `pending`).
- **API endpoints**: `GET /research-runs/{id}/opportunities`, `GET /opportunities`.
- **Frontend screens**: `ResearchPage.tsx`, `OpportunitiesPage.tsx`.
- **What user sees**: Topic cards showing title, search volume, confidence badge (`high`, `medium`, `low`), rationale, and evidence bullet points.
- **What can go wrong**: Topics overlapping with existing articles are heavily penalized and suppressed.
- **What happens next**: Editor chooses to Approve or Reject.

#### Stage 4: Human Opportunity Approval
- **What enters**: A `pending` opportunity.
- **What happens**: Editor reviews signals and makes a decision.
- **Database records**: `content_opportunities` status changes to `approved` or `rejected`.
- **API endpoints**: `POST /opportunities/{id}/approve` or `POST /opportunities/{id}/reject`.
- **Frontend screen**: `OpportunitiesPage.tsx`.
- **What user sees**: Badges update; "Approve/Reject" buttons disappear. Approved items show "Create Content Brief".
- **What can go wrong**: Attempting to approve an already approved/rejected opportunity returns HTTP 409 Conflict.
- **What happens next**: Editor clicks "Create Content Brief".

#### Stage 5: Content Brief Generation
- **What enters**: An `approved` opportunity.
- **What happens**: System constructs an editorial blueprint specifying search intent, target audience profile, angle, and a recommended 5-section outline.
- **Database records**: `content_briefs` (status: `draft`).
- **API endpoints**: `POST /opportunities/{id}/create-brief`, `GET /content-briefs`.
- **Frontend screen**: `BriefsPage.tsx`.
- **What user sees**: Brief cards displaying search intent chips, audience description, and numbered section outlines.
- **What can go wrong**: Creating a brief for a pending/rejected opportunity or creating duplicate briefs returns HTTP 409.
- **What happens next**: Editor clicks "Generate Draft".

#### Stage 6: Draft Generation
- **What enters**: A `draft` content brief.
- **What happens**: Content generator constructs an introduction, structured markdown body with numbered headings, safety disclaimer, and conclusion.
- **Database records**: `content_drafts` (status: `draft`), `content_briefs` (status transitions to `completed`).
- **API endpoints**: `POST /briefs/{id}/generate-draft`, `GET /content-drafts`.
- **Frontend screen**: `BriefsPage.tsx` auto-redirects to `DraftsPage.tsx`.
- **What user sees**: Draft created notification; editor view opens.
- **What can go wrong**: Generating a duplicate draft from the same brief returns HTTP 409.
- **What happens next**: Human editor reviews and edits the draft.

#### Stage 7: Human In-Place Editing
- **What enters**: A `draft` status content draft.
- **What happens**: User edits Title, Introduction, Body (Markdown), or Conclusion fields.
- **Database records**: `content_drafts` updated with new text and timestamp.
- **API endpoint**: `PUT /content-drafts/{id}`.
- **Frontend screen**: `DraftsPage.tsx` (Editorial Studio).
- **What user sees**: Form inputs for Title, Intro, Body, Conclusion; "Save Changes" button.
- **What can go wrong**: Submitting empty fields returns HTTP 400; attempting to edit approved/rejected drafts returns HTTP 409.
- **What happens next**: Editor clicks "Approve Draft".

#### Stage 8: Human Draft Approval
- **What enters**: An edited draft in `draft` status.
- **What happens**: Editor formally signs off on the text.
- **Database records**: `content_drafts` status transitions to `approved`.
- **API endpoints**: `POST /content-drafts/{id}/approve` (or `POST /content-drafts/{id}/reject`).
- **Frontend screen**: `DraftsPage.tsx`.
- **What user sees**: Edit fields become read-only; status badge turns green; "Publish Article Now" button activates.
- **What can go wrong**: Transitioning a non-draft returns HTTP 409.
- **What happens next**: Editor clicks "Publish Article Now".

#### Stage 9: Publishing Pipeline
- **What enters**: An `approved` draft.
- **What happens**: Atomic database transaction generates a safe hyphenated slug, checks for slug collisions (`-2`, `-3`), records publication date, and marks status active.
- **Database records**: `published_content` (status: `published`).
- **API endpoints**: `POST /content-drafts/{id}/publish`, `GET /published-content`.
- **Frontend screen**: `DraftsPage.tsx` redirects to `PublishedPage.tsx`.
- **What user sees**: Table entry with live URL link `/blog/{slug}`, publication timestamp, and "View Article" button.
- **What can go wrong**: Publishing an unapproved or rejected draft returns HTTP 409.
- **What happens next**: User can view the live customer article or unpublish it.

#### Stage 10: Live Public Article
- **What enters**: Customer or editor visiting `/blog/{slug}`.
- **What happens**: System verifies article is in `published` status and renders customer-facing reading view.
- **Database records**: Reads `published_content` joined with `content_drafts`.
- **API endpoint**: `GET /blog/{slug}`.
- **Frontend screen**: `PublicArticlePage.tsx`.
- **What user sees**: Clean reader layout with title, publication date, primary keyword tag, intro blockquote, markdown body, and takeaway card.
- **What can go wrong**: Unpublished or non-existent slugs return HTTP 404 with a branded "Not Available" screen.
- **What happens next**: Editor can click "Unpublish" on the Published page at any time to immediately disable public access.

---

## Part 3 — Frontend Map

### Frontend Pages Summary Table

| Screen | File | Purpose | API Calls | Main User Actions | Next Screen |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Dashboard** | `pages/DashboardPage.tsx` | High-level metrics & workflow pipeline overview | `GET /dashboard/stats` | View KPI cards; click workflow shortcuts | Any selected page |
| **Products** | `pages/ProductsPage.tsx` | Catalog inventory management | `GET /products`, `POST /products`, `DELETE /products/{id}` | Add Product modal; Delete product | Products / Research |
| **Keywords** | `pages/KeywordsPage.tsx` | Search demand query tracking | `GET /keywords`, `POST /keywords`, `DELETE /keywords/{id}` | Add Keyword modal; Delete keyword | Keywords / Research |
| **Research** | `pages/ResearchPage.tsx` | Execution of automated opportunity scans | `POST /research-runs`, `GET /research-runs`, `POST /research-runs/{id}/execute`, `GET /research-runs/{id}/opportunities`, `POST /opportunities/{id}/approve`, `POST /opportunities/{id}/reject` | Click "Run Research"; Select historical run; Approve/Reject opportunities directly | Opportunities |
| **Opportunities** | `pages/OpportunitiesPage.tsx` | Decision hub for discovered topic opportunities | `GET /opportunities`, `POST /opportunities/{id}/approve`, `POST /opportunities/{id}/reject`, `POST /opportunities/{id}/create-brief` | Filter by status (`all`, `pending`, `approved`, `rejected`); Approve; Reject; Create Brief | Briefs |
| **Briefs** | `pages/BriefsPage.tsx` | Content blueprint viewer & draft trigger | `GET /content-briefs`, `POST /briefs/{id}/generate-draft` | Review outline, intent, and audience; Click "Generate Draft" | Drafts Studio |
| **Drafts** | `pages/DraftsPage.tsx` | In-place human editorial studio | `GET /content-drafts`, `PUT /content-drafts/{id}`, `POST /content-drafts/{id}/approve`, `POST /content-drafts/{id}/reject`, `POST /content-drafts/{id}/publish` | Select draft; Edit Title/Intro/Body/Conclusion; Save Changes; Approve; Reject; Publish | Published Content |
| **Published Content** | `pages/PublishedPage.tsx` | Publication ledger & URL management | `GET /published-content`, `POST /published-content/{id}/unpublish` | Click "View Article"; Click "Unpublish" | Public Article View |
| **Public Article** | `pages/PublicArticlePage.tsx` | Customer-facing live article reader | `GET /blog/{slug}` | Read public article; Return to dashboard | Dashboard / Published |

### Frontend Architecture Details

- **Navigation Coordinator (`src/App.tsx`)**: Controls `currentView` state (`dashboard`, `products`, `keywords`, `research`, `opportunities`, `briefs`, `drafts`, `published`, `public-blog`). Checks URL on load for direct deep links (`/blog/:slug`).
- **Design System (`src/index.css`)**: Dark-mode palette (`#090d16` background, `#131b2e` cards), glassmorphic top bar, responsive sidebar, pill status badges, and typography using Google Font *Plus Jakarta Sans*.
- **API Client (`src/api/client.ts`)**: Typed wrapper around native `fetch` with centralized error unwrapping (`errorDetail = errJson.detail`).
- **UI Components (`src/components/`)**:
  - `Sidebar.tsx`: Fixed navigation with active route highlights and live KPI counts.
  - `Header.tsx`: Contextual title, subtitle, refresh button, and AI status pill.
  - `StatusBadge.tsx`: Color-coded status pills (`pending`, `approved`, `rejected`, `draft`, `completed`, `published`, `unpublished`).
  - `Modal.tsx`: Accessible dialog with backdrop click and ESC key dismissals.

---

## Part 4 — Backend Map

### Backend Architecture Table

| Domain | Router File | Service File | Database Tables | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Dashboard** | `backend/app/api/dashboard.py` | Aggregates DB queries | All tables | Computes counts for KPI cards |
| **Products** | `backend/app/api/products.py` | Direct DB execution | `products` | CRUD management for store merchandise |
| **Keywords** | `backend/app/api/keywords.py` | Direct DB execution | `keywords` | CRUD management for search demand queries |
| **Content** | `backend/app/api/content.py` | `content_analysis_service.py` | `existing_content`, `products` | Manages existing articles; provides store profile |
| **Research** | `backend/app/api/research.py` | `research_service.py` | `research_runs`, `content_opportunities` | Manages research runs and scans catalog |
| **Opportunities**| `backend/app/api/opportunities.py`| `opportunity_service.py` | `content_opportunities`, `content_briefs` | Opportunity discovery, scoring, approvals, brief trigger |
| **Briefs** | `backend/app/api/briefs.py` | `brief_service.py` | `content_briefs`, `content_drafts` | Blueprint creation, outline drafting, draft trigger |
| **Drafts** | `backend/app/api/drafts.py` | `draft_service.py` | `content_drafts`, `published_content` | Draft generation, in-place edit validation, sign-off |
| **Publishing** | `backend/app/api/publishing.py` | `publishing_service.py` | `published_content`, `content_drafts` | Atomic slug creation, unpublishing, public reader |

### Code Request Flow: Concrete Example

**Trace: "User clicks Approve Opportunity"**

1. **User action**: User clicks `<button onClick={() => handleApprove(opp.id)}>Approve</button>` in `frontend/src/pages/OpportunitiesPage.tsx`.
2. **Frontend Client**: Calls `api.approveOpportunity(id)` in `frontend/src/api/client.ts`.
3. **HTTP Request**: Sends `POST http://localhost:8000/opportunities/2/approve`.
4. **Vite Proxy**: `frontend/vite.config.ts` proxies `/opportunities` to `http://127.0.0.1:8000`.
5. **FastAPI Routing**: `backend/app/main.py` routes request to `backend/app/api/opportunities.py`:
   ```python
   @router.post("/opportunities/{opportunity_id}/approve")
   def approve_opportunity(opportunity_id: int, db: sqlite3.Connection = Depends(get_db)):
   ```
6. **Connection Dependency**: `backend/app/database/connection.py` opens SQLite connection and runs `PRAGMA foreign_keys = ON;`.
7. **Service Layer**: Router calls `opportunity_service.approve_opportunity(db, opportunity_id)` in `backend/app/services/opportunity_service.py`.
8. **Validation Guard**: Service queries `content_opportunities` by ID. Checks if `opp["status"] == "pending"`. If already approved or rejected, returns `409 Conflict`.
9. **Database Update**: Service runs `UPDATE content_opportunities SET status = 'approved' WHERE id = ?` and executes `conn.commit()`.
10. **HTTP Response**: Router returns JSON `{ "id": 2, "status": "approved", "message": "Opportunity approved successfully." }` with status 200.
11. **Frontend Update**: `OpportunitiesPage.tsx` receives response, sets success toast, and refreshes opportunities list. Badge turns green.

---

## Part 5 — Database Map

The database is an SQLite database stored locally at `adaptive_content.db`. Foreign keys are strictly enforced on every connection via `PRAGMA foreign_keys = ON;`.

### Tables Breakdown

#### 1. `products`
- **Purpose**: Represents merchandise sold by the online store.
- **Columns**: `id` (INTEGER PK AUTOINCREMENT), `name` (TEXT), `category` (TEXT), `description` (TEXT), `created_at` (TEXT), `updated_at` (TEXT).
- **Created by**: Seed script (`seed.py`) or user via `POST /products`.
- **Updated by**: User via `PUT /products/{id}`.
- **Read by**: Research engine, Products page, Store profile endpoint.

#### 2. `keywords`
- **Purpose**: Target search terms with estimated monthly search volumes.
- **Columns**: `id` (INTEGER PK AUTOINCREMENT), `keyword` (TEXT UNIQUE), `search_volume` (INTEGER), `created_at` (TEXT), `updated_at` (TEXT).
- **Constraints**: Unique constraint on `keyword`.
- **Created by**: Seed script or user via `POST /keywords`.
- **Updated by**: User via `PUT /keywords/{id}`.
- **Read by**: Research engine, Keywords page.

#### 3. `existing_content`
- **Purpose**: Registry of articles already published on the store to prevent keyword cannibalization.
- **Columns**: `id` (INTEGER PK AUTOINCREMENT), `title` (TEXT), `url` (TEXT), `primary_keyword` (TEXT nullable), `created_at` (TEXT), `updated_at` (TEXT).
- **Created by**: Seed script or user via `POST /existing-content`.
- **Read by**: Research engine (`ContentAnalysisService`) during deduplication check.

#### 4. `research_runs`
- **Purpose**: Session log of each opportunity scan executed.
- **Columns**: `id` (INTEGER PK AUTOINCREMENT), `status` (TEXT: `created`, `running`, `completed`, `failed`), `created_at` (TEXT), `completed_at` (TEXT nullable).
- **Created by**: User clicking "Run Research" via `POST /research-runs`.
- **Updated by**: System during `POST /research-runs/{id}/execute`.
- **Read by**: Research page.

#### 5. `content_opportunities`
- **Purpose**: Suggested article ideas derived from products and keywords.
- **Columns**: `id` (INTEGER PK AUTOINCREMENT), `research_run_id` (INTEGER FK), `title` (TEXT), `reason` (TEXT), `primary_keyword` (TEXT nullable), `search_volume` (INTEGER), `confidence` (TEXT), `status` (TEXT: `pending`, `approved`, `rejected`), `created_at` (TEXT), `evidence` (TEXT JSON array).
- **Foreign Key**: `research_run_id` references `research_runs(id)` ON DELETE CASCADE.
- **Created by**: Research engine during execution.
- **Updated by**: Editor approving/rejecting via `POST /opportunities/{id}/approve` or `reject`.
- **Read by**: Research page, Opportunities page, Brief service.

#### 6. `content_briefs`
- **Purpose**: Editorial strategy outlines for approved opportunities.
- **Columns**: `id` (INTEGER PK AUTOINCREMENT), `opportunity_id` (INTEGER FK UNIQUE), `title` (TEXT), `objective` (TEXT), `primary_keyword` (TEXT), `search_volume` (INTEGER), `search_intent` (TEXT), `target_audience` (TEXT), `suggested_sections` (TEXT JSON array), `suggested_angle` (TEXT), `related_keywords` (TEXT JSON array), `opportunity_evidence` (TEXT JSON array), `status` (TEXT: `draft`, `completed`), `created_at` (TEXT), `updated_at` (TEXT).
- **Foreign Key**: `opportunity_id` references `content_opportunities(id)` ON DELETE CASCADE.
- **Unique Constraint**: Exactly one brief per opportunity (`opportunity_id UNIQUE`).
- **Created by**: User via `POST /opportunities/{id}/create-brief`.
- **Updated by**: System when draft is generated (transitions status from `draft` to `completed`).
- **Read by**: Briefs page, Draft generator.

#### 7. `content_drafts`
- **Purpose**: Full article copy with editable sections.
- **Columns**: `id` (INTEGER PK AUTOINCREMENT), `brief_id` (INTEGER FK UNIQUE), `title` (TEXT), `primary_keyword` (TEXT nullable), `introduction` (TEXT), `body` (TEXT), `conclusion` (TEXT), `status` (TEXT: `draft`, `approved`, `rejected`), `created_at` (TEXT), `updated_at` (TEXT).
- **Foreign Key**: `brief_id` references `content_briefs(id)` ON DELETE CASCADE.
- **Unique Constraint**: Exactly one draft per brief (`brief_id UNIQUE`).
- **Created by**: System via `POST /briefs/{id}/generate-draft`.
- **Updated by**: Editor editing text (`PUT /content-drafts/{id}`) or approving/rejecting.
- **Read by**: Drafts studio, Publishing service, Public blog route.

#### 8. `published_content`
- **Purpose**: Ledger of publicly released articles with live slugs.
- **Columns**: `id` (INTEGER PK AUTOINCREMENT), `draft_id` (INTEGER FK UNIQUE), `title` (TEXT), `slug` (TEXT UNIQUE), `url` (TEXT), `published_at` (TEXT), `status` (TEXT: `published`, `unpublished`), `created_at` (TEXT), `updated_at` (TEXT).
- **Foreign Key**: `draft_id` references `content_drafts(id)` ON DELETE CASCADE.
- **Unique Constraints**: Unique `draft_id`, unique `slug`.
- **Created by**: System via `POST /content-drafts/{id}/publish`.
- **Updated by**: Editor via `POST /published-content/{id}/unpublish`.
- **Read by**: Published page, Public article viewer (`GET /blog/{slug}`).

---

## Part 6 — Complete Article Lifecycle Trace

Concrete walk-through of an article moving through the system:

```text
Product: "Niacinamide Serum" (Category: Skincare)
   │
Keyword: "niacinamide serum benefits" (8,000 searches/mo)
   │
[Research Execution] ──▶ Opportunity ID #3: "What Is Niacinamide Serum Good For?"
   │                     Status: pending | Confidence: high
   │
[Human Approval] ─────▶ Opportunity ID #3 Status: approved
   │
[Create Brief] ──────▶ Brief ID #1: "What Is Niacinamide Serum Good For?"
   │                     Intent: informational | Status: draft
   │
[Generate Draft] ────▶ Draft ID #1 Status: draft | Brief #1 Status: completed
   │
[Human Editing] ─────▶ Title: "Niacinamide Serum: The Complete Daily Routine Guide"
   │                     Status remains: draft
   │
[Approve Draft] ─────▶ Draft ID #1 Status: approved
   │
[Publishing] ────────▶ Published Content ID #1
   │                     Slug: "niacinamide-serum-the-complete-daily-routine-guide"
   │                     URL: "/blog/niacinamide-serum-the-complete-daily-routine-guide"
   │                     Status: published
   ▼
[Public Blog] ───────▶ Visitor loads GET /blog/niacinamide-serum-the-complete-daily-routine-guide
```

| Step | Database Record | Status | API Endpoint Called | Service Responsible | Frontend Screen |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Catalog** | `products` (id: 3) | N/A | `GET /products` | Direct DB query | Products Page |
| **Demand** | `keywords` (id: 3) | N/A | `GET /keywords` | Direct DB query | Keywords Page |
| **Research** | `research_runs` (id: 1) | `completed` | `POST /research-runs/1/execute` | `ResearchService` | Research Page |
| **Opportunity**| `content_opportunities` (id: 3) | `pending` | `GET /research-runs/1/opportunities` | `OpportunityService` | Research Page |
| **Approval** | `content_opportunities` (id: 3) | `approved` | `POST /opportunities/3/approve` | `OpportunityService` | Opportunities Page |
| **Brief** | `content_briefs` (id: 1) | `draft` | `POST /opportunities/3/create-brief`| `BriefService` | Briefs Page |
| **Draft** | `content_drafts` (id: 1) | `draft` | `POST /briefs/1/generate-draft` | `DraftService` & Generator | Drafts Studio |
| **Editing** | `content_drafts` (id: 1) | `draft` | `PUT /content-drafts/1` | `DraftService` | Drafts Studio |
| **Draft Appr** | `content_drafts` (id: 1) | `approved` | `POST /content-drafts/1/approve` | `DraftService` | Drafts Studio |
| **Publishing** | `published_content` (id: 1) | `published` | `POST /content-drafts/1/publish` | `PublishingService` | Drafts Studio |
| **Public View**| `published_content` (id: 1) | `published` | `GET /blog/{slug}` | `PublishingService` | Public Article Page |

---

## Part 7 — State Machines & Backend Guards

### 1. Research Run State Machine
```text
[created] ──▶ [running] ──▶ [completed]
                   │
                   └──▶ [failed]
```
- **Guards**: `POST /research-runs/{id}/execute` checks if `run["status"] == "completed"` or `"running"`. If so, raises `HTTPException(409, "This research run has already been completed.")`.

### 2. Content Opportunity State Machine
```text
              ┌──▶ [approved]
[pending] ────┤
              └──▶ [rejected]
```
- **Guards**:
  - `POST /opportunities/{id}/approve` verifies `opp["status"] == "pending"`. If already approved or rejected, raises `HTTPException(409)`.
  - `POST /opportunities/{id}/reject` verifies `opp["status"] == "pending"`. If already approved or rejected, raises `HTTPException(409)`.
  - `POST /opportunities/{id}/create-brief` verifies `opp["status"] == "approved"`. If pending or rejected, raises `HTTPException(409)`. Also queries `SELECT id FROM content_briefs WHERE opportunity_id = ?`; if found, raises `HTTPException(409, "A content brief already exists for this opportunity.")`.

### 3. Content Brief State Machine
```text
[draft] ──▶ [completed]
```
- **Guards**: `POST /briefs/{id}/generate-draft` checks if a draft already exists for `brief_id`. If so, raises `HTTPException(409)`. On success, sets brief status to `completed`.

### 4. Content Draft State Machine
```text
              ┌──▶ [approved] (locks edits; enables publish)
[draft] ──────┤
              └──▶ [rejected] (locks edits; disables publish)
```
- **Guards**:
  - `PUT /content-drafts/{id}` checks `draft["status"] == "draft"`. If status is `approved` or `rejected`, raises `HTTPException(409, "Only drafts with status 'draft' can be edited.")`.
  - `POST /content-drafts/{id}/approve` checks `draft["status"] == "draft"`. If already approved or rejected, raises `HTTPException(409)`.
  - `POST /content-drafts/{id}/reject` checks `draft["status"] == "draft"`. If already approved or rejected, raises `HTTPException(409)`.
  - `POST /content-drafts/{id}/publish` checks `draft["status"] == "approved"`. If draft is still in `draft` or `rejected` status, raises `HTTPException(409, "Only approved drafts can be published.")`.

### 5. Published Content State Machine
```text
[published] ──▶ [unpublished]
```
- **Guards**:
  - `POST /published-content/{id}/unpublish` checks `pub["status"] == "unpublished"`. If already unpublished, raises `HTTPException(409)`.
  - `GET /blog/{slug}` checks `p.status == 'published'`. If unpublished or non-existent, raises `HTTPException(404, "Article not found or not published.")`.

---

## Part 8 — The Actual "AI"

### Technical Answers

1. **Is an LLM currently being called?** **NO.** There are zero active outbound HTTP requests to OpenAI, Anthropic, Google, or any local LLM.
2. **Which file generates content?** `backend/app/services/generators/mock_generator.py` (`MockContentGenerator`).
3. **Is the generator deterministic?** **YES.** Given the same brief inputs, it produces the same structured article using procedural Python string templating.
4. **Is OpenAI implemented?** No API client call exists. A skeleton method exists in `ai_generator.py` with comments showing where `openai` would be called.
5. **Is Anthropic implemented?** No.
6. **Is Gemini implemented?** No.
7. **Where is an API key read?** `backend/app/config.py` reads `AI_API_KEY = os.getenv("AI_API_KEY", "")` and `AI_PROVIDER = os.getenv("AI_PROVIDER", "mock")`.
8. **What happens if no API key exists?** `ai_generator.py` automatically falls back to `MockContentGenerator`.
9. **Which parts of Agentify are genuinely algorithmic?** Text tokenization, stopword removal, duplicate overlap ratio computation, 100-point opportunity scoring, and unique slug formatting with collision handling.
10. **Which parts are AI-generated?** **None.**
11. **Which parts are mock/demo behavior?** The draft generation text and the keyword search volume numbers.

### Categorization Table

| Capability | Actual Implementation Category | Details |
| :--- | :--- | :--- |
| Product Catalog Storage | **DATABASE-BACKED** | Real SQLite table with full CRUD |
| Keyword Search Volumes | **SEEDED / MOCK DATA** | Real database table populated with fixed demo numbers (12,000; 8,000; etc.) |
| Duplicate Detection | **DETERMINISTIC LOGIC** | Real algorithmic word tokenization and intersection math |
| Opportunity Scoring | **DETERMINISTIC LOGIC** | Real mathematical formula (40 + demand + keyword - penalty) |
| Content Brief Generation | **DETERMINISTIC LOGIC** | Real Python rule engine matching keywords to intent and section outlines |
| Draft Generation | **MOCK AI (Template)** | Procedural template populating skincare sections and medical disclaimers |
| Slug Resolution | **DETERMINISTIC LOGIC** | Real regex sanitization and SQL collision checks (`-2`, `-3`) |
| Public Article Serving | **DATABASE-BACKED** | Real SQL query joining `published_content` and `content_drafts` |

---

## Part 9 — Research Engine & Scoring Logic

The research engine runs entirely inside `backend/app/services/research_service.py` and `opportunity_service.py`.

```text
[Products Table] + [Keywords Table] + [Existing Content Table]
                                │
                                ▼
         ContentAnalysisService.check_existing_content()
             (Strips stopwords, computes token overlap)
                                │
                                ▼
         OpportunityService.discover_opportunities()
             (Calculates 100-point transparent score)
                                │
                                ▼
         Persists to content_opportunities Table (status: pending)
```

### The Exact Scoring Formula (from `opportunity_service.py`)

$$\text{Opportunity Score} = \text{Product Relevance} + \text{Search Demand Signal} + \text{Keyword Relevance} - \text{Duplicate Penalty}$$

Where:
- **Product Relevance** = `40.0` points if the product exists in the store catalog.
- **Search Demand Signal** = $\min\left(35.0, \frac{\text{Total Search Volume}}{20,000} \times 35.0\right)$ (scaled up to 35 points; defaults to `5.0` if zero volume).
- **Keyword Relevance** = `25.0` points if specific matching keywords exist in the database (otherwise `10.0`).
- **Duplicate Penalty** = `80.0` points deducted if `ContentAnalysisService` detects an existing article covering the topic.

### Real Example Using Seed Data

#### Product: "Vitamin C Serum"
- Existing article detected: *"Vitamin C Serum Benefits and How to Use It"*.
- Duplicate check result: `exists = True`.
- Score calculation: $40.0 + 21.0 + 25.0 - 80.0 = 6.0$.
- **Action**: Suppressed completely. The engine does not propose a redundant Vitamin C article.

#### Product: "Niacinamide Serum"
- Existing article detected: None.
- Matching keyword: `"niacinamide serum benefits"` (8,000 searches/mo).
- Product relevance: `40.0`
- Search demand signal: $\frac{8000}{20000} \times 35.0 = 14.0$
- Keyword relevance: `25.0`
- Duplicate penalty: `0.0`
- **Total Score**: $40.0 + 14.0 + 25.0 - 0.0 = \mathbf{79.0}$ (Confidence: `medium` $\rightarrow$ rounds to high potential).
- **Result**: Generates opportunity *"What Is Niacinamide Serum Good For?"*.

### How Duplicate Detection Works (`content_analysis_service.py`)
1. Strips all punctuation using regex `r"[^\w\s]"`.
2. Lowercases text and splits into words.
3. Filters out 45 common English stop words (e.g., `the`, `is`, `for`, `what`, `and`, `to`, `in`).
4. Calculates token overlap between query tokens and existing article titles.
5. If $\ge 60\%$ of significant query words match, or $\ge 2$ core keywords overlap, flags `exists = True` with matched article ID and title.

### Limitations of Current Approach
- It uses exact token matching. It cannot detect semantic synonyms (e.g. it does not know that "blemish" means "acne" or that "wrinkle treatment" means "anti-aging").
- A future iteration should integrate vector embeddings (e.g. ChromaDB or pgvector) to detect conceptual overlap.

---

## Part 10 — Complete API Inventory

| Method | Path | Category | Request Body | Response | Tables Touched | Service | Caller | Auth |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/dashboard/stats` | **CORE** | None | `DashboardStatsResponse` | All 8 tables | Direct query | `App.tsx`, `DashboardPage` | None |
| `GET` | `/products` | **CORE** | None | `list[ProductResponse]` | `products` | Direct query | `ProductsPage` | None |
| `POST`| `/products` | **CORE** | `ProductCreate` | `ProductResponse` (201) | `products` | Direct query | `ProductsPage` modal | None |
| `GET` | `/products/{id}` | AUXILIARY | None | `ProductResponse` | `products` | Direct query | Admin/Dev | None |
| `PUT` | `/products/{id}` | AUXILIARY | `ProductUpdate` | `ProductResponse` | `products` | Direct query | Admin/Dev | None |
| `DELETE`| `/products/{id}`| **CORE** | None | `{detail: string}` | `products` | Direct query | `ProductsPage` | None |
| `GET` | `/keywords` | **CORE** | None | `list[KeywordResponse]` | `keywords` | Direct query | `KeywordsPage` | None |
| `POST`| `/keywords` | **CORE** | `KeywordCreate` | `KeywordResponse` (201) | `keywords` | Direct query | `KeywordsPage` modal | None |
| `PUT` | `/keywords/{id}` | AUXILIARY | `KeywordUpdate` | `KeywordResponse` | `keywords` | Direct query | Admin/Dev | None |
| `DELETE`| `/keywords/{id}`| **CORE** | None | `{detail: string}` | `keywords` | Direct query | `KeywordsPage` | None |
| `GET` | `/existing-content` | **CORE** | None | `list[ExistingContentResponse]` | `existing_content` | Direct query | Admin/Dev | None |
| `POST`| `/existing-content` | AUXILIARY | `ExistingContentCreate` | `ExistingContentResponse` (201)| `existing_content` | Direct query | Admin/Dev | None |
| `DELETE`| `/existing-content/{id}`| AUXILIARY | None | `{detail: string}` | `existing_content` | Direct query | Admin/Dev | None |
| `GET` | `/content` | **LEGACY** | None | `list[ExistingContentResponse]` | `existing_content` | Direct query | Alias for `/existing-content` | None |
| `GET` | `/store-profile` | AUXILIARY | None | `StoreProfileResponse` | `products` | Direct query | Admin/Dev | None |
| `POST`| `/research-runs` | **CORE** | None | `ResearchRunResponse` (201) | `research_runs` | `research_service` | `ResearchPage` | None |
| `GET` | `/research-runs` | **CORE** | None | `list[ResearchRunResponse]` | `research_runs` | `research_service` | `ResearchPage` | None |
| `GET` | `/research-runs/{id}`| AUXILIARY | None | `ResearchRunResponse` | `research_runs` | `research_service` | `ResearchPage` | None |
| `POST`| `/research-runs/{id}/execute` | **CORE** | None | `ResearchRunExecuteResponse` | `research_runs`, `content_opportunities` | `research_service` | `ResearchPage` | None |
| `GET` | `/research-runs/{id}/opportunities` | **CORE** | None | `list[OpportunityResponse]` | `content_opportunities` | `research_service` | `ResearchPage` | None |
| `GET` | `/opportunities` | **CORE** | Query: `?status=` | `list[OpportunityResponse]` | `content_opportunities` | `opportunity_service` | `OpportunitiesPage` | None |
| `GET` | `/opportunities/{id}`| AUXILIARY | None | `OpportunityResponse` | `content_opportunities` | `opportunity_service` | Admin/Dev | None |
| `POST`| `/opportunities/{id}/approve` | **CORE** | None | `OpportunityActionResponse` | `content_opportunities` | `opportunity_service` | `OpportunitiesPage`, `ResearchPage` | None |
| `POST`| `/opportunities/{id}/reject` | **CORE** | None | `OpportunityActionResponse` | `content_opportunities` | `opportunity_service` | `OpportunitiesPage`, `ResearchPage` | None |
| `POST`| `/opportunities/{id}/create-brief` | **CORE** | None | `BriefResponse` (201) | `content_opportunities`, `content_briefs` | `brief_service` | `OpportunitiesPage` | None |
| `GET` | `/content-opportunities` | **LEGACY** | None | `list[dict]` | None (in-memory compute) | `opportunity_service` | Old tests | None |
| `GET` | `/content-briefs` | **CORE** | None | `list[BriefResponse]` | `content_briefs` | `brief_service` | `BriefsPage` | None |
| `GET` | `/content-briefs/{id}`| AUXILIARY | None | `BriefResponse` | `content_briefs` | `brief_service` | Admin/Dev | None |
| `POST`| `/briefs/{id}/generate-draft` | **CORE** | None | `DraftResponse` (201) | `content_briefs`, `content_drafts` | `draft_service` | `BriefsPage` | None |
| `POST`| `/content-briefs/{id}/generate-draft` | **LEGACY** | None | `DraftResponse` (201) | `content_briefs`, `content_drafts` | `draft_service` | Alias for `/briefs/{id}/...` | None |
| `GET` | `/content-drafts` | **CORE** | None | `list[DraftResponse]` | `content_drafts` | `draft_service` | `DraftsPage` | None |
| `GET` | `/content-drafts/{id}`| **CORE** | None | `DraftResponse` | `content_drafts` | `draft_service` | `DraftsPage` | None |
| `PUT` | `/content-drafts/{id}`| **CORE** | `DraftUpdate` | `DraftResponse` | `content_drafts` | `draft_service` | `DraftsPage` (Save Changes) | None |
| `POST`| `/content-drafts/{id}/approve` | **CORE** | None | `DraftActionResponse` | `content_drafts` | `draft_service` | `DraftsPage` (Approve) | None |
| `POST`| `/content-drafts/{id}/reject` | **CORE** | None | `DraftActionResponse` | `content_drafts` | `draft_service` | `DraftsPage` (Reject) | None |
| `POST`| `/content-drafts/{draft_id}/publish` | **CORE** | None | `PublishedContentResponse` (201) | `content_drafts`, `published_content` | `publishing_service` | `DraftsPage` (Publish) | None |
| `GET` | `/published-content` | **CORE** | Query: `?status=` | `list[PublishedContentResponse]` | `published_content` | `publishing_service` | `PublishedPage` | None |
| `GET` | `/published-content/{id}` | AUXILIARY | None | `PublishedContentResponse` | `published_content` | `publishing_service` | Admin/Dev | None |
| `POST`| `/published-content/{id}/unpublish` | **CORE** | None | `PublishedContentResponse` | `published_content` | `publishing_service` | `PublishedPage` (Unpublish) | None |
| `GET` | `/blog/{slug}` | **CORE** | None | `PublicArticleResponse` | `published_content`, `content_drafts` | `publishing_service` | `PublicArticlePage` | None |
| `GET` | `/health` | AUXILIARY | None | `{status: "ok", environment: "..."}` | None | None | Monitoring | None |
| `GET` | `/` | AUXILIARY | None | `{message: "...", version: "1.0.0"}` | None | None | Root health check | None |

---

## Part 11 — File Map & Learning Order

```text
Agentify/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI app factory, CORS, lifespan, and router mounting
│   │   ├── config.py                   # Environment settings and configuration
│   │   ├── database/
│   │   │   ├── connection.py           # Database connection factory enforcing PRAGMA foreign_keys = ON
│   │   │   ├── schema.py               # Table creation DDL and non-destructive column migration helpers
│   │   │   └── seed.py                 # Initial seed records for products, keywords, and existing content
│   │   ├── schemas/                    # Pydantic v2 validation models
│   │   │   ├── product.py, keyword.py, content.py, research.py
│   │   │   ├── opportunity.py, brief.py, draft.py, publishing.py, dashboard.py
│   │   ├── services/                   # Business logic and opportunity scoring engine
│   │   │   ├── content_analysis_service.py # Text normalization, stopword filtering, duplicate detection
│   │   │   ├── opportunity_service.py  # 100-point opportunity scoring formula and transitions
│   │   │   ├── research_service.py     # Research run execution and opportunity persistence
│   │   │   ├── brief_service.py        # Editorial blueprint and section outline generation
│   │   │   ├── draft_service.py        # Draft generation, in-place edit validation, and sign-offs
│   │   │   ├── publishing_service.py   # Atomic publishing transactions and slug collision handling
│   │   │   └── generators/
│   │   │       ├── base.py             # Abstract ContentGenerator interface
│   │   │       ├── mock_generator.py   # Deterministic structured template content generator
│   │   │       └── ai_generator.py     # AI provider adapter skeleton with graceful mock fallback
│   │   ├── api/                        # FastAPI route controllers partitioned by resource domain
│   │   │   ├── products.py, keywords.py, content.py, research.py
│   │   │   ├── opportunities.py, briefs.py, drafts.py, publishing.py, dashboard.py
│   │   └── utils/
│   │       ├── slug.py                 # Safe URL slug generator with collision resolution (-2, -3)
│   │       ├── text.py                 # Stop words list and tokenization helpers
│   │       └── dates.py                # ISO 8601 UTC timestamp helper
│   └── tests/                          # 11 automated pytest test suites
├── frontend/
│   ├── src/
│   │   ├── App.tsx                     # Main dashboard coordinator, routing, and stats loader
│   │   ├── main.tsx                    # React DOM root entrypoint
│   │   ├── index.css                   # Custom dark-mode CSS design system
│   │   ├── api/client.ts               # Typed client connecting frontend to backend API
│   │   ├── types/index.ts              # TypeScript interfaces for all data objects
│   │   ├── components/
│   │   │   ├── Sidebar.tsx             # Left sidebar navigation with dynamic live count badges
│   │   │   ├── Header.tsx              # Top bar with view titles and refresh button
│   │   │   ├── StatusBadge.tsx         # Reusable color-coded status badge pill
│   │   │   └── Modal.tsx               # Reusable dialog modal
│   │   └── pages/                      # 9 dedicated page views
│   ├── package.json                    # Frontend dependencies (React 19, TypeScript, Lucide, Vite)
│   └── vite.config.ts                  # Vite server config with API proxy to port 8000
├── app.py                              # Root proxy re-exporting backend.app.main:app for uvicorn
├── .env.example                        # Template for environment variables
└── README.md                           # System documentation and instructions
```

### Files I Should Understand First (Ranked Learning Order)

1. **`frontend/src/App.tsx`**: Start here to see the big picture. You will see how navigation works, how pages are switched, and how dashboard stats are loaded.
2. **`frontend/src/api/client.ts`**: Understand every API call the frontend makes to the backend.
3. **`backend/app/main.py`**: Understand how the backend starts up, registers routers, and initializes the database.
4. **`backend/app/database/schema.py`**: Understand the 8 database tables, columns, foreign keys, and relationships.
5. **`backend/app/services/opportunity_service.py`**: Understand the core intelligence algorithm: how products and keywords are scored.
6. **`backend/app/services/draft_service.py`**: Understand how drafts are generated, edited, and validated.
7. **`backend/app/services/publishing_service.py`**: Understand how approved articles become live URLs with safe slugs.

---

## Part 12 — "If I Want To Change X, Where Do I Go?"

| What You Want To Change | File(s) to Inspect | Layer | What NOT to Change | Tests to Update |
| :--- | :--- | :--- | :--- | :--- |
| **Dashboard Appearance** | `frontend/src/pages/DashboardPage.tsx`, `frontend/src/index.css` | Frontend Presentation | Do not change `DashboardStatsResponse` schema | None |
| **Product Catalog Fields** | `backend/app/schemas/product.py`, `backend/app/database/schema.py`, `frontend/src/pages/ProductsPage.tsx` | Full Stack (DB, Schema, UI) | Do not break `id` primary key | `backend/tests/test_products_keywords.py` |
| **Keyword Fields / Demand** | `backend/app/schemas/keyword.py`, `backend/app/api/keywords.py`, `frontend/src/pages/KeywordsPage.tsx` | Full Stack | Do not remove `search_volume` | `backend/tests/test_products_keywords.py` |
| **Opportunity Scoring Math** | `backend/app/services/opportunity_service.py` | Business Service | Do not change the dictionary return keys (`title`, `search_volume`, `confidence`, `evidence`) | `backend/tests/test_opportunities.py` |
| **Duplicate Content Rules** | `backend/app/services/content_analysis_service.py` | Business Service | Keep the return structure (`exists`, `matched_content_id`, `similarity_reason`) | `backend/tests/test_content_analysis.py` |
| **Brief Sections & Structure** | `backend/app/services/brief_service.py` | Business Service | Do not change JSON serialization of `suggested_sections` | `backend/tests/test_briefs.py` |
| **Draft Content Structure** | `backend/app/services/generators/mock_generator.py` | Generator Engine | Keep returned keys: `title`, `introduction`, `body`, `conclusion` | `backend/tests/test_drafts.py` |
| **Connect Real AI (LLM)** | `backend/app/services/generators/ai_generator.py`, `.env` | Generator Engine | Do not change `generate(self, brief)` method signature | `backend/tests/test_drafts.py` |
| **Editorial Studio Form** | `frontend/src/pages/DraftsPage.tsx` | Frontend Presentation | Do not bypass `isEditable` status guard check | None |
| **Publishing State Machine** | `backend/app/services/publishing_service.py` | Business Service | Do not remove the atomic transaction (`conn.commit()` / `conn.rollback()`) | `backend/tests/test_publishing.py` |
| **Slug Formatting Rules** | `backend/app/utils/slug.py` | Utility Helper | Keep `generate_unique_slug` collision loop intact | `backend/tests/test_publishing.py` |
| **Public Blog Page Design** | `frontend/src/pages/PublicArticlePage.tsx`, `frontend/src/index.css` | Frontend Presentation | Keep the `404` guard when article is unpublished | None |
| **Database Schema** | `backend/app/database/schema.py` | Database Layer | Always use `_ensure_column` for existing tables so migrations don't crash | `backend/tests/conftest.py` |
| **Add User Authentication** | `backend/app/main.py` (middleware), `backend/app/api/...` | Security / API Layer | Do not block public `GET /blog/{slug}` endpoint | All test files (add auth headers) |

---

## Part 13 — Real vs Mock Audit

| Feature | Real | Mock | Explanation from Actual Source Code |
| :--- | :---: | :---: | :--- |
| **Product Catalog** | **YES** | NO | Real SQLite table with real CRUD operations in `backend/app/api/products.py`. |
| **Keywords Tracking** | **YES** | NO | Real SQLite table with real CRUD operations in `backend/app/api/keywords.py`. |
| **Search Volume Numbers** | NO | **YES** | Seed data defaults (e.g. 12,000; 8,000) defined in `backend/app/database/seed.py`. |
| **Research Execution** | **YES** | NO | Real Python code in `research_service.py` executing scans, persisting run IDs, and recording timestamps. |
| **Opportunity Scoring** | **YES** | NO | Real mathematical calculation in `opportunity_service.py` computing relevance, volume signal, and penalties. |
| **Duplicate Detection** | **YES** | NO | Real text tokenization and Jaccard-style overlap logic in `content_analysis_service.py`. |
| **Brief Generation** | **YES** | NO | Real service in `brief_service.py` dynamically determining search intent, audience, and outlines. |
| **Draft Generation** | NO | **YES** | Deterministic procedural string generator in `mock_generator.py`. |
| **AI (LLM Model)** | NO | **YES** | No external LLM is called; `ai_generator.py` falls back to `mock_generator.py`. |
| **Human Editing Studio** | **YES** | NO | Real interactive form in `DraftsPage.tsx` saving changes to SQLite via `PUT /content-drafts/{id}`. |
| **Editorial Approvals** | **YES** | NO | Real state transitions enforced with HTTP 409 Conflict guards in backend services. |
| **Publishing Pipeline** | **YES** | NO | Real atomic database transaction creating `published_content` records with timestamps. |
| **Slug Collision Resolution**| **YES** | NO | Real regex sanitization and collision resolver in `utils/slug.py` appending `-2`, `-3`. |
| **Public Blog Page** | **YES** | NO | Real route at `GET /blog/{slug}` rendering live content and returning 404 for unpublished items. |
| **External CMS (Shopify/WP)**| NO | **NOT IMPLEMENTED** | System publishes internally to SQLite; no external webhook or CMS exporter exists yet. |
| **External Search APIs** | NO | **NOT IMPLEMENTED** | No live API connection to Google Search Console, Ahrefs, or Semrush exists. |
| **User Authentication** | NO | **NOT IMPLEMENTED** | No login, session cookies, or JWT tokens exist; endpoints are currently open. |
| **Analytics Tracking** | NO | **NOT IMPLEMENTED** | Post-publication pageviews or revenue attribution tracking is not yet implemented. |

---

## Part 14 — Production Readiness & Risk Audit

### Risks Breakdown

#### 1. CRITICAL RISKS (Blocks production deployment)
- **Zero Authentication / Authorization**:
  - *Exact File*: `backend/app/main.py`
  - *Why it matters*: Any user with network access to the API can delete products, approve low-quality drafts, or unpublish active articles.
  - *How it could fail*: An unauthorized visitor could send `DELETE /products/1` or `POST /published-content/1/unpublish`.
  - *Suggested fix*: Add JWT authentication or API key middleware (e.g. FastAPI `OAuth2PasswordBearer` or `Security(APIKeyHeader)`).
  - *Blocks production?*: **YES.** Must be added before deploying to a public domain.

#### 2. HIGH RISKS (Must be addressed before scaling)
- **Simulated Search Volumes**:
  - *Exact File*: `backend/app/database/seed.py`
  - *Why it matters*: Editorial decisions are being made based on mock seed numbers rather than verified customer search demand.
  - *How it could fail*: Store could publish articles for topics that have zero actual search demand on Google.
  - *Suggested fix*: Connect a keyword provider API (e.g. Google Keyword Planner or DataForSEO).
  - *Blocks production?*: No for internal testing; **YES** for autonomous marketing ROI.
- **Single-File SQLite Database Concurrency**:
  - *Exact File*: `backend/app/database/connection.py`
  - *Why it matters*: SQLite locks the entire database file during write transactions.
  - *How it could fail*: Under multiple simultaneous editors or background workers, requests could throw `sqlite3.OperationalError: database is locked`.
  - *Suggested fix*: For high-concurrency multi-user production, migrate `connection.py` to PostgreSQL.
  - *Blocks production?*: No for single-editor MVP; Yes for multi-tenant SaaS.

#### 3. MEDIUM RISKS (Performance or UX bottlenecks)
- **Deterministic Mock Drafts**:
  - *Exact File*: `backend/app/services/generators/mock_generator.py`
  - *Why it matters*: Articles generated for different products follow identical phrasing and structure.
  - *How it could fail*: Readers or search engine algorithms could detect repetitive boilerplate.
  - *Suggested fix*: Connect an LLM API key in `.env` (`AI_PROVIDER=openai`, `AI_API_KEY=sk-...`) inside `ai_generator.py`.
  - *Blocks production?*: No (human can manually rewrite), but limits automation value.
- **Keyword Matching is Exact Word Overlap**:
  - *Exact File*: `backend/app/services/content_analysis_service.py`
  - *Why it matters*: Does not recognize synonyms or semantic meaning.
  - *How it could fail*: Might miss duplicate content if an existing article uses "acne" while a product says "blemish".
  - *Suggested fix*: Add vector embeddings for semantic similarity.

#### 4. LOW RISKS (Minor code hygiene)
- **Legacy Endpoint Aliases**:
  - *Exact File*: `backend/app/api/opportunities.py` (`/content-opportunities`)
  - *Why it matters*: Minor redundancy in API surface.
  - *Suggested fix*: Deprecate legacy aliases once all external consumers use `/opportunities`.

### Things That Look Risky But Are Handled Correctly
1. **Database Connection Leaks**: Handled safely via FastAPI's `Depends(get_db)` generator with `try ... finally: conn.close()`.
2. **Foreign Key Enforcement**: SQLite foreign keys are explicitly turned on via `conn.execute("PRAGMA foreign_keys = ON")` on every connection.
3. **Publishing Race Conditions**: Publishing operations are wrapped in atomic SQL transactions with explicit `conn.commit()` and `conn.rollback()` on failure.
4. **Duplicate Slugs**: Handled robustly by `generate_unique_slug` querying SQLite and appending `-2`, `-3` in a `while` loop.
5. **Editing Approved Drafts**: Prevented strictly at the database service level (`HTTP 409 Conflict`).

---

## Part 15 — Documentation Contradictions

| Documentation / Claim | Actual Implementation | Match? | Explanation |
| :--- | :--- | :---: | :--- |
| **"AI Content Intelligence"** | Deterministic procedural templating (`mock_generator.py`) | **MISMATCH** | The system currently uses smart Python templates, not a live AI model. Real AI is an architectural extension point ready for an API key. |
| **"Search Demand Data"** | Fixed seed data (12,000; 8,000; etc.) | **MISMATCH** | Search volumes are hardcoded numbers in `seed.py`, not real-time search engine data. |
| **"Publishing Content"** | Publishes internally to SQLite and `/blog/{slug}` | **MATCH (with caveat)** | It genuinely publishes to a live web page, but it does **not** publish to Shopify, WordPress, or Webflow. |
| **"Draft Approval / Rejection"** | Returns HTTP 409 on invalid status transitions | **MATCH** | Source code strictly enforces state transitions. |
| **"Content Brief Schema"** | Contains `search_intent`, `target_audience`, `suggested_sections` | **MATCH** | All specified fields are present in SQLite and Pydantic schemas. |
| **`app.py` Architecture** | Modular package in `backend/app/` with root proxy | **MATCH** | Root `app.py` re-exports `backend.app.main:app` for seamless uvicorn reloading. |

---

## Part 16 — The Simplest Possible Mental Model

# Agentify In One Picture

```text
       ┌─────────────────────────────────────────────────────────┐
       │                   YOUR STORE CATALOG                    │
       │           (What products you have to sell)              │
       └────────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │                    RESEARCH ENGINE                      │
       │    (Matches products to customer search questions &     │
       │           suppresses already-written articles)          │
       └────────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │                 EDITORIAL STUDIO & EDIT                 │
       │   (Human reviews ideas, approves briefs, polishes text) │
       └────────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │                   LIVE STORE BLOG                       │
       │             (/blog/{slug} reads to shoppers)            │
       └─────────────────────────────────────────────────────────┘
```

> **Agentify is basically an automated SEO content assembly line for an ecommerce store.** It looks at what products you sell, finds the most popular questions customers search on Google, and checks that you haven't already answered them. It then drafts complete, ready-to-read guides with product recommendations and hands them to you for review. Once you approve the draft, it publishes the article directly to your store's blog with a clean web address. In short: it automates the research, outline, and drafting so you only have to review and approve.

---

## Part 17 — How I Should Learn Agentify

To master Agentify without feeling overwhelmed, follow this 8-stage learning path:

### Stage 1 — Understand the Product
- Read: `README.md`
- Inspect: `frontend/src/pages/DashboardPage.tsx` (Look at the visual pipeline bar and KPI cards).

### Stage 2 — Understand the Article Lifecycle
- Inspect: `backend/tests/test_e2e_workflow.py` (Read this test from top to bottom; it walks through every single step in 50 lines of Python).

### Stage 3 — Understand the Frontend
- Inspect: `frontend/src/App.tsx` (See how view switching works).
- Inspect: `frontend/src/api/client.ts` (See all API calls made by the browser).

### Stage 4 — Understand the Backend
- Inspect: `backend/app/main.py` (See how FastAPI mounts the routers).
- Inspect: `backend/app/api/opportunities.py` (See how an endpoint accepts a request and delegates to a service).

### Stage 5 — Understand the Database
- Inspect: `backend/app/database/schema.py` (Review the 8 tables and foreign key constraints).
- Inspect: `backend/app/database/seed.py` (Review the demo products and keywords).

### Stage 6 — Understand the Research Engine
- Inspect: `backend/app/services/content_analysis_service.py` (See how stopwords are removed and duplicates detected).
- Inspect: `backend/app/services/opportunity_service.py` (See the exact 100-point scoring formula).

### Stage 7 — Understand Content Generation
- Inspect: `backend/app/services/generators/mock_generator.py` (See how articles are generated from brief outlines).
- Inspect: `backend/app/services/generators/ai_generator.py` (See where real AI can be plugged in).

### Stage 8 — Understand Publishing
- Inspect: `backend/app/utils/slug.py` (See how URLs are cleaned and deduplicated).
- Inspect: `backend/app/services/publishing_service.py` (See the atomic database publishing transaction).
- Inspect: `frontend/src/pages/PublicArticlePage.tsx` (See how live articles are rendered at `/blog/{slug}`).

---

*Document created: September 2026 | Version: 1.0.0-MVP*
