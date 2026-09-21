"""
Research Actions — the finite set of operations the agent can request.

ARCHITECTURAL PRINCIPLE:
  The LLM may ONLY select from this predefined list of actions.
  It may NEVER execute arbitrary Python, shell commands, or network calls.
  Python executes actions; the LLM selects them.

Each action has:
  - A type (from the ActionType enum)
  - Arguments (validated by Pydantic)
  - A reason (why the planner chose it — for observability)
  - Optional estimated cost (future billing/rate-limit awareness)

The PlannerDecision wraps the action selection with a top-level
decision: research_more | generate_opportunities | stop.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Action types — the complete, bounded vocabulary of agent operations
# ---------------------------------------------------------------------------

class ActionType(str, Enum):
    """
    The complete set of permitted research actions.

    Adding a new capability requires adding it here first, then
    implementing its executor in the orchestrator. This ensures
    the LLM can never request an action that hasn't been reviewed.
    """
    ANALYZE_STORE = "ANALYZE_STORE"
    ANALYZE_EXISTING_CONTENT = "ANALYZE_EXISTING_CONTENT"
    DISCOVER_KEYWORDS = "DISCOVER_KEYWORDS"
    SEARCH_WEB = "SEARCH_WEB"
    DISCOVER_COMPETITORS = "DISCOVER_COMPETITORS"
    ANALYZE_COMPETITOR = "ANALYZE_COMPETITOR"
    GENERATE_OPPORTUNITIES = "GENERATE_OPPORTUNITIES"
    STOP = "STOP"


# ---------------------------------------------------------------------------
# Budget requirements per action type
# ---------------------------------------------------------------------------

# How much of each budget resource each action consumes
ACTION_COSTS: dict[ActionType, dict[str, int]] = {
    ActionType.ANALYZE_STORE: {
        "iterations": 1,
        "searches": 0,
        "domains": 0,
        "pages": 0,
    },
    ActionType.ANALYZE_EXISTING_CONTENT: {
        "iterations": 1,
        "searches": 0,
        "domains": 0,
        "pages": 0,
    },
    ActionType.DISCOVER_KEYWORDS: {
        "iterations": 1,
        "searches": 1,
        "domains": 0,
        "pages": 0,
    },
    ActionType.SEARCH_WEB: {
        "iterations": 1,
        "searches": 3,
        "domains": 3,
        "pages": 10,
    },
    ActionType.DISCOVER_COMPETITORS: {
        "iterations": 1,
        "searches": 2,
        "domains": 5,
        "pages": 5,
    },
    ActionType.ANALYZE_COMPETITOR: {
        "iterations": 1,
        "searches": 0,
        "domains": 1,
        "pages": 5,
    },
    ActionType.GENERATE_OPPORTUNITIES: {
        "iterations": 1,
        "searches": 0,
        "domains": 0,
        "pages": 0,
    },
    ActionType.STOP: {
        "iterations": 0,
        "searches": 0,
        "domains": 0,
        "pages": 0,
    },
}


# ---------------------------------------------------------------------------
# Research action model
# ---------------------------------------------------------------------------

class ResearchAction(BaseModel):
    """
    A single, validated action selected by the planner.

    The orchestrator receives this and routes it to the appropriate
    deterministic tool/service. The LLM never sees the tool output directly —
    it only sees the evidence that Python extracted from it.
    """
    action_type: ActionType
    arguments: dict[str, Any] = Field(default_factory=dict)
    reason: str = ""               # Why the planner chose this action
    estimated_cost: Optional[dict[str, Any]] = None   # Future: token/$ estimates

    def budget_cost(self) -> dict[str, int]:
        """Return how much of each budget resource this action will consume."""
        return ACTION_COSTS.get(self.action_type, {})

    def can_execute(self, budget: "ResearchBudget") -> tuple[bool, str]:  # type: ignore[name-defined]  # noqa
        """
        Check whether the budget allows this action to be executed.
        Returns (allowed: bool, reason: str).
        """
        from backend.app.agents.state import ResearchBudget  # local import to avoid circular

        costs = self.budget_cost()

        if budget.iterations_used + costs.get("iterations", 0) > budget.max_iterations:
            return False, f"Action would exceed max_iterations ({budget.max_iterations})"

        if budget.searches_used + costs.get("searches", 0) > budget.max_searches:
            return False, f"Action would exceed max_searches ({budget.max_searches})"

        if budget.domains_analyzed + costs.get("domains", 0) > budget.max_domains:
            return False, f"Action would exceed max_domains ({budget.max_domains})"

        if budget.pages_analyzed + costs.get("pages", 0) > budget.max_pages:
            return False, f"Action would exceed max_pages ({budget.max_pages})"

        return True, "ok"


# ---------------------------------------------------------------------------
# Planner decision model
# ---------------------------------------------------------------------------

class PlannerDecisionType(str, Enum):
    RESEARCH_MORE = "research_more"
    GENERATE_OPPORTUNITIES = "generate_opportunities"
    STOP = "stop"


class PlannerDecision(BaseModel):
    """
    The structured output of the research planner.

    The planner always returns one of three top-level decisions:
      1. research_more  — with a specific, budget-permitted action
      2. generate_opportunities — enough evidence exists, proceed
      3. stop — nothing useful to do, or an error occurred

    This is validated by Pydantic, so malformed LLM output is caught
    before it reaches the orchestrator.

    Example (RESEARCH_MORE):
      {
        "decision": "research_more",
        "reason": "Products loaded but no keyword evidence yet.",
        "action": {"action_type": "DISCOVER_KEYWORDS", "arguments": {}}
      }

    Example (GENERATE_OPPORTUNITIES):
      {
        "decision": "generate_opportunities",
        "reason": "Product, keyword, and content-audit evidence present."
      }
    """
    decision: PlannerDecisionType
    reason: str
    action: Optional[ResearchAction] = None   # Required when decision == research_more

    def is_terminal(self) -> bool:
        """True if this decision ends the research loop."""
        return self.decision in (
            PlannerDecisionType.GENERATE_OPPORTUNITIES,
            PlannerDecisionType.STOP,
        )
