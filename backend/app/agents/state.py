"""
Research State — the single source of truth for a research run.

This module defines what the agent knows at any point in time:
  - What store is being researched
  - What evidence has been collected
  - What products/keywords/content the system has observed
  - How many iterations have been used
  - What the budget limits are
  - Whether enough evidence exists to generate opportunities

The state is serializable (Pydantic model) and does NOT depend on
FastAPI request objects or database connections.

Design principle: Python is responsible for building and mutating this state.
The LLM only reads it and returns structured decisions.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Evidence types — every meaningful external/internal observation
# ---------------------------------------------------------------------------

class EvidenceType(str, Enum):
    """The semantic category of a piece of evidence."""
    STORE_PRODUCT = "store_product"
    KEYWORD = "keyword"
    EXISTING_CONTENT = "existing_content"
    SEARCH_RESULT = "search_result"
    COMPETITOR_DOMAIN = "competitor_domain"
    COMPETITOR_PAGE = "competitor_page"
    SEARCH_CONSOLE = "search_console"
    TOPIC_CLUSTER = "topic_cluster"
    CONTENT_GAP = "content_gap"


class SourceType(str, Enum):
    """Where the evidence came from."""
    STORE_DATABASE = "store_database"
    KEYWORD_PROVIDER = "keyword_provider"
    SEARCH_PROVIDER = "search_provider"
    SHOPIFY = "shopify"
    GOOGLE_SEARCH_CONSOLE = "google_search_console"
    WEB_RESEARCH = "web_research"
    INTERNAL = "internal"


class EvidenceItem(BaseModel):
    """
    A single piece of research evidence.

    Every meaningful observation — product found, keyword discovered,
    competitor identified, search query seen — becomes an EvidenceItem.
    This allows the system to explain WHY an opportunity was recommended:
    'Because we found evidence items ev_1, ev_3, ev_7.'
    """
    id: str = Field(default_factory=lambda: f"ev_{uuid.uuid4().hex[:8]}")
    evidence_type: EvidenceType
    source_type: SourceType
    source_reference: str = ""           # e.g. "keywords table", "shopify_api"
    data: dict[str, Any] = Field(default_factory=dict)
    reliability: float = 1.0            # 0.0–1.0; do NOT invent this — only set from real signals
    collected_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    research_run_id: Optional[int] = None
    store_id: Optional[str] = None
    notes: str = ""                      # Optional human-readable summary


# ---------------------------------------------------------------------------
# Research budget — hard limits that prevent runaway loops
# ---------------------------------------------------------------------------

class ResearchBudget(BaseModel):
    """
    Hard limits on what the research loop is allowed to do.

    Once any limit is reached, the orchestrator must stop gracefully
    and record the reason. These are not soft suggestions.
    """
    max_iterations: int = 5
    max_searches: int = 10
    max_domains: int = 5
    max_pages: int = 50
    max_runtime_seconds: int = 120

    # Future cost controls (track but don't enforce yet)
    max_llm_calls: Optional[int] = None
    max_tokens: Optional[int] = None
    max_cost_usd: Optional[float] = None

    # Current usage counters (mutated by orchestrator)
    iterations_used: int = 0
    searches_used: int = 0
    domains_analyzed: int = 0
    pages_analyzed: int = 0
    llm_calls_used: int = 0
    tokens_used: int = 0
    cost_usd: float = 0.0
    started_at: Optional[str] = None

    def is_exhausted(self) -> tuple[bool, str]:
        """
        Check if any hard budget limit has been reached.
        Returns (exhausted: bool, reason: str).
        """
        if self.iterations_used >= self.max_iterations:
            return True, f"max_iterations reached ({self.max_iterations})"
        if self.searches_used >= self.max_searches:
            return True, f"max_searches reached ({self.max_searches})"
        if self.domains_analyzed >= self.max_domains:
            return True, f"max_domains reached ({self.max_domains})"
        if self.pages_analyzed >= self.max_pages:
            return True, f"max_pages reached ({self.max_pages})"
        if self.started_at and self.max_runtime_seconds:
            elapsed = (
                datetime.now(timezone.utc)
                - datetime.fromisoformat(self.started_at)
            ).total_seconds()
            if elapsed >= self.max_runtime_seconds:
                return True, f"max_runtime_seconds reached ({self.max_runtime_seconds}s)"
        return False, ""

    def remaining_summary(self) -> dict[str, Any]:
        """Return a human-readable budget summary for the UI."""
        return {
            "iterations": f"{self.iterations_used}/{self.max_iterations}",
            "searches": f"{self.searches_used}/{self.max_searches}",
            "domains": f"{self.domains_analyzed}/{self.max_domains}",
            "pages": f"{self.pages_analyzed}/{self.max_pages}",
        }


# ---------------------------------------------------------------------------
# Research status
# ---------------------------------------------------------------------------

class ResearchStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    EVIDENCE_SUFFICIENT = "evidence_sufficient"
    BUDGET_EXHAUSTED = "budget_exhausted"
    MAX_ITERATIONS_REACHED = "max_iterations_reached"
    FAILED = "failed"
    COMPLETED = "completed"
    STOPPED = "stopped"


# ---------------------------------------------------------------------------
# Opportunity draft — intermediate representation before DB storage
# ---------------------------------------------------------------------------

class ConfidenceLevel(str, Enum):
    STRONG = "strong"
    MODERATE = "moderate"
    EXPLORATORY = "exploratory"


class OpportunityDraft(BaseModel):
    """
    An intermediate opportunity representation produced by the planner/LLM.
    This is NOT a database record — it becomes one after human review.
    """
    topic: str
    primary_keyword: str
    search_intent: str = "informational"     # informational | commercial | transactional | navigational
    why_it_matters: str                       # Evidence-backed explanation (not just a score)
    evidence_ids: list[str] = Field(default_factory=list)  # IDs of supporting EvidenceItems
    supporting_evidence: list[str] = Field(default_factory=list)  # Human-readable bullets
    missing_evidence: list[str] = Field(default_factory=list)     # What we don't know yet
    confidence_level: ConfidenceLevel = ConfidenceLevel.EXPLORATORY

    # Backward-compatible fields for existing DB schema
    title: str = ""                          # Set to topic if empty
    reason: str = ""                         # Set to why_it_matters if empty
    search_volume: int = 0
    confidence: str = "medium"               # legacy: high/medium/low


# ---------------------------------------------------------------------------
# The main research state
# ---------------------------------------------------------------------------

class ResearchState(BaseModel):
    """
    The complete knowledge state of a research run.

    This is the single source of truth passed between the planner
    and orchestrator on every iteration. It answers:
      - What do we know?
      - What have we done?
      - What are our constraints?
      - What have we found so far?

    The state is serializable (no FastAPI/DB objects).
    The orchestrator is responsible for loading data from the DB
    and converting it into evidence items before storing in state.
    """

    # Identity
    research_run_id: Optional[int] = None
    store_id: str = "demo-store"
    goal: str = "Find content opportunities"

    # Evidence — the core of the evidence-first architecture
    evidence: list[EvidenceItem] = Field(default_factory=list)

    # Raw data loaded from the store/DB (separate from evidence for clarity)
    products: list[dict[str, Any]] = Field(default_factory=list)
    keywords: list[dict[str, Any]] = Field(default_factory=list)
    existing_content: list[dict[str, Any]] = Field(default_factory=list)
    competitors: list[dict[str, Any]] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)

    # Opportunities generated so far (intermediate, not yet in DB)
    opportunities: list[OpportunityDraft] = Field(default_factory=list)

    # Iteration tracking
    iteration: int = 0
    research_budget: ResearchBudget = Field(default_factory=ResearchBudget)

    # Status and audit trail
    status: ResearchStatus = ResearchStatus.PENDING
    stop_reason: str = ""
    actions_taken: list[dict[str, Any]] = Field(default_factory=list)  # audit log

    # Errors encountered (non-fatal — we log and continue)
    errors: list[str] = Field(default_factory=list)

    def add_evidence(self, item: EvidenceItem) -> None:
        """Add an evidence item, stamping run ID and store ID."""
        item.research_run_id = self.research_run_id
        item.store_id = self.store_id
        self.evidence.append(item)

    def has_evidence_of_type(self, evidence_type: EvidenceType) -> bool:
        """Check whether any evidence of a given type has been collected."""
        return any(e.evidence_type == evidence_type for e in self.evidence)

    def evidence_count_by_type(self) -> dict[str, int]:
        """Return a count of evidence items by type (useful for planner decisions)."""
        counts: dict[str, int] = {}
        for item in self.evidence:
            key = item.evidence_type.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    def get_evidence_by_ids(self, ids: list[str]) -> list[EvidenceItem]:
        """Retrieve specific evidence items by their IDs."""
        id_set = set(ids)
        return [e for e in self.evidence if e.id in id_set]

    def record_action(self, action_type: str, arguments: dict, result_summary: str, status: str = "completed") -> None:
        """Add an action to the audit trail."""
        self.actions_taken.append({
            "iteration": self.iteration,
            "action_type": action_type,
            "arguments": arguments,
            "result_summary": result_summary,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def is_evidence_sufficient(self) -> bool:
        """
        Deterministic check: do we have enough evidence to generate opportunities?

        Policy: We need at minimum:
          - At least one product (we know what the store sells)
          - At least one keyword (we have some demand signal)
          - Existing content analyzed (we checked for duplicates)

        The planner can override this with LLM reasoning for nuanced cases.
        """
        has_products = self.has_evidence_of_type(EvidenceType.STORE_PRODUCT)
        has_keywords = self.has_evidence_of_type(EvidenceType.KEYWORD)
        has_content_check = self.has_evidence_of_type(EvidenceType.EXISTING_CONTENT)
        return has_products and has_keywords and has_content_check

    def to_summary_dict(self) -> dict[str, Any]:
        """Return a concise summary for API responses and logging."""
        return {
            "research_run_id": self.research_run_id,
            "store_id": self.store_id,
            "goal": self.goal,
            "iteration": self.iteration,
            "status": self.status.value,
            "stop_reason": self.stop_reason,
            "evidence_count": len(self.evidence),
            "evidence_by_type": self.evidence_count_by_type(),
            "opportunities_found": len(self.opportunities),
            "actions_taken": len(self.actions_taken),
            "budget": self.research_budget.remaining_summary(),
            "errors": self.errors,
        }
