"""
Research Planner — decides what to do next based on current state.

RESPONSIBILITIES:
  1. Evaluate whether enough evidence exists (deterministic check)
  2. If not, select the best next action from the permitted set
  3. Check that the selected action fits within the budget
  4. Return a structured PlannerDecision

PHASE 1 (current): Deterministic rule-based planner.
  No LLM required. The planner follows a fixed priority order:
    1. If no products → ANALYZE_STORE
    2. If no existing content → ANALYZE_EXISTING_CONTENT
    3. If no keywords → DISCOVER_KEYWORDS
    4. If evidence sufficient → GENERATE_OPPORTUNITIES
    5. If budget exhausted → STOP
    6. Otherwise → STOP (nothing new to gather without search)

PHASE 5 (future): LLM-augmented planner.
  The LLM will receive the state and produce a PlannerDecision.
  Python validates it, checks the budget, and only then executes.
  The deterministic fallback remains for when the LLM is unavailable.

NOTE: The planner never executes actions — it only decides.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from backend.app.agents.actions import (
    ActionType,
    PlannerDecision,
    PlannerDecisionType,
    ResearchAction,
)
from backend.app.agents.state import EvidenceType, ResearchState

if TYPE_CHECKING:
    pass  # avoid circular imports

logger = logging.getLogger(__name__)


class ResearchPlanner:
    """
    Decides what research action to take next.

    The planner is stateless — it receives the current ResearchState
    and returns a PlannerDecision. It does not modify state.

    This makes it trivially testable: given a state, assert the decision.
    """

    def decide(self, state: ResearchState) -> PlannerDecision:
        """
        Main entry point. Returns the next PlannerDecision.

        Called by the orchestrator on every iteration.
        """
        logger.info(
            "Planner deciding (iteration=%d, evidence=%d items, status=%s)",
            state.iteration,
            len(state.evidence),
            state.status.value,
        )

        # 1. Check budget first — never start something we can't afford
        exhausted, reason = state.research_budget.is_exhausted()
        if exhausted:
            logger.warning("Budget exhausted: %s", reason)
            return PlannerDecision(
                decision=PlannerDecisionType.STOP,
                reason=f"Research budget exhausted: {reason}",
            )

        # 2. Apply deterministic rules in priority order
        return self._apply_rules(state)

    def _apply_rules(self, state: ResearchState) -> PlannerDecision:
        """
        Deterministic priority rules for Phase 1.

        Priority order:
          1. Know what the store sells (ANALYZE_STORE)
          2. Know what content exists (ANALYZE_EXISTING_CONTENT)
          3. Know what customers search for (DISCOVER_KEYWORDS)
          4. If all three present → generate opportunities
          5. Stop if nothing else to do

        This is the minimum viable evidence set. The LLM planner (Phase 5)
        will extend this with nuanced reasoning like:
          - "We have keywords but they're all generic — SEARCH_WEB for specifics"
          - "We have no competitor data — DISCOVER_COMPETITORS"
        """
        budget = state.research_budget

        has_products = state.has_evidence_of_type(EvidenceType.STORE_PRODUCT)
        has_keywords = state.has_evidence_of_type(EvidenceType.KEYWORD)
        has_content = state.has_evidence_of_type(EvidenceType.EXISTING_CONTENT)

        # Rule 1: Load store products first — we must know what we sell
        if not has_products:
            action = ResearchAction(
                action_type=ActionType.ANALYZE_STORE,
                arguments={},
                reason="No product evidence found. Must analyze store catalog before anything else.",
            )
            allowed, reason = action.can_execute(budget)
            if not allowed:
                return PlannerDecision(
                    decision=PlannerDecisionType.STOP,
                    reason=f"Cannot analyze store — budget constraint: {reason}",
                )
            return PlannerDecision(
                decision=PlannerDecisionType.RESEARCH_MORE,
                reason="Store products not yet loaded into evidence.",
                action=action,
            )

        # Rule 2: Check existing content — avoid duplicate opportunities
        if not has_content:
            action = ResearchAction(
                action_type=ActionType.ANALYZE_EXISTING_CONTENT,
                arguments={},
                reason="Must audit existing content before generating opportunities to prevent duplicates.",
            )
            allowed, reason = action.can_execute(budget)
            if not allowed:
                return PlannerDecision(
                    decision=PlannerDecisionType.STOP,
                    reason=f"Cannot analyze existing content — budget constraint: {reason}",
                )
            return PlannerDecision(
                decision=PlannerDecisionType.RESEARCH_MORE,
                reason="Existing content not yet audited.",
                action=action,
            )

        # Rule 3: Discover keyword demand — we need search signals
        if not has_keywords:
            action = ResearchAction(
                action_type=ActionType.DISCOVER_KEYWORDS,
                arguments={},
                reason="No keyword demand evidence. Searching for keyword signals related to store products.",
            )
            allowed, reason = action.can_execute(budget)
            if not allowed:
                return PlannerDecision(
                    decision=PlannerDecisionType.STOP,
                    reason=f"Cannot discover keywords — budget constraint: {reason}",
                )
            return PlannerDecision(
                decision=PlannerDecisionType.RESEARCH_MORE,
                reason="No keyword demand evidence collected yet.",
                action=action,
            )

        # Rule 4: All minimum evidence present → generate opportunities
        if state.is_evidence_sufficient():
            logger.info(
                "Evidence sufficient: products=%d, keywords=%d, content_items=%d",
                sum(1 for e in state.evidence if e.evidence_type == EvidenceType.STORE_PRODUCT),
                sum(1 for e in state.evidence if e.evidence_type == EvidenceType.KEYWORD),
                sum(1 for e in state.evidence if e.evidence_type == EvidenceType.EXISTING_CONTENT),
            )
            return PlannerDecision(
                decision=PlannerDecisionType.GENERATE_OPPORTUNITIES,
                reason=(
                    "Sufficient evidence collected: store products, keyword demand signals, "
                    "and existing content audit are all present. Ready to generate opportunities."
                ),
            )

        # Rule 5: Fallback stop — no obvious next step
        # (In Phase 5, the LLM planner would decide to SEARCH_WEB or DISCOVER_COMPETITORS here)
        return PlannerDecision(
            decision=PlannerDecisionType.STOP,
            reason="No additional deterministic research steps available. Consider enabling search or competitor discovery.",
        )

    def explain(self, state: ResearchState) -> dict:
        """
        Return a human-readable explanation of the current evidence state.
        Useful for the UI's 'Why did it stop?' panel.
        """
        return {
            "has_products": state.has_evidence_of_type(EvidenceType.STORE_PRODUCT),
            "has_keywords": state.has_evidence_of_type(EvidenceType.KEYWORD),
            "has_existing_content": state.has_evidence_of_type(EvidenceType.EXISTING_CONTENT),
            "has_competitor_data": state.has_evidence_of_type(EvidenceType.COMPETITOR_DOMAIN),
            "evidence_sufficient": state.is_evidence_sufficient(),
            "budget_exhausted": state.research_budget.is_exhausted()[0],
            "evidence_counts": state.evidence_count_by_type(),
        }
