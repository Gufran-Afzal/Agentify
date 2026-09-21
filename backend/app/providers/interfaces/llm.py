"""
LLM Provider Interface — the contract all LLM implementations must fulfill.

DESIGN PRINCIPLE:
  The rest of the application imports LLMProvider, not GeminiLLMProvider.
  This means switching from Gemini to any other LLM requires only:
    1. Write a new class implementing LLMProvider
    2. Update the factory in provider_factory.py

  No service file, no orchestrator file, no test file needs to change.

METHODS:
  - plan_research: Given a state, decide what to do next (Phase 5 LLM planning)
  - extract_topics: Extract key topics from product/content text
  - classify_search_intent: Classify a query/topic into intent category
  - qualify_competitor: Assess if a domain is a real competitor
  - generate_opportunities: Produce evidence-backed opportunity drafts
  - generate_content_brief: Expand an opportunity into a structured brief
  - generate_draft: Write a full article draft from a brief

FALLBACK CONTRACT:
  Every method MUST have a graceful fallback path that does not raise
  an exception when the LLM is unavailable, rate-limited, or key-missing.
  The system must remain usable at all times.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from backend.app.agents.actions import PlannerDecision
    from backend.app.agents.state import OpportunityDraft, ResearchState


class LLMProvider(ABC):
    """
    Abstract base class for all LLM providers.

    Implementations: GeminiLLMProvider, MockLLMProvider
    """

    @abstractmethod
    def is_available(self) -> bool:
        """
        Return True if the provider is configured and reachable.
        Used by services to decide whether to use real LLM or fall back.
        """
        ...

    @abstractmethod
    def plan_research(self, state: "ResearchState") -> "PlannerDecision":
        """
        Given the current research state, decide what action to take next.

        Phase 1: Not called (deterministic planner handles this).
        Phase 5: Called by the planner when deterministic rules don't resolve.

        Must return a valid PlannerDecision even if the LLM fails.
        """
        ...

    @abstractmethod
    def extract_topics(self, text: str, context: Optional[str] = None) -> list[str]:
        """
        Extract key topics/themes from a block of text (product description,
        existing article, etc.).

        Returns an empty list if the LLM is unavailable.
        """
        ...

    @abstractmethod
    def classify_search_intent(self, topic: str) -> str:
        """
        Classify a topic/query into one of:
          informational | commercial | transactional | navigational

        Returns 'informational' as default if LLM is unavailable.
        """
        ...

    @abstractmethod
    def qualify_competitor(
        self,
        domain: str,
        store_products: list[str],
        context: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Assess whether a domain is a real competitor.

        Returns:
          {
            "is_competitor": bool,
            "competitor_type": "business|content|search|none",
            "reason": str,
            "relevant_topics": list[str]
          }

        Returns a safe non-competitor result if LLM is unavailable.
        """
        ...

    @abstractmethod
    def generate_opportunities(
        self,
        state: "ResearchState",
    ) -> list["OpportunityDraft"]:
        """
        Generate evidence-backed content opportunity drafts from research state.

        Phase 1: Not called (orchestrator's _execute_generate_opportunities handles this).
        Phase 5: Called when we want LLM-enhanced reasoning about opportunities.

        Returns empty list if LLM is unavailable (fall back to deterministic).
        """
        ...

    @abstractmethod
    def generate_content_brief(
        self,
        opportunity: dict[str, Any],
        evidence: list[dict[str, Any]],
        store_context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Generate a structured content brief for an approved opportunity.

        Returns a dict with keys matching ContentBrief schema.
        Returns a minimal deterministic brief if LLM is unavailable.
        """
        ...

    @abstractmethod
    def generate_draft(
        self,
        brief: dict[str, Any],
        evidence: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, str]:
        """
        Generate a full article draft from a content brief.

        Returns dict with keys: title, introduction, body, conclusion.
        Returns mock content if LLM is unavailable.
        """
        ...
